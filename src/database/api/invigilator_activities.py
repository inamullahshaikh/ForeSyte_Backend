from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from database.db import get_db
from database.models import InvigilatorActivity, Invigilator, Room
from database.auth import get_current_user

router = APIRouter(prefix="/invigilator-activities", tags=["Invigilator Activities"])

# -------------------------
# Pydantic Schemas
# -------------------------
class InvigilatorActivityCreate(BaseModel):
    invigilator_id: UUID
    room_id: UUID
    activity_type: str
    notes: Optional[str] = None


class InvigilatorActivityRead(BaseModel):
    activity_id: UUID
    invigilator_id: UUID
    room_id: UUID
    timestamp: datetime
    activity_type: str
    notes: Optional[str]

    model_config = {
        "from_attributes": True
    }

class InvigilatorActivityDetailedRead(BaseModel):
    activity_id: UUID
    invigilator_id: UUID
    room_id: UUID
    timestamp: datetime
    activity_type: str
    notes: Optional[str]
    room_number: Optional[str] = None
    block: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class InvigilatorActivityUpdate(BaseModel):
    activity_type: Optional[str] = None
    notes: Optional[str] = None


# -------------------------
# CRUD Routes
# -------------------------

# CREATE (Admin Only)
@router.post("/", response_model=InvigilatorActivityRead, status_code=status.HTTP_201_CREATED)
def create_invigilator_activity(
    activity: InvigilatorActivityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can create invigilator activity records.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create invigilator activities")

    # Validate invigilator
    invigilator = db.query(Invigilator).filter(Invigilator.invigilator_id == activity.invigilator_id).first()
    if not invigilator:
        raise HTTPException(status_code=404, detail="Invigilator not found")

    # Validate room
    room = db.query(Room).filter(Room.room_id == activity.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    new_activity = InvigilatorActivity(**activity.dict())
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity


# READ All (Admin + Investigator)
@router.get("/", response_model=List[InvigilatorActivityRead])
def get_all_invigilator_activities(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admins and Investigators can view all invigilator activities.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return db.query(InvigilatorActivity).all()


@router.get("/me", response_model=List[InvigilatorActivityDetailedRead])
def get_my_invigilator_activities(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Invigilators can view only their own activities.
    Admins and investigators can also call this endpoint but it will
    return an empty list unless the caller is an invigilator.
    """
    if current_user.get("user_type") == "invigilator":
        invigilator_id = UUID(current_user.get("id"))
        activities = (
            db.query(InvigilatorActivity, Room)
            .join(Room, InvigilatorActivity.room_id == Room.room_id, isouter=True)
            .filter(InvigilatorActivity.invigilator_id == invigilator_id)
            .order_by(InvigilatorActivity.timestamp.desc())
            .all()
        )

        return [
            InvigilatorActivityDetailedRead(
                activity_id=activity.activity_id,
                invigilator_id=activity.invigilator_id,
                room_id=activity.room_id,
                timestamp=activity.timestamp,
                activity_type=activity.activity_type,
                notes=activity.notes,
                room_number=room.room_number if room else None,
                block=room.block if room else None,
            )
            for activity, room in activities
        ]

    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return []


# READ by ID (Admin + Investigator)
@router.get("/{activity_id}", response_model=InvigilatorActivityRead)
def get_invigilator_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admins and Investigators can view a specific invigilator activity.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    activity = db.query(InvigilatorActivity).filter(InvigilatorActivity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Invigilator activity not found")

    return activity


# UPDATE (Admin Only)
@router.put("/{activity_id}", response_model=InvigilatorActivityRead)
def update_invigilator_activity(
    activity_id: UUID,
    updated: InvigilatorActivityUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can update invigilator activity records.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update invigilator activities")

    activity = db.query(InvigilatorActivity).filter(InvigilatorActivity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Invigilator activity not found")

    for key, value in updated.dict(exclude_unset=True).items():
        setattr(activity, key, value)

    db.commit()
    db.refresh(activity)
    return activity


# DELETE (Admin Only)
@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invigilator_activity(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can delete invigilator activity records.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete invigilator activities")

    activity = db.query(InvigilatorActivity).filter(InvigilatorActivity.activity_id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Invigilator activity not found")

    db.delete(activity)
    db.commit()
    return None


