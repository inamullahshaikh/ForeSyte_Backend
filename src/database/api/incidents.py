from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from database.db import get_db
from database.models import StudentActivity, Student, Exam, Violation
from database.auth import get_current_user

router = APIRouter(prefix="/incidents", tags=["Incidents"])


# -------------------------
# Response Schemas
# -------------------------
class IncidentRead(BaseModel):
    id: str
    camera_id: Optional[str] = None
    student_id: str
    student_name: str
    exam_id: Optional[str] = None
    exam_name: Optional[str] = None
    instructor: Optional[str] = None
    type: str
    severity: str
    timestamp: datetime
    status: str
    confidence: float
    video_url: Optional[str] = None
    description: Optional[str] = None


class IncidentStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


class IncidentListResponse(BaseModel):
    incidents: List[IncidentRead]
    total: int
    page: int
    limit: int


# -------------------------
# Get All Incidents
# -------------------------
@router.get("/", response_model=IncidentListResponse)
def get_incidents(
    severity: Optional[str] = Query(None, regex="^(low|medium|high|critical)$"),
    status: Optional[str] = Query(None, regex="^(investigating|resolved|dismissed)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all incidents with filtering and pagination.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Base query - get student activities that are incidents
    query = db.query(StudentActivity).join(Student)

    # Apply filters
    if severity:
        query = query.filter(StudentActivity.severity == severity)
    
    if status:
        # Map status to violation status if needed
        # For now, we'll use activity severity as a proxy
        pass  # Status filtering can be added when violations are linked

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * limit
    activities = query.order_by(StudentActivity.timestamp.desc()).offset(offset).limit(limit).all()

    # Convert to incident format
    incidents = []
    for activity in activities:
        student = db.query(Student).filter(Student.student_id == activity.student_id).first()
        exam = db.query(Exam).filter(Exam.exam_id == activity.exam_id).first() if activity.exam_id else None
        violation = db.query(Violation).filter(Violation.activity_id == activity.activity_id).first()

        incidents.append(IncidentRead(
            id=str(activity.activity_id),
            camera_id=None,  # Can be added if camera tracking is implemented
            student_id=str(activity.student_id),
            student_name=student.name if student else "Unknown",
            exam_id=str(activity.exam_id) if activity.exam_id else None,
            exam_name=exam.course if exam else None,
            instructor=None,  # Can be added if instructor tracking is implemented
            type=activity.activity_type or "Unknown",
            severity=activity.severity or "low",
            timestamp=activity.timestamp,
            status=violation.status if violation else "investigating",
            confidence=activity.confidence or 0.0,
            video_url=activity.evidence_url,
            description=None
        ))

    return IncidentListResponse(
        incidents=incidents,
        total=total,
        page=page,
        limit=limit
    )


# -------------------------
# Get Incident by ID
# -------------------------
@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific incident by ID.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    activity = db.query(StudentActivity).filter(StudentActivity.activity_id == incident_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Incident not found")

    student = db.query(Student).filter(Student.student_id == activity.student_id).first()
    exam = db.query(Exam).filter(Exam.exam_id == activity.exam_id).first() if activity.exam_id else None
    violation = db.query(Violation).filter(Violation.activity_id == activity.activity_id).first()

    return IncidentRead(
        id=str(activity.activity_id),
        camera_id=None,
        student_id=str(activity.student_id),
        student_name=student.name if student else "Unknown",
        exam_id=str(activity.exam_id) if activity.exam_id else None,
        exam_name=exam.course if exam else None,
        instructor=None,
        type=activity.activity_type or "Unknown",
        severity=activity.severity or "low",
        timestamp=activity.timestamp,
        status=violation.status if violation else "investigating",
        confidence=activity.confidence or 0.0,
        video_url=activity.evidence_url,
        description=None
    )


# -------------------------
# Update Incident Status
# -------------------------
@router.put("/{incident_id}/status", response_model=IncidentRead)
def update_incident_status(
    incident_id: UUID,
    update: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update the status of an incident.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    activity = db.query(StudentActivity).filter(StudentActivity.activity_id == incident_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Get or create violation record
    violation = db.query(Violation).filter(Violation.activity_id == activity.activity_id).first()
    if not violation:
        # Create violation if it doesn't exist
        violation = Violation(
            activity_id=activity.activity_id,
            violation_type=activity.activity_type or "Unknown",
            severity=1,  # Default severity
            status=update.status
        )
        db.add(violation)
    else:
        violation.status = update.status

    db.commit()
    db.refresh(violation)
    db.refresh(activity)

    student = db.query(Student).filter(Student.student_id == activity.student_id).first()
    exam = db.query(Exam).filter(Exam.exam_id == activity.exam_id).first() if activity.exam_id else None

    return IncidentRead(
        id=str(activity.activity_id),
        camera_id=None,
        student_id=str(activity.student_id),
        student_name=student.name if student else "Unknown",
        exam_id=str(activity.exam_id) if activity.exam_id else None,
        exam_name=exam.course if exam else None,
        instructor=None,
        type=activity.activity_type or "Unknown",
        severity=activity.severity or "low",
        timestamp=activity.timestamp,
        status=violation.status,
        confidence=activity.confidence or 0.0,
        video_url=activity.evidence_url,
        description=update.notes
    )

