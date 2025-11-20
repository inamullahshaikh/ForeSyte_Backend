import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text  # ✅ Added this
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from database.db import engine, SessionLocal  # ✅ your db.py defines engine + SessionLocal
from database.models import Admin, Base       # ✅ import Base for metadata ops

# -------------------------
# Database Configuration
# -------------------------
DB_NAME = os.getenv("POSTGRES_DB", "foresyte_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "fe118emaan2004")  # ✅ your real password here
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

def create_database_if_not_exists():
    """Create the database if it doesn't already exist."""
    default_engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres",
        isolation_level='AUTOCOMMIT'
    )

    with default_engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'"))
        exists = result.scalar()
        if not exists:
            conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
            print(f"✅ Database '{DB_NAME}' created successfully!")
        else:
            print(f"ℹ️ Database '{DB_NAME}' already exists.")

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
        existing = db.query(Admin).filter(Admin.email == SUPER_ADMIN["email"]).first()
        if existing:
            print(f"⚠️ Super admin with email {SUPER_ADMIN['email']} already exists!")
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

        print("🎉 Super admin created successfully!")
        print(f"   Email: {new_admin.email}")
        print(f"   Username: {new_admin.username}")

    finally:
        db.close()

# -------------------------
# Run Script
# -------------------------
if __name__ == "__main__":
    # 1️⃣ Create the database if needed
    create_database_if_not_exists()

    # 2️⃣ Drop and recreate tables
    Base.metadata.drop_all(bind=engine)
    print("🗑️  All tables dropped successfully!")

    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")

    # 3️⃣ Create the default super admin
    create_super_admin()
