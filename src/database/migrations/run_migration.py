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


def run_sql_file(conn, filename: str, description: str) -> bool:
    """Run a single SQL migration file."""
    migration_file = Path(__file__).parent / filename
    if not migration_file.exists():
        logger.warning("Migration file not found: %s", migration_file)
        return True  # skip
    with open(migration_file, "r") as f:
        sql = f.read()
    logger.info("Running migration: %s...", description)
    conn.execute(text(sql))
    return True


def run_migration():
    """Run pending migrations (stream_url, report name, report status)."""
    try:
        with engine.connect() as conn:
            run_sql_file(conn, "add_stream_url_to_rooms.sql", "Add stream_url to rooms")
            run_sql_file(conn, "add_report_name.sql", "Add name to reports")
            run_sql_file(conn, "add_report_status.sql", "Add status to reports")
            conn.commit()
            logger.info("[SUCCESS] Migrations completed successfully!")
            return True
    except Exception as e:
        logger.error("[ERROR] Migration failed: %s", e)
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Database migrations: rooms stream_url, reports name & status")
    print("=" * 60)

    success = run_migration()

    if success:
        print("\n[SUCCESS] Migrations completed successfully!")
    else:
        print("\n[ERROR] Migration failed. Please check the error above.")
        sys.exit(1)

