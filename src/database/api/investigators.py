from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from database.db import get_db
from database.models import Investigator
from database.auth import create_access_token, get_current_user, verify_password, hash_password

router = APIRouter(prefix="/investigators", tags=["Investigators"])


# -------------------------
# Pydantic Schemas
# -------------------------
class InvestigatorCreate(BaseModel):
    name: str
    email: EmailStr
    designation: Optional[str] = None
    password: str

class InvestigatorRead(BaseModel):
    investigator_id: UUID
    name: str
    email: EmailStr
    designation: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class InvestigatorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    designation: Optional[str] = None
    password: Optional[str] = None

class InvestigatorLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    id: UUID

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# -------------------------
# CRUD Routes
# -------------------------

# CREATE Investigator (Admin only)
@router.post("/", response_model=InvestigatorRead, status_code=status.HTTP_201_CREATED)
def create_investigator(
    investigator: InvestigatorCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create investigators")

    existing = db.query(Investigator).filter(Investigator.email == investigator.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_investigator = Investigator(
        name=investigator.name,
        email=investigator.email,
        designation=investigator.designation,
        created_at=datetime.utcnow(),
    )
    # Add password_hash manually (need to add this column in model)
    new_investigator.password_hash = hash_password(investigator.password)

    db.add(new_investigator)
    db.commit()
    db.refresh(new_investigator)
    return new_investigator


# READ All (Admin only)
@router.get("/", response_model=List[InvestigatorRead])
def get_investigators(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view investigators")
    return db.query(Investigator).all()


# READ Single (self or admin)
@router.get("/{investigator_id}", response_model=InvestigatorRead)
def get_investigator(
    investigator_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    investigator = db.query(Investigator).filter(Investigator.investigator_id == investigator_id).first()
    if not investigator:
        raise HTTPException(status_code=404, detail="Investigator not found")

    if current_user["user_type"] != "admin" and current_user["id"] != str(investigator.investigator_id):
        raise HTTPException(status_code=403, detail="Access denied")

    return investigator


# UPDATE Investigator (self or admin)
@router.put("/{investigator_id}", response_model=InvestigatorRead)
def update_investigator(
    investigator_id: UUID,
    updated: InvestigatorUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    investigator = db.query(Investigator).filter(Investigator.investigator_id == investigator_id).first()
    if not investigator:
        raise HTTPException(status_code=404, detail="Investigator not found")

    if current_user["user_type"] != "admin" and current_user["id"] != str(investigator.investigator_id):
        raise HTTPException(status_code=403, detail="Access denied")

    for key, value in updated.dict(exclude_unset=True).items():
        if key == "password":
            value = hash_password(value)
            key = "password_hash"
        setattr(investigator, key, value)

    db.commit()
    db.refresh(investigator)
    return investigator


# DELETE Investigator (Admin only)
@router.delete("/{investigator_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_investigator(
    investigator_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete investigators")

    investigator = db.query(Investigator).filter(Investigator.investigator_id == investigator_id).first()
    if not investigator:
        raise HTTPException(status_code=404, detail="Investigator not found")

    db.delete(investigator)
    db.commit()
    return None


# -------------------------
# LOGIN (JWT)
# -------------------------
@router.post("/login", response_model=TokenResponse)
def login_investigator(login: InvestigatorLogin, db: Session = Depends(get_db)):
    investigator = db.query(Investigator).filter(Investigator.email == login.email).first()
    if not investigator:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not hasattr(investigator, "password_hash") or not verify_password(login.password, investigator.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        user_id=str(investigator.investigator_id),
        user_type="investigator",
        expires_delta=timedelta(hours=1)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "investigator",
        "id": investigator.investigator_id
    }


# -------------------------
# CHANGE PASSWORD
# -------------------------
@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Change password for the current investigator.
    Requires current password verification.
    """
    if current_user["user_type"] != "investigator":
        raise HTTPException(status_code=403, detail="Only investigators can change their password")
    
    user_id = UUID(current_user["id"])
    investigator = db.query(Investigator).filter(Investigator.investigator_id == user_id).first()
    
    if not investigator:
        raise HTTPException(status_code=404, detail="Investigator not found")
    
    # Verify current password
    if not hasattr(investigator, "password_hash") or not verify_password(password_data.current_password, investigator.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    # Validate new password length
    if len(password_data.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long")
    
    # Update password
    investigator.password_hash = hash_password(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}
