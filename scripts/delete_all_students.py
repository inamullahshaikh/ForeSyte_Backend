#!/usr/bin/env python3
"""
Script to delete all students from the database.

WARNING: This script will permanently delete all student records and their related data.
Make sure you have a database backup before running this script.

Related data that will be affected:
- Student seat assignments (will be set to NULL)
- Student activities
- Violations linked to student activities
- Reports linked to violations
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Get the script directory and resolve paths
SCRIPT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = SCRIPT_DIR.parent
SRC_DIR = BACKEND_DIR / "src"

# Load environment variables from .env file (should be in backend or project root)
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
from database.db import SessionLocal, engine
from database.models import Student, Seat, StudentActivity, Violation, Report

def delete_all_students(confirm: bool = False):
    """
    Delete all students from the database.
    
    Args:
        confirm: If True, skip confirmation prompt
        
    Returns:
        int: Number of students deleted
    """
    db: Session = SessionLocal()
    
    try:
        # Count students before deletion
        student_count = db.query(Student).count()
        
        if student_count == 0:
            print("No students found in the database.")
            return 0
        
        # Show summary of what will be deleted
        print("\n" + "="*60)
        print("STUDENT DELETION SUMMARY")
        print("="*60)
        print(f"Total students to delete: {student_count}")
        
        # Count related records
        seats_count = db.query(Seat).filter(Seat.student_id.isnot(None)).count()
        activities_count = db.query(StudentActivity).count()
        
        # Count violations and reports linked to student activities
        violation_count = db.query(Violation).join(
            StudentActivity, Violation.activity_id == StudentActivity.activity_id
        ).count()
        
        report_count = db.query(Report).join(
            Violation, Report.violation_id == Violation.violation_id
        ).join(
            StudentActivity, Violation.activity_id == StudentActivity.activity_id
        ).count()
        
        print(f"\nRelated records that will be affected:")
        print(f"  - Seat assignments: {seats_count} (student_id will be set to NULL)")
        print(f"  - Student activities: {activities_count}")
        print(f"  - Violations: {violation_count}")
        print(f"  - Reports: {report_count}")
        print("="*60 + "\n")
        
        # Confirmation prompt
        if not confirm:
            response = input(f"Are you sure you want to delete ALL {student_count} students? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Deletion cancelled.")
                return 0
        
        print("\nStarting deletion process...")
        
        # Step 1: Delete reports linked to student activities
        print("Step 1: Deleting reports linked to student violations...")
        reports_to_delete = db.query(Report).join(
            Violation, Report.violation_id == Violation.violation_id
        ).join(
            StudentActivity, Violation.activity_id == StudentActivity.activity_id
        ).all()
        
        for report in reports_to_delete:
            db.delete(report)
        
        if reports_to_delete:
            db.commit()
            print(f"  Deleted {len(reports_to_delete)} reports.")
        
        # Step 2: Delete violations linked to student activities
        print("Step 2: Deleting violations linked to student activities...")
        violations_to_delete = db.query(Violation).join(
            StudentActivity, Violation.activity_id == StudentActivity.activity_id
        ).all()
        
        for violation in violations_to_delete:
            db.delete(violation)
        
        if violations_to_delete:
            db.commit()
            print(f"  Deleted {len(violations_to_delete)} violations.")
        
        # Step 3: Delete student activities
        print("Step 3: Deleting student activities...")
        activities_deleted = db.query(StudentActivity).delete(synchronize_session=False)
        db.commit()
        print(f"  Deleted {activities_deleted} student activities.")
        
        # Step 4: Remove student assignments from seats (set to NULL)
        print("Step 4: Removing student assignments from seats...")
        seats_updated = db.query(Seat).filter(Seat.student_id.isnot(None)).update(
            {Seat.student_id: None}, synchronize_session=False
        )
        db.commit()
        print(f"  Updated {seats_updated} seat assignments (set student_id to NULL).")
        
        # Step 5: Delete all students
        print("Step 5: Deleting all students...")
        students_deleted = db.query(Student).delete(synchronize_session=False)
        db.commit()
        print(f"  Deleted {students_deleted} students.")
        
        print("\n" + "="*60)
        print("DELETION COMPLETE")
        print("="*60)
        print(f"Successfully deleted {students_deleted} students from the database.")
        print("="*60 + "\n")
        
        return students_deleted
        
    except Exception as e:
        db.rollback()
        print(f"\nERROR: An error occurred during deletion: {str(e)}")
        print("Transaction rolled back. No changes were made.")
        raise
    
    finally:
        db.close()


def main():
    """Main function with command-line argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Delete all students from the database.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (will ask for confirmation)
  python delete_all_students.py
  
  # Non-interactive mode (skip confirmation)
  python delete_all_students.py --yes
  
  # Show help
  python delete_all_students.py --help
        """
    )
    
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt and delete immediately'
    )
    
    args = parser.parse_args()
    
    try:
        delete_all_students(confirm=args.yes)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

