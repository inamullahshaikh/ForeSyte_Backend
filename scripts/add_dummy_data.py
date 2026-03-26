#!/usr/bin/env python3
"""
Script to add dummy data for all users and related tables in the database.

This script populates the database with sample data for testing and development.
It carefully respects foreign key constraints by creating data in the correct order.

Tables populated:
- Admins
- Invigilators
- Investigators
- Students
- Exams
- Rooms
- Seats
- StudentActivities
- InvigilatorActivities
- Violations
- Reports
- Notifications
- VideoStreams
- ProcessingJobs
- FrameLogs
"""

import sys
import os
import random
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, date, time, timedelta

# Get the script directory and resolve paths
SCRIPT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = SCRIPT_DIR.parent
SRC_DIR = BACKEND_DIR / "src"

# Load environment variables from .env file
env_file = BACKEND_DIR / ".env"
if not env_file.exists():
    env_file = BACKEND_DIR.parent / ".env"
load_dotenv(env_file)

# Add src directory to path to import database modules
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Change to backend directory for relative path resolution
os.chdir(BACKEND_DIR)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.db import SessionLocal
from database.models import (
    Admin, Invigilator, Investigator, Student,
    Exam, Room, Seat,
    StudentActivity, InvigilatorActivity,
    Violation, Report, Notification,
    VideoStream, ProcessingJob, FrameLog
)
from database.auth import hash_password


# Default password for all dummy users
DEFAULT_PASSWORD = "Password123!"

# Sample data generators
FIRST_NAMES = [
    "Ahmed", "Ali", "Hassan", "Hussain", "Muhammad", "Fatima", "Ayesha", "Zainab",
    "Ibrahim", "Omar", "Usman", "Khalid", "Amir", "Bilal", "Tariq", "Yusuf",
    "Sara", "Amina", "Maryam", "Noor", "Zara", "Layla", "Hafsa", "Aisha"
]

LAST_NAMES = [
    "Khan", "Ali", "Ahmed", "Hassan", "Malik", "Sheikh", "Butt", "Raza",
    "Shah", "Ahmed", "Iqbal", "Hussain", "Rehman", "Akhtar", "Siddiqui", "Rashid"
]

COURSES = [
    "Calculus I", "Linear Algebra", "Data Structures", "Database Systems",
    "Computer Networks", "Operating Systems", "Software Engineering", "AI Fundamentals",
    "Machine Learning", "Web Development", "Mobile Development", "Cloud Computing"
]

ACTIVITY_TYPES = [
    "Looking Away", "Suspicious Movement", "Device Detected", "Multiple Faces",
    "Audio Detected", "Unauthorized Communication", "Looking at Phone", "Cheating Attempt"
]

VIOLATION_TYPES = [
    "Academic Dishonesty", "Unauthorized Device", "Communication", "Disruptive Behavior"
]

NOTIFICATION_TYPES = ["incident", "exam", "system", "violation"]
NOTIFICATION_TITLES = {
    "incident": ["New Incident Detected", "Incident Resolved", "Incident Requires Attention"],
    "exam": ["Exam Scheduled", "Exam Reminder", "Exam Completed"],
    "system": ["System Update", "Maintenance Scheduled", "System Alert"],
    "violation": ["Violation Reported", "Violation Under Review", "Violation Resolved"]
}


def generate_random_email(name: str, domain: str = "nu.edu.pk") -> str:
    """Generate a random email from name."""
    name_parts = name.lower().split()
    if len(name_parts) >= 2:
        return f"{name_parts[0]}.{name_parts[1]}@{domain}"
    return f"{name_parts[0]}{random.randint(100, 999)}@{domain}"


def generate_roll_number(batch: str = "22", program: str = "I") -> str:
    """Generate a roll number in format XXY-AAAA."""
    number = random.randint(100, 9999)
    return f"{batch}{program}-{number:04d}"


