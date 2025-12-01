from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from database.db import get_db
from database.models import Invigilator
from database.auth import create_access_token, get_current_user, verify_password, hash_password

router = APIRouter(prefix="/invigilators", tags=["Invigilators"])

# -------------------------
# Schemas
# -------------------------
class InvigilatorCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    photo_url: Optional[str] = None

class InvigilatorRead(BaseModel):
    invigilator_id: UUID
    name: str
    email: EmailStr
    photo_url: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class InvigilatorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    photo_url: Optional[str] = None

class InvigilatorLogin(BaseModel):
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

# CREATE (only admin can add invigilators)
@router.post("/", response_model=InvigilatorRead, status_code=status.HTTP_201_CREATED)
def create_invigilator(
    invigilator: InvigilatorCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create invigilators")

    existing = db.query(Invigilator).filter(Invigilator.email == invigilator.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_invigilator = Invigilator(
        name=invigilator.name,
        email=invigilator.email,
        photo_url=invigilator.photo_url,
        created_at=datetime.utcnow(),
    )
    # Hash password dynamically (we’ll handle password in a separate field later if needed)
    new_invigilator.password_hash = hash_password(invigilator.password)

    db.add(new_invigilator)
    db.commit()
    db.refresh(new_invigilator)
    return new_invigilator


# READ all (admin only)
@router.get("/", response_model=List[InvigilatorRead])
def get_invigilators(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view invigilators")
    return db.query(Invigilator).all()


# READ one (self or admin)
@router.get("/{invigilator_id}", response_model=InvigilatorRead)
def get_invigilator(
    invigilator_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    invigilator = db.query(Invigilator).filter(Invigilator.invigilator_id == invigilator_id).first()
    if not invigilator:
        raise HTTPException(status_code=404, detail="Invigilator not found")

    if current_user["user_type"] != "admin" and current_user["id"] != str(invigilator.invigilator_id):
        raise HTTPException(status_code=403, detail="Access denied")

    return invigilator


# UPDATE (self or admin)
@router.put("/{invigilator_id}", response_model=InvigilatorRead)
def update_invigilator(
    invigilator_id: UUID,
    updated: InvigilatorUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    invigilator = db.query(Invigilator).filter(Invigilator.invigilator_id == invigilator_id).first()
    if not invigilator:
        raise HTTPException(status_code=404, detail="Invigilator not found")

    if current_user["user_type"] != "admin" and current_user["id"] != str(invigilator.invigilator_id):
        raise HTTPException(status_code=403, detail="Access denied")

    for key, value in updated.dict(exclude_unset=True).items():
        if key == "password":
            value = hash_password(value)
            key = "password_hash"
        setattr(invigilator, key, value)

    db.commit()
    db.refresh(invigilator)
    return invigilator


# DELETE (admin only)
@router.delete("/{invigilator_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invigilator(
    invigilator_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete invigilators")

    invigilator = db.query(Invigilator).filter(Invigilator.invigilator_id == invigilator_id).first()
    if not invigilator:
        raise HTTPException(status_code=404, detail="Invigilator not found")

    db.delete(invigilator)
    db.commit()
    return None


# -------------------------
# LOGIN (JWT)
# -------------------------
@router.post("/login", response_model=TokenResponse)
def login_invigilator(login: InvigilatorLogin, db: Session = Depends(get_db)):
    invigilator = db.query(Invigilator).filter(Invigilator.email == login.email).first()
    if not invigilator:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # If you later store password_hash in Invigilator, verify here
    if not hasattr(invigilator, "password_hash") or not verify_password(login.password, invigilator.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        data={
            "id": str(invigilator.invigilator_id),
            "user_type": "invigilator"
        },
        expires_delta=timedelta(hours=1)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "invigilator",
        "id": invigilator.invigilator_id
    }
