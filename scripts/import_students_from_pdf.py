#!/usr/bin/env python3
"""
Script to import students from a seating plan PDF into the database.

This script:
1. Reads a seating plan PDF file
2. Extracts student information (roll number, name, seat number)
3. Generates email addresses based on roll number pattern
4. Inserts students into the database following the Student model schema

Email pattern: If roll number is XXY-AAAA, email will be YXXAAAA@nu.edu.pk (Y is lowercase)
Example: 22I-0857 -> i220857@nu.edu.pk
        22I-0839 -> i220839@nu.edu.pk
        22P-0507 -> p220507@nu.edu.pk
"""

import sys
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

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

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber is not installed. Please install it using:")
    print("  pip install pdfplumber")
    sys.exit(1)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.db import SessionLocal
from database.models import Student
from database.auth import hash_password


def generate_email_from_roll_number(roll_number: str) -> str:
    """
    Generate email address from roll number.
    
    Pattern: XXY-AAAA -> YXXAAAA@nu.edu.pk (Y is lowercase)
    
    Example: 22I-0857 -> i220857@nu.edu.pk
             22I-0839 -> i220839@nu.edu.pk
             22P-0507 -> p220507@nu.edu.pk
    
    Args:
        roll_number: Roll number in format XXY-AAAA
        
    Returns:
        Email address in format YXXAAAA@nu.edu.pk (where Y is lowercase letter)
    """
    # Remove any whitespace
    roll_number = roll_number.strip()
    
    # Match pattern: XXY-AAAA where XX is 2 digits, Y is a letter, AAAA is 4 digits
    match = re.match(r'^(\d{2})([A-Za-z])-(\d{4})$', roll_number)
    
    if not match:
        raise ValueError(f"Invalid roll number format: {roll_number}. Expected format: XXY-AAAA (e.g., 22I-0839)")
    
    digits1 = match.group(1)  # XX (e.g., "22")
    letter = match.group(2).lower()  # Y (e.g., "I" -> "i")
    digits2 = match.group(3)  # AAAA (e.g., "0857")
    
    # Generate email: Y(lowercase) + XX + AAAA + @nu.edu.pk
    # Example: 22I-0857 -> i220857@nu.edu.pk
    email = f"{letter}{digits1}{digits2}@nu.edu.pk"
    
    return email


def parse_pdf_table(pdf_path: Path) -> list:
    """
    Parse PDF and extract student information from tables.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries with student data:
        [
            {
                'roll_number': '22I-0839',
                'name': 'Muhammad Talha',
                'seat_number': 'C1R1'
            },
            ...
        ]
    """
    students = []
    
    print(f"Reading PDF file: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF has {len(pdf.pages)} page(s)")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"Processing page {page_num}...")
                
                # Try to extract tables
                tables = page.extract_tables()
                
                if tables:
                    for table_num, table in enumerate(tables, 1):
                        print(f"  Found table {table_num} with {len(table)} rows")
                        
                        # Find header row (usually first row)
                        header_row = None
                        roll_col_idx = None
                        name_col_idx = None
                        seat_col_idx = None
                        
                        for row_idx, row in enumerate(table):
                            if not row:
                                continue
                            
                            # Look for header row (contains "Roll No" or "Name")
                            row_text = " ".join(str(cell) if cell else "" for cell in row).lower()
                            
                            if "roll" in row_text or "name" in row_text:
                                header_row = row_idx
                                # Find column indices
                                for col_idx, cell in enumerate(row):
                                    cell_text = str(cell).lower() if cell else ""
                                    if "roll" in cell_text and "no" in cell_text:
                                        roll_col_idx = col_idx
                                    elif "name" in cell_text and "roll" not in cell_text:
                                        name_col_idx = col_idx
                                    elif "seat" in cell_text and "no" in cell_text:
                                        seat_col_idx = col_idx
                                break
                        
                        # Extract data rows
                        if header_row is not None:
                            for row_idx in range(header_row + 1, len(table)):
                                row = table[row_idx]
                                if not row or len(row) == 0:
                                    continue
                                
                                # Extract roll number
                                roll_number = None
                                if roll_col_idx is not None and roll_col_idx < len(row):
                                    roll_number = str(row[roll_col_idx]).strip() if row[roll_col_idx] else None
                                
                                # Extract name
                                name = None
                                if name_col_idx is not None and name_col_idx < len(row):
                                    name = str(row[name_col_idx]).strip() if row[name_col_idx] else None
                                
                                # Extract seat number (optional)
                                seat_number = None
                                if seat_col_idx is not None and seat_col_idx < len(row):
                                    seat_number = str(row[seat_col_idx]).strip() if row[seat_col_idx] else None
                                
                                # Validate and add student
                                if roll_number and name:
                                    # Clean up roll number (remove extra spaces, ensure format)
                                    roll_number = re.sub(r'\s+', '', roll_number)
                                    name = re.sub(r'\s+', ' ', name).strip()
                                    
                                    # Validate roll number format
                                    if re.match(r'^\d{2}[A-Za-z]-\d{4}$', roll_number):
                                        students.append({
                                            'roll_number': roll_number,
                                            'name': name,
                                            'seat_number': seat_number
                                        })
                                    else:
                                        print(f"  Warning: Skipping invalid roll number format: {roll_number} (Name: {name})")
                                elif roll_number or name:
                                    # Partial data - might be a header or footer row
                                    pass
                
                # If no tables found, try extracting text and parsing
                if not tables:
                    text = page.extract_text()
                    if text:
                        # Try to find student data in text format
                        # Pattern: Roll number, Name, Seat number
                        # This is a fallback for PDFs without proper table structure
                        lines = text.split('\n')
                        for line in lines:
                            # Look for roll number pattern
                            roll_match = re.search(r'(\d{2}[A-Za-z]-\d{4})', line)
                            if roll_match:
                                roll_number = roll_match.group(1)
                                # Try to extract name from the same line or next line
                                # This is a simple fallback - may need adjustment based on actual PDF format
                                pass
    
    except Exception as e:
        print(f"ERROR: Failed to parse PDF: {str(e)}")
        raise
    
    return students