def add_dummy_users(db: Session, num_each: int = 5):
    """Add dummy users (admins, invigilators, investigators, students)."""
    print("\n=== Adding Dummy Users ===")
    
    users_created = {
        'admins': [],
        'invigilators': [],
        'investigators': [],
        'students': []
    }
    
    # Add Admins
    print(f"Creating {num_each} admins...")
    for i in range(num_each):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        username = f"admin{i+1}_{first_name.lower()}"
        email = f"{username}@admin.nu.edu.pk"
        
        try:
            admin = Admin(
                username=username,
                email=email,
                password_hash=hash_password(DEFAULT_PASSWORD),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            db.add(admin)
            db.flush()
            users_created['admins'].append(admin)
            print(f"  ✓ Created admin: {name} ({email})")
        except IntegrityError:
            db.rollback()
            print(f"  ✗ Admin already exists: {email}")
    
    # Add Invigilators
    print(f"\nCreating {num_each} invigilators...")
    for i in range(num_each):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        email = generate_random_email(name, "invigilator.nu.edu.pk")
        
        try:
            invigilator = Invigilator(
                name=name,
                email=email,
                password_hash=hash_password(DEFAULT_PASSWORD),
                photo_url=f"https://example.com/photos/invigilator_{i+1}.jpg",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            db.add(invigilator)
            db.flush()
            users_created['invigilators'].append(invigilator)
            print(f"  ✓ Created invigilator: {name} ({email})")
        except IntegrityError:
            db.rollback()
            print(f"  ✗ Invigilator already exists: {email}")
    
    print(f"\nCreating {num_each} investigators...")
    designations = ["Senior Investigator", "Lead Investigator", "Investigator", "Associate Investigator"]
    for i in range(num_each):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        email = generate_random_email(name, "investigator.nu.edu.pk")
        
        try:
            investigator = Investigator(
                name=name,
                email=email,
                designation=random.choice(designations),
                password_hash=hash_password(DEFAULT_PASSWORD),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            db.add(investigator)
            db.flush()
            users_created['investigators'].append(investigator)
            print(f"  ✓ Created investigator: {name} ({email})")
        except IntegrityError:
            db.rollback()
            print(f"  ✗ Investigator already exists: {email}")
    
    # Add Students
    print(f"\nCreating {num_each * 3} students...")
    for i in range(num_each * 3):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        roll_number = generate_roll_number()
        email = f"{roll_number.lower().replace('-', '')}@nu.edu.pk"
        
        try:
            student = Student(
                name=name,
                email=email,
                roll_number=roll_number,
                password_hash=hash_password(DEFAULT_PASSWORD),
                photo_url=f"https://example.com/photos/student_{i+1}.jpg",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            db.add(student)
            db.flush()
            users_created['students'].append(student)
            if (i + 1) % 5 == 0:
                print(f"  ✓ Created {i+1} students...")
        except IntegrityError:
            db.rollback()
            continue
    
    print(f"  ✓ Created {len(users_created['students'])} students total")
    
    db.commit()
    return users_created


def add_dummy_exams(db: Session, num_exams: int = 10):
    """Add dummy exams."""
    print("\n=== Adding Dummy Exams ===")
    
    exams = []
    start_date = date.today() - timedelta(days=30)
    
    for i in range(num_exams):
        exam_date = start_date + timedelta(days=random.randint(0, 60))
        start_hour = random.randint(9, 14)
        start_min = random.choice([0, 30])
        duration_hours = random.choice([2, 3])
        
        start_time = time(start_hour, start_min)
        end_time = time(start_hour + duration_hours, start_min)
        
        exam = Exam(
            course=random.choice(COURSES),
            exam_date=exam_date,
            start_time=start_time,
            end_time=end_time,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
        )
        db.add(exam)
        db.flush()
        exams.append(exam)
        print(f"  ✓ Created exam: {exam.course} on {exam_date}")
    
    db.commit()
    return exams


def add_dummy_rooms(db: Session, exams: list, rooms_per_exam: int = 2):
    """Add dummy rooms for each exam."""
    print("\n=== Adding Dummy Rooms ===")
    
    rooms = []
    blocks = ["A", "B", "C", "D", "E"]
    
    for exam in exams:
        for i in range(rooms_per_exam):
            room_number = f"{random.randint(100, 300)}"
            block = random.choice(blocks)
            total_seats = random.choice([30, 40, 50, 60])
            camera_id = f"CAM-{block}-{room_number}"
            stream_url = f"http://192.168.1.{random.randint(100, 200)}:8080/video.mjpeg"
            
            room = Room(
                room_number=room_number,
                block=block,
                total_seats=total_seats,
                camera_id=camera_id,
                stream_url=stream_url,
                exam_id=exam.exam_id
            )
            db.add(room)
            db.flush()
            rooms.append(room)
            print(f"  ✓ Created room: {block} {room_number} for {exam.course}")
    
    db.commit()
    return rooms


def add_dummy_seats(db: Session, rooms: list, students: list):
    """Add dummy seat assignments."""
    print("\n=== Adding Dummy Seat Assignments ===")
    
    seats_added = 0
    student_index = 0
    
    for room in rooms:
        num_seats = min(room.total_seats or 30, len(students) - student_index, 30)
        rows = ['A', 'B', 'C', 'D', 'E', 'F']
        cols = range(1, 7)
        
        for i in range(num_seats):
            if student_index >= len(students):
                break
            
            row = rows[i // 6]
            col = (i % 6) + 1
            seat_number = f"{row}{col}"
            
            seat = Seat(
                seat_number=seat_number,
                room_id=room.room_id,
                student_id=students[student_index].student_id
            )
            db.add(seat)
            seats_added += 1
            student_index += 1
        
        print(f"  ✓ Assigned {num_seats} seats in room {room.block} {room.room_number}")
    
    db.commit()
    print(f"  ✓ Total seats assigned: {seats_added}")
    return seats_added


def add_dummy_student_activities(db: Session, students: list, exams: list, num_activities: int = 50):
    """Add dummy student activities."""
    print("\n=== Adding Dummy Student Activities ===")
    
    activities = []
    severities = ["low", "medium", "high", "critical"]
    
    for _ in range(num_activities):
        student = random.choice(students)
        exam = random.choice(exams)
        
        # Generate timestamp within exam date range
        exam_datetime = datetime.combine(exam.exam_date, exam.start_time)
        activity_time = exam_datetime + timedelta(minutes=random.randint(0, 120))
        
        activity = StudentActivity(
            student_id=student.student_id,
            exam_id=exam.exam_id,
            timestamp=activity_time,
            activity_type=random.choice(ACTIVITY_TYPES),
            severity=random.choice(severities),
            confidence=random.uniform(60.0, 99.9),
            evidence_url=f"https://example.com/evidence/{random.randint(1000, 9999)}.mp4"
        )
        db.add(activity)
        db.flush()
        activities.append(activity)
    
    db.commit()
    print(f"  ✓ Created {len(activities)} student activities")
    return activities


def add_dummy_invigilator_activities(db: Session, invigilators: list, rooms: list, num_activities: int = 30):
    """Add dummy invigilator activities."""
    print("\n=== Adding Dummy Invigilator Activities ===")
    
    activity_types = ["Room Check", "Incident Report", "Student Assistance", "System Check"]
    
    for _ in range(num_activities):
        invigilator = random.choice(invigilators)
        room = random.choice(rooms)
        
        activity = InvigilatorActivity(
            invigilator_id=invigilator.invigilator_id,
            room_id=room.room_id,
            timestamp=datetime.utcnow() - timedelta(minutes=random.randint(0, 720)),
            activity_type=random.choice(activity_types),
            notes=f"Activity note: {random.choice(['All clear', 'Issue resolved', 'Monitoring ongoing'])}"
        )
        db.add(activity)
    
    db.commit()
    print(f"  ✓ Created {num_activities} invigilator activities")


def add_dummy_violations(db: Session, activities: list, num_violations: int = None):
    """Add dummy violations from student activities."""
    print("\n=== Adding Dummy Violations ===")
    
    if num_violations is None:
        num_violations = min(len(activities) // 2, 20)  # Violations for half the activities
    
    violations = []
    statuses = ["pending", "investigating", "resolved", "dismissed"]
    selected_activities = random.sample(activities, min(num_violations, len(activities)))
    
    for activity in selected_activities:
        violation = Violation(
            activity_id=activity.activity_id,
            violation_type=random.choice(VIOLATION_TYPES),
            timestamp=activity.timestamp + timedelta(minutes=random.randint(1, 30)),
            severity=random.randint(1, 5),
            status=random.choice(statuses),
            evidence_url=activity.evidence_url
        )
        db.add(violation)
        db.flush()
        violations.append(violation)
    
    db.commit()
    print(f"  ✓ Created {len(violations)} violations")
    return violations


def add_dummy_reports(db: Session, violations: list, investigators: list, num_reports: int = None):
    """Add dummy reports for violations."""
    print("\n=== Adding Dummy Reports ===")
    
    if num_reports is None:
        num_reports = min(len(violations) // 2, 10)
    
    report_types = ["incident", "exam", "analytics"]
    selected_violations = random.sample(violations, min(num_reports, len(violations)))
    
    for violation in selected_violations:
        investigator = random.choice(investigators)
        report = Report(
            report_type=random.choice(report_types),
            generated_date=date.today() - timedelta(days=random.randint(0, 30)),
            file_path=f"/reports/{violation.violation_id}.pdf",
            violation_id=violation.violation_id,
            generated_by=investigator.investigator_id
        )
        db.add(report)
    
    db.commit()
    print(f"  ✓ Created {len(selected_violations)} reports")


def add_dummy_notifications(db: Session, users_dict: dict, num_notifications: int = 100):
    """Add dummy notifications for all user types."""
    print("\n=== Adding Dummy Notifications ===")
    
    notifications_created = 0
    
    # Notifications for admins
    for admin in users_dict['admins']:
        for _ in range(random.randint(5, 15)):
            notif_type = random.choice(NOTIFICATION_TYPES)
            title = random.choice(NOTIFICATION_TITLES[notif_type])
            
            notification = Notification(
                user_id=admin.admin_id,
                user_type="admin",
                type=notif_type,
                title=title,
                message=f"Notification message for {title}",
                read=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 720))
            )
            db.add(notification)
            notifications_created += 1
    
    # Notifications for invigilators
    for invigilator in users_dict['invigilators']:
        for _ in range(random.randint(3, 10)):
            notif_type = random.choice(NOTIFICATION_TYPES)
            title = random.choice(NOTIFICATION_TITLES[notif_type])
            
            notification = Notification(
                user_id=invigilator.invigilator_id,
                user_type="invigilator",
                type=notif_type,
                title=title,
                message=f"Notification message for {title}",
                read=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 720))
            )
            db.add(notification)
            notifications_created += 1
    
    # Notifications for investigators
    for investigator in users_dict['investigators']:
        for _ in range(random.randint(5, 15)):
            notif_type = random.choice(NOTIFICATION_TYPES)
            title = random.choice(NOTIFICATION_TITLES[notif_type])
            
            notification = Notification(
                user_id=investigator.investigator_id,
                user_type="investigator",
                type=notif_type,
                title=title,
                message=f"Notification message for {title}",
                read=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 720))
            )
            db.add(notification)
            notifications_created += 1
    
    # Notifications for students
    for student in users_dict['students'][:20]:  # Only first 20 students
        for _ in range(random.randint(1, 5)):
            notification = Notification(
                user_id=student.student_id,
                user_type="student",
                type="exam",
                title="Exam Reminder",
                message="You have an upcoming exam scheduled",
                read=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 168))
            )
            db.add(notification)
            notifications_created += 1
    
    db.commit()
    print(f"  ✓ Created {notifications_created} notifications")


