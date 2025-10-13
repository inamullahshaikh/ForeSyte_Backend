from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from typing import List

from database.db import get_db
from database.models import Admin
from database.auth import create_access_token, get_current_user, verify_password, hash_password

router = APIRouter(prefix="/admins", tags=["Admins"])


# -------------------------
# Pydantic Schemas
# -------------------------
class AdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class AdminRead(BaseModel):
    admin_id: UUID
    username: str
    email: EmailStr
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class AdminUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    id: UUID


# -------------------------
# CRUD Routes
# -------------------------

# CREATE Admin (only Admins)
@router.post("/", response_model=AdminRead, status_code=status.HTTP_201_CREATED)
def create_admin(
    admin: AdminCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create admins")

    if db.query(Admin).filter(Admin.email == admin.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_admin = Admin(
        username=admin.username,
        email=admin.email,
        password_hash=hash_password(admin.password)
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return new_admin


# READ All Admins
@router.get("/", response_model=List[AdminRead])
def get_admins(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view admins")
    return db.query(Admin).all()


# READ Single Admin
@router.get("/{admin_id}", response_model=AdminRead)
def get_admin(
    admin_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    admin = db.query(Admin).filter(Admin.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    # Allow access only to same admin or another admin
    if current_user["user_type"] != "admin" and current_user["id"] != str(admin.admin_id):
        raise HTTPException(status_code=403, detail="Access denied")

    return admin


# UPDATE Admin
@router.put("/{admin_id}", response_model=AdminRead)
def update_admin(
    admin_id: UUID,
    updated: AdminUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    admin = db.query(Admin).filter(Admin.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    if current_user["user_type"] != "admin" and current_user["id"] != str(admin.admin_id):
        raise HTTPException(status_code=403, detail="Access denied")

    for key, value in updated.dict(exclude_unset=True).items():
        if key == "password":
            value = hash_password(value)
            key = "password_hash"
        setattr(admin, key, value)

    db.commit()
    db.refresh(admin)
    return admin


# DELETE Admin
@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(
    admin_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete admins")

    admin = db.query(Admin).filter(Admin.admin_id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    db.delete(admin)
    db.commit()
    return None


# -------------------------
# LOGIN Route (JWT)
# -------------------------
@router.post("/login", response_model=TokenResponse)
def login_admin(login: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == login.email).first()
    if not admin or not verify_password(login.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        data={
            "id": str(admin.admin_id),
            "user_type": "admin",
        },
        expires_delta=timedelta(hours=1)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "admin",
        "id": admin.admin_id
    }