def import_students(pdf_path: Path, default_password: str = "Student@123", skip_existing: bool = True):
    """
    Import students from PDF into the database.
    
    Args:
        pdf_path: Path to the seating plan PDF file
        default_password: Default password for students (will be hashed)
        skip_existing: If True, skip students that already exist (by roll_number or email)
        
    Returns:
        tuple: (total_parsed, created, skipped, errors)
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Parse PDF
    print("\n" + "="*60)
    print("PARSING PDF FILE")
    print("="*60)
    students_data = parse_pdf_table(pdf_path)
    print(f"\nParsed {len(students_data)} students from PDF")
    
    if not students_data:
        print("ERROR: No students found in PDF. Please check the PDF format.")
        return 0, 0, 0, []
    
    # Display sample of parsed data
    print("\nSample of parsed data:")
    for i, student in enumerate(students_data[:3], 1):
        email = generate_email_from_roll_number(student['roll_number'])
        print(f"  {i}. Roll: {student['roll_number']}, Name: {student['name']}, Email: {email}")
    if len(students_data) > 3:
        print(f"  ... and {len(students_data) - 3} more")
    
    # Database operations
    db: Session = SessionLocal()
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    errors = []
    
    print("\n" + "="*60)
    print("IMPORTING TO DATABASE")
    print("="*60)
    
    try:
        # Hash default password once
        password_hash = hash_password(default_password)
        
        for idx, student_data in enumerate(students_data, 1):
            roll_number = student_data['roll_number']
            name = student_data['name']
            
            try:
                # Generate email
                email = generate_email_from_roll_number(roll_number)
                
                # Check if student already exists
                existing_student = db.query(Student).filter(
                    (Student.roll_number == roll_number) | (Student.email == email)
                ).first()
                
                if existing_student:
                    if skip_existing:
                        skipped_count += 1
                        print(f"[{idx}/{len(students_data)}] Skipped (exists): {name} ({roll_number})")
                        continue
                    else:
                        # Update existing student
                        existing_student.name = name
                        existing_student.email = email
                        if student_data.get('seat_number'):
                            # Note: Seat assignment is handled separately
                            pass
                        db.commit()
                        created_count += 1
                        print(f"[{idx}/{len(students_data)}] Updated: {name} ({roll_number})")
                        continue
                
                # Create new student
                new_student = Student(
                    name=name,
                    email=email,
                    roll_number=roll_number,
                    password_hash=password_hash,
                    photo_url=None,
                    created_at=datetime.utcnow()
                )
                
                db.add(new_student)
                db.commit()
                db.refresh(new_student)
                
                created_count += 1
                print(f"[{idx}/{len(students_data)}] Created: {name} ({roll_number}) - {email}")
                
            except ValueError as e:
                # Invalid roll number format
                error_count += 1
                errors.append({
                    'roll_number': roll_number,
                    'name': name,
                    'error': str(e)
                })
                print(f"[{idx}/{len(students_data)}] ERROR: {name} ({roll_number}): {str(e)}")
                db.rollback()
                
            except IntegrityError as e:
                # Duplicate entry or constraint violation
                error_count += 1
                error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
                errors.append({
                    'roll_number': roll_number,
                    'name': name,
                    'error': f"Database constraint violation: {error_msg}"
                })
                print(f"[{idx}/{len(students_data)}] ERROR: {name} ({roll_number}): Constraint violation")
                db.rollback()
                
            except Exception as e:
                # Other errors
                error_count += 1
                errors.append({
                    'roll_number': roll_number,
                    'name': name,
                    'error': str(e)
                })
                print(f"[{idx}/{len(students_data)}] ERROR: {name} ({roll_number}): {str(e)}")
                db.rollback()
        
    finally:
        db.close()
    
    # Summary
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Total students parsed: {len(students_data)}")
    print(f"Successfully created: {created_count}")
    print(f"Skipped (already exist): {skipped_count}")
    print(f"Errors: {error_count}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error['name']} ({error['roll_number']}): {error['error']}")
    
    print("="*60 + "\n")
    
    return len(students_data), created_count, skipped_count, errors


def main():
    """Main function with command-line argument parsing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Import students from a seating plan PDF into the database.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import from default PDF location
  python scripts/import_students_from_pdf.py
  
  # Import from specific PDF file
  python scripts/import_students_from_pdf.py --pdf path/to/seating_plan.pdf
  
  # Import with custom password
  python scripts/import_students_from_pdf.py --password MyPassword123
  
  # Update existing students instead of skipping
  python scripts/import_students_from_pdf.py --update-existing
        """
    )
    
    parser.add_argument(
        '--pdf', '-p',
        type=str,
        default=str(SCRIPT_DIR / "seating_plan.pdf"),
        help='Path to the seating plan PDF file (default: scripts/seating_plan.pdf)'
    )
    
    parser.add_argument(
        '--password',
        type=str,
        default='Student@123',
        help='Default password for students (default: Student@123)'
    )
    
    parser.add_argument(
        '--update-existing',
        action='store_true',
        help='Update existing students instead of skipping them'
    )
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf).resolve()
    
    try:
        total, created, skipped, errors = import_students(
            pdf_path=pdf_path,
            default_password=args.password,
            skip_existing=not args.update_existing
        )
        
        if errors:
            sys.exit(1)
        else:
            print("Import completed successfully!")
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

