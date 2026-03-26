#!/usr/bin/env python3
"""
Create or update invigilator accounts required for the invigilator portal.

Usage:
  python scripts/create_invigilators.py
  python scripts/create_invigilators.py --password "YourStrongPassword123!"
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv


SCRIPT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = SCRIPT_DIR.parent
SRC_DIR = BACKEND_DIR / "src"

env_file = BACKEND_DIR / ".env"
if not env_file.exists():
    env_file = BACKEND_DIR.parent / ".env"
load_dotenv(env_file)

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

os.chdir(BACKEND_DIR)

from database.db import SessionLocal  # noqa: E402
from database.models import Invigilator  # noqa: E402
from database.auth import hash_password  # noqa: E402


DEFAULT_PASSWORD = "Invigilator@123"

INVIGILATORS = [
    {"name": "Ms. Saira Qamar", "email": "saira.qamar@invigilator.foresyte.local"},
    {"name": "Mr. Inam Ullah Shaikh", "email": "inam.shaikh@invigilator.foresyte.local"},
    {"name": "Ms. Aden Sial", "email": "aden.sial@invigilator.foresyte.local"},
    {"name": "Ms. Emaan Fatima", "email": "emaan.fatima@invigilator.foresyte.local"},
]


def parse_args():
    parser = argparse.ArgumentParser(description="Create required invigilator accounts.")
    parser.add_argument(
        "--password",
        default=os.getenv("DEFAULT_INVIGILATOR_PASSWORD", DEFAULT_PASSWORD),
        help="Password for created invigilator accounts.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    password_hash = hash_password(args.password)

    db = SessionLocal()
    created = 0
    updated = 0
    try:
        for record in INVIGILATORS:
            email = record["email"].strip().lower()
            name = record["name"].strip()

            existing = db.query(Invigilator).filter(Invigilator.email == email).first()
            if existing:
                changed = False
                if existing.name != name:
                    existing.name = name
                    changed = True
                if not existing.password_hash:
                    existing.password_hash = password_hash
                    changed = True
                if changed:
                    updated += 1
                continue

            new_invigilator = Invigilator(
                name=name,
                email=email,
                password_hash=password_hash,
                created_at=datetime.utcnow(),
            )
            db.add(new_invigilator)
            created += 1

        db.commit()
        print("Invigilator account sync completed.")
        print(f"Created: {created}")
        print(f"Updated: {updated}")
        print(f"Password used: {args.password}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
