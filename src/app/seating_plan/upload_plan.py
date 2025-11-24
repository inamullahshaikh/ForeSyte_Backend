# routers/seating_plan.py
from fastapi import APIRouter, File, UploadFile, Query, Depends, HTTPException
from sqlalchemy.orm import Session
import pdfplumber
import re
import io
from datetime import datetime, date, time as dt_time
from pathlib import Path
import time
import json
import cv2
import numpy as np
from typing import List, Dict, Optional

from database.db import get_db
from database.models import Exam, Room, Seat, Student
from .room_config import RoomConfigManager, SeatMapManager, CCTVFrameManager

router = APIRouter(prefix="/seating-plan", tags=["Seating Plan"])

# Global store for latest extracted room
latest_room_data = {}

# Paths for storage and visualization
EXTRACTIONS_DIR = Path("./app/seating_plan/extractions")
EXTRACTIONS_DIR.mkdir(exist_ok=True, parents=True)

# Initialize managers
room_config_manager = RoomConfigManager()
seat_map_manager = SeatMapManager()
cctv_manager = CCTVFrameManager()

# -------- Utility Functions --------
def normalize_time_slot(time_str):
    if not time_str:
        return None
    normalized = re.sub(r'\s+', ' ', time_str.strip().lower())
    normalized = normalized.replace('a.m.', 'am').replace('p.m.', 'pm')
    return normalized

def time_slots_match(time1, time2):
    if not time1 or not time2:
        return False
    return normalize_time_slot(time1) == normalize_time_slot(time2)

def parse_date_time(date_str: str, time_str: str):
    """Parse date and time strings into Python date and time objects."""
    # Parse date (e.g., "January 15, 2024")
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})', date_str, re.IGNORECASE)
    if date_match:
        month_name = date_match.group(1).lower()[:3]
        day = int(date_match.group(2))
        year = int(date_match.group(3))
        month = months.get(month_name, 1)
        exam_date = date(year, month, day)
    else:
        exam_date = date.today()
    
    # Parse time (e.g., "10:20 AM to 11:20 AM")
    time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_str, re.IGNORECASE)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        am_pm = time_match.group(3).upper()
        if am_pm == 'PM' and hour != 12:
            hour += 12
        elif am_pm == 'AM' and hour == 12:
            hour = 0
        start_time = dt_time(hour, minute)
        
        # Parse end time
        end_match = re.search(r'to\s+(\d{1,2}):(\d{2})\s*(AM|PM)', time_str, re.IGNORECASE)
        if end_match:
            end_hour = int(end_match.group(1))
            end_minute = int(end_match.group(2))
            end_am_pm = end_match.group(3).upper()
            if end_am_pm == 'PM' and end_hour != 12:
                end_hour += 12
            elif end_am_pm == 'AM' and end_hour == 12:
                end_hour = 0
            end_time = dt_time(end_hour, end_minute)
        else:
            end_time = dt_time(hour + 2, minute)  # Default 2 hours
    else:
        start_time = dt_time(9, 0)
        end_time = dt_time(12, 0)
    
    return exam_date, start_time, end_time


