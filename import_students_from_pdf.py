"""
Script to import students from seating plan PDF into the database.
Extracts student information and creates Student records.
"""

import re
import sys
import argparse
from pathlib import Path
import pdfplumber
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Add src directory to path to import database modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.db import SessionLocal, engine
from database.models import Student, Base
from database.auth import hash_password


def roll_number_to_email(roll_number: str) -> str:
    """
    Convert roll number to email format.
    Format: XXI-YYYY -> iXXYYYY@nu.edu.pk
    Example: 22K-0857 -> k220857@nu.edu.pk
    Example: 22I-0502 -> i220502@nu.edu.pk
    Example: 24I-0003 -> i240003@nu.edu.pk
    Example: 221-0532 -> i220532@nu.edu.pk (handles lowercase 'i')
    
    Args:
        roll_number: Roll number in format XXI-YYYY or XX[letter]YYYY
        
    Returns:
        Email address in format iXXYYYY@nu.edu.pk
    """
    # Remove any whitespace
    roll_number = roll_number.strip()
    
    # Pattern: XX[Letter]-YYYY or XX[Letter]YYYY
    # Extract: first 2 digits, letter, last 4 digits
    # Handle both with and without dash, and case variations
    match = re.match(r'(\d{2})([A-Za-z])(?:-)?(\d{4})', roll_number)
    if not match:
        raise ValueError(f"Invalid roll number format: {roll_number}")
    
    year_prefix = match.group(1)  # e.g., "22"
    letter = match.group(2).lower()  # e.g., "k" or "i"
    number_suffix = match.group(3)  # e.g., "0857"
    
    # Format: [lowercase letter][year][number]@nu.edu.pk
    email = f"{letter}{year_prefix}{number_suffix}@nu.edu.pk"
    return email


