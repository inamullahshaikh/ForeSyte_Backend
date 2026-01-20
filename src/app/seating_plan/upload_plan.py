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

CSFYP_DIR = Path("./app/seating_plan/CSFYP")

# Default paths (fallback)
SEAT_MAP_PATH = Path("./app/seating_plan/seat_map.json")
CCTV_IMAGE_PATH = Path("./app/seating_plan/cctv_frame.jpg")

# -------- Utility Functions --------
def normalize_time_slot(time_str):
    """Normalize time slot format for comparison"""
    if not time_str:
        return None
    normalized = re.sub(r'\s+', ' ', time_str.strip().lower())
    normalized = normalized.replace('a.m.', 'am').replace('p.m.', 'pm')
    return normalized

def time_slots_match(time1, time2):
    """Check if two time slots match (allowing format variations)"""
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

def get_room_paths(room_no: str):
    """
    Get room-specific seat_map.json and image paths based on room number.
    
    Args:
        room_no: Room number like "A-104", "A104", "B-127", "C-301", "C-311", "D-314"
    
    Returns:
        tuple: (seat_map_path, image_path) or (None, None) if not found
    """
    # Normalize room number (handle both "A-104" and "A104" formats)
    room_no_upper = room_no.upper().replace('-', '').replace(' ', '')
    room_block = room_no_upper[0] if room_no_upper and room_no_upper[0].isalpha() else None
    room_num = room_no_upper[1:] if len(room_no_upper) > 1 else None
    
    if not room_block or not room_num:
        return None, None
    
    # Determine which CSFYP folder to use
    if room_block == 'A':
        # A block uses A104-25112025 folder
        room_folder = CSFYP_DIR / "A104-25112025"
    elif room_block == 'B':
        # B block uses B127-25112025 folder
        room_folder = CSFYP_DIR / "B127-25112025"
    elif room_block == 'C':
        # C block: C311 is exception, others use C301-25112025
        if room_num == '311':
            room_folder = CSFYP_DIR / "C311-25112025"
        else:
            # C301, C307, etc. use C301-25112025
            room_folder = CSFYP_DIR / "C301-25112025"
    elif room_block == 'D':
        # D block uses D314-25112025 folder
        room_folder = CSFYP_DIR / "D314-25112025"
    else:
        return None, None
    
    # Find seat_map.json
    seat_map_path = room_folder / "seat_map.json"
    if not seat_map_path.exists():
        return None, None
    
    # Find corresponding image (.jpg file)
    image_files = list(room_folder.glob("*.jpg"))
    if not image_files:
        return None, None
    
    image_path = image_files[0]  # Use first .jpg file found
    
    return seat_map_path, image_path

def get_column_mapping(room_no: str, max_col: int):
    """
    Get column mapping based on room block and max column.
    
    Args:
        room_no: Room number like "A-104", "A104", "B-127", "C-301", "C-311", "D-314"
        max_col: Maximum column number from seating plan
    
    Returns:
        dict: Mapping from input column to seat_map column
    """
    # Normalize room number (handle both "A-104" and "A104" formats)
    room_no_upper = room_no.upper().replace('-', '').replace(' ', '')
    room_block = room_no_upper[0] if room_no_upper and room_no_upper[0].isalpha() else None
    room_num = room_no_upper[1:] if len(room_no_upper) > 1 else None
    
    if room_block == 'A':
        # A block (e.g., A104): max c6 or c5
        # For A104, always use the full mapping based on detected max column
        # If max_col is exactly 5, use c5 mapping; otherwise use c6 mapping
        if max_col == 5:
            # c1→c1, c2→c3, c3→c5, c4→c7, c5→c9
            return {1: 1, 2: 3, 3: 5, 4: 7, 5: 9}
        else:
            # Default to c6 mapping for A104 (c1→c1, c2→c3, c3→c4, c4→c7, c5→c8, c6→c10)
            # This handles cases where max_col is 6 or any other value
            return {1: 1, 2: 3, 3: 4, 4: 7, 5: 8, 6: 10}
    
    elif room_block == 'B':
        # B block (e.g., B127): max c4
        if max_col == 4:
            return {1: 1, 2: 3, 3: 5, 4: 7}
        else:
            return {i: i for i in range(1, max_col + 1)}
    
    elif room_block == 'C':
        if room_num == '311':
            # C311: max c4
            if max_col == 4:
                return {1: 1, 2: 3, 3: 6, 4: 8}
            else:
                return {i: i for i in range(1, max_col + 1)}
        else:
            # C301, C307, etc.: max c6 or c5
            if max_col == 6:
                return {1: 1, 2: 3, 3: 5, 4: 6, 5: 8, 6: 10}
            elif max_col == 5:
                return {1: 1, 2: 4, 3: 6, 4: 8, 5: 10}
            else:
                return {i: i for i in range(1, max_col + 1)}
    
    elif room_block == 'D':
        # D block (e.g., D314): max c6 or c5
        if max_col == 6:
            return {1: 1, 2: 3, 3: 5, 4: 6, 5: 8, 6: 10}
        elif max_col == 5:
            return {1: 1, 2: 4, 3: 6, 4: 8, 5: 10}
        else:
            return {i: i for i in range(1, max_col + 1)}
    
    # Default: 1:1 mapping
    return {i: i for i in range(1, max_col + 1)}


