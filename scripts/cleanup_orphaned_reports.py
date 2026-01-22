#!/usr/bin/env python3
"""
Script to clean up orphaned reports in the database.

This script will:
1. Find all reports in the database
2. Check if their files actually exist
3. Delete database records for missing files OR mark them as failed
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

def cleanup_orphaned_reports():
    """Clean up orphaned report records."""
    db = SessionLocal()
    try:
        print("=" * 80)
        print("CLEANING UP ORPHANED REPORTS")
        print("=" * 80)
        
        # Get all reports
        reports = db.query(Report).all()
        
        if not reports:
            print("\n✓ No reports found in database.")
            return
        
        print(f"\nFound {len(reports)} reports in database")
        print(f"Reports directory: {REPORTS_DIR}")
        
        # List actual files
        actual_files = list(REPORTS_DIR.glob("*"))
        print(f"Actual files in directory: {len(actual_files)}")
        
        orphaned_reports = []
        valid_reports = []
        
        print("\n" + "=" * 80)
        print("CHECKING REPORTS")
        print("=" * 80)
        
        for report in reports:
            report_id = str(report.report_id)
            file_path = report.file_path
            status = report.status
            
            print(f"\nReport ID: {report_id[:8]}...")
            print(f"  File path: {file_path}")
            print(f"  Status: {status}")
            
            if not file_path:
                print(f"  ⚠️  No file path set")
                orphaned_reports.append(report)
                continue
            
            # Extract filename and check if file exists
            filename = Path(file_path).name
            base_name = Path(filename).stem
            
            # Check all possible extensions
            found = False
            for ext in ['.pdf', '.txt', '.csv', '.json']:
                test_path = REPORTS_DIR / f"{base_name}{ext}"
                if test_path.exists():
                    print(f"  ✓ File exists: {test_path.name}")
                    valid_reports.append(report)
                    found = True
                    break
            
            if not found:
                print(f"  ✗ File NOT FOUND (checked all extensions)")
                orphaned_reports.append(report)
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total reports in database: {len(reports)}")
        print(f"  ✓ Valid reports (file exists): {len(valid_reports)}")
        print(f"  ✗ Orphaned reports (no file): {len(orphaned_reports)}")
        
        if len(orphaned_reports) == 0:
            print("\n✓ No orphaned reports found. Database is clean!")
            return
        
        # Ask user what to do
        print("\n" + "=" * 80)
        print("ORPHANED REPORTS")
        print("=" * 80)
        print("\nThe following reports have no files:")
        for report in orphaned_reports:
            print(f"  - {report.report_id} ({report.report_type}) - {report.status}")
        
        print("\nOptions:")
        print("  1. Delete orphaned reports from database (recommended)")
        print("  2. Mark them as 'failed' (keep in database)")
        print("  3. Cancel (do nothing)")
        
        choice = input("\nSelect option (1/2/3) [default: 1]: ").strip() or "1"
        
        if choice == "1":
            print("\nDeleting orphaned reports...")
            for report in orphaned_reports:
                print(f"  Deleting: {report.report_id}")
                db.delete(report)
            db.commit()
            print(f"\n✓ Deleted {len(orphaned_reports)} orphaned report(s)")
        
        elif choice == "2":
            print("\nMarking orphaned reports as 'failed'...")
            for report in orphaned_reports:
                print(f"  Marking as failed: {report.report_id}")
                report.status = "failed"
            db.commit()
            print(f"\n✓ Marked {len(orphaned_reports)} report(s) as failed")
        
        else:
            print("\n✓ No changes made")
        
        print("\n" + "=" * 80)
        print("DONE")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Refresh your Reports page")
        print("2. Generate new reports")
        print("3. These will be proper PDFs with all violation details")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_orphaned_reports()
