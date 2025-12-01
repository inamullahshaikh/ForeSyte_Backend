from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database.db import get_db
from database.models import Room, Exam, Seat
from database.auth import get_current_user

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# -------------------------
# Response Schemas
# -------------------------
class CameraFeed(BaseModel):
    camera_id: str
    room_id: str
    room_name: str
    stream_url: Optional[str] = None
    status: str
    students_monitored: int


class MonitoringFeedsResponse(BaseModel):
    feeds: List[CameraFeed]


class CameraStatus(BaseModel):
    camera_id: str
    status: str
    last_heartbeat: Optional[datetime] = None
    students_detected: int


# -------------------------
# Get Live Monitoring Feeds
# -------------------------
@router.get("/feeds", response_model=MonitoringFeedsResponse)
def get_monitoring_feeds(
    exam_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get live monitoring feeds for all cameras.
    """
    if current_user.get("user_type") not in ["admin", "investigator", "invigilator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Query rooms with cameras
    query = db.query(Room)
    if exam_id:
        query = query.filter(Room.exam_id == exam_id)

    rooms = query.all()

    feeds = []
    for room in rooms:
        # Count students in this room
        students_count = db.query(Seat).filter(Seat.room_id == room.room_id).count()

        # Determine status based on exam and room
        exam = db.query(Exam).filter(Exam.exam_id == room.exam_id).first() if room.exam_id else None
        status = "active" if exam and exam.exam_date else "inactive"

        # Generate room name
        room_name = f"{room.block} {room.room_number}" if room.block else room.room_number

        # Use actual stream_url from database (IP Webcam URL) or generate placeholder
        stream_url = room.stream_url
        if not stream_url and room.camera_id:
            # If no stream_url but camera_id exists, could be IP Webcam
            # Format: http://IP:PORT/video.mjpeg
            # For now, return None - admin should set stream_url via API
            stream_url = None
        
        feeds.append(CameraFeed(
            camera_id=room.camera_id or f"CAM-{room.room_id}",
            room_id=str(room.room_id),
            room_name=room_name,
            stream_url=stream_url,  # Use actual IP Webcam URL from database
            status=status,
            students_monitored=students_count
        ))

    return MonitoringFeedsResponse(feeds=feeds)


# -------------------------
# Get Camera Status
# -------------------------
@router.get("/cameras/{camera_id}/status", response_model=CameraStatus)
def get_camera_status(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get status of a specific camera.
    """
    if current_user.get("user_type") not in ["admin", "investigator", "invigilator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Find room by camera_id
    room = db.query(Room).filter(Room.camera_id == camera_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Count students in this room
    students_count = db.query(Seat).filter(Seat.room_id == room.room_id).count()

    # Determine status
    exam = db.query(Exam).filter(Exam.exam_id == room.exam_id).first() if room.exam_id else None
    status = "active" if exam and exam.exam_date else "inactive"

    return CameraStatus(
        camera_id=camera_id,
        status=status,
        last_heartbeat=datetime.utcnow(),  # Can be updated with actual heartbeat tracking
        students_detected=students_count
    )

