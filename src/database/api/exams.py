from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, date, time
from pydantic import BaseModel
from typing import List
from database.db import get_db
from database.models import Exam
from database.auth import get_current_user

router = APIRouter(prefix="/exams", tags=["Exams"])

# -------------------------
# Pydantic Schemas
# -------------------------
class ExamCreate(BaseModel):
    course: str
    exam_date: date
    start_time: time
    end_time: time


class ExamRead(BaseModel):
    exam_id: UUID
    course: str
    exam_date: date
    start_time: time
    end_time: time
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ExamUpdate(BaseModel):
    course: str | None = None
    exam_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None


# -------------------------
# CRUD Routes
# -------------------------

# CREATE Exam (Admin Only)
@router.post("/", response_model=ExamRead, status_code=status.HTTP_201_CREATED)
def create_exam(
    exam: ExamCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can create exams.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create exams")

    new_exam = Exam(**exam.dict())
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return new_exam


# READ All Exams (Everyone)
@router.get("/", response_model=List[ExamRead])
def get_exams(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    All authenticated users can view all exams.
    """
    return db.query(Exam).order_by(Exam.exam_date.desc()).all()


# READ Single Exam by ID (Everyone)
@router.get("/{exam_id}", response_model=ExamRead)
def get_exam(
    exam_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    All authenticated users can view a single exam.
    """
    exam = db.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


# UPDATE Exam (Admin Only)
@router.put("/{exam_id}", response_model=ExamRead)
def update_exam(
    exam_id: UUID,
    updated: ExamUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can update exams.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update exams")

    exam = db.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    for key, value in updated.dict(exclude_unset=True).items():
        setattr(exam, key, value)

    db.commit()
    db.refresh(exam)
    return exam


# DELETE Exam (Admin Only)
@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can delete exams.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete exams")

    exam = db.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    db.delete(exam)
    db.commit()
    return None
