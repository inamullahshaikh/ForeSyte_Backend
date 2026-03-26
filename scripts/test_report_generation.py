#!/usr/bin/env python3
"""
Script to test comprehensive report generation with violations.

This script will:
1. Check if exams and violations exist
2. Generate reports in all formats (PDF, CSV, JSON)
3. Verify files are created correctly
4. Display report summaries
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import time

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
    Exam, StudentActivity, Violation, Report, Student
)
from uuid import UUID

def test_report_generation():
    """Test comprehensive report generation."""
    db = SessionLocal()
    try:
        print("=" * 80)
        print("TESTING REPORT GENERATION WITH VIOLATIONS")
        print("=" * 80)
        
        # Step 1: Check for exams with violations
        print("\n1. Checking for exams with violations...")
        exams_with_violations = db.query(Exam).join(
            StudentActivity, Exam.exam_id == StudentActivity.exam_id
        ).join(
            Violation, StudentActivity.activity_id == Violation.activity_id
        ).distinct().all()
        
        if not exams_with_violations:
            print("   ❌ No exams with violations found!")
            print("   Please run: python scripts/add_exam_violations.py")
            return
        
        print(f"   ✓ Found {len(exams_with_violations)} exam(s) with violations")
        
        # Display exam options
        print("\nAvailable exams:")
        for i, exam in enumerate(exams_with_violations, 1):
            # Count violations for this exam
            violation_count = db.query(Violation).join(
                StudentActivity, Violation.activity_id == StudentActivity.activity_id
            ).filter(StudentActivity.exam_id == exam.exam_id).count()
            
            activity_count = db.query(StudentActivity).filter(
                StudentActivity.exam_id == exam.exam_id
            ).count()
            
            print(f"   {i}. {exam.course}")
            print(f"      ID: {exam.exam_id}")
            print(f"      Date: {exam.exam_date}")
            print(f"      Activities: {activity_count}, Violations: {violation_count}")
        
        # Step 2: Get user selection
        if len(exams_with_violations) > 1:
            choice = input(f"\nSelect exam (1-{len(exams_with_violations)}) [default: 1]: ").strip()
            exam_index = int(choice) - 1 if choice.isdigit() else 0
        else:
            exam_index = 0
        
        selected_exam = exams_with_violations[exam_index]
        print(f"\n✓ Selected: {selected_exam.course}")
        
        # Step 3: Gather detailed statistics
        print("\n2. Gathering detailed statistics...")
        activities = db.query(StudentActivity).filter(
            StudentActivity.exam_id == selected_exam.exam_id
        ).all()
        
        violations = db.query(Violation).join(
            StudentActivity, Violation.activity_id == StudentActivity.activity_id
        ).filter(StudentActivity.exam_id == selected_exam.exam_id).all()
        
        unique_students = set(act.student_id for act in activities)
        
        print(f"   Activities: {len(activities)}")
        print(f"   Violations: {len(violations)}")
        print(f"   Unique students: {len(unique_students)}")
        
        # Display sample data
        if activities:
            print(f"\n   Sample activities:")
            for act in activities[:3]:
                student = db.query(Student).filter(Student.student_id == act.student_id).first()
                violation = db.query(Violation).filter(Violation.activity_id == act.activity_id).first()
                print(f"   - {student.name if student else 'Unknown'}: {act.activity_type}")
                if violation:
                    print(f"     Violation: {violation.violation_type} (Severity: {violation.severity})")
        
        # Step 4: Test file generation
        print("\n3. Testing report file generation...")
        print("   Note: This script tests the file generation functions directly.")
        print("   For full async generation, use the API endpoints.")
        
        from database.api.reports import generate_json_report, generate_csv_report, generate_pdf_report
        from datetime import datetime
        
        # Prepare test data
        test_data = {
            'title': f'Exam Report - {selected_exam.course}',
            'generated_at': datetime.utcnow().isoformat(),
            'report_type': 'exam',
            'summary': {
                'total_activities': len(activities),
                'total_violations': len(violations),
                'unique_students_flagged': len(unique_students),
                'exam_name': selected_exam.course,
                'exam_date': str(selected_exam.exam_date),
                'severity_breakdown': {
                    'low': 0,
                    'medium': 0,
                    'high': 0,
                    'critical': 0
                }
            },
            'exam': {
                'id': str(selected_exam.exam_id),
                'name': selected_exam.course,
                'date': str(selected_exam.exam_date),
                'start_time': str(selected_exam.start_time) if selected_exam.start_time else 'N/A',
                'end_time': str(selected_exam.end_time) if selected_exam.end_time else 'N/A'
            },
            'activities': []
        }
        
        # Build detailed activity data
        for act in activities[:50]:  # Limit for test
            student = db.query(Student).filter(Student.student_id == act.student_id).first()
            violation = db.query(Violation).filter(Violation.activity_id == act.activity_id).first()
            
            # Count severity
            if act.severity:
                severity_key = 'low' if act.severity in ['low', 1] else \
                              'medium' if act.severity in ['medium', 2] else \
                              'high' if act.severity in ['high', 3] else 'critical'
                test_data['summary']['severity_breakdown'][severity_key] += 1
            
            activity_detail = {
                'activity_id': str(act.activity_id),
                'activity_type': act.activity_type or 'Unknown',
                'timestamp': act.timestamp.strftime('%Y-%m-%d %H:%M:%S') if act.timestamp else '',
                'student_id': str(act.student_id),
                'student_name': student.name if student else 'Unknown',
                'student_roll_number': student.roll_number if student else 'N/A',
                'severity': str(act.severity) if act.severity else 'N/A',
                'confidence': f"{act.confidence * 100:.1f}%" if act.confidence else 'N/A',
                'evidence_url': act.evidence_url or 'N/A',
                'description': f"{act.activity_type} detected",
                'violation': None
            }
            
            if violation:
                activity_detail['violation'] = {
                    'violation_id': str(violation.violation_id),
                    'type': violation.violation_type or 'N/A',
                    'severity': violation.severity or 0,
                    'status': violation.status or 'pending',
                    'timestamp': violation.timestamp.strftime('%Y-%m-%d %H:%M:%S') if violation.timestamp else ''
                }
            
            test_data['activities'].append(activity_detail)
        
        # Generate files
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_filename = f"test_exam_report_{selected_exam.exam_id}_{timestamp}"
        
        formats_to_test = ['json', 'csv', 'pdf']
        results = {}
        
        for fmt in formats_to_test:
            filename = f"{base_filename}.{fmt}"
            filepath = f"reports/{filename}"
            
            print(f"\n   Testing {fmt.upper()} generation...")
            if fmt == 'json':
                success = generate_json_report(test_data, filepath)
            elif fmt == 'csv':
                success = generate_csv_report(test_data, filepath)
            elif fmt == 'pdf':
                success = generate_pdf_report(test_data, filepath)
            
            results[fmt] = success
            if success:
                file_path = Path(SRC_DIR) / "uploads" / "reports" / filename
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    print(f"   ✓ {fmt.upper()} generated successfully")
                    print(f"     File: {filename}")
                    print(f"     Size: {file_size:,} bytes")
                else:
                    print(f"   ⚠️  {fmt.upper()} function returned success but file not found")
            else:
                print(f"   ❌ {fmt.upper()} generation failed")
        
        # Step 5: Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Exam: {selected_exam.course}")
        print(f"Activities: {len(activities)}")
        print(f"Violations: {len(violations)}")
        print(f"Students: {len(unique_students)}")
        print("\nFile Generation Results:")
        for fmt, success in results.items():
            status = "✓ SUCCESS" if success else "❌ FAILED"
            print(f"  {fmt.upper()}: {status}")
        
        if all(results.values()):
            print("\n✓ All tests passed!")
            print("\nNext steps:")
            print("1. Restart your backend server")
            print("2. Generate reports via the API")
            print("3. Test view and download buttons in the frontend")
        else:
            print("\n⚠️  Some tests failed. Check the errors above.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_report_generation()
