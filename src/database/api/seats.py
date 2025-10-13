from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional
from database.db import get_db
from database.models import Seat, Room, Student
from database.auth import get_current_user

router = APIRouter(prefix="/seats", tags=["Seats"])

# -------------------------
# Pydantic Schemas
# -------------------------
class SeatCreate(BaseModel):
    seat_number: str
    room_id: UUID
    student_id: Optional[UUID] = None


class SeatRead(BaseModel):
    seat_id: UUID
    seat_number: str
    room_id: UUID
    student_id: Optional[UUID]

    model_config = {
        "from_attributes": True
    }


class SeatUpdate(BaseModel):
    seat_number: Optional[str] = None
    room_id: Optional[UUID] = None
    student_id: Optional[UUID] = None


# -------------------------
# CRUD Routes
# -------------------------

# CREATE Seat (Admin Only)
@router.post("/", response_model=SeatRead, status_code=status.HTTP_201_CREATED)
def create_seat(
    seat: SeatCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can create seats.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create seats")

    # Validate room
    room = db.query(Room).filter(Room.room_id == seat.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Validate student (optional)
    if seat.student_id:
        student = db.query(Student).filter(Student.student_id == seat.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

    new_seat = Seat(**seat.dict())
    db.add(new_seat)
    db.commit()
    db.refresh(new_seat)
    return new_seat


# READ All Seats (Everyone)
@router.get("/", response_model=List[SeatRead])
def get_seats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    All authenticated users can view all seats.
    """
    return db.query(Seat).all()


# READ Seat by ID (Everyone)
@router.get("/{seat_id}", response_model=SeatRead)
def get_seat(
    seat_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    All authenticated users can view a specific seat.
    """
    seat = db.query(Seat).filter(Seat.seat_id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")
    return seat


# UPDATE Seat (Admin Only)
@router.put("/{seat_id}", response_model=SeatRead)
def update_seat(
    seat_id: UUID,
    updated: SeatUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can update seats.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update seats")

    seat = db.query(Seat).filter(Seat.seat_id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    # Validate relationships if updating
    if updated.room_id:
        room = db.query(Room).filter(Room.room_id == updated.room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

    if updated.student_id:
        student = db.query(Student).filter(Student.student_id == updated.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

    for key, value in updated.dict(exclude_unset=True).items():
        setattr(seat, key, value)

    db.commit()
    db.refresh(seat)
    return seat


# DELETE Seat (Admin Only)
@router.delete("/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seat(
    seat_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can delete seats.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete seats")

    seat = db.query(Seat).filter(Seat.seat_id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    db.delete(seat)
    db.commit()
    return None
