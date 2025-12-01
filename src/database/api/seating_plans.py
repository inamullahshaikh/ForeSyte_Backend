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

router = APIRouter(prefix="/seating-plans", tags=["seating-plans"])


# -------------------------
# Helper Functions
# -------------------------
def is_valid_uuid_string(value) -> bool:
    """Check if a value can be converted to a valid UUID"""
    if value is None:
        return False
    try:
        value_str = str(value).strip()
        # Skip obvious non-UUID strings (route names, etc.)
        if value_str.startswith(('seating-', 'room-', 'exam-', 'seat-', 'student-')):
            return False
        # Try to parse as UUID
        UUID(value_str)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def safe_uuid_convert(value):
    """Safely convert a value to UUID, returning None if invalid"""
    if value is None:
        return None
    try:
        if isinstance(value, UUID):
            return value
        value_str = str(value).strip()
        if is_valid_uuid_string(value_str):
            return UUID(value_str)
        return None
    except (ValueError, TypeError, AttributeError):
        return None


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
        
        # Filter and validate exam IDs - only keep valid UUIDs
        exam_ids_list = []
        for exam_id_tuple in room_exam_ids:
            exam_id = exam_id_tuple[0]
            if exam_id is not None:
                validated_uuid = safe_uuid_convert(exam_id)
                if validated_uuid is not None:
                    exam_ids_list.append(validated_uuid)
        
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
            
            # Filter and validate exam IDs - only keep valid UUIDs
            exam_ids_list = []
            for exam_id_tuple in room_exam_ids:
                exam_id = exam_id_tuple[0]
                if exam_id is not None:
                    validated_uuid = safe_uuid_convert(exam_id)
                    if validated_uuid is not None:
                        exam_ids_list.append(validated_uuid)
            
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
        
        # Pre-fetch all seats for all rooms - validate room_ids first
        room_ids_list = []
        for room in all_rooms:
            validated_uuid = safe_uuid_convert(room.room_id)
            if validated_uuid is not None:
                room_ids_list.append(validated_uuid)
        
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
                        # Safely convert student_id to string
                        student_id_str = None
                        if seat.student_id:
                            try:
                                # Handle both UUID objects and strings
                                if isinstance(seat.student_id, UUID):
                                    student_id_str = str(seat.student_id)
                                else:
                                    # Try to validate and convert string to UUID first
                                    UUID(str(seat.student_id))
                                    student_id_str = str(seat.student_id)
                            except (ValueError, TypeError, AttributeError):
                                # Skip invalid UUIDs
                                student_id_str = None
                        
                        seat_infos.append(SeatInfo(
                            seat_number=seat.seat_number,
                            assigned_student_id=student_id_str
                        ))
                        total_seats += 1
                    
                    room_name = f"{room.block} {room.room_number}" if room.block else room.room_number
                    
                    # Safely convert room_id to string
                    room_id_str = None
                    try:
                        if isinstance(room.room_id, UUID):
                            room_id_str = str(room.room_id)
                        else:
                            UUID(str(room.room_id))
                            room_id_str = str(room.room_id)
                    except (ValueError, TypeError, AttributeError):
                        # Skip rooms with invalid UUIDs
                        continue
                    
                    room_infos.append(RoomInfo(
                        room_id=room_id_str,
                        room_name=room_name,
                        capacity=room.total_seats or len(seats),
                        seats=seat_infos
                    ))
                
                # Determine status based on exam date
                plan_status = "completed" if exam.exam_date and exam.exam_date < today else "processing"
                
                # Safely convert exam_id to string
                exam_id_str = None
                try:
                    if isinstance(exam.exam_id, UUID):
                        exam_id_str = str(exam.exam_id)
                    else:
                        UUID(str(exam.exam_id))
                        exam_id_str = str(exam.exam_id)
                except (ValueError, TypeError, AttributeError):
                    # Skip exams with invalid UUIDs
                    continue
                
                # Ensure uploaded_at is not None
                uploaded_at = exam.created_at if exam.created_at else datetime.utcnow()
                
                plans.append(SeatingPlanRead(
                    id=exam_id_str,
                    filename=f"Seating Plan - {exam.course}",
                    uploaded_by="System",  # Can be tracked if needed
                    uploaded_at=uploaded_at,
                    status=plan_status,
                    total_seats=total_seats,
                    rooms=room_infos
                ))
            except Exception as e:
                # Skip exams with errors but continue processing others
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error processing exam {exam.exam_id if exam else 'unknown'}: {str(e)}")
                continue
        
        # Sort plans by uploaded_at (most recent first) if available, otherwise by exam date
        # Handle None values safely for sorting
        plans.sort(key=lambda x: x.uploaded_at if x.uploaded_at else datetime(1970, 1, 1), reverse=True)
        
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
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing seating plans: {str(e)}")
        logger.error(traceback.format_exc())
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
            student_id_str = None
            
            if seat.student_id:
                try:
                    # Handle both UUID objects and strings
                    if isinstance(seat.student_id, UUID):
                        student_id_str = str(seat.student_id)
                        student = db.query(Student).filter(Student.student_id == seat.student_id).first()
                        student_name = student.name if student else None
                    else:
                        # Try to validate and convert string to UUID first
                        student_uuid = UUID(str(seat.student_id))
                        student_id_str = str(student_uuid)
                        student = db.query(Student).filter(Student.student_id == student_uuid).first()
                        student_name = student.name if student else None
                except (ValueError, TypeError, AttributeError):
                    # Skip invalid UUIDs
                    student_id_str = None
                    student_name = None
            
            seat_infos.append(SeatInfo(
                seat_number=seat.seat_number,
                assigned_student_id=student_id_str,
                assigned_student_name=student_name
            ))
            total_seats += 1
        
        room_name = f"{room.block} {room.room_number}" if room.block else room.room_number
        
        # Safely convert room_id to string
        room_id_str = None
        try:
            if isinstance(room.room_id, UUID):
                room_id_str = str(room.room_id)
            else:
                UUID(str(room.room_id))
                room_id_str = str(room.room_id)
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(
                status_code=500,
                detail="Invalid room_id format in database"
            )
        
        room_infos.append(RoomInfo(
            room_id=room_id_str,
            room_name=room_name,
            capacity=room.total_seats or len(seats),
            seats=seat_infos
        ))
    
    plan_status = "completed" if exam.exam_date < datetime.utcnow().date() else "processing"
    
    # Safely convert exam_id to string
    exam_id_str = None
    try:
        if isinstance(exam.exam_id, UUID):
            exam_id_str = str(exam.exam_id)
        else:
            UUID(str(exam.exam_id))
            exam_id_str = str(exam.exam_id)
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=500,
            detail="Invalid exam_id format in database"
        )
    
    return SeatingPlanRead(
        id=exam_id_str,
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
    
    # Validate and convert UUIDs
    try:
        room_uuid = UUID(assignment.room_id)
        student_uuid = UUID(assignment.student_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid UUID format: {str(e)}"
        )
    
    # Verify room exists and belongs to this exam
    room = db.query(Room).filter(
        Room.room_id == room_uuid,
        Room.exam_id == plan_id
    ).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found in this seating plan")
    
    # Check if seat exists
    seat = db.query(Seat).filter(
        Seat.room_id == room_uuid,
        Seat.seat_number == assignment.seat_number
    ).first()
    
    if seat:
        # Update existing seat assignment
        seat.student_id = student_uuid
    else:
        # Create new seat assignment
        seat = Seat(
            room_id=room_uuid,
            seat_number=assignment.seat_number,
            student_id=student_uuid
        )
        db.add(seat)
    
    db.commit()
    db.refresh(seat)
    
    # Return updated seating plan (use plan_id string, not UUID)
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

