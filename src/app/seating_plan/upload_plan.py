# routers/seating_plan.py
from fastapi import APIRouter, File, UploadFile, Query
import pdfplumber
import re
import io
from datetime import datetime
from pathlib import Path
import time
import json
import cv2
import numpy as np
from bson import ObjectId

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

# -------- Main Endpoint --------
@router.post("/upload-seating-plan")
async def upload_seating_plan(
    file: UploadFile = File(...),
    room_no: str = Query(None, description="Room number to extract, e.g. C-301"),
    time_slot: str = Query(None, description="Time slot to extract, e.g. 10:20 AM to 11:20 AM")
):
    global latest_room_data
    start_time = time.time()
    print(f"[DEBUG] Request started | File: {file.filename}")

    try:
        pdf_bytes = await file.read()
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        text = re.sub(r'\s+', ' ', text)

        block_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)?\s*to\s*\d{1,2}:\d{2}\s*(?:AM|PM)?.*?Name\s*of\s*Invigilator:.*?)(?=(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4}|$)'
        all_blocks = re.finditer(block_pattern, text, re.IGNORECASE | re.DOTALL)

        matching_exams = []
        for block_match in all_blocks:
            block_text = block_match.group(1)
            date_time_match = re.search(
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4})\s+(\d{1,2}:\d{2}\s*(?:AM|PM)?\s*to\s*\d{1,2}:\d{2}\s*(?:AM|PM)?)',
                block_text,
                re.IGNORECASE,
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

            course_match = re.search(
                r'((?:CS|EE|SE|AI|DS|SS|CY|MG|MT)\d{4}\s*-\s*[A-Za-z\s&]+)\s+([A-Z]{2,}-\d+[A-Z]?)',
                block_text,
            )
            invigilator_match = re.search(r'Name\s*of\s*Invigilator:\s*([A-Za-z\s]*)', block_text)

            course_name = course_match.group(1).strip() if course_match else None
            section = course_match.group(2).strip() if course_match else None
            invigilator_name = invigilator_match.group(1).strip() if invigilator_match else None

            # Extract students
            pattern = r'(\d+)\s+(\d{2}[A-Z]-\d{4})\s+([A-Za-z\s]+?)\s+(C\dR\d|Chair\d)'
            students = []
            for s_no, roll_no, name, seat in re.findall(pattern, block_text):
                students.append({
                    "serial_no": s_no.strip(),
                    "roll_no": roll_no.strip(),
                    "name": name.strip(),
                    "seat_no": seat.strip()
                })

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

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        json_filename = f"seating_plan_{selected_exam['room_no']}_{timestamp}.json"
        json_path = EXTRACTIONS_DIR / json_filename

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(selected_exam, f, indent=4, default=str)

        # ---------- Visualize ----------
        frame = cv2.imread(str(CCTV_IMAGE_PATH))
        if frame is None:
            raise FileNotFoundError("Could not load CCTV image")

        with open(SEAT_MAP_PATH) as f:
            seat_map = json.load(f)["seats"]

        def find_student(seat_id):
            seat_id = seat_id.replace("seat_", "").upper()
            for s in selected_exam["students"]:
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
            "message": f"Seating plan extracted for room {selected_exam['room_no']}",
            "exam_date": selected_exam["exam_date"],
            "exam_time": selected_exam["exam_time"],
            "course": selected_exam["course"],
            "room_no": selected_exam["room_no"],
            "students_count": len(selected_exam["students"]),
            "json_file": str(json_path),
            "annotated_image": str(annotated_path),
            "processing_time": f"{time.time() - start_time:.2f}s",
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