def add_dummy_video_streams(db: Session, rooms: list, exams: list, num_streams: int = 20):
    """Add dummy video streams."""
    print("\n=== Adding Dummy Video Streams ===")
    
    streams = []
    stream_types = ["live", "recorded"]
    statuses = ["pending", "processing", "completed", "failed"]
    
    selected_rooms = random.sample(rooms, min(num_streams, len(rooms)))
    
    for room in selected_rooms:
        # Find exam for this room
        exam = next((e for e in exams if e.exam_id == room.exam_id), None)
        if not exam:
            continue
        
        stream = VideoStream(
            room_id=room.room_id,
            exam_id=exam.exam_id,
            stream_type=random.choice(stream_types),
            source_url=room.stream_url or f"http://example.com/stream/{random.randint(1000, 9999)}.mjpeg",
            status=random.choice(statuses),
            created_at=datetime.utcnow() - timedelta(hours=random.randint(0, 720)),
            started_at=datetime.utcnow() - timedelta(hours=random.randint(0, 700)) if random.choice([True, False]) else None,
            completed_at=datetime.utcnow() - timedelta(hours=random.randint(0, 680)) if random.choice([True, False]) else None
        )
        db.add(stream)
        db.flush()
        streams.append(stream)
    
    db.commit()
    print(f"  ✓ Created {len(streams)} video streams")
    return streams


