"""
Database Migration Script: Add stream_url to rooms table
Run this script to add the stream_url column to the rooms table.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database.db import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Add stream_url column to rooms table"""
    try:
        with engine.connect() as conn:
            # Read migration SQL
            migration_file = Path(__file__).parent / "add_stream_url_to_rooms.sql"
            
            if not migration_file.exists():
                logger.error(f"Migration file not found: {migration_file}")
                return False
            
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            # Execute migration
            logger.info("Running migration: Add stream_url to rooms table...")
            conn.execute(text(sql))
            conn.commit()
            
            logger.info("[SUCCESS] Migration completed successfully!")
            logger.info("The stream_url column has been added to the rooms table.")
            return True
            
    except Exception as e:
        logger.error(f"[ERROR] Migration failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add stream_url to rooms")
    print("=" * 60)
    
    success = run_migration()
    
    if success:
        print("\n[SUCCESS] Migration completed successfully!")
        print("You can now use stream_url in the rooms table.")
    else:
        print("\n[ERROR] Migration failed. Please check the error above.")
        sys.exit(1)

