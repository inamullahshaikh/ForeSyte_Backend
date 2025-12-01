"""
Script to create missing database tables.
This will create any tables that don't exist without dropping existing ones.
"""

import sys
from pathlib import Path

# Add src directory to path to import database modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.db import engine
from database.models import Base


def create_missing_tables():
    """
    Create all tables defined in models.py that don't already exist.
    This is safe to run multiple times - it won't drop existing tables.
    """
    print("=" * 80)
    print("Creating Missing Database Tables")
    print("=" * 80)
    print()
    
    try:
        # Create all tables (only creates if they don't exist)
        Base.metadata.create_all(bind=engine)
        print("[SUCCESS] All tables created successfully!")
        print()
        print("Note: This command only creates tables that don't exist.")
        print("Existing tables and data are not affected.")
        
    except Exception as e:
        print(f"[ERROR] Error creating tables: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = create_missing_tables()
    sys.exit(0 if success else 1)

