from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from database.db import get_db
from database.models import Room, Exam
from database.auth import get_current_user

router = APIRouter(prefix="/rooms", tags=["Rooms"])

# -------------------------
# Pydantic Schemas
# -------------------------
class RoomCreate(BaseModel):
    room_number: str
    block: Optional[str] = None
    total_seats: Optional[int] = None
    camera_id: Optional[str] = None
    stream_url: Optional[str] = None  # IP Webcam URL (e.g., http://192.168.1.100:8080/video.mjpeg)
    exam_id: Optional[UUID] = None


class RoomRead(BaseModel):
    room_id: UUID
    room_number: str
    block: Optional[str]
    total_seats: Optional[int]
    camera_id: Optional[str]
    stream_url: Optional[str]  # IP Webcam stream URL
    exam_id: Optional[UUID]

    model_config = {
        "from_attributes": True
    }


class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    block: Optional[str] = None
    total_seats: Optional[int] = None
    camera_id: Optional[str] = None
    stream_url: Optional[str] = None  # IP Webcam URL (e.g., http://192.168.1.100:8080/video.mjpeg)
    exam_id: Optional[UUID] = None


# -------------------------
# CRUD Routes
# -------------------------

# CREATE Room (Admin Only)
@router.post("/", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can create rooms.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create rooms")

    # If exam_id provided, verify exam exists
    if room.exam_id:
        exam = db.query(Exam).filter(Exam.exam_id == room.exam_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="Associated exam not found")

    new_room = Room(**room.dict())
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return new_room


# READ All Rooms (Everyone)
@router.get("/", response_model=List[RoomRead])
def get_rooms(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    All authenticated users can view all rooms.
    """
    return db.query(Room).all()


# READ Single Room by ID (Everyone)
@router.get("/{room_id}", response_model=RoomRead)
def get_room(
    room_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    All authenticated users can view a single room.
    """
    room = db.query(Room).filter(Room.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


# UPDATE Room (Admin Only)
@router.put("/{room_id}", response_model=RoomRead)
def update_room(
    room_id: UUID,
    updated: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can update rooms.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update rooms")

    room = db.query(Room).filter(Room.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if updated.exam_id:
        exam = db.query(Exam).filter(Exam.exam_id == updated.exam_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="Associated exam not found")

    for key, value in updated.dict(exclude_unset=True).items():
        setattr(room, key, value)

    db.commit()
    db.refresh(room)
    return room


# DELETE Room (Admin Only)
@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(
    room_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can delete rooms.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete rooms")

    room = db.query(Room).filter(Room.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    db.delete(room)
    db.commit()
    return None
