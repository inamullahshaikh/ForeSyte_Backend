"""
Script to seed dummy data for testing the investigator portal.
Run this script to populate the database with sample data.
"""
import os
import uuid
from datetime import datetime, timedelta, date, time
from sqlalchemy.orm import Session

from database.db import SessionLocal
from database.models import (
    Student, Invigilator, Investigator, Exam, Room, Seat,
    StudentActivity, InvigilatorActivity, Violation, Report
)
from database.auth import hash_password


def seed_dummy_data():
    """Seed the database with dummy data."""
    db: Session = SessionLocal()
    
    try:
        print("🌱 Starting to seed dummy data...")
        
        # 1. Create Investigators
        print("\n📋 Creating Investigators...")
        investigator1 = Investigator(
            investigator_id=uuid.uuid4(),
            name="Dr. Sarah Ahmed",
            email="sarah.ahmed@university.edu",
            designation="Senior Investigator",
            password_hash=hash_password("password123"),
            created_at=datetime.utcnow() - timedelta(days=30)
        )
        investigator2 = Investigator(
            investigator_id=uuid.uuid4(),
            name="Mr. Ali Hassan",
            email="ali.hassan@university.edu",
            designation="Investigator",
            password_hash=hash_password("password123"),
            created_at=datetime.utcnow() - timedelta(days=20)
        )
        db.add_all([investigator1, investigator2])
        db.flush()
        print(f"✅ Created 2 investigators")
        
        # 2. Create Students
        print("\n👥 Creating Students...")
        students = []
        student_names = [
            ("Ahmed Ali", "ahmed.ali@student.edu", "20220123"),
            ("Fatima Khan", "fatima.khan@student.edu", "20220456"),
            ("Omar Hassan", "omar.hassan@student.edu", "20220789"),
            ("Sara Ahmed", "sara.ahmed@student.edu", "20220321"),
            ("Youssef Ibrahim", "youssef.ibrahim@student.edu", "20220654"),
            ("Ayesha Malik", "ayesha.malik@student.edu", "20220987"),
            ("Hassan Raza", "hassan.raza@student.edu", "20221234"),
            ("Zainab Shah", "zainab.shah@student.edu", "20221567"),
        ]
        
        for name, email, roll_number in student_names:
            student = Student(
                student_id=uuid.uuid4(),
                name=name,
                email=email,
                roll_number=roll_number,
                password_hash=hash_password("password123"),
                created_at=datetime.utcnow() - timedelta(days=60)
            )
            students.append(student)
            db.add(student)
        
        db.flush()
        print(f"✅ Created {len(students)} students")
        
        # 3. Create Invigilators
        print("\n👨‍🏫 Creating Invigilators...")
        invigilators = []
        invigilator_names = [
            ("Dr. Muhammad Ahmed", "muhammad.ahmed@university.edu"),
            ("Ms. Ayesha Khan", "ayesha.khan@university.edu"),
            ("Mr. Ali Hassan", "ali.hassan.invigilator@university.edu"),
        ]
        
        for name, email in invigilator_names:
            invigilator = Invigilator(
                invigilator_id=uuid.uuid4(),
                name=name,
                email=email,
                password_hash=hash_password("password123"),
                created_at=datetime.utcnow() - timedelta(days=40)
            )
            invigilators.append(invigilator)
            db.add(invigilator)
        
        db.flush()
        print(f"✅ Created {len(invigilators)} invigilators")
        
        # 4. Create Exams
        print("\n📝 Creating Exams...")
        exam1 = Exam(
            exam_id=uuid.uuid4(),
            course="CS101 Final Examination",
            exam_date=date.today() - timedelta(days=2),
            start_time=time(9, 0),
            end_time=time(12, 0),
            created_at=datetime.utcnow() - timedelta(days=10)
        )
        exam2 = Exam(
            exam_id=uuid.uuid4(),
            course="MATH201 Midterm",
            exam_date=date.today() - timedelta(days=1),
            start_time=time(14, 0),
            end_time=time(16, 0),
            created_at=datetime.utcnow() - timedelta(days=8)
        )
        exam3 = Exam(
            exam_id=uuid.uuid4(),
            course="PHY301 Final",
            exam_date=date.today(),
            start_time=time(10, 0),
            end_time=time(13, 0),
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        db.add_all([exam1, exam2, exam3])
        db.flush()
        print(f"✅ Created 3 exams")
        
        # 5. Create Rooms
        print("\n🏢 Creating Rooms...")
        rooms = []
        room_data = [
            ("Room 101", "Block A", 30, exam1.exam_id),
            ("Room 102", "Block A", 25, exam2.exam_id),
            ("Room 103", "Block B", 35, exam3.exam_id),
        ]
        
        for room_number, block, total_seats, exam_id in room_data:
            room = Room(
                room_id=uuid.uuid4(),
                room_number=room_number,
                block=block,
                total_seats=total_seats,
                exam_id=exam_id,
                stream_url=f"http://192.168.1.100:8080/video.mjpeg"  # Dummy stream URL
            )
            rooms.append(room)
            db.add(room)
        
        db.flush()
        print(f"✅ Created {len(rooms)} rooms")
        
        # 6. Create Seats (assign students to rooms)
        print("\n🪑 Creating Seat Assignments...")
        seat_assignments = []
        seat_numbers = ["A-15", "B-10", "C-05", "A-20", "D-12", "B-05", "C-10", "A-08"]
        
        for i, student in enumerate(students):
            room = rooms[i % len(rooms)]  # Distribute students across rooms
            seat = Seat(
                seat_id=uuid.uuid4(),
                seat_number=seat_numbers[i],
                room_id=room.room_id,
                student_id=student.student_id
            )
            seat_assignments.append(seat)
            db.add(seat)
        
        db.flush()
        print(f"✅ Created {len(seat_assignments)} seat assignments")
        
        # 7. Create Student Activities
        print("\n📊 Creating Student Activities...")
        activities = []
        activity_types = [
            ("Phone Usage", "high", 0.95),
            ("Looking Around", "medium", 0.82),
            ("Hand Gesture", "medium", 0.78),
            ("Left Seat", "low", 0.91),
            ("Paper Exchange", "high", 0.88),
            ("Talking", "medium", 0.75),
            ("Unauthorized Movement", "low", 0.85),
        ]
        
        base_time = datetime.utcnow() - timedelta(hours=2)
        for i, (activity_type, severity, confidence) in enumerate(activity_types):
            student = students[i % len(students)]
            exam = [exam1, exam2, exam3][i % 3]
            room = rooms[i % len(rooms)]
            
            activity = StudentActivity(
                activity_id=uuid.uuid4(),
                student_id=student.student_id,
                exam_id=exam.exam_id,
                timestamp=base_time + timedelta(minutes=i * 15),
                activity_type=activity_type,
                severity=severity,
                confidence=confidence,
                evidence_url=f"/evidence/{activity_type.lower().replace(' ', '_')}_{i+1}.jpg"
            )
            activities.append(activity)
            db.add(activity)
        
        db.flush()
        print(f"✅ Created {len(activities)} student activities")
        
        # 8. Create Violations
        print("\n⚠️ Creating Violations...")
        violations = []
        violation_data = [
            ("Phone Usage", 3, "pending"),
            ("Looking Around", 2, "pending"),
            ("Hand Gesture", 2, "confirmed"),
            ("Unauthorized Movement", 1, "dismissed"),
            ("Phone Usage", 3, "pending"),
            ("Paper Exchange", 3, "pending"),
            ("Talking", 2, "confirmed"),
        ]
        
        for i, (violation_type, severity, status) in enumerate(violation_data):
            if i < len(activities):
                activity = activities[i]
                violation = Violation(
                    violation_id=uuid.uuid4(),
                    activity_id=activity.activity_id,
                    violation_type=violation_type,
                    timestamp=activity.timestamp,
                    severity=severity,
                    status=status,
                    evidence_url=activity.evidence_url
                )
                violations.append(violation)
                db.add(violation)
        
        db.flush()
        print(f"✅ Created {len(violations)} violations")
        
        # 9. Create Invigilator Activities
        print("\n👨‍💼 Creating Invigilator Activities...")
        invigilator_activities = []
        invigilator_activity_types = [
            ("Entered Room", "Started exam supervision"),
            ("Absent from Zone", "Left room for 15+ minutes - potential negligence"),
            ("Phone Usage", "Using phone during exam - unauthorized"),
            ("Walking Around", "Regular patrol of exam hall"),
            ("Idle Period", "Sitting idle for prolonged period"),
        ]
        
        base_time = datetime.utcnow() - timedelta(hours=3)
        for i, (activity_type, notes) in enumerate(invigilator_activity_types):
            invigilator = invigilators[i % len(invigilators)]
            room = rooms[i % len(rooms)]
            
            invig_activity = InvigilatorActivity(
                activity_id=uuid.uuid4(),
                invigilator_id=invigilator.invigilator_id,
                room_id=room.room_id,
                timestamp=base_time + timedelta(minutes=i * 20),
                activity_type=activity_type,
                notes=notes
            )
            invigilator_activities.append(invig_activity)
            db.add(invig_activity)
        
        db.flush()
        print(f"✅ Created {len(invigilator_activities)} invigilator activities")
        
        # 10. Create Reports
        print("\n📄 Creating Reports...")
        reports = []
        report_data = [
            ("incident", violations[0].violation_id if violations else None),
            ("exam", violations[1].violation_id if len(violations) > 1 else None),
            ("incident", violations[2].violation_id if len(violations) > 2 else None),
            ("exam", violations[3].violation_id if len(violations) > 3 else None),
        ]
        
        # Ensure reports directory exists
        current_file = Path(__file__)  # seed_dummy_data.py
        src_dir = current_file.parent  # src/
        backend_dir = src_dir.parent  # FORESYTE_Backend/
        reports_dir = backend_dir / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Find a sample PDF to copy (or create a placeholder)
        # Look for any existing PDF in the reports directory
        sample_pdf = None
        for pdf_file in reports_dir.glob("*.pdf"):
            sample_pdf = pdf_file
            break
        
        # If no PDF exists, create a simple text-based placeholder
        # (In production, reports would be generated properly)
        for i, (report_type, violation_id) in enumerate(report_data):
            if violation_id:
                report_date = date.today() - timedelta(days=i)
                filename = f"{report_type}_report_{report_date}.pdf"
                file_path = reports_dir / filename
                
                # Create a simple PDF placeholder if no sample exists
                if not sample_pdf:
                    # Create a minimal text file that looks like a PDF header
                    with open(file_path, 'wb') as f:
                        # Write a minimal PDF structure
                        pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 100 >>
stream
BT
/F1 12 Tf
100 700 Td
({report_type.upper()} Report - {report_date}) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000205 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
305
%%EOF""".encode('utf-8')
                        f.write(pdf_content)
                else:
                    # Copy the sample PDF
                    shutil.copy2(sample_pdf, file_path)
                
                report = Report(
                    report_id=uuid.uuid4(),
                    report_type=report_type,
                    generated_date=report_date,
                    file_path=f"/reports/{filename}",
                    violation_id=violation_id,
                    generated_by=investigator1.investigator_id
                )
                reports.append(report)
                db.add(report)
        
        db.flush()
        print(f"✅ Created {len(reports)} reports with PDF files")
        
        # Commit all changes
        db.commit()
        print("\n🎉 Successfully seeded all dummy data!")
        print("\n📊 Summary:")
        print(f"   - Investigators: 2")
        print(f"   - Students: {len(students)}")
        print(f"   - Invigilators: {len(invigilators)}")
        print(f"   - Exams: 3")
        print(f"   - Rooms: {len(rooms)}")
        print(f"   - Seat Assignments: {len(seat_assignments)}")
        print(f"   - Student Activities: {len(activities)}")
        print(f"   - Violations: {len(violations)}")
        print(f"   - Invigilator Activities: {len(invigilator_activities)}")
        print(f"   - Reports: {len(reports)}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_dummy_data()

