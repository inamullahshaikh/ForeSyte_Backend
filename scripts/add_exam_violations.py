#!/usr/bin/env python3
"""
Script to add dummy violations and incidents (student_activities) for a specific exam.

Usage: python scripts/add_exam_violations.py

This script will:
1. Find or verify the exam exists
2. Get students enrolled in the exam
3. Create student activities (incidents) for the exam
4. Create violations linked to those activities
"""

import sys
import os
import random
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta
from uuid import UUID

# Get the script directory and resolve paths
SCRIPT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = SCRIPT_DIR.parent
SRC_DIR = BACKEND_DIR / "src"

# Load environment variables
env_file = BACKEND_DIR / ".env"
if not env_file.exists():
    env_file = BACKEND_DIR.parent / ".env"
load_dotenv(env_file)

# Add src directory to path
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.chdir(BACKEND_DIR)

from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import (
    Exam, Student, StudentActivity, Violation, Seat, Room
)
from database.auth import hash_password

# Exam details
EXAM_ID = "b424986c-d41a-4086-af61-014967e718fe"
EXAM_COURSE = "CS4049 - Blockchain and Cryptocurrency"
EXAM_DATE = "2025-09-24"

# Activity types for incidents
ACTIVITY_TYPES = [
    "Looking Away",
    "Suspicious Movement",
    "Device Detected",
    "Multiple Faces",
    "Audio Detected",
    "Unauthorized Communication",
    "Looking at Phone",
    "Cheating Attempt",
    "Talking to Neighbor",
    "Using Unauthorized Materials"
]

# Violation types
VIOLATION_TYPES = [
    "Academic Dishonesty",
    "Unauthorized Device",
    "Communication",
    "Disruptive Behavior",
    "Cheating Attempt",
    "Using Phone"
]

# Severity levels
SEVERITY_LEVELS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4
}

def get_severity_for_activity(activity_type: str) -> int:
    """Determine severity based on activity type."""
    if "Cheating" in activity_type or "Unauthorized" in activity_type:
        return SEVERITY_LEVELS["high"]
    elif "Device" in activity_type or "Phone" in activity_type:
        return SEVERITY_LEVELS["high"]
    elif "Communication" in activity_type:
        return SEVERITY_LEVELS["medium"]
    elif "Talking" in activity_type:
        return SEVERITY_LEVELS["medium"]
    else:
        return SEVERITY_LEVELS["low"]