# -------- Main Endpoint --------
@router.post("/upload-seating-plan")
async def upload_seating_plan(
    file: UploadFile = File(...),
    room_no: str = Query(None, description="Room number to extract, e.g. C-301"),
    time_slot: str = Query(None, description="Time slot to extract, e.g. 10:20 AM to 11:20 AM"),
    db: Session = Depends(get_db)
):
    global latest_room_data
    process_start_time = time.time()

    try:
        # --- Read PDF ---
        pdf_bytes = await file.read()
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        text = re.sub(r'\s+', ' ', text)

        # --- Extract blocks based on date/time ---
        block_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)?\s*to\s*\d{1,2}:\d{2}\s*(?:AM|PM)?.*?)(?=(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4}|$)'
        all_blocks = re.finditer(block_pattern, text, re.IGNORECASE | re.DOTALL)

        matching_exams = []

        for block_match in all_blocks:
            block_text = block_match.group(1)

            # --- Extract date, time, room ---
            date_time_match = re.search(
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4})\s+(\d{1,2}:\d{2}\s*(?:AM|PM)?\s*to\s*\d{1,2}:\d{2}\s*(?:AM|PM)?)',
                block_text,
                re.IGNORECASE
            )
            room_match = re.search(r'Room\s*No\.?\s*([A-Z]-\d+)', block_text, re.IGNORECASE)
            if not date_time_match or not room_match:
                continue

            exam_date = date_time_match.group(1)
            exam_time = date_time_match.group(2)
            detected_room = room_match.group(1).strip()

            # Filter by room/time
            room_matches = detected_room.upper() == room_no.upper() if room_no else True
            time_matches = time_slots_match(exam_time, time_slot) if time_slot else True
            if not (room_matches and time_matches):
                continue

            # --- Extract sections ---
            section_header_pattern = r'((?:CS|EE|SE|AI|DS|SS|CY|MG|MT)\d{4}\s*-\s*.+?\s+[A-Z0-9-]+)\s+Room No\.[A-Z]-\d+'
            headers = list(re.finditer(section_header_pattern, block_text, re.IGNORECASE))

            sections_list = []

            for i, header in enumerate(headers):
                start = header.end()
                end = headers[i+1].start() if i+1 < len(headers) else len(block_text)
                section_text = block_text[start:end]

                course_section = header.group(1).strip()
                course_match = re.match(r'((?:CS|EE|SE|AI|DS|SS|CY|MG|MT)\d{4}\s*-\s*.+)\s+([A-Z0-9-]+)', course_section)
                course_name = course_match.group(1).strip()
                section_id = course_match.group(2).strip()

                # Extract students in this section
                student_pattern = r'(\d+)\s+(\d{2}[A-Z]-\d{4})\s+([A-Za-z\s]+?)\s+(C\dR\d|Chair\d)'
                students = []
                for s_no, roll_no, name, seat in re.findall(student_pattern, section_text):
                    students.append({
                        "serial_no": s_no.strip(),
                        "roll_no": roll_no.strip(),
                        "name": name.strip(),
                        "seat_no": seat.strip()
                    })

                sections_list.append({
                    "course": course_name,
                    "section": section_id,
                    "students": students,
                    "total_students": len(students)
                })

            # --- Extract invigilator (optional fallback) ---
            invigilator_match = re.search(r'Name\s*of\s*Invigilator:\s*([A-Za-z\s]*)', block_text)
            invigilator_name = invigilator_match.group(1).strip() if invigilator_match else None

            matching_exams.append({
                "exam_date": exam_date,
                "exam_time": exam_time,
                "room_no": detected_room,
                "invigilator_name": invigilator_name,
                "sections": sections_list,
                "uploaded_at": datetime.utcnow()
            })

        if not matching_exams:
            return {"error": f"No seating plan found for room {room_no} / {time_slot}"}

        selected_exam = matching_exams[0]
        latest_room_data = selected_exam

        # Parse date and time
        exam_date, start_time, end_time = parse_date_time(
            selected_exam['exam_date'],
            selected_exam['exam_time']
        )

        # Create or find Exam
        course_name = selected_exam.get('course') or 'Unknown Course'
        existing_exam = db.query(Exam).filter(
            Exam.course == course_name,
            Exam.exam_date == exam_date,
            Exam.start_time == start_time
        ).first()

        if existing_exam:
            exam = existing_exam
        else:
            exam = Exam(
                course=course_name,
                exam_date=exam_date,
                start_time=start_time,
                end_time=end_time
            )
            db.add(exam)
            db.commit()
            db.refresh(exam)

        # Create or find Room
        room_number = selected_exam['room_no']
        room_block = room_number.split('-')[0] if '-' in room_number else None
        room_num = room_number.split('-')[1] if '-' in room_number else room_number

        existing_room = db.query(Room).filter(
            Room.room_number == room_num,
            Room.exam_id == exam.exam_id
        ).first()

        if existing_room:
            room = existing_room
        else:
            total_students = sum(len(sec.get("students", [])) for sec in selected_exam.get("sections", []))
            room = Room(
                room_number=room_num,
                block=room_block,
                total_seats=total_students,
                exam_id=exam.exam_id,
                camera_id=f"CAM-{room_number}"
            )
            db.add(room)
            db.commit()
            db.refresh(room)

        # Flatten students from all sections
        all_students = []
        for section in selected_exam.get('sections', []):
            all_students.extend(section.get('students', []))

        # Create or find Students and assign Seats
        for student_data in all_students:
            roll_number = student_data['roll_no']
            student_name = student_data['name']
            
            # Find or create student
            student = db.query(Student).filter(Student.roll_number == roll_number).first()
            if not student:
                # Generate email from roll number (fallback)
                email = f"{roll_number.lower().replace('-', '')}@nu.edu.pk"
                student = Student(
                    name=student_name,
                    email=email,
                    roll_number=roll_number
                )
                db.add(student)
                db.commit()
                db.refresh(student)

            # Create or update seat assignment
            seat_number = student_data['seat_no']
            existing_seat = db.query(Seat).filter(
                Seat.room_id == room.room_id,
                Seat.seat_number == seat_number
            ).first()

            if existing_seat:
                existing_seat.student_id = student.student_id
            else:
                seat = Seat(
                    room_id=room.room_id,
                    seat_number=seat_number,
                    student_id=student.student_id
                )
                db.add(seat)
        
        db.commit()

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        json_filename = f"seating_plan_{selected_exam['room_no']}_{timestamp}.json"
        json_path = EXTRACTIONS_DIR / json_filename
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(selected_exam, f, indent=4, default=str)

        # --- Visualize seat map using room configuration ---
        room_id = selected_exam['room_no']
        room_config = room_config_manager.get_or_create_config(room_id)
        
        # Get CCTV frame for this room
        cctv_path = cctv_manager.get_frame_path(room_id)
        if not cctv_path or not cctv_path.exists():
            raise FileNotFoundError(f"Could not load CCTV image for room {room_id}. Please upload a CCTV frame for this room.")
        
        frame = cv2.imread(str(cctv_path))
        if frame is None:
            raise FileNotFoundError(f"Could not load CCTV image from {cctv_path}")

        # Get seat map for this room
        seat_map = seat_map_manager.get_seat_map(room_id)
        if not seat_map:
            raise FileNotFoundError(f"Could not load seat map for room {room_id}. Please configure a seat map for this room.")

        def find_student(seat_id: str) -> Optional[Dict]:
            """Find student assigned to a seat"""
            # Normalize seat ID based on room's numbering scheme
            normalized_seat_id = seat_map_manager.normalize_seat_id(
                seat_id, 
                room_config.seat_numbering_scheme
            )
            
            # Try to match seat in seat map
            matched_seat = seat_map_manager.match_seat(
                seat_id,
                seat_map,
                room_config.seat_numbering_scheme
            )
            
            if not matched_seat:
                return None
            
            # Find student in extracted data
            seat_id_clean = seat_id.upper().strip()
            for sec in selected_exam["sections"]:
                for s in sec["students"]:
                    if s["seat_no"].upper().strip() == seat_id_clean:
                        return s
            return None

        # Scale coordinates if image resolution differs from seat map
        frame_height, frame_width = frame.shape[:2]
        seat_map_meta = seat_map_manager.get_seat_map_metadata(room_id)
        scale_x = frame_width / (seat_map_meta.get("base_w", frame_width) or frame_width)
        scale_y = frame_height / (seat_map_meta.get("base_h", frame_height) or frame_height)
        
        # Annotate frame with seat assignments
        for seat_id, points in seat_map.items():
            # Scale points to match current frame resolution
            scaled_points = [
                [int(p[0] * scale_x), int(p[1] * scale_y)] 
                for p in points
            ]
            pts = np.array(scaled_points, np.int32)
            cv2.polylines(frame, [pts], True, (0, 255, 0), 2)

            # Extract seat number from seat_id (e.g., "seat_c1r1" -> "C1R1")
            seat_number = seat_id.replace("seat_", "").upper()
            student = find_student(seat_number)
            
            if student:
                text = f"{student['name']} ({student['roll_no']})"
                color = (0, 0, 255)  # Red for assigned
            else:
                text = f"[{seat_number}]"
                color = (128, 128, 128)  # Gray for unassigned

            # Calculate center of polygon for text placement (using scaled points)
            M = cv2.moments(pts)
            if M["m00"] != 0:
                cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
            else:
                cx, cy = pts[0] if len(pts) > 0 else (0, 0)

            (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.putText(frame, text, (cx - w//2, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        annotated_filename = f"annotated_{selected_exam['room_no']}_{timestamp}.jpg"
        annotated_path = EXTRACTIONS_DIR / annotated_filename
        cv2.imwrite(str(annotated_path), frame)

        return {
            "message": f"Seating plan extracted and saved for room {selected_exam['room_no']}",
            "exam_date": selected_exam["exam_date"],
            "exam_time": selected_exam["exam_time"],
            "room_no": selected_exam["room_no"],
            "students_count": sum(len(sec.get("students", [])) for sec in selected_exam.get("sections", [])),
            "exam_id": str(exam.exam_id),
            "room_id": str(room.room_id),
            "json_file": str(json_path),
            "annotated_image": str(annotated_path),
            "processing_time": f"{time.time() - process_start_time:.2f}s",
        }


    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# --------- Utility Routes ---------
@router.get("/get-latest-room")
async def get_latest_room():
    """Get the latest extracted room data"""
    global latest_room_data
    if not latest_room_data:
        return {"error": "No seating plan extracted yet"}

    return {
        "message": f"Latest room ({latest_room_data.get('room_no')}) data fetched successfully",
        "data": latest_room_data,
    }


# --------- Room Configuration Routes ---------
@router.get("/rooms")
async def list_rooms():
    """List all configured rooms"""
    configs = room_config_manager.list_configs()
    return {
        "rooms": [config.to_dict() for config in configs],
        "total": len(configs)
    }


@router.get("/rooms/{room_id}")
async def get_room_config(room_id: str):
    """Get configuration for a specific room"""
    config = room_config_manager.get_config(room_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
    return config.to_dict()


@router.post("/rooms/{room_id}/config")
async def set_room_config(
    room_id: str,
    seat_map_path: Optional[str] = Query(None),
    cctv_frame_path: Optional[str] = Query(None),
    seat_numbering_scheme: str = Query("column_row", description="column_row, chair_number, or custom"),
    room_name: Optional[str] = Query(None)
):
    """Set or update room configuration"""
    from .room_config import RoomConfig
    
    config = room_config_manager.get_or_create_config(room_id)
    
    if seat_map_path:
        config.seat_map_path = seat_map_path
    if cctv_frame_path:
        config.cctv_frame_path = cctv_frame_path
    if seat_numbering_scheme:
        config.seat_numbering_scheme = seat_numbering_scheme
    if room_name:
        config.room_name = room_name
    
    room_config_manager.set_config(config)
    return {"message": f"Configuration updated for room {room_id}", "config": config.to_dict()}


@router.post("/rooms/{room_id}/cctv-frame")
async def upload_cctv_frame(
    room_id: str,
    file: UploadFile = File(...)
):
    """Upload CCTV frame for a room"""
    frame_data = await file.read()
    frame_path = cctv_manager.save_frame(room_id, frame_data, file.filename.split('.')[-1])
    
    # Update room config
    config = room_config_manager.get_or_create_config(room_id)
    config.cctv_frame_path = str(frame_path)
    room_config_manager.set_config(config)
    
    return {
        "message": f"CCTV frame uploaded for room {room_id}",
        "path": str(frame_path)
    }


@router.post("/rooms/{room_id}/seat-map")
async def upload_seat_map(
    room_id: str,
    seat_map_data: Dict
):
    """Upload or update seat map for a room"""
    seats = seat_map_data.get("seats", seat_map_data)
    metadata = seat_map_data.get("_meta", {})
    seat_map_manager.save_seat_map(room_id, seats, metadata)
    
    # Update room config
    config = room_config_manager.get_or_create_config(room_id)
    config.seat_map_path = str(seat_map_manager.seat_maps_dir / f"{room_id.upper()}.json")
    room_config_manager.set_config(config)
    
    return {
        "message": f"Seat map saved for room {room_id}",
        "seats_count": len(seats)
    }


@router.get("/rooms/{room_id}/seat-map")
async def get_seat_map(room_id: str):
    """Get seat map for a room"""
    seat_map = seat_map_manager.get_seat_map(room_id)
    if not seat_map:
        raise HTTPException(status_code=404, detail=f"Seat map not found for room {room_id}")
    return {"seats": seat_map}


@router.get("/annotator")
async def get_annotator():
    """Serve the seat boundary annotator tool"""
    from fastapi.responses import FileResponse
    annotator_path = Path(__file__).parent / "seat_annotator.html"
    if not annotator_path.exists():
        raise HTTPException(status_code=404, detail="Annotator tool not found")
    return FileResponse(annotator_path)


@router.get("/rooms/{room_id}/cctv-image")
async def get_cctv_image(room_id: str):
    """Get CCTV frame image for annotation"""
    from fastapi.responses import FileResponse
    cctv_path = cctv_manager.get_frame_path(room_id)
    if not cctv_path or not cctv_path.exists():
        raise HTTPException(status_code=404, detail=f"CCTV frame not found for room {room_id}")
    return FileResponse(cctv_path)