# -------- Main Endpoint --------
@router.post("/upload-seating-plan")
async def upload_seating_plan(
    file: UploadFile = File(...),
    room_no: str = Query(None, description="Room number to extract, e.g. C-301"),
    time_slot: str = Query(None, description="Time slot to extract, e.g. 10:20 AM to 11:20 AM"),
    db: Session = Depends(get_db)
):
    global latest_room_data
    processing_start_time = time.time()
    print(f"[DEBUG] Request started | File: {file.filename}")

    try:
        pdf_bytes = await file.read()
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            # Extract text from each page separately to track page boundaries
            page_texts = [page.extract_text() or "" for page in pdf.pages]
            full_text = "\n".join(page_texts)
            full_text = re.sub(r'\s+', ' ', full_text)

        # Find all exam block headers (date/time) across all pages
        exam_header_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4})\s+(\d{1,2}:\d{2}\s*(?:AM|PM)?\s*to\s*\d{1,2}:\d{2}\s*(?:AM|PM)?)'
        all_headers = list(re.finditer(exam_header_pattern, full_text, re.IGNORECASE))
        
        matching_exams = []
        
        # Process each exam block
        for i, header_match in enumerate(all_headers):
            header_start = header_match.start()
            exam_date = header_match.group(1)
            exam_time = header_match.group(2)
            
            # Find the end of this block - continue until we hit a different exam
            block_end = len(full_text)
            
            # Check if there's a next header
            if i + 1 < len(all_headers):
                next_header_start = all_headers[i + 1].start()
                next_header_date = all_headers[i + 1].group(1)
                next_header_time = all_headers[i + 1].group(2)
                
                # Extract text from current header to next header to check room
                text_before_next = full_text[header_start:next_header_start]
                current_room_match = re.search(r'Room\s*No\.?\s*([A-Z]-\d+)', text_before_next, re.IGNORECASE)
                
                # Extract text from next header to check if it's same exam
                text_after_next = full_text[next_header_start:min(next_header_start + 500, len(full_text))]
                next_room_match = re.search(r'Room\s*No\.?\s*([A-Z]-\d+)', text_after_next, re.IGNORECASE)
                
                # Determine if next header is a different exam
                is_different_exam = False
                
                # Different date = different exam
                if next_header_date != exam_date:
                    is_different_exam = True
                # Different time = different exam
                elif not time_slots_match(next_header_time, exam_time):
                    is_different_exam = True
                # Different room = different exam
                elif current_room_match and next_room_match:
                    current_room = current_room_match.group(1).strip().upper()
                    next_room = next_room_match.group(1).strip().upper()
                    if current_room != next_room:
                        is_different_exam = True
                
                # If it's a different exam, stop at next header
                if is_different_exam:
                    block_end = next_header_start
                # Otherwise, same exam continues - include content up to next different exam
                # (we'll handle this by continuing to collect students)
            
            # Extract block text from header to determined end
            block_text = full_text[header_start:block_end]
            
            # Find room number in this block
            room_match = re.search(r'Room\s*No\.?\s*([A-Z]-\d+)', block_text, re.IGNORECASE)
            if not room_match:
                continue
            
            detected_room = room_match.group(1).strip()

            # Filter by room/time (normalize both for comparison)
            detected_room_normalized = detected_room.upper().replace('-', '').replace(' ', '')
            room_no_normalized = room_no.upper().replace('-', '').replace(' ', '') if room_no else None
            room_matches = detected_room_normalized == room_no_normalized if room_no else True
            time_matches = time_slots_match(exam_time, time_slot) if time_slot else True
            if not (room_matches and time_matches):
                continue

            course_match = re.search(
                r'((?:CS|EE|SE|AI|DS|SS|CY|MG|MT)\d{4}\s*-\s*[A-Za-z\s&]+)\s+([A-Z]{2,}-\d+[A-Z]?)',
                block_text,
            )
            invigilator_match = re.search(r'Name\s*of\s*Invigilator:\s*([A-Za-z\s]*)', block_text)

            course_name = course_match.group(1).strip() if course_match else None
            section = course_match.group(2).strip() if course_match else None
            invigilator_name = invigilator_match.group(1).strip() if invigilator_match else None

            # Extract students from the entire block (may span multiple pages)
            # Pattern matches: serial number, roll number, name, seat number
            pattern = r'(\d+)\s+(\d{2}[A-Z]-\d{4})\s+([A-Za-z\s]+?)\s+(C\dR\d|Chair\d)'
            students = []
            seen_roll_nos = set()  # To avoid duplicates if same student appears multiple times
            
            all_matches = re.findall(pattern, block_text)
            print(f"[DEBUG] Found {len(all_matches)} student matches in block for room {detected_room}")
            
            for s_no, roll_no, name, seat in all_matches:
                roll_no_clean = roll_no.strip()
                # Skip if we've already seen this roll number (duplicate)
                if roll_no_clean in seen_roll_nos:
                    print(f"[DEBUG] Skipping duplicate roll number: {roll_no_clean}")
                    continue
                seen_roll_nos.add(roll_no_clean)
                
                students.append({
                    "serial_no": s_no.strip(),
                    "roll_no": roll_no_clean,
                    "name": name.strip(),
                    "seat_no": seat.strip()
                })
            
            print(f"[DEBUG] Extracted {len(students)} unique students for room {detected_room} (date: {exam_date}, time: {exam_time})")

            matching_exams.append({
                "exam_date": exam_date,
                "exam_time": exam_time,
                "course": course_name,
                "section": section,
                "room_no": detected_room,
                "invigilator_name": invigilator_name,
                "students": students,
                "total_students": len(students),
                "uploaded_at": datetime.utcnow(),
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

        # ---------- Visualize ----------
        # Get room-specific paths
        room_number = selected_exam['room_no']
        seat_map_path, image_path = get_room_paths(room_number)
        
        if not seat_map_path or not image_path:
            raise FileNotFoundError(f"Could not find seat_map.json or image for room {room_number}")
        
        print(f"[DEBUG] Using seat_map: {seat_map_path}")
        print(f"[DEBUG] Using image: {image_path}")
        
        # Load room-specific image
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise FileNotFoundError(f"Could not load image from {image_path}")

        # Load room-specific seat map
        with open(seat_map_path) as f:
            seat_map = json.load(f)["seats"]

        # Find maximum column from seating plan
        max_column = 0
        for student in selected_exam["students"]:
            seat_no = student["seat_no"].upper()
            # Extract column number from formats like C1R1, C2R3, etc.
            col_match = re.search(r'C(\d+)', seat_no)
            if col_match:
                col_num = int(col_match.group(1))
                max_column = max(max_column, col_num)

        # Get column mapping based on room and max column
        # Normalize room number for mapping (handle both "A-104" and "A104" formats)
        room_number_normalized = room_number.upper().replace('-', '').replace(' ', '')
        column_mapping = get_column_mapping(room_number, max_column)
        
        # Debug: Show all unique seat columns found
        unique_cols = []
        for student in selected_exam["students"]:
            seat_no = student["seat_no"].upper()
            col_match = re.search(r'C(\d+)', seat_no)
            if col_match:
                unique_cols.append(int(col_match.group(1)))
        unique_cols = sorted(set(unique_cols))
        print(f"[DEBUG] Room: {room_number} (normalized: {room_number_normalized})")
        print(f"[DEBUG] Detected columns in seating plan: {unique_cols}, Max column: {max_column}")
        print(f"[DEBUG] Column mapping applied: {column_mapping}")
        
        # Check if we got a default mapping (indicates room block not recognized)
        default_mapping = {i: i for i in range(1, max_column + 1)}
        if column_mapping == default_mapping and max_column > 0:
            print(f"[WARNING] Using default 1:1 mapping for room {room_number}. Room block may not be recognized.")
        
        # Debug: Show sample seat mappings
        if selected_exam["students"]:
            print(f"[DEBUG] Sample seat mappings (first 5 students):")
            for student in selected_exam["students"][:5]:
                seat_no = student["seat_no"].upper()
                match = re.search(r'C(\d+)R(\d+)', seat_no)
                if match:
                    input_col = int(match.group(1))
                    row = int(match.group(2))
                    mapped_col = column_mapping.get(input_col)
                    if mapped_col:
                        mapped_seat = f"seat_c{mapped_col}r{row}"
                        print(f"  {seat_no} -> {mapped_seat} (col {input_col} -> {mapped_col})")
                    else:
                        print(f"  {seat_no} -> NO MAPPING (col {input_col} not in mapping)")

        # Create a mapping from input seat numbers to seat_map IDs
        def map_seat_to_seat_map(seat_no):
            """Map input seat number (e.g., C1R1) to seat_map ID (e.g., seat_c1r1)"""
            seat_no = seat_no.upper()
            # Extract column and row
            match = re.search(r'C(\d+)R(\d+)', seat_no)
            if not match:
                return None
            
            input_col = int(match.group(1))
            row = int(match.group(2))
            
            # Map to seat_map column
            mapped_col = column_mapping.get(input_col)
            if not mapped_col:
                return None
            
            return f"seat_c{mapped_col}r{row}"

        # Build a set of filled seat_map IDs (seats with students)
        filled_seats = set()
        student_seat_map = {}  # Map seat_map_id to student data
        
        for student in selected_exam["students"]:
            seat_map_id = map_seat_to_seat_map(student["seat_no"])
            if seat_map_id:
                filled_seats.add(seat_map_id)
                student_seat_map[seat_map_id] = student

        print(f"[DEBUG] Filled seats: {len(filled_seats)} out of {len(seat_map)} total seats")

        # Only draw polygons for filled seats
        for seat_id, points in seat_map.items():
            # Skip if seat is not filled
            if seat_id not in filled_seats:
                continue
            
            pts = np.array([tuple(p) for p in points], np.int32)
            cv2.polylines(frame, [pts], True, (0, 255, 0), 2)

            student = student_seat_map.get(seat_id)
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
            "course": selected_exam["course"],
            "room_no": selected_exam["room_no"],
            "students_count": len(selected_exam["students"]),
            "exam_id": str(exam.exam_id),
            "room_id": str(room.room_id),
            "json_file": str(json_path),
            "annotated_image": str(annotated_path),
            "processing_time": f"{time.time() - processing_start_time:.2f}s",
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# --------- Utility Routes ---------
@router.get("/get-latest-room")
async def get_latest_room():
    global latest_room_data
    if not latest_room_data:
        return {"error": "No seating plan extracted yet"}

    if "_id" in latest_room_data and isinstance(latest_room_data["_id"], ObjectId):
        latest_room_data["_id"] = str(latest_room_data["_id"])

    return {
        "message": f"Latest room ({latest_room_data.get('room_no')}) data fetched successfully",
        "data": latest_room_data,
    }


def clean_mongo_doc(doc):
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc