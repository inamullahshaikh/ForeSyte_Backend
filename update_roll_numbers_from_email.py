"""
Script to update student roll numbers by extracting them from email addresses.
Email format: xYYAAAA@nu.edu.pk -> Roll number: YYX-AAAA
Example: k220857@nu.edu.pk -> 22K-0857
"""

import sys
import re
from pathlib import Path
from sqlalchemy.orm import Session

# Add src directory to path to import database modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.db import SessionLocal
from database.models import Student


def email_to_roll_number(email: str) -> str:
    """
    Convert email to roll number format.
    Format: xYYAAAA@nu.edu.pk -> YYX-AAAA
    Example: k220857@nu.edu.pk -> 22K-0857
    Example: i220502@nu.edu.pk -> 22I-0502
    
    Args:
        email: Email address in format xYYAAAA@nu.edu.pk
        
    Returns:
        Roll number in format YYX-AAAA
    """
    # Remove any whitespace and convert to lowercase
    email = email.strip().lower()
    
    # Remove @nu.edu.pk if present
    email = email.replace("@nu.edu.pk", "")
    
    # Pattern: [letter][2 digits][4 digits]
    # Example: k220857 -> k, 22, 0857
    match = re.match(r'^([a-z])(\d{2})(\d{4})$', email)
    if not match:
        raise ValueError(f"Invalid email format: {email}. Expected format: xYYAAAA@nu.edu.pk")
    
    letter = match.group(1).upper()  # e.g., "k" -> "K"
    year = match.group(2)  # e.g., "22"
    number = match.group(3)  # e.g., "0857"
    
    # Format: YYX-AAAA
    roll_number = f"{year}{letter}-{number}"
    return roll_number


def update_all_students_roll_numbers(db: Session) -> dict:
    """
    Update roll numbers for all students by extracting from their email addresses.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with statistics: {'success': count, 'failed': count, 'skipped': count, 'errors': list}
    """
    stats = {
        'success': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    # Get all students
    students = db.query(Student).all()
    print(f"Found {len(students)} students in database")
    print()
    
    for student in students:
        try:
            if not student.email:
                print(f"⚠️  Skipped: Student {student.student_id} has no email")
                stats['skipped'] += 1
                continue
            
            # Extract roll number from email
            try:
                roll_number = email_to_roll_number(student.email)
            except ValueError as e:
                error_msg = f"Invalid email format for {student.email}: {str(e)}"
                print(f"❌ {error_msg}")
                stats['errors'].append(error_msg)
                stats['failed'] += 1
                continue
            
            # Check if roll number already matches
            if student.roll_number == roll_number:
                print(f"⏭️  Skipped (already correct): {roll_number} - {student.name} ({student.email})")
                stats['skipped'] += 1
                continue
            
            # Update roll number
            old_roll = student.roll_number or "None"
            student.roll_number = roll_number
            db.commit()
            db.refresh(student)
            
            print(f"🔄 Updated: {roll_number} - {student.name} ({student.email}) - Changed from {old_roll}")
            stats['success'] += 1
            
        except Exception as e:
            error_msg = f"Error processing {student.email}: {str(e)}"
            print(f"❌ {error_msg}")
            stats['errors'].append(error_msg)
            stats['failed'] += 1
            db.rollback()
    
    return stats


def main():
    """Main function to run the update process."""
    print("=" * 80)
    print("Update Student Roll Numbers from Email")
    print("=" * 80)
    print("This script will extract roll numbers from student emails and update the database.")
    print("Email format: xYYAAAA@nu.edu.pk -> Roll number: YYX-AAAA")
    print()
    
    response = input("Do you want to proceed with updating all students? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Operation cancelled.")
        return
    
    db = SessionLocal()
    
    try:
        print("\n" + "=" * 80)
        print("Updating student roll numbers...")
        print("=" * 80)
        print()
        
        stats = update_all_students_roll_numbers(db)
        
        # Print summary
        print("\n" + "=" * 80)
        print("Update Summary")
        print("=" * 80)
        print(f"🔄 Successfully updated: {stats['success']}")
        print(f"⏭️  Skipped (no changes needed): {stats['skipped']}")
        print(f"❌ Failed: {stats['failed']}")
        
        if stats['errors']:
            print("\nErrors:")
            for error in stats['errors'][:20]:  # Show first 20 errors
                print(f"  - {error}")
            if len(stats['errors']) > 20:
                print(f"  ... and {len(stats['errors']) - 20} more errors")
        
        print("\n✅ Update process completed!")
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