def add_dummy_processing_jobs(db: Session, streams: list, num_jobs: int = 15):
    """Add dummy processing jobs."""
    print("\n=== Adding Dummy Processing Jobs ===")
    
    jobs = []
    statuses = ["queued", "processing", "completed", "failed"]
    
    selected_streams = random.sample(streams, min(num_jobs, len(streams)))
    
    for stream in selected_streams:
        job_status = random.choice(statuses)
        job = ProcessingJob(
            stream_id=stream.stream_id,
            status=job_status,
            progress=random.uniform(0.0, 100.0) if job_status != "queued" else 0.0,
            total_frames=random.randint(1000, 10000),
            processed_frames=random.randint(0, 9000),
            detected_activities=random.randint(0, 50),
            detected_violations=random.randint(0, 10),
            created_at=stream.created_at + timedelta(minutes=random.randint(1, 60)),
            started_at=stream.created_at + timedelta(minutes=random.randint(5, 120)) if job_status in ["processing", "completed"] else None,
            completed_at=stream.created_at + timedelta(minutes=random.randint(60, 360)) if job_status == "completed" else None,
            error_message=f"Error occurred: {random.choice(['Timeout', 'Network error', 'Processing failed'])}" if job_status == "failed" else None
        )
        db.add(job)
        db.flush()
        jobs.append(job)
    
    db.commit()
    print(f"  ✓ Created {len(jobs)} processing jobs")
    return jobs