def add_exam_violations_and_incidents():
    """Add violations and incidents for the specified exam."""
    db = SessionLocal()
    try:
        # Step 1: Verify exam exists
        exam_id_uuid = UUID(EXAM_ID)
        exam = db.query(Exam).filter(Exam.exam_id == exam_id_uuid).first()
        
        if not exam:
            print(f"❌ Exam with ID {EXAM_ID} not found!")
            print(f"   Course: {EXAM_COURSE}")
            print("\nPlease create the exam first or check the exam ID.")
            return
        
        print(f"✓ Found exam: {exam.course}")
        print(f"  Exam ID: {exam.exam_id}")
        print(f"  Date: {exam.exam_date}")
        
        # Step 2: Get students enrolled in this exam (via seats in rooms assigned to exam)
        # First, get rooms for this exam
        rooms = db.query(Room).filter(Room.exam_id == exam_id_uuid).all()
        
        if not rooms:
            print(f"\n⚠️  No rooms found for this exam.")
            print("   Creating incidents for all students in database...")
            students = db.query(Student).limit(20).all()
        else:
            # Get students from seats in these rooms
            room_ids = [room.room_id for room in rooms]
            seats = db.query(Seat).filter(Seat.room_id.in_(room_ids)).all()
            student_ids = [seat.student_id for seat in seats if seat.student_id]
            
            if student_ids:
                students = db.query(Student).filter(Student.student_id.in_(student_ids)).all()
            else:
                print(f"\n⚠️  No students found in exam rooms.")
                print("   Creating incidents for all students in database...")
                students = db.query(Student).limit(20).all()
        
        if not students:
            print("❌ No students found in database!")
            print("   Please add students first.")
            return
        
        print(f"\n✓ Found {len(students)} students for this exam")
        
        # Step 3: Ask user how many incidents/violations to create
        num_incidents = input(f"\nHow many incidents/violations to create? [default: {min(10, len(students))}]: ").strip()
        num_incidents = int(num_incidents) if num_incidents.isdigit() else min(10, len(students))
        
        # Step 4: Create student activities (incidents)
        print(f"\nCreating {num_incidents} incidents (student activities)...")
        activities_created = []
        
        # Use exam date for timestamps (or current time if exam is in future)
        exam_datetime = datetime.combine(exam.exam_date, exam.start_time) if exam.exam_date and exam.start_time else datetime.utcnow()
        
        for i in range(num_incidents):
            student = random.choice(students)
            activity_type = random.choice(ACTIVITY_TYPES)
            severity_str = random.choice(["low", "medium", "high"])
            severity = SEVERITY_LEVELS[severity_str]
            
            # Create timestamp during exam time (random time between start and end)
            if exam.start_time and exam.end_time:
                start_dt = datetime.combine(exam.exam_date, exam.start_time)
                end_dt = datetime.combine(exam.exam_date, exam.end_time)
                # Random time during exam
                time_diff = (end_dt - start_dt).total_seconds()
                random_seconds = random.randint(0, int(time_diff))
                activity_timestamp = start_dt + timedelta(seconds=random_seconds)
            else:
                activity_timestamp = exam_datetime + timedelta(minutes=random.randint(10, 120))
            
            activity = StudentActivity(
                student_id=student.student_id,
                exam_id=exam_id_uuid,
                timestamp=activity_timestamp,
                activity_type=activity_type,
                severity=severity_str,
                confidence=round(random.uniform(0.7, 0.95), 2),
                evidence_url=f"/evidence/activity_{i+1}.jpg"
            )
            
            db.add(activity)
            activities_created.append((activity, severity))
        
        db.commit()
        print(f"✓ Created {len(activities_created)} student activities")
        
        # Step 5: Create violations linked to activities
        print(f"\nCreating violations for {len(activities_created)} activities...")
        violations_created = []
        
        for activity, activity_severity in activities_created:
            db.refresh(activity)
            
            # Determine violation type based on activity
            if "Cheating" in activity.activity_type or "Unauthorized" in activity.activity_type:
                violation_type = "Academic Dishonesty"
                violation_severity = SEVERITY_LEVELS["high"]
                violation_status = "pending"
            elif "Device" in activity.activity_type or "Phone" in activity.activity_type:
                violation_type = "Unauthorized Device"
                violation_severity = SEVERITY_LEVELS["high"]
                violation_status = "pending"
            elif "Communication" in activity.activity_type or "Talking" in activity.activity_type:
                violation_type = "Communication"
                violation_severity = SEVERITY_LEVELS["medium"]
                violation_status = "pending"
            else:
                violation_type = random.choice(VIOLATION_TYPES)
                violation_severity = activity_severity
                violation_status = random.choice(["pending", "under_review"])
            
            violation = Violation(
                activity_id=activity.activity_id,
                violation_type=violation_type,
                timestamp=activity.timestamp,
                severity=violation_severity,
                status=violation_status,
                evidence_url=activity.evidence_url
            )
            
            db.add(violation)
            violations_created.append(violation)
        
        db.commit()
        print(f"✓ Created {len(violations_created)} violations")
        
        # Step 6: Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Exam: {exam.course}")
        print(f"Exam ID: {exam.exam_id}")
        print(f"Date: {exam.exam_date}")
        print(f"\nCreated:")
        print(f"  - {len(activities_created)} Student Activities (Incidents)")
        print(f"  - {len(violations_created)} Violations")
        
        # Show breakdown by severity
        severity_breakdown = {}
        for _, severity in activities_created:
            severity_name = [k for k, v in SEVERITY_LEVELS.items() if v == severity][0]
            severity_breakdown[severity_name] = severity_breakdown.get(severity_name, 0) + 1
        
        print(f"\nSeverity Breakdown:")
        for severity, count in severity_breakdown.items():
            print(f"  - {severity.capitalize()}: {count}")
        
        print("\n✓ All data added successfully!")
        print("\nYou can now generate reports for this exam and they will include these violations.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_exam_violations_and_incidents()
