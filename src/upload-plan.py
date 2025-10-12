from fastapi import FastAPI, File, UploadFile, Query
import pdfplumber
import re
import io
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import os
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
import time
from bson import ObjectId

# Load environment variables
load_dotenv()
DB_URL = os.getenv("DB_URL")
DB_NAME = os.getenv("DB_NAME")

# MongoDB setup
client = MongoClient(DB_URL)
db = client[DB_NAME]

# Store the most recent extracted room
latest_room_data = {}

app = FastAPI(title="ForeSyte Seating Plan Extractor")

# Add CORS middleware configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directory for storing JSON files if it doesn't exist
EXTRACTIONS_DIR = Path("extractions")
EXTRACTIONS_DIR.mkdir(exist_ok=True)


def normalize_time_slot(time_str):
    """Normalize time slot format for comparison"""
    if not time_str:
        return None
    # Remove extra spaces and convert to lowercase
    normalized = re.sub(r'\s+', ' ', time_str.strip().lower())
    # Handle AM/PM variations
    normalized = normalized.replace('a.m.', 'am').replace('p.m.', 'pm')
    return normalized


def time_slots_match(time1, time2):
    """Check if two time slots match (allowing for format variations)"""
    if not time1 or not time2:
        return False
    
    t1 = normalize_time_slot(time1)
    t2 = normalize_time_slot(time2)
    
    return t1 == t2


@app.post("/upload-seating-plan")
async def upload_seating_plan(
    file: UploadFile = File(...),
    room_no: str = Query(None, description="Room number to extract, e.g. C-301"),
    time_slot: str = Query(None, description="Time slot to extract, e.g. 10:20 AM to 11:20 AM")
):
    start_time = time.time()
    print(f"[DEBUG] Request started at {datetime.now().isoformat()} | File: {file.filename}")
    print(f"[DEBUG] Requested Room: {room_no}, Time Slot: {time_slot}")

    try:
        # Read bytes
        pdf_bytes = await file.read()
        print(f"[DEBUG] File size: {len(pdf_bytes)} bytes")

        pdf_start = time.time()
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = ""
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        print(f"[DEBUG] PDF extraction took {time.time() - pdf_start:.2f}s")

        # Clean text
        text = re.sub(r'\s+', ' ', text)

        # Extract all exam blocks
        # Pattern to match exam blocks with date/time/room info
        block_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)?\s*to\s*\d{1,2}:\d{2}\s*(?:AM|PM)?.*?Name\s*of\s*Invigilator:.*?)(?=(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s*\d{4}|$)'
        
        all_blocks = re.finditer(block_pattern, text, re.IGNORECASE | re.DOTALL)
        
        matching_exams = []
        room_only_matches = []
        time_only_matches = []
        
        for block_match in all_blocks:
            block_text = block_match.group(1)
            
            # Extract metadata from this block
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
            
            # Check if this block matches the search criteria
            room_matches = detected_room.upper() == room_no.upper() if room_no else True
            time_matches = time_slots_match(exam_time, time_slot) if time_slot else True
            
            # Store different types of matches
            if room_matches and time_matches:
                # Extract additional metadata
                course_match = re.search(
                    r'((?:CS|EE|SE|AI|DS|SS|CY|MG|MT)\d{4}\s*-\s*[A-Za-z\s&]+)\s+([A-Z]{2,}-\d+[A-Z]?)',
                    block_text
                )
                invigilator_match = re.search(
                    r'Name\s*of\s*Invigilator:\s*([A-Za-z\s]*)',
                    block_text
                )
                
                course_name = course_match.group(1).strip() if course_match else None
                section = course_match.group(2).strip() if course_match else None
                invigilator_name = invigilator_match.group(1).strip() if invigilator_match else None
                
                # Extract students
                pattern = r'(\d+)\s+(\d{2}[A-Z]-\d{4})\s+([A-Za-z\s]+?)\s+(C\dR\d|Chair\d)'
                students = []
                for match in re.findall(pattern, block_text):
                    s_no, roll_no, name, seat = match
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
                    "uploaded_at": datetime.utcnow()
                })
        
        # Handle results based on what was found
        if not matching_exams:
            error_msg = "No seating plan found"
            if room_no and time_slot:
                error_msg += f" for room {room_no} at time {time_slot}"
            elif room_no:
                error_msg += f" for room {room_no}"
            elif time_slot:
                error_msg += f" for time slot {time_slot}"
            
            print(f"[DEBUG] {error_msg}")
            return {"error": error_msg}
        
        # Return the first matching exam (or could return all matches)
        selected_exam = matching_exams[0]
        latest_room_data = selected_exam
        
        # Save to JSON file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"seating_plan_{selected_exam['room_no']}_{timestamp}.json"
        json_path = EXTRACTIONS_DIR / filename
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(selected_exam, f, indent=4, default=str)
        
        print(f"[DEBUG] Found {len(selected_exam['students'])} students | Room: {selected_exam['room_no']} | Course: {selected_exam['course']}")
        print(f"[DEBUG] Total matching exams: {len(matching_exams)}")
        print(f"[DEBUG] Total processing time: {time.time() - start_time:.2f}s")
        
        return {
            "message": f"Seating plan extracted for room {selected_exam['room_no']}",
            "exam_date": selected_exam['exam_date'],
            "exam_time": selected_exam['exam_time'],
            "course": selected_exam['course'],
            "room_no": selected_exam['room_no'],
            "students_count": len(selected_exam['students']),
            "json_file": str(json_path),
            "total_matches": len(matching_exams)
        }
        
    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.get("/get-latest-room")
async def get_latest_room():
    """
    Get the most recently extracted room's data (from variables in memory).
    """
    global latest_room_data

    if not latest_room_data:
        return {"error": "No seating plan extracted yet"}

    # Convert ObjectId to string (if present)
    if "_id" in latest_room_data and isinstance(latest_room_data["_id"], ObjectId):
        latest_room_data["_id"] = str(latest_room_data["_id"])

    return {
        "message": f"Latest room ({latest_room_data.get('room_no')}) data fetched successfully",
        "data": latest_room_data
    }


def clean_mongo_doc(doc):
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)