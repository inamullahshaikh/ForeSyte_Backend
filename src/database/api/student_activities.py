from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from database.db import get_db
from database.models import StudentActivity, Student, Exam
from database.auth import get_current_user
from database.severity_logic import compute_severity

router = APIRouter(prefix="/student-activities", tags=["Student Activities"])

# -------------------------
# Pydantic Schemas
# -------------------------
class StudentActivityCreate(BaseModel):
    student_id: UUID
    exam_id: UUID
    activity_type: str
    severity: Optional[str] = None
    confidence: Optional[float] = None
    evidence_url: Optional[str] = None


class StudentActivityRead(BaseModel):
    activity_id: UUID
    student_id: UUID
    exam_id: UUID
    timestamp: datetime
    activity_type: str
    severity: Optional[str]
    confidence: Optional[float]
    evidence_url: Optional[str]

    model_config = {
        "from_attributes": True
    }


class StudentActivityUpdate(BaseModel):
    activity_type: Optional[str] = None
    severity: Optional[str] = None
    confidence: Optional[float] = None
    evidence_url: Optional[str] = None


# -------------------------
# CRUD Routes
# -------------------------

# CREATE (Admin Only)
@router.post("/", response_model=StudentActivityRead, status_code=status.HTTP_201_CREATED)
def create_student_activity(
    activity: StudentActivityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can create student activity records.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create student activities")

    # Validate student
    student = db.query(Student).filter(Student.student_id == activity.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Validate exam
    exam = db.query(Exam).filter(Exam.exam_id == activity.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Frequency-based severity: if not provided, compute from how often this student
    # has done this action in this exam
    severity = activity.severity
    if not severity or (isinstance(severity, str) and not severity.strip()):
        severity = compute_severity(
            activity.student_id,
            activity.exam_id,
            activity.activity_type,
            db,
        )
    payload = activity.dict()
    payload["severity"] = severity
    new_activity = StudentActivity(**payload)
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity


# READ All (Admin + Investigator)
@router.get("/", response_model=List[StudentActivityRead])
def get_all_student_activities(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admins and Investigators can view all student activities.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return db.query(StudentActivity).all()


# READ by ID (Admin + Investigator)
@router.get("/{activity_id}", response_model=StudentActivityRead)
def get_student_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admins and Investigators can view a specific student activity.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    activity = db.query(StudentActivity).filter(StudentActivity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Student activity not found")

    return activity


# UPDATE (Admin Only)
@router.put("/{activity_id}", response_model=StudentActivityRead)
def update_student_activity(
    activity_id: UUID,
    updated: StudentActivityUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can update student activity records.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update student activities")

    activity = db.query(StudentActivity).filter(StudentActivity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Student activity not found")

    for key, value in updated.dict(exclude_unset=True).items():
        setattr(activity, key, value)

    db.commit()
    db.refresh(activity)
    return activity


# DELETE (Admin Only)
@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can delete student activity records.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete student activities")

    activity = db.query(StudentActivity).filter(StudentActivity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Student activity not found")

    db.delete(activity)
    db.commit()
    return None


# READ by Student ID (Accessible by Admin, Investigator, and the Student themselves)
@router.get("/student/{student_id}", response_model=List[StudentActivityRead])
def get_activities_by_student_id(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all activities for a specific student.
    Returns empty list if no activities found (instead of 404).
    """
    user_type = current_user.get("user_type")
    user_id = current_user.get("id")

    if user_type == "invigilator":
        raise HTTPException(status_code=403, detail="Invigilators are not allowed to access this resource")

    if user_type == "student" and str(user_id) != str(student_id):
        raise HTTPException(status_code=403, detail="Students can only view their own activities")

    # Verify student exists
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    activities = db.query(StudentActivity).filter(StudentActivity.student_id == student_id).all()

    # Return empty list instead of 404 if no activities found
    return activities
