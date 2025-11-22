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
from bson import ObjectId

from database.db import get_db
from database.models import Exam, Room, Seat, Student

router = APIRouter()

# Global store for latest extracted room
latest_room_data = {}

# Paths for storage and visualization
EXTRACTIONS_DIR = Path("./app/seating_plan/extractions")
EXTRACTIONS_DIR.mkdir(exist_ok=True)

SEAT_MAP_PATH = Path("./app/seating_plan/seat_map.json")
CCTV_IMAGE_PATH = Path("./app/seating_plan/cctv_frame.jpg")

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
    start_time = time.time()

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
            room = Room(
                room_number=room_num,
                block=room_block,
                total_seats=len(selected_exam['students']),
                exam_id=exam.exam_id,
                camera_id=f"CAM-{room_number}"
            )
            db.add(room)
            db.commit()
            db.refresh(room)

        # Create or find Students and assign Seats
        for student_data in selected_exam['students']:
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

        # --- Visualize seat map ---
        frame = cv2.imread(str(CCTV_IMAGE_PATH))
        if frame is None:
            raise FileNotFoundError("Could not load CCTV image")

        with open(SEAT_MAP_PATH) as f:
            seat_map = json.load(f)["seats"]

        def find_student(seat_id):
            seat_id = seat_id.replace("seat_", "").upper()
            for sec in selected_exam["sections"]:
                for s in sec["students"]:
                    if s["seat_no"].upper() == seat_id:
                        return s
            return None

        for seat_id, points in seat_map.items():
            pts = np.array([tuple(p) for p in points], np.int32)
            cv2.polylines(frame, [pts], True, (0, 255, 0), 2)

            student = find_student(seat_id)
            text = f"{student['name']} ({student['roll_no']})" if student else f"[{seat_id}]"

            M = cv2.moments(pts)
            if M["m00"] != 0:
                cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
            else:
                cx, cy = pts[0]

            (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.putText(frame, text, (cx - w//2, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        annotated_filename = f"annotated_{selected_exam['room_no']}_{timestamp}.jpg"
        annotated_path = EXTRACTIONS_DIR / annotated_filename
        cv2.imwrite(str(annotated_path), frame)

        return {
            "message": f"Seating plan extracted and saved for room {selected_exam['room_no']}",
            "exam_date": selected_exam["exam_date"],
            "exam_time": selected_exam["exam_time"],
            "room_no": selected_exam["room_no"],
            "students_count": len(selected_exam["students"]),
            "exam_id": str(exam.exam_id),
            "room_id": str(room.room_id),
            "json_file": str(json_path),
            "annotated_image": str(annotated_path),
            "processing_time": f"{time.time() - start_time:.2f}s",
        }


    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# --------- Utility Route ---------
@router.get("/get-latest-room")
async def get_latest_room():
    global latest_room_data
    if not latest_room_data:
        return {"error": "No seating plan extracted yet"}

    return {
        "message": f"Latest room ({latest_room_data.get('room_no')}) data fetched successfully",
        "data": clean_mongo_doc(latest_room_data),
    }
