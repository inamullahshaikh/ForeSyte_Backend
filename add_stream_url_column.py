"""
Script to add the stream_url column to the rooms table.
This is safe to run multiple times - it checks if the column exists first.
"""

import sys
from pathlib import Path

# Add src directory to path to import database modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database.db import engine
from sqlalchemy import text, inspect


def add_stream_url_column():
    """
    Add stream_url column to rooms table if it doesn't exist.
    """
    print("=" * 80)
    print("Adding stream_url Column to Rooms Table")
    print("=" * 80)
    print()
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('rooms')]
            
            if 'stream_url' in columns:
                print("[INFO] Column 'stream_url' already exists in 'rooms' table.")
                print("No changes needed.")
                return True
            
            # Add the column
            print("Adding 'stream_url' column to 'rooms' table...")
            conn.execute(text("""
                ALTER TABLE rooms 
                ADD COLUMN stream_url TEXT;
            """))
            conn.commit()
            
            print("[SUCCESS] Column 'stream_url' added successfully!")
            print()
            print("The stream_url column has been added to the rooms table.")
            return True
            
    except Exception as e:
        print(f"[ERROR] Error adding column: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = add_stream_url_column()
    sys.exit(0 if success else 1)

