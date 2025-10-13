import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database.db import engine, SessionLocal
from database.models import Admin  # adjust import path if different
# create_tables.py
from database.db import engine
from database.models import *  # import all your models
# Drop all existing tables
Base.metadata.drop_all(bind=engine)
print("All tables dropped successfully!")

# Create all tables
Base.metadata.create_all(bind=engine)
print("All tables created successfully!")

# -------------------------
# Password hashing setup
# -------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# -------------------------
# Super Admin Configuration
# -------------------------
SUPER_ADMIN = {
    "username": "superadmin",
    "email": "superadmin@example.com",
    "password": "SuperSecurePassword123!"
}

# -------------------------
# Create Super Admin
# -------------------------
def create_super_admin():
    db: Session = SessionLocal()

    try:
        # Check if super admin already exists
        existing = db.query(Admin).filter(Admin.email == SUPER_ADMIN["email"]).first()
        if existing:
            print(f"Super admin with email {SUPER_ADMIN['email']} already exists!")
            return

        new_admin = Admin(
            admin_id=uuid.uuid4(),
            username=SUPER_ADMIN["username"],
            email=SUPER_ADMIN["email"],
            password_hash=hash_password(SUPER_ADMIN["password"]),
            created_at=datetime.utcnow()
        )

        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        print("Super admin created successfully!")
        print(f"Email: {new_admin.email}")
        print(f"Username: {new_admin.username}")

    finally:
        db.close()

# -------------------------
# Run Script
# -------------------------
if __name__ == "__main__":
    create_super_admin()