def extract_students_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract student information from the seating plan PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries with student information:
        [{'roll_number': '22I-0502', 'name': 'Mohummad Haider Ali'}, ...]
    """
    students = []
    
    print(f"Opening PDF: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        print(f"PDF has {len(pdf.pages)} pages")
        
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"Processing page {page_num}...")
            
            # Extract tables from the page
            tables = page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue
                
                # Find header row (look for "Roll No." or "S. No.")
                header_row_idx = None
                for idx, row in enumerate(table):
                    if row and any(cell and ("Roll No" in str(cell) or "S. No" in str(cell)) for cell in row):
                        header_row_idx = idx
                        break
                
                if header_row_idx is None:
                    continue
                
                # Extract column indices
                header = table[header_row_idx]
                roll_col = None
                name_col = None
                
                for idx, cell in enumerate(header):
                    if cell and "Roll No" in str(cell):
                        roll_col = idx
                    if cell and "Name" in str(cell):
                        name_col = idx
                
                if roll_col is None or name_col is None:
                    continue
                
                # Extract student data from data rows
                for row_idx in range(header_row_idx + 1, len(table)):
                    row = table[row_idx]
                    if not row or len(row) <= max(roll_col, name_col):
                        continue
                    
                    roll_number = str(row[roll_col]).strip() if row[roll_col] else None
                    name = str(row[name_col]).strip() if row[name_col] else None
                    
                    # Validate roll number format (XXI-YYYY or XX[letter]YYYY)
                    if roll_number and name and re.match(r'\d{2}[A-Za-z](?:-)?\d{4}', roll_number):
                        # Skip if already added (avoid duplicates)
                        if not any(s['roll_number'] == roll_number for s in students):
                            students.append({
                                'roll_number': roll_number,
                                'name': name
                            })
                            print(f"  Found: {roll_number} - {name}")
    
    print(f"\nTotal students extracted: {len(students)}")
    return students


def insert_students_to_db(students: list[dict], db: Session, default_password: str = "password123") -> dict:
    """
    Insert or update students in the database.
    Updates existing students with roll numbers if missing.
    
    Args:
        students: List of student dictionaries with 'roll_number' and 'name'
        db: Database session
        default_password: Default password for new students (will be hashed)
        
    Returns:
        Dictionary with statistics: {'success': count, 'updated': count, 'failed': count, 'skipped': count, 'errors': list}
    """
    stats = {
        'success': 0,
        'updated': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    password_hash = hash_password(default_password)
    
    for student_data in students:
        roll_number = student_data['roll_number']
        name = student_data['name']
        
        try:
            # Convert roll number to email
            email = roll_number_to_email(roll_number)
            
            # Check if student already exists by email
            existing_by_email = db.query(Student).filter(Student.email == email).first()
            
            # Check if student already exists by roll number
            existing_by_roll = db.query(Student).filter(Student.roll_number == roll_number).first()
            
            if existing_by_email:
                # Student exists with this email - always update roll number and name
                updated = False
                change_notes = []
                old_roll = existing_by_email.roll_number
                
                # Update roll number if different or missing
                if existing_by_email.roll_number != roll_number:
                    existing_by_email.roll_number = roll_number
                    updated = True
                    if old_roll:
                        change_notes.append(f"updated roll number from {old_roll} to {roll_number}")
                    else:
                        change_notes.append("added roll number")
                
                # Update name if different
                if existing_by_email.name != name:
                    existing_by_email.name = name
                    updated = True
                    change_notes.append("updated name")
                
                if updated:
                    db.commit()
                    db.refresh(existing_by_email)
                    print(f"🔄 Updated: {roll_number} - {name} ({email}) - {', '.join(change_notes)}")
                    stats['updated'] += 1
                else:
                    print(f"⏭️  Skipped (no changes): {roll_number} - {name} ({email})")
                    stats['skipped'] += 1
                continue
            
            if existing_by_roll:
                # Student exists with this roll number - update email and name if different
                updated = False
                change_notes = []
                
                if existing_by_roll.email != email:
                    existing_by_roll.email = email
                    updated = True
                    change_notes.append("updated email")
                
                if existing_by_roll.name != name:
                    existing_by_roll.name = name
                    updated = True
                    change_notes.append("updated name")
                
                if updated:
                    db.commit()
                    db.refresh(existing_by_roll)
                    print(f"🔄 Updated: {roll_number} - {name} ({email}) - {', '.join(change_notes)}")
                    stats['updated'] += 1
                else:
                    print(f"⏭️  Skipped (no changes): {roll_number} - {name} ({email})")
                    stats['skipped'] += 1
                continue
            
            # Create new student
            new_student = Student(
                name=name,
                email=email,
                roll_number=roll_number,
                password_hash=password_hash
            )
            
            db.add(new_student)
            db.commit()
            db.refresh(new_student)
            
            print(f"✅ Inserted: {roll_number} - {name} ({email})")
            stats['success'] += 1
            
        except ValueError as e:
            error_msg = f"Invalid roll number format for {roll_number}: {str(e)}"
            print(f"❌ {error_msg}")
            stats['errors'].append(error_msg)
            stats['failed'] += 1
            db.rollback()
            
        except IntegrityError as e:
            error_msg = f"Database error for {roll_number}: {str(e)}"
            print(f"❌ {error_msg}")
            stats['errors'].append(error_msg)
            stats['failed'] += 1
            db.rollback()
            
        except Exception as e:
            error_msg = f"Unexpected error for {roll_number}: {str(e)}"
            print(f"❌ {error_msg}")
            stats['errors'].append(error_msg)
            stats['failed'] += 1
            db.rollback()
    
    return stats


def preview_students(students: list[dict], limit: int = 10):
    """
    Preview student data with email conversion.
    
    Args:
        students: List of student dictionaries
        limit: Number of students to preview
    """
    print("\n" + "=" * 80)
    print("Preview (first 10 students):")
    print("=" * 80)
    print(f"{'Roll Number':<15} {'Name':<30} {'Email':<30}")
    print("-" * 80)
    
    for student in students[:limit]:
        try:
            email = roll_number_to_email(student['roll_number'])
            print(f"{student['roll_number']:<15} {student['name']:<30} {email:<30}")
        except Exception as e:
            print(f"{student['roll_number']:<15} {student['name']:<30} ERROR: {str(e)}")
    
    if len(students) > limit:
        print(f"\n... and {len(students) - limit} more students")


def main():
    """Main function to run the import process."""
    parser = argparse.ArgumentParser(description='Import students from seating plan PDF')
    parser.add_argument('pdf_path', nargs='?', help='Path to the PDF file (default: ../seating_plan.pdf)')
    parser.add_argument('--dry-run', action='store_true', help='Preview students without inserting to database')
    parser.add_argument('--password', default='password123', help='Default password for students (default: password123)')
    
    args = parser.parse_args()
    
    # Get PDF path
    if args.pdf_path:
        pdf_path = Path(args.pdf_path)
    else:
        # Default path relative to project root
        pdf_path = Path(__file__).parent.parent / "seating_plan.pdf"
    
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found at {pdf_path}")
        print("Usage: python import_students_from_pdf.py [path_to_pdf] [--dry-run] [--password PASSWORD]")
        sys.exit(1)
    
    print("=" * 80)
    print("Student Import Script")
    print("=" * 80)
    print(f"PDF File: {pdf_path}")
    if args.dry_run:
        print("Mode: DRY RUN (no database changes)")
    print()
    
    # Extract students from PDF
    try:
        students = extract_students_from_pdf(str(pdf_path))
    except Exception as e:
        print(f"❌ Error extracting students from PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    if not students:
        print("⚠️  No students found in PDF. Exiting.")
        sys.exit(0)
    
    # Preview students
    preview_students(students)
    
    if args.dry_run:
        print(f"\n✅ Dry run complete. Found {len(students)} students.")
        print("Run without --dry-run to insert into database.")
        sys.exit(0)
    
    # Confirm before inserting
    print(f"\nFound {len(students)} students to import.")
    response = input("Do you want to proceed with database insertion? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Import cancelled.")
        sys.exit(0)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Insert students into database
        print("\n" + "=" * 80)
        print("Inserting students into database...")
        print("=" * 80)
        
        stats = insert_students_to_db(students, db, default_password=args.password)
        
        # Print summary
        print("\n" + "=" * 80)
        print("Import Summary")
        print("=" * 80)
        print(f"✅ Successfully inserted: {stats['success']}")
        print(f"🔄 Updated (added/updated roll numbers): {stats['updated']}")
        print(f"⏭️  Skipped (no changes needed): {stats['skipped']}")
        print(f"❌ Failed: {stats['failed']}")
        
        if stats['errors']:
            print("\nErrors:")
            for error in stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(stats['errors']) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more errors")
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()

