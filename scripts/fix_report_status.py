"""
Script to fix reports that are stuck in "generating" status.
This script will:
1. Add the status column if it doesn't exist (for existing databases)
2. Update all reports without a status to "completed"
3. Update all reports with null status to "completed"

Usage: python scripts/fix_report_status.py
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

# Add src to path
sys.path.insert(0, str(SRC_DIR))

from database.db import SessionLocal, engine
from database.models import Report
from sqlalchemy import text

def fix_report_status():
    """Fix reports that are stuck in generating status."""
    db = SessionLocal()
    try:
        # Check if status column exists
        inspector = engine.dialect.get_inspector(engine)
        columns = [col['name'] for col in inspector.get_columns('reports')]
        
        if 'status' not in columns:
            print("Status column doesn't exist. Adding it...")
            # Add status column with default 'generating'
            db.execute(text("ALTER TABLE reports ADD COLUMN status VARCHAR DEFAULT 'generating'"))
            db.commit()
            print("✓ Status column added successfully!")
        else:
            print("✓ Status column already exists.")
        
        # Count reports without status or with null status
        reports_without_status = db.query(Report).filter(
            (Report.status == None) | (Report.status == '')
        ).count()
        
        # Count reports with "generating" status
        reports_generating = db.query(Report).filter(Report.status == 'generating').count()
        
        total_to_fix = reports_without_status + reports_generating
        
        if total_to_fix == 0:
            print("No reports need fixing. All reports have a valid status.")
            return
        
        print(f"\nFound {total_to_fix} reports to fix:")
        print(f"  - {reports_without_status} reports without status")
        print(f"  - {reports_generating} reports stuck in 'generating' status")
        
        # Update reports without status to "generating" (they need to be processed)
        if reports_without_status > 0:
            db.query(Report).filter(
                (Report.status == None) | (Report.status == '')
            ).update({Report.status: 'generating'}, synchronize_session=False)
            print(f"  ✓ Updated {reports_without_status} reports without status to 'generating'")
        
        # For reports stuck in "generating", ask user what to do
        if reports_generating > 0:
            print(f"\nFound {reports_generating} reports stuck in 'generating' status.")
            print("Options:")
            print("  1. Mark as 'completed' (if files already exist)")
            print("  2. Keep as 'generating' (to be processed by async tasks)")
            print("  3. Mark as 'failed' (if generation failed)")
            
            choice = input("Enter choice (1/2/3) [default: 1]: ").strip() or "1"
            
            if choice == "1":
                db.query(Report).filter(Report.status == 'generating').update(
                    {Report.status: 'completed'}, synchronize_session=False
                )
                print(f"  ✓ Marked {reports_generating} reports as 'completed'")
            elif choice == "3":
                db.query(Report).filter(Report.status == 'generating').update(
                    {Report.status: 'failed'}, synchronize_session=False
                )
                print(f"  ✓ Marked {reports_generating} reports as 'failed'")
            else:
                print(f"  ✓ Kept {reports_generating} reports as 'generating'")
        
        db.commit()
        
        # Verify
        remaining = db.query(Report).filter(
            (Report.status == None) | (Report.status == '')
        ).count()
        
        print(f"\n✓ Fix completed.")
        print(f"  Remaining reports without status: {remaining}")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error fixing reports: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_report_status()
