from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from database.db import get_db
from database.models import Notification
from database.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# -------------------------
# Response Schemas
# -------------------------
class NotificationRead(BaseModel):
    id: str
    type: str
    title: str
    message: str
    read: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class NotificationListResponse(BaseModel):
    notifications: List[NotificationRead]
    unread_count: int


# -------------------------
# Get Notifications
# -------------------------
@router.get("/", response_model=NotificationListResponse)
def get_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get notifications for the current user.
    """
    user_id = current_user.get("id")
    user_type = current_user.get("user_type")
    
    query = db.query(Notification).filter(
        Notification.user_id == UUID(user_id),
        Notification.user_type == user_type
    )
    
    if unread_only:
        query = query.filter(Notification.read == False)
    
    # Get total unread count
    unread_count = db.query(Notification).filter(
        Notification.user_id == UUID(user_id),
        Notification.user_type == user_type,
        Notification.read == False
    ).count()
    
    # Apply pagination
    offset = (page - 1) * limit
    notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
    
    return NotificationListResponse(
        notifications=[NotificationRead(
            id=str(n.id),
            type=n.type,
            title=n.title,
            message=n.message,
            read=n.read,
            created_at=n.created_at
        ) for n in notifications],
        unread_count=unread_count
    )


# -------------------------
# Mark Notification as Read
# -------------------------
@router.put("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Mark a notification as read.
    """
    user_id = current_user.get("id")
    user_type = current_user.get("user_type")
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == UUID(user_id),
        Notification.user_type == user_type
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read = True
    db.commit()
    
    return {"message": "Notification marked as read"}


# -------------------------
# Mark All as Read
# -------------------------
@router.put("/read-all")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Mark all notifications as read for the current user.
    """
    user_id = current_user.get("id")
    user_type = current_user.get("user_type")
    
    db.query(Notification).filter(
        Notification.user_id == UUID(user_id),
        Notification.user_type == user_type,
        Notification.read == False
    ).update({"read": True})
    
    db.commit()
    
    return {"message": "All notifications marked as read"}

