"""
Script to add dummy data for student testing.
Creates exams, activities, violations, and other test data for a specific student.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, date, time
from uuid import UUID
from sqlalchemy.orm import Session

# Add src directory to path to import database modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.db import SessionLocal
from database.models import (
    Student, Exam, Room, Seat, StudentActivity, Violation
)


# Student ID to add data for
STUDENT_ID = UUID("ae261e24-8622-400e-b2a9-45a95392d763")


def create_dummy_data(db: Session, student_id: UUID):
    """Create dummy data for the specified student."""
    
    # Check if student exists
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        print(f"❌ Error: Student with ID {student_id} not found!")
        print("Please make sure the student exists in the database.")
        return False
    
    print(f"✅ Found student: {student.name} ({student.email})")
    print(f"   Roll Number: {student.roll_number}")
    print()
    
    # Create an exam
    print("Creating exam...")
    exam = Exam(
        course="CS5020 - Agentic AI",
        exam_date=date.today() - timedelta(days=5),
        start_time=time(10, 0),
        end_time=time(12, 0)
    )
    db.add(exam)
    db.flush()  # Get exam_id without committing
    print(f"✅ Created exam: {exam.course} (ID: {exam.exam_id})")
    
    # Create a room
    print("Creating room...")
    room = Room(
        room_number="C-304",
        block="3rd Floor",
        total_seats=30,
        exam_id=exam.exam_id
    )
    db.add(room)
    db.flush()
    print(f"✅ Created room: {room.room_number}")
    
    # Create a seat assignment
    print("Creating seat assignment...")
    seat = Seat(
        seat_number="C1R1",
        room_id=room.room_id,
        student_id=student_id
    )
    db.add(seat)
    db.flush()
    print(f"✅ Created seat: {seat.seat_number}")
    print()
    
    # Create student activities with different types and severities
    print("Creating student activities...")
    activities_data = [
        {
            "activity_type": "suspicious_head_movement",
            "severity": "high",
            "confidence": 0.92,
            "timestamp": datetime.now() - timedelta(days=5, hours=2, minutes=30),
            "evidence_url": "/evidence/suspicious_movement_1.jpg"
        },
        {
            "activity_type": "multiple_faces_detected",
            "severity": "medium",
            "confidence": 0.75,
            "timestamp": datetime.now() - timedelta(days=4, hours=14, minutes=12),
            "evidence_url": "/evidence/multiple_faces_1.jpg"
        },
        {
            "activity_type": "keyboard_activity_spike",
            "severity": "low",
            "confidence": 0.65,
            "timestamp": datetime.now() - timedelta(days=3, hours=18, minutes=5),
            "evidence_url": "/evidence/keyboard_spike_1.jpg"
        },
        {
            "activity_type": "looking_away_frequently",
            "severity": "medium",
            "confidence": 0.80,
            "timestamp": datetime.now() - timedelta(days=2, hours=11, minutes=15),
            "evidence_url": "/evidence/looking_away_1.jpg"
        },
        {
            "activity_type": "phone_detected",
            "severity": "high",
            "confidence": 0.95,
            "timestamp": datetime.now() - timedelta(days=1, hours=9, minutes=45),
            "evidence_url": "/evidence/phone_detected_1.jpg"
        },
        {
            "activity_type": "background_noise",
            "severity": "low",
            "confidence": 0.55,
            "timestamp": datetime.now() - timedelta(hours=2),
            "evidence_url": "/evidence/noise_1.jpg"
        }
    ]
    
    created_activities = []
    for activity_data in activities_data:
        activity = StudentActivity(
            student_id=student_id,
            exam_id=exam.exam_id,
            **activity_data
        )
        db.add(activity)
        db.flush()
        created_activities.append(activity)
        print(f"✅ Created activity: {activity.activity_type} (Severity: {activity.severity})")
    
    print()
    
    # Create violations for high and medium severity activities
    print("Creating violations...")
    violations_data = [
        {
            "activity": created_activities[0],  # suspicious_head_movement
            "violation_type": "suspicious_head_movement",
            "severity": 3,
            "status": "pending",
            "evidence_url": created_activities[0].evidence_url
        },
        {
            "activity": created_activities[1],  # multiple_faces_detected
            "violation_type": "multiple_faces_detected",
            "severity": 2,
            "status": "confirmed",
            "evidence_url": created_activities[1].evidence_url
        },
        {
            "activity": created_activities[3],  # looking_away_frequently
            "violation_type": "looking_away_frequently",
            "severity": 2,
            "status": "dismissed",
            "evidence_url": created_activities[3].evidence_url
        },
        {
            "activity": created_activities[4],  # phone_detected
            "violation_type": "phone_detected",
            "severity": 3,
            "status": "pending",
            "evidence_url": created_activities[4].evidence_url
        }
    ]
    
    for violation_data in violations_data:
        activity = violation_data.pop("activity")
        violation = Violation(
            activity_id=activity.activity_id,
            timestamp=activity.timestamp,
            **violation_data
        )
        db.add(violation)
        db.flush()
        print(f"✅ Created violation: {violation.violation_type} (Status: {violation.status}, Severity: {violation.severity})")
    
    print()
    
    # Commit all changes
    try:
        db.commit()
        print("✅ All dummy data created successfully!")
        print()
        print("Summary:")
        print(f"  - Exam: {exam.course}")
        print(f"  - Room: {room.room_number}")
        print(f"  - Seat: {seat.seat_number}")
        print(f"  - Activities: {len(created_activities)}")
        print(f"  - Violations: {len(violations_data)}")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error committing data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("=" * 80)
    print("Dummy Student Data Generator")
    print("=" * 80)
    print(f"Student ID: {STUDENT_ID}")
    print()
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_activities = db.query(StudentActivity).filter(
            StudentActivity.student_id == STUDENT_ID
        ).count()
        
        if existing_activities > 0:
            response = input(
                f"⚠️  Found {existing_activities} existing activities for this student. "
                "Do you want to add more data? (yes/no): "
            )
            if response.lower() not in ['yes', 'y']:
                print("Operation cancelled.")
                return
        
        success = create_dummy_data(db, STUDENT_ID)
        
        if success:
            print()
            print("🎉 You can now test the student portal with this data!")
            print("   - Dashboard will show activities and violations")
            print("   - Disciplinary Records will show violation cases")
            print("   - Stats will be calculated from the data")
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

