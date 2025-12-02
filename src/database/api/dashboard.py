from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import logging

from database.db import get_db
from database.models import Exam, StudentActivity, Student, Room, Seat, Violation
from database.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# -------------------------
# Response Schemas
# -------------------------
class DashboardStats(BaseModel):
    active_exams: int
    incidents_detected: int
    students_monitored: int
    avg_exam_duration: float
    incidents_trend: str
    students_trend: str
    exams_trend: str


class ActivityDataPoint(BaseModel):
    time: str
    incidents: int
    exams: int


class ActivityResponse(BaseModel):
    data: List[ActivityDataPoint]


class RecentIncident(BaseModel):
    id: str
    student_name: str
    type: str
    severity: str
    timestamp: datetime
    confidence: float


# -------------------------
# Dashboard Stats
# -------------------------
@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    period: str = Query("today", regex="^(today|week|month)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get dashboard statistics for admin/investigator.
    """
    logger.info(f"Dashboard stats requested by user_type: {current_user.get('user_type')}")
    
    if current_user.get("user_type") not in ["admin", "investigator"]:
        logger.warning(f"Access denied for user_type: {current_user.get('user_type')}")
        raise HTTPException(status_code=403, detail="Access denied")

    # Calculate date range based on period
    now = datetime.utcnow()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        prev_start = start_date - timedelta(days=1)
        prev_end = start_date
    elif period == "week":
        start_date = now - timedelta(days=7)
        prev_start = start_date - timedelta(days=7)
        prev_end = start_date
    else:  # month
        start_date = now - timedelta(days=30)
        prev_start = start_date - timedelta(days=30)
        prev_end = start_date

    # Active exams (exams scheduled for today or future)
    active_exams = db.query(Exam).filter(
        Exam.exam_date >= now.date()
    ).count()

    # Previous period active exams for trend
    prev_active_exams = db.query(Exam).filter(
        and_(
            Exam.exam_date >= prev_start.date(),
            Exam.exam_date < prev_end.date()
        )
    ).count()

    # Incidents detected in current period
    incidents_detected = db.query(StudentActivity).filter(
        StudentActivity.timestamp >= start_date
    ).count()

    # Previous period incidents
    prev_incidents = db.query(StudentActivity).filter(
        and_(
            StudentActivity.timestamp >= prev_start,
            StudentActivity.timestamp < prev_end
        )
    ).count()

    # Students monitored (students with seat assignments in active exams)
    students_monitored = db.query(Seat).join(Room).join(Exam).filter(
        Exam.exam_date >= now.date()
    ).distinct(Seat.student_id).count()

    # Previous period students
    prev_students = db.query(Seat).join(Room).join(Exam).filter(
        and_(
            Exam.exam_date >= prev_start.date(),
            Exam.exam_date < prev_end.date()
        )
    ).distinct(Seat.student_id).count()

    # Average exam duration (calculate from start_time and end_time)
    exams_with_duration = db.query(Exam).filter(
        Exam.exam_date >= start_date.date()
    ).all()
    
    total_minutes = 0
    for exam in exams_with_duration:
        if exam.start_time and exam.end_time:
            start = datetime.combine(exam.exam_date, exam.start_time)
            end = datetime.combine(exam.exam_date, exam.end_time)
            duration = (end - start).total_seconds() / 60
            total_minutes += duration
    
    avg_exam_duration = total_minutes / len(exams_with_duration) if exams_with_duration else 0

    # Calculate trends
    incidents_trend = calculate_trend(incidents_detected, prev_incidents)
    students_trend = calculate_trend(students_monitored, prev_students)
    exams_trend = calculate_trend(active_exams, prev_active_exams)

    return DashboardStats(
        active_exams=active_exams,
        incidents_detected=incidents_detected,
        students_monitored=students_monitored,
        avg_exam_duration=round(avg_exam_duration, 1),
        incidents_trend=incidents_trend,
        students_trend=students_trend,
        exams_trend=exams_trend
    )


def calculate_trend(current: int, previous: int) -> str:
    """Calculate percentage trend between current and previous period."""
    if previous == 0:
        return f"+{current}%" if current > 0 else "0%"
    change = ((current - previous) / previous) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{round(change, 1)}%"


# -------------------------
# Activity Chart Data
# -------------------------
@router.get("/activity", response_model=ActivityResponse)
def get_activity_data(
    period: str = Query("today", regex="^(today|week|month)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get activity chart data for incidents and exams over time.
    """
    logger.info(f"Dashboard activity requested by user_type: {current_user.get('user_type')}")
    
    if current_user.get("user_type") not in ["admin", "investigator"]:
        logger.warning(f"Access denied for user_type: {current_user.get('user_type')}")
        raise HTTPException(status_code=403, detail="Access denied")

    # Calculate date range
    now = datetime.utcnow()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        intervals = 6  # 4-hour intervals
        interval_hours = 4
    elif period == "week":
        start_date = now - timedelta(days=7)
        intervals = 7  # Daily intervals
        interval_hours = 24
    else:  # month
        start_date = now - timedelta(days=30)
        intervals = 30  # Daily intervals
        interval_hours = 24

    data_points = []
    for i in range(intervals):
        interval_start = start_date + timedelta(hours=i * interval_hours)
        interval_end = interval_start + timedelta(hours=interval_hours)

        # Count incidents in this interval
        incidents_count = db.query(StudentActivity).filter(
            and_(
                StudentActivity.timestamp >= interval_start,
                StudentActivity.timestamp < interval_end
            )
        ).count()

        # Count exams in this interval (exams scheduled during this time)
        exams_count = db.query(Exam).filter(
            and_(
                Exam.exam_date >= interval_start.date(),
                Exam.exam_date < interval_end.date()
            )
        ).count()

        # Format time label
        if period == "today":
            time_label = interval_start.strftime("%H:00")
        else:
            time_label = interval_start.strftime("%m/%d")

        data_points.append(ActivityDataPoint(
            time=time_label,
            incidents=incidents_count,
            exams=exams_count
        ))

    return ActivityResponse(data=data_points)


# -------------------------
# Recent Incidents
# -------------------------
@router.get("/recent-incidents", response_model=List[RecentIncident])
def get_recent_incidents(
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent incidents for dashboard.
    """
    logger.info(f"Recent incidents requested by user_type: {current_user.get('user_type')}")
    
    if current_user.get("user_type") not in ["admin", "investigator"]:
        logger.warning(f"Access denied for user_type: {current_user.get('user_type')}")
        raise HTTPException(status_code=403, detail="Access denied")

    # Get recent student activities (incidents)
    activities = db.query(StudentActivity).join(Student).order_by(
        StudentActivity.timestamp.desc()
    ).limit(limit).all()

    incidents = []
    for activity in activities:
        student = db.query(Student).filter(Student.student_id == activity.student_id).first()
        incidents.append(RecentIncident(
            id=str(activity.activity_id),
            student_name=student.name if student else "Unknown",
            type=activity.activity_type or "Unknown",
            severity=activity.severity or "low",
            timestamp=activity.timestamp,
            confidence=activity.confidence or 0.0
        ))

    return incidents


# -------------------------
# Analytics Endpoints
# -------------------------

class IncidentTypeStat(BaseModel):
    type: str
    count: int
    percentage: float


class IncidentTypeResponse(BaseModel):
    types: List[IncidentTypeStat]
    total: int


class ExamPerformance(BaseModel):
    exam_id: str
    exam_name: str
    students: int
    incidents: int
    rate: float


class ExamPerformanceResponse(BaseModel):
    exams: List[ExamPerformance]


class AnalyticsMetrics(BaseModel):
    total_incidents: int
    resolution_rate: float
    avg_response_time: float  # in minutes
    false_positive_rate: float  # percentage


class IncidentTrendPoint(BaseModel):
    period: str
    incidents: int
    resolved: int


class IncidentTrendResponse(BaseModel):
    data: List[IncidentTrendPoint]


@router.get("/analytics/incident-types", response_model=IncidentTypeResponse)
def get_incident_type_distribution(
    period: str = Query("month", regex="^(today|week|month|year)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get distribution of incident types for analytics.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # year
        start_date = now - timedelta(days=365)
    
    # Get all activities in period
    activities = db.query(StudentActivity).filter(
        StudentActivity.timestamp >= start_date
    ).all()
    
    # Count by type
    type_counts = {}
    for activity in activities:
        activity_type = activity.activity_type or "Unknown"
        type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
    
    total = len(activities)
    
    # Convert to list and calculate percentages
    types = []
    for activity_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        types.append(IncidentTypeStat(
            type=activity_type,
            count=count,
            percentage=round(percentage, 1)
        ))
    
    return IncidentTypeResponse(types=types, total=total)


@router.get("/analytics/exam-performance", response_model=ExamPerformanceResponse)
def get_exam_performance(
    period: str = Query("month", regex="^(today|week|month|year)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get exam performance statistics (students, incidents, rates).
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0).date()
    elif period == "week":
        start_date = (now - timedelta(days=7)).date()
    elif period == "month":
        start_date = (now - timedelta(days=30)).date()
    else:  # year
        start_date = (now - timedelta(days=365)).date()
    
    # Get exams in period
    exams = db.query(Exam).filter(Exam.exam_date >= start_date).all()
    
    exam_performances = []
    for exam in exams:
        # Count students assigned to this exam
        students_count = db.query(Seat).join(Room).filter(
            Room.exam_id == exam.exam_id
        ).distinct(Seat.student_id).count()
        
        # Count incidents for this exam
        incidents_count = db.query(StudentActivity).filter(
            StudentActivity.exam_id == exam.exam_id
        ).count()
        
        # Calculate incident rate (per 100 students)
        rate = (incidents_count / students_count * 100) if students_count > 0 else 0
        
        exam_performances.append(ExamPerformance(
            exam_id=str(exam.exam_id),
            exam_name=exam.course or f"Exam {str(exam.exam_id)[:8]}",
            students=students_count,
            incidents=incidents_count,
            rate=round(rate, 1)
        ))
    
    # Sort by incident rate (highest first)
    exam_performances.sort(key=lambda x: x.rate, reverse=True)
    
    return ExamPerformanceResponse(exams=exam_performances)


@router.get("/analytics/metrics", response_model=AnalyticsMetrics)
def get_analytics_metrics(
    period: str = Query("month", regex="^(today|week|month|year)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get analytics metrics (resolution rate, response time, etc.).
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:  # year
        start_date = now - timedelta(days=365)
    
    # Get all incidents
    total_incidents = db.query(StudentActivity).filter(
        StudentActivity.timestamp >= start_date
    ).count()
    
    # Get resolved incidents (via violations with status resolved)
    resolved_incidents = db.query(Violation).join(StudentActivity).filter(
        and_(
            StudentActivity.timestamp >= start_date,
            Violation.status == "resolved"
        )
    ).count()
    
    # Calculate resolution rate
    resolution_rate = (resolved_incidents / total_incidents * 100) if total_incidents > 0 else 0
    
    # Calculate average response time (placeholder - would need timestamps for resolved)
    avg_response_time = 4.2  # Placeholder - would need actual response time tracking
    
    # Calculate false positive rate (dismissed incidents / total)
    dismissed_count = db.query(Violation).join(StudentActivity).filter(
        and_(
            StudentActivity.timestamp >= start_date,
            Violation.status == "dismissed"
        )
    ).count()
    
    false_positive_rate = (dismissed_count / total_incidents * 100) if total_incidents > 0 else 0
    
    return AnalyticsMetrics(
        total_incidents=total_incidents,
        resolution_rate=round(resolution_rate, 1),
        avg_response_time=round(avg_response_time, 1),
        false_positive_rate=round(false_positive_rate, 1)
    )


@router.get("/analytics/incident-trends", response_model=IncidentTrendResponse)
def get_incident_trends(
    period: str = Query("month", regex="^(week|month|year)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get incident trends over time periods for analytics charts.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate date range and intervals
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
        intervals = 7
        interval_days = 1
        date_format = "%m/%d"
    elif period == "month":
        start_date = now - timedelta(days=30)
        intervals = 6  # 5-day intervals
        interval_days = 5
        date_format = "%m/%d"
    else:  # year
        start_date = now - timedelta(days=365)
        intervals = 12  # Monthly intervals
        interval_days = 30
        date_format = "%b"
    
    trend_points = []
    for i in range(intervals):
        interval_start = start_date + timedelta(days=i * interval_days)
        interval_end = interval_start + timedelta(days=interval_days)
        
        # Count total incidents in this interval
        incidents_count = db.query(StudentActivity).filter(
            and_(
                StudentActivity.timestamp >= interval_start,
                StudentActivity.timestamp < interval_end
            )
        ).count()
        
        # Count resolved incidents in this interval
        resolved_count = db.query(Violation).join(StudentActivity).filter(
            and_(
                StudentActivity.timestamp >= interval_start,
                StudentActivity.timestamp < interval_end,
                Violation.status == "resolved"
            )
        ).count()
        
        period_label = interval_start.strftime(date_format)
        
        trend_points.append(IncidentTrendPoint(
            period=period_label,
            incidents=incidents_count,
            resolved=resolved_count
        ))
    
    return IncidentTrendResponse(data=trend_points)

