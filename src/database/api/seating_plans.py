from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from database.db import get_db
from database.models import Room, Seat, Exam
from database.auth import get_current_user

router = APIRouter(prefix="/seating-plans", tags=["Seating Plans"])


# -------------------------
# Response Schemas
# -------------------------
class SeatInfo(BaseModel):
    seat_number: str
    row: Optional[str] = None
    column: Optional[str] = None
    assigned_student_id: Optional[str] = None


class RoomInfo(BaseModel):
    room_id: str
    room_name: str
    capacity: int
    seats: List[SeatInfo]


class SeatingPlanRead(BaseModel):
    id: str
    filename: str
    uploaded_by: str
    uploaded_at: datetime
    status: str
    total_seats: int
    rooms: List[RoomInfo]


class SeatingPlanListResponse(BaseModel):
    plans: List[SeatingPlanRead]
    total: int
    page: int
    limit: int


class SeatAssignment(BaseModel):
    student_id: str
    room_id: str
    seat_number: str


# -------------------------
# Get All Seating Plans
# -------------------------
@router.get("/", response_model=SeatingPlanListResponse)
def get_seating_plans(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, regex="^(completed|processing|failed)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all seating plans with pagination.
    """
    # Get all rooms grouped by exam (each exam represents a seating plan)
    query = db.query(Exam).join(Room)
    
    if status:
        # Filter by exam date to determine status
        if status == "completed":
            query = query.filter(Exam.exam_date < datetime.utcnow().date())
        elif status == "processing":
            query = query.filter(Exam.exam_date >= datetime.utcnow().date())
    
    exams = query.distinct().all()
    
    plans = []
    for exam in exams:
        rooms = db.query(Room).filter(Room.exam_id == exam.exam_id).all()
        
        room_infos = []
        total_seats = 0
        
        for room in rooms:
            seats = db.query(Seat).filter(Seat.room_id == room.room_id).all()
            seat_infos = []
            
            for seat in seats:
                seat_infos.append(SeatInfo(
                    seat_number=seat.seat_number,
                    assigned_student_id=str(seat.student_id) if seat.student_id else None
                ))
                total_seats += 1
            
            room_name = f"{room.block} {room.room_number}" if room.block else room.room_number
            room_infos.append(RoomInfo(
                room_id=str(room.room_id),
                room_name=room_name,
                capacity=room.total_seats or len(seats),
                seats=seat_infos
            ))
        
        # Determine status
        plan_status = "completed" if exam.exam_date < datetime.utcnow().date() else "processing"
        
        plans.append(SeatingPlanRead(
            id=str(exam.exam_id),
            filename=f"Seating Plan - {exam.course}",
            uploaded_by="System",  # Can be tracked if needed
            uploaded_at=exam.created_at,
            status=plan_status,
            total_seats=total_seats,
            rooms=room_infos
        ))
    
    # Apply pagination
    total = len(plans)
    offset = (page - 1) * limit
    paginated_plans = plans[offset:offset + limit]
    
    return SeatingPlanListResponse(
        plans=paginated_plans,
        total=total,
        page=page,
        limit=limit
    )


# -------------------------
# Get Seating Plan by ID
# -------------------------
@router.get("/{plan_id}", response_model=SeatingPlanRead)
def get_seating_plan_by_id(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific seating plan by ID.
    """
    exam = db.query(Exam).filter(Exam.exam_id == plan_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Seating plan not found")
    
    rooms = db.query(Room).filter(Room.exam_id == exam.exam_id).all()
    
    room_infos = []
    total_seats = 0
    
    for room in rooms:
        seats = db.query(Seat).filter(Seat.room_id == room.room_id).all()
        seat_infos = []
        
        for seat in seats:
            seat_infos.append(SeatInfo(
                seat_number=seat.seat_number,
                assigned_student_id=str(seat.student_id) if seat.student_id else None
            ))
            total_seats += 1
        
        room_name = f"{room.block} {room.room_number}" if room.block else room.room_number
        room_infos.append(RoomInfo(
            room_id=str(room.room_id),
            room_name=room_name,
            capacity=room.total_seats or len(seats),
            seats=seat_infos
        ))
    
    plan_status = "completed" if exam.exam_date < datetime.utcnow().date() else "processing"
    
    return SeatingPlanRead(
        id=str(exam.exam_id),
        filename=f"Seating Plan - {exam.course}",
        uploaded_by="System",
        uploaded_at=exam.created_at,
        status=plan_status,
        total_seats=total_seats,
        rooms=room_infos
    )


# -------------------------
# Assign Student to Seat
# -------------------------
@router.post("/{plan_id}/assign")
def assign_student_to_seat(
    plan_id: UUID,
    assignment: SeatAssignment,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Assign a student to a specific seat in a seating plan.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign seats")
    
    # Verify exam exists
    exam = db.query(Exam).filter(Exam.exam_id == plan_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Seating plan not found")
    
    # Verify room exists and belongs to this exam
    room = db.query(Room).filter(
        Room.room_id == UUID(assignment.room_id),
        Room.exam_id == plan_id
    ).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found in this seating plan")
    
    # Check if seat exists
    seat = db.query(Seat).filter(
        Seat.room_id == UUID(assignment.room_id),
        Seat.seat_number == assignment.seat_number
    ).first()
    
    if seat:
        # Update existing seat assignment
        seat.student_id = UUID(assignment.student_id)
    else:
        # Create new seat assignment
        seat = Seat(
            room_id=UUID(assignment.room_id),
            seat_number=assignment.seat_number,
            student_id=UUID(assignment.student_id)
        )
        db.add(seat)
    
    db.commit()
    db.refresh(seat)
    
    # Return updated seating plan
    return get_seating_plan_by_id(plan_id, db, current_user)


# -------------------------
# Delete Seating Plan
# -------------------------
@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seating_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a seating plan (Admin only).
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete seating plans")
    
    exam = db.query(Exam).filter(Exam.exam_id == plan_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Seating plan not found")
    
    # Delete associated rooms and seats
    rooms = db.query(Room).filter(Room.exam_id == plan_id).all()
    for room in rooms:
        seats = db.query(Seat).filter(Seat.room_id == room.room_id).all()
        for seat in seats:
            db.delete(seat)
        db.delete(room)
    
    db.delete(exam)
    db.commit()
    
    return None

