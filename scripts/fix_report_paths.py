#!/usr/bin/env python3
"""
Script to fix report file paths in the database.

This script:
1. Finds all reports in the database
2. Checks if the file actually exists
3. If not, searches for alternative extensions (.txt, .pdf, .csv, .json)
4. Updates the database with the correct file path
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

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
from database.models import Report

# Reports directory
REPORTS_DIR = SRC_DIR / "uploads" / "reports"

def fix_report_paths():
    """Fix report file paths in the database."""
    db = SessionLocal()
    try:
        print("=" * 80)
        print("FIXING REPORT FILE PATHS")
        print("=" * 80)
        
        # Get all reports
        reports = db.query(Report).all()
        
        if not reports:
            print("\n✓ No reports found in database.")
            return
        
        print(f"\nFound {len(reports)} reports in database")
        print(f"Reports directory: {REPORTS_DIR}")
        
        fixed_count = 0
        missing_count = 0
        correct_count = 0
        
        for report in reports:
            print(f"\n{'='*60}")
            print(f"Report ID: {report.report_id}")
            print(f"Type: {report.report_type}")
            print(f"Status: {report.status}")
            print(f"Current file_path: {report.file_path}")
            
            if not report.file_path:
                print("  ⚠️  No file_path set")
                missing_count += 1
                continue
            
            # Extract filename from path
            filename = Path(report.file_path).name
            file_full_path = REPORTS_DIR / filename
            
            # Check if file exists
            if file_full_path.exists():
                print(f"  ✓ File exists: {filename}")
                correct_count += 1
                continue
            
            # File doesn't exist, try alternative extensions
            print(f"  ✗ File not found: {filename}")
            base_name = file_full_path.stem
            possible_extensions = ['.pdf', '.txt', '.csv', '.json']
            
            found = False
            for ext in possible_extensions:
                alternative_path = REPORTS_DIR / f"{base_name}{ext}"
                if alternative_path.exists():
                    print(f"  ✓ Found alternative: {alternative_path.name}")
                    
                    # Update database
                    old_path = report.file_path
                    report.file_path = f"/reports/{alternative_path.name}"
                    db.commit()
                    
                    print(f"  ✓ Updated database:")
                    print(f"    Old: {old_path}")
                    print(f"    New: {report.file_path}")
                    
                    fixed_count += 1
                    found = True
                    break
            
            if not found:
                print(f"  ✗ No alternative file found for {base_name}")
                print(f"    Checked: {', '.join(possible_extensions)}")
                missing_count += 1
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total reports: {len(reports)}")
        print(f"  ✓ Correct paths: {correct_count}")
        print(f"  ✓ Fixed paths: {fixed_count}")
        print(f"  ✗ Missing files: {missing_count}")
        
        if fixed_count > 0:
            print(f"\n✓ Successfully fixed {fixed_count} report path(s)")
        
        if missing_count > 0:
            print(f"\n⚠️  {missing_count} report(s) have missing files")
            print("   These reports may need to be regenerated or deleted.")
        
        if fixed_count == 0 and missing_count == 0:
            print("\n✓ All report paths are correct!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_report_paths()
