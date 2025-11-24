from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from database.db import get_db
from database.models import Violation, StudentActivity
from database.auth import get_current_user

router = APIRouter(prefix="/violations", tags=["Violations"])

# -------------------------
# Pydantic Schemas
# -------------------------
class ViolationCreate(BaseModel):
    activity_id: UUID
    violation_type: str
    severity: int
    status: Optional[str] = "pending"
    evidence_url: Optional[str] = None


class ViolationRead(BaseModel):
    violation_id: UUID
    activity_id: UUID
    violation_type: str
    timestamp: datetime
    severity: int
    status: str
    evidence_url: Optional[str]

    model_config = {
        "from_attributes": True
    }


class ViolationUpdate(BaseModel):
    violation_type: Optional[str] = None
    severity: Optional[int] = None
    status: Optional[str] = None
    evidence_url: Optional[str] = None


# -------------------------
# CRUD Routes
# -------------------------

# CREATE (Admin Only)
@router.post("/", response_model=ViolationRead, status_code=status.HTTP_201_CREATED)
def create_violation(
    violation: ViolationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can create violations.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create violations")

    # Validate student activity
    activity = db.query(StudentActivity).filter(StudentActivity.activity_id == violation.activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Student activity not found")

    new_violation = Violation(**violation.dict())
    db.add(new_violation)
    db.commit()
    db.refresh(new_violation)
    return new_violation


# READ All (Admin + Investigator)
@router.get("/", response_model=List[ViolationRead])
def get_all_violations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admins and Investigators can view all violations.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return db.query(Violation).all()


# READ by ID (Admin + Investigator)
@router.get("/{violation_id}", response_model=ViolationRead)
def get_violation(
    violation_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admins and Investigators can view a specific violation.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    violation = db.query(Violation).filter(Violation.violation_id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    return violation


# UPDATE (Admin Only)
@router.put("/{violation_id}", response_model=ViolationRead)
def update_violation(
    violation_id: UUID,
    updated: ViolationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can update violations.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update violations")

    violation = db.query(Violation).filter(Violation.violation_id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    for key, value in updated.dict(exclude_unset=True).items():
        setattr(violation, key, value)

    db.commit()
    db.refresh(violation)
    return violation


# DELETE (Admin Only)
@router.delete("/{violation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_violation(
    violation_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can delete violations.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete violations")

    violation = db.query(Violation).filter(Violation.violation_id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    db.delete(violation)
    db.commit()
    return None


# READ by Activity ID (Admin, Investigator, or the Student themselves)
@router.get("/activity/{activity_id}", response_model=List[ViolationRead])
def get_violations_by_activity_id(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    user_type = current_user.get("user_type")
    user_id = current_user.get("id")

    if user_type == "invigilator":
        raise HTTPException(status_code=403, detail="Invigilators are not allowed to access this resource")


    activity = db.query(StudentActivity).filter(StudentActivity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Student activity not found")

    if user_type == "student" and str(activity.student_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Students can only view violations for their own activities")

    violations = db.query(Violation).filter(Violation.activity_id == activity_id).all()

    if not violations:
        raise HTTPException(status_code=404, detail="No violations found for this activity")

    return violations
