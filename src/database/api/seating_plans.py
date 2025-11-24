from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, StatementError
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from database.db import get_db
from database.models import Room, Seat, Exam, Student
from database.auth import get_current_user

router = APIRouter()


# -------------------------
# Response Schemas
# -------------------------
class SeatInfo(BaseModel):
    seat_number: str
    row: Optional[str] = None
    column: Optional[str] = None
    assigned_student_id: Optional[str] = None
    assigned_student_name: Optional[str] = None


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
    # Get all exams that have at least one room (seating plan)
    from datetime import date as date_class
    
    try:
        # First, get all unique exam IDs that have rooms
        room_exam_ids = db.query(Room.exam_id).distinct().all()
        exam_ids_list = [exam_id[0] for exam_id in room_exam_ids if exam_id[0] is not None]
        
        if not exam_ids_list:
            # No seating plans found
            return SeatingPlanListResponse(
                plans=[],
                total=0,
                page=page,
                limit=limit
            )
        
        # Query exams that have rooms
        query = db.query(Exam).filter(Exam.exam_id.in_(exam_ids_list))
        
        if status:
            # Filter by exam date to determine status
            today = date_class.today()
            if status == "completed":
                query = query.filter(Exam.exam_date < today)
            elif status == "processing":
                query = query.filter(Exam.exam_date >= today)
        
        # Get exams ordered by creation date (most recent first)
        exams = query.order_by(Exam.created_at.desc()).all()
    except (OperationalError, StatementError) as e:
        # Handle database transaction errors
        db.rollback()
        # Retry once after rollback
        try:
            room_exam_ids = db.query(Room.exam_id).distinct().all()
            exam_ids_list = [exam_id[0] for exam_id in room_exam_ids if exam_id[0] is not None]
            
            if not exam_ids_list:
                return SeatingPlanListResponse(plans=[], total=0, page=page, limit=limit)
            
            query = db.query(Exam).filter(Exam.exam_id.in_(exam_ids_list))
            if status:
                today = date_class.today()
                if status == "completed":
                    query = query.filter(Exam.exam_date < today)
                elif status == "processing":
                    query = query.filter(Exam.exam_date >= today)
            exams = query.order_by(Exam.created_at.desc()).all()
        except Exception as retry_error:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching seating plans after retry: {str(retry_error)}"
            )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching seating plans: {str(e)}"
        )
    
    try:
        # Pre-fetch all rooms for all exams to reduce database queries
        if not exams:
            return SeatingPlanListResponse(plans=[], total=0, page=page, limit=limit)
        
        exam_ids_list = [exam.exam_id for exam in exams]
        all_rooms = db.query(Room).filter(Room.exam_id.in_(exam_ids_list)).all()
        
        # Pre-fetch all seats for all rooms
        room_ids_list = [room.room_id for room in all_rooms]
        all_seats = []
        if room_ids_list:
            all_seats = db.query(Seat).filter(Seat.room_id.in_(room_ids_list)).all()
        
        # Organize rooms and seats by exam_id and room_id for quick lookup
        rooms_by_exam = {}
        for room in all_rooms:
            if room.exam_id not in rooms_by_exam:
                rooms_by_exam[room.exam_id] = []
            rooms_by_exam[room.exam_id].append(room)
        
        seats_by_room = {}
        for seat in all_seats:
            if seat.room_id not in seats_by_room:
                seats_by_room[seat.room_id] = []
            seats_by_room[seat.room_id].append(seat)
        
        plans = []
        today = date_class.today()
        
        for exam in exams:
            try:
                rooms = rooms_by_exam.get(exam.exam_id, [])
                room_infos = []
                total_seats = 0
                
                for room in rooms:
                    seats = seats_by_room.get(room.room_id, [])
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
                
                # Determine status based on exam date
                plan_status = "completed" if exam.exam_date and exam.exam_date < today else "processing"
                
                plans.append(SeatingPlanRead(
                    id=str(exam.exam_id),
                    filename=f"Seating Plan - {exam.course}",
                    uploaded_by="System",  # Can be tracked if needed
                    uploaded_at=exam.created_at,
                    status=plan_status,
                    total_seats=total_seats,
                    rooms=room_infos
                ))
            except Exception as e:
                # Skip exams with errors but continue processing others
                continue
        
        # Sort plans by uploaded_at (most recent first) if available, otherwise by exam date
        plans.sort(key=lambda x: x.uploaded_at if x.uploaded_at else datetime.min.replace(tzinfo=None), reverse=True)
        
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
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing seating plans: {str(e)}"
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
            student_name = None
            if seat.student_id:
                student = db.query(Student).filter(Student.student_id == seat.student_id).first()
                student_name = student.name if student else None
            
            seat_infos.append(SeatInfo(
                seat_number=seat.seat_number,
                assigned_student_id=str(seat.student_id) if seat.student_id else None,
                assigned_student_name=student_name
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

