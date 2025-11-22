from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, date, time, timedelta
from pydantic import BaseModel
from typing import List, Optional
from database.db import get_db
from database.models import Exam
from database.auth import get_current_user

router = APIRouter(prefix="/exams", tags=["Exams"])

# -------------------------
# Pydantic Schemas
# -------------------------
class ExamCreate(BaseModel):
    name: Optional[str] = None
    course_code: Optional[str] = None
    course: Optional[str] = None  # For backward compatibility
    instructor_id: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    exam_date: Optional[date] = None  # For backward compatibility
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    seating_plan_id: Optional[str] = None
    description: Optional[str] = None


class ExamRead(BaseModel):
    id: str
    exam_id: Optional[UUID] = None
    name: Optional[str] = None
    course_code: Optional[str] = None
    course: Optional[str] = None
    instructor_id: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    seating_plan_id: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


class ExamListResponse(BaseModel):
    exams: List[ExamRead]
    total: int
    page: int
    limit: int


class ExamUpdate(BaseModel):
    name: Optional[str] = None
    course_code: Optional[str] = None
    course: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None


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

    # Map API spec fields to model fields
    exam_data = {}
    if exam.course or exam.course_code:
        exam_data["course"] = exam.course or exam.course_code or exam.name
    if exam.scheduled_date:
        exam_data["exam_date"] = exam.scheduled_date.date()
        exam_data["start_time"] = exam.scheduled_date.time()
        if exam.duration_minutes:
            end_time = exam.scheduled_date + timedelta(minutes=exam.duration_minutes)
            exam_data["end_time"] = end_time.time()
    elif exam.exam_date:
        exam_data["exam_date"] = exam.exam_date
        exam_data["start_time"] = exam.start_time or time(9, 0)
        if exam.duration_minutes:
            start_datetime = datetime.combine(exam.exam_date, exam_data["start_time"])
            end_datetime = start_datetime + timedelta(minutes=exam.duration_minutes)
            exam_data["end_time"] = end_datetime.time()
        else:
            exam_data["end_time"] = exam.end_time or time(12, 0)

    new_exam = Exam(**exam_data)
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    
    return convert_exam_to_read(new_exam)


def convert_exam_to_read(exam: Exam) -> ExamRead:
    """Convert Exam model to ExamRead response."""
    duration_minutes = None
    if exam.start_time and exam.end_time:
        start = datetime.combine(exam.exam_date, exam.start_time)
        end = datetime.combine(exam.exam_date, exam.end_time)
        duration_minutes = int((end - start).total_seconds() / 60)
    
    scheduled_date = None
    if exam.exam_date and exam.start_time:
        scheduled_date = datetime.combine(exam.exam_date, exam.start_time)
    
    # Determine status
    status = "scheduled"
    if exam.exam_date:
        if exam.exam_date < date.today():
            status = "completed"
        elif exam.exam_date == date.today():
            status = "active"
    
    return ExamRead(
        id=str(exam.exam_id),
        exam_id=exam.exam_id,
        name=exam.course,
        course_code=exam.course,
        course=exam.course,
        scheduled_date=scheduled_date,
        exam_date=exam.exam_date,
        start_time=exam.start_time,
        end_time=exam.end_time,
        duration_minutes=duration_minutes,
        status=status,
        created_at=exam.created_at
    )


# READ All Exams (Everyone)
@router.get("/", response_model=ExamListResponse)
def get_exams(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    All authenticated users can view all exams with pagination.
    """
    query = db.query(Exam)
    
    # Apply status filter
    if status_filter:
        today = date.today()
        if status_filter == "active":
            query = query.filter(Exam.exam_date == today)
        elif status_filter == "completed":
            query = query.filter(Exam.exam_date < today)
        elif status_filter == "scheduled":
            query = query.filter(Exam.exam_date > today)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    exams = query.order_by(Exam.exam_date.desc()).offset(offset).limit(limit).all()
    
    return ExamListResponse(
        exams=[convert_exam_to_read(exam) for exam in exams],
        total=total,
        page=page,
        limit=limit
    )


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
    return convert_exam_to_read(exam)


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

    update_data = updated.dict(exclude_unset=True)
    
    # Map API spec fields to model fields
    if "name" in update_data or "course_code" in update_data:
        exam.course = update_data.get("name") or update_data.get("course_code") or update_data.get("course") or exam.course
    if "course" in update_data:
        exam.course = update_data["course"]
    if "scheduled_date" in update_data:
        scheduled = update_data["scheduled_date"]
        if isinstance(scheduled, datetime):
            exam.exam_date = scheduled.date()
            exam.start_time = scheduled.time()
            if "duration_minutes" in update_data:
                end_time = scheduled + timedelta(minutes=update_data["duration_minutes"])
                exam.end_time = end_time.time()
    if "exam_date" in update_data:
        exam.exam_date = update_data["exam_date"]
    if "start_time" in update_data:
        exam.start_time = update_data["start_time"]
    if "end_time" in update_data:
        exam.end_time = update_data["end_time"]
    if "duration_minutes" in update_data and exam.start_time:
        start_datetime = datetime.combine(exam.exam_date or date.today(), exam.start_time)
        end_datetime = start_datetime + timedelta(minutes=update_data["duration_minutes"])
        exam.end_time = end_datetime.time()

    db.commit()
    db.refresh(exam)
    return convert_exam_to_read(exam)


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


# -------------------------
# Get Active Exams
# -------------------------
@router.get("/active", response_model=List[ExamRead])
def get_active_exams(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all active exams (exams scheduled for today).
    """
    today = date.today()
    exams = db.query(Exam).filter(Exam.exam_date == today).order_by(Exam.start_time).all()
    return [convert_exam_to_read(exam) for exam in exams]
