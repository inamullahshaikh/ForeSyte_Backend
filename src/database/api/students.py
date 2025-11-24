from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from database.db import get_db
from database.models import Student
from database.auth import create_access_token, get_current_user

router = APIRouter(prefix="/students", tags=["Students"])

# -------------------------
# Pydantic Schemas
# -------------------------
class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    roll_number: str
    photo_url: Optional[str] = None


class StudentRead(BaseModel):
    student_id: UUID
    name: str
    email: EmailStr
    roll_number: Optional[str]
    photo_url: Optional[str]
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    roll_number: Optional[str] = None
    photo_url: Optional[str] = None


class StudentLogin(BaseModel):
    email: EmailStr
    roll_number: str


# -------------------------
# Login Route (no auth)
# -------------------------
@router.post("/login")
def login_student(credentials: StudentLogin, db: Session = Depends(get_db)):
    """
    Public route — authenticates student using email + roll number.
    """
    student = db.query(Student).filter(Student.email == credentials.email).first()
    if not student or student.roll_number != credentials.roll_number:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or roll number",
        )

    access_token = create_access_token(
        data={"user_type": "student", "user_id": str(student.student_id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": "student",
        "user_id": str(student.student_id),
    }


# -------------------------
# CRUD Routes (Protected)
# -------------------------

@router.post("/", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Protected — Only admins can create students.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create students")

    existing = db.query(Student).filter(Student.email == student.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student with this email already exists")

    # ✅ ensure roll_number is a valid string
    roll_number = student.roll_number or student.email.split("@")[0]

    new_student = Student(
        name=student.name.strip(),
        email=student.email.lower(),
        roll_number=roll_number.strip(),
        photo_url=student.photo_url,
        created_at=datetime.utcnow()
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@router.get("/", response_model=List[StudentRead])
def get_students(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Protected — Only admins can view all students.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view all students")

    return db.query(Student).all()


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Protected — Students can view their own record; Admins can view any.
    """
    # Fetch the student
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    user_type = current_user.get("user_type")
    user_id = str(current_user.get("id")).strip()  # ✅ fixed key name

    # ✅ Allow if Admin or Owner
    if user_type == "admin" or str(student_id) == current_user.get("id"):
        return student

    # ❌ Otherwise, block
    raise HTTPException(
        status_code=403,
        detail="You are not authorized to view this student record"
    )



@router.put("/{student_id}", response_model=StudentRead)
def update_student(
    student_id: UUID,
    updated: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Protected — Admin can update any student; student can update only self.
    """
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user.get("user_type") == "student" and str(student.student_id) != current_user.get("id"):
        raise HTTPException(status_code=403, detail="You can only update your own profile")

    for key, value in updated.dict(exclude_unset=True).items():
        setattr(student, key, value)

    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Protected — Only admins can delete students.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete students")

    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()
    return None