def add_dummy_frame_logs(db: Session, jobs: list, num_logs: int = 50):
    """Add dummy frame logs."""
    print("\n=== Adding Dummy Frame Logs ===")
    
    logs_created = 0
    
    for job in jobs[:5]:  # Only for first 5 jobs
        num_frames = random.randint(5, 15)
        for i in range(num_frames):
            frame_log = FrameLog(
                job_id=job.job_id,
                frame_number=random.randint(1, job.total_frames or 1000),
                timestamp=job.created_at + timedelta(seconds=random.randint(0, 3600)),
                detected_objects='{"persons": 1, "devices": 0}',
                activity_detected=random.choice(ACTIVITY_TYPES) if random.choice([True, False]) else None,
                confidence_score=random.uniform(0.0, 1.0) if random.choice([True, False]) else None,
                frame_path=f"/frames/job_{job.job_id}/frame_{i}.jpg"
            )
            db.add(frame_log)
            logs_created += 1
    
    db.commit()
    print(f"  ✓ Created {logs_created} frame logs")


def main():
    """Main function to populate database with dummy data."""
    print("=" * 60)
    print("DUMMY DATA GENERATION SCRIPT")
    print("=" * 60)
    print("\nThis script will populate the database with sample data.")
    print("All users will have the default password:", DEFAULT_PASSWORD)
    print("\nWarning: This will add data to your database.")

    # Auto-confirm for non-interactive execution
    print("\nAuto-confirmed. Continuing with dummy data generation...")
    response = "yes"

    db: Session = SessionLocal()
    
    try:
        # Step 1: Create users (must be first - no dependencies)
        users_dict = add_dummy_users(db, num_each=5)
        
        # Step 2: Create exams (no dependencies)
        exams = add_dummy_exams(db, num_exams=10)
        
        # Step 3: Create rooms (depends on exams)
        rooms = add_dummy_rooms(db, exams, rooms_per_exam=2)
        
        # Step 4: Create seats (depends on rooms and students)
        add_dummy_seats(db, rooms, users_dict['students'])
        
        # Step 5: Create student activities (depends on students and exams)
        activities = add_dummy_student_activities(db, users_dict['students'], exams, num_activities=50)
        
        # Step 6: Create invigilator activities (depends on invigilators and rooms)
        add_dummy_invigilator_activities(db, users_dict['invigilators'], rooms, num_activities=30)
        
        # Step 7: Create violations (depends on student activities)
        violations = add_dummy_violations(db, activities, num_violations=20)
        
        # Step 8: Create reports (depends on violations and investigators)
        add_dummy_reports(db, violations, users_dict['investigators'], num_reports=10)
        
        # Step 9: Create notifications (depends on all users)
        add_dummy_notifications(db, users_dict, num_notifications=100)
        
        # Step 10: Create video streams (depends on rooms and exams)
        streams = add_dummy_video_streams(db, rooms, exams, num_streams=20)
        
        # Step 11: Create processing jobs (depends on video streams)
        jobs = add_dummy_processing_jobs(db, streams, num_jobs=15)
        
        # Step 12: Create frame logs (depends on processing jobs)
        add_dummy_frame_logs(db, jobs, num_logs=50)
        
        print("\n" + "=" * 60)
        print("✅ DUMMY DATA GENERATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  - Admins: {len(users_dict['admins'])}")
        print(f"  - Invigilators: {len(users_dict['invigilators'])}")
        print(f"  - Investigators: {len(users_dict['investigators'])}")
        print(f"  - Students: {len(users_dict['students'])}")
        print(f"  - Exams: {len(exams)}")
        print(f"  - Rooms: {len(rooms)}")
        print(f"  - Student Activities: {len(activities)}")
        print(f"  - Violations: {len(violations)}")
        print(f"\nDefault password for all users: {DEFAULT_PASSWORD}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
