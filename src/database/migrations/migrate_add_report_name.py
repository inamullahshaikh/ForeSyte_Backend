"""
Database Migration: Add name column to reports table.
Run from ForeSyte_Backend with: PYTHONPATH=src python -m database.migrations.migrate_add_report_name
Or from src: python -m database.migrations.migrate_add_report_name
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from database.db import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Add name column to reports table."""
    try:
        with engine.connect() as conn:
            migration_file = Path(__file__).parent / "add_report_name.sql"
            if not migration_file.exists():
                logger.error("Migration file not found: %s", migration_file)
                return False
            sql = migration_file.read_text()
            logger.info("Running migration: Add name to reports table...")
            conn.execute(text(sql))
            conn.commit()
            logger.info("Migration completed: reports.name column added.")
            return True
    except Exception as e:
        logger.exception("Migration failed: %s", e)
        return False


if __name__ == "__main__":
    print("Database Migration: Add name to reports")
    success = run_migration()
    if not success:
        sys.exit(1)
    print("Done. You can now rename reports via PATCH /reports/{id}/name")
