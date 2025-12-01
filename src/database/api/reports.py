from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel
import os
from pathlib import Path

from database.db import get_db
from database.models import Report, Violation, Investigator, StudentActivity, Exam, Room, Seat, Student
from database.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

# -------------------------
# Pydantic Schemas
# -------------------------
class ReportCreate(BaseModel):
    report_type: str
    file_path: str
    violation_id: UUID
    generated_by: UUID


class ReportRead(BaseModel):
    report_id: UUID
    report_type: str
    generated_date: date
    file_path: str
    violation_id: UUID
    generated_by: UUID
    # Enriched fields for frontend
    violation_count: Optional[int] = None
    exam_name: Optional[str] = None
    generated_by_name: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class ReportUpdate(BaseModel):
    report_type: Optional[str] = None
    file_path: Optional[str] = None
    violation_id: Optional[UUID] = None
    generated_by: Optional[UUID] = None


class IncidentReportRequest(BaseModel):
    incident_ids: List[str]
    format: str  # pdf, csv, json
    include_video_links: bool


class ExamReportRequest(BaseModel):
    format: str  # pdf, csv, json
    include_statistics: bool


class ReportListResponse(BaseModel):
    reports: List[ReportRead]
    total: int


# -------------------------
# CRUD Routes
# -------------------------

# CREATE (Admin Only)
@router.post("/", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can create reports.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create reports")

    # Validate violation
    violation = db.query(Violation).filter(Violation.violation_id == report.violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")

    # Validate investigator
    investigator = db.query(Investigator).filter(Investigator.investigator_id == report.generated_by).first()
    if not investigator:
        raise HTTPException(status_code=404, detail="Investigator not found")

    new_report = Report(**report.dict())
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report


# -------------------------
# Generate Incident Report
# -------------------------
@router.post("/incidents")
def generate_incident_report(
    request: IncidentReportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate an incident report for specified incidents.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Validate incident IDs
    activities = []
    for incident_id in request.incident_ids:
        try:
            activity = db.query(StudentActivity).filter(
                StudentActivity.activity_id == UUID(incident_id)
            ).first()
            if activity:
                activities.append(activity)
        except ValueError:
            continue

    if not activities:
        raise HTTPException(status_code=404, detail="No valid incidents found")

    # Generate report file (simplified - in production, use a proper report generator)
    report_id = UUID(current_user.get("id"))
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"incident_report_{timestamp}.{request.format}"
    file_path = os.path.join("reports", filename)

    # Create report record
    # For now, we'll create a report linked to the first violation if available
    violation = None
    if activities:
        violation = db.query(Violation).filter(
            Violation.activity_id == activities[0].activity_id
        ).first()

    if not violation:
        # Create a placeholder violation if needed
        violation = Violation(
            activity_id=activities[0].activity_id,
            violation_type=activities[0].activity_type or "Unknown",
            severity=1,
            status="pending"
        )
        db.add(violation)
        db.commit()
        db.refresh(violation)

    new_report = Report(
        report_type="incident",
        file_path=file_path,
        violation_id=violation.violation_id,
        generated_by=UUID(current_user.get("id"))
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    # Return report URL or file path
    return {
        "id": str(new_report.report_id),
        "file_path": file_path,
        "format": request.format,
        "status": "generating"  # In production, this would be async
    }


# -------------------------
# Generate Exam Report
# -------------------------
@router.post("/exams/{exam_id}")
def generate_exam_report(
    exam_id: UUID,
    request: ExamReportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a report for a specific exam.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    exam = db.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Generate report file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"exam_report_{exam_id}_{timestamp}.{request.format}"
    file_path = os.path.join("reports", filename)

    # Get violations/incidents for this exam
    activities = db.query(StudentActivity).filter(
        StudentActivity.exam_id == exam_id
    ).all()

    violation = None
    if activities:
        violation = db.query(Violation).filter(
            Violation.activity_id == activities[0].activity_id
        ).first()

    if not violation and activities:
        violation = Violation(
            activity_id=activities[0].activity_id,
            violation_type="Exam Report",
            severity=1,
            status="pending"
        )
        db.add(violation)
        db.commit()
        db.refresh(violation)

    new_report = Report(
        report_type="exam",
        file_path=file_path,
        violation_id=violation.violation_id if violation else None,
        generated_by=UUID(current_user.get("id"))
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return {
        "id": str(new_report.report_id),
        "file_path": file_path,
        "format": request.format,
        "status": "generating"
    }


# READ All (Admin + Investigator)
@router.get("/", response_model=ReportListResponse)
def get_all_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admins and Investigators can view all reports with pagination and enriched data.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(Report)
    total = query.count()
    
    offset = (page - 1) * limit
    reports = query.order_by(Report.generated_date.desc()).offset(offset).limit(limit).all()
    
    enriched_reports = []
    for report in reports:
        report_data = {
            "report_id": report.report_id,
            "report_type": report.report_type,
            "generated_date": report.generated_date,
            "file_path": report.file_path,
            "violation_id": report.violation_id,
            "generated_by": report.generated_by,
            "violation_count": None,
            "exam_name": None,
            "generated_by_name": None,
        }
        
        # Get investigator name
        investigator = db.query(Investigator).filter(
            Investigator.investigator_id == report.generated_by
        ).first()
        if investigator:
            report_data["generated_by_name"] = investigator.name
        
        # Get violation and related data
        if report.violation_id:
            violation = db.query(Violation).filter(
                Violation.violation_id == report.violation_id
            ).first()
            
            if violation:
                # Count violations for the same activity/exam (simplified - count 1 for now)
                report_data["violation_count"] = 1
                
                # Get activity to find exam
                activity = db.query(StudentActivity).filter(
                    StudentActivity.activity_id == violation.activity_id
                ).first()
                
                if activity and activity.exam_id:
                    exam = db.query(Exam).filter(Exam.exam_id == activity.exam_id).first()
                    if exam:
                        report_data["exam_name"] = exam.course
        
        enriched_reports.append(ReportRead(**report_data))

    return ReportListResponse(
        reports=enriched_reports,
        total=total
    )


# READ by ID (Admin + Investigator)
@router.get("/{report_id}", response_model=ReportRead)
def get_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Admins and Investigators can view a specific report with enriched data.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Enrich report data
    report_data = {
        "report_id": report.report_id,
        "report_type": report.report_type,
        "generated_date": report.generated_date,
        "file_path": report.file_path,
        "violation_id": report.violation_id,
        "generated_by": report.generated_by,
        "violation_count": None,
        "exam_name": None,
        "generated_by_name": None,
    }
    
    # Get investigator name
    investigator = db.query(Investigator).filter(
        Investigator.investigator_id == report.generated_by
    ).first()
    if investigator:
        report_data["generated_by_name"] = investigator.name
    
    # Get violation and related data
    if report.violation_id:
        violation = db.query(Violation).filter(
            Violation.violation_id == report.violation_id
        ).first()
        
        if violation:
            report_data["violation_count"] = 1
            
            # Get activity to find exam
            activity = db.query(StudentActivity).filter(
                StudentActivity.activity_id == violation.activity_id
            ).first()
            
            if activity and activity.exam_id:
                exam = db.query(Exam).filter(Exam.exam_id == activity.exam_id).first()
                if exam:
                    report_data["exam_name"] = exam.course
    
    return ReportRead(**report_data)


# Download Report (Admin + Investigator)
@router.get("/{report_id}/download")
def download_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Download a report file. Serves the file directly to the browser.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Extract filename from file_path
    file_path = report.file_path
    if file_path.startswith("/reports/"):
        filename = file_path.replace("/reports/", "")
    elif file_path.startswith("reports/"):
        filename = file_path.replace("reports/", "")
    else:
        filename = os.path.basename(file_path)
    
    # Construct full path to the file
    # Backend runs from src/, so reports/ is one level up
    # Try multiple path resolutions
    current_file = Path(__file__)  # database/api/reports.py
    src_dir = current_file.parent.parent  # src/
    backend_dir = src_dir.parent  # FORESYTE_Backend/
    reports_dir = backend_dir / "reports"
    
    file_full_path = reports_dir / filename
    
    # Alternative: if running from different location, try relative path from src
    if not file_full_path.exists():
        file_full_path = Path("../reports") / filename
        file_full_path = file_full_path.resolve()
    
    # Check if file exists
    if not file_full_path.exists():
        # If file doesn't exist, return a helpful error message with debug info
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Report file not found. Tried path: {file_full_path.absolute()}")
        logger.error(f"Reports directory exists: {reports_dir.exists()}")
        logger.error(f"Reports directory: {reports_dir.absolute()}")
        
        raise HTTPException(
            status_code=404, 
            detail=f"Report file not found: {filename}. The report record exists but the file hasn't been generated yet. Tried path: {file_full_path.absolute()}"
        )
    
    # Determine media type based on file extension
    media_type = "application/pdf"
    if filename.endswith(".csv"):
        media_type = "text/csv"
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith(".json"):
        media_type = "application/json"
    
    # Serve the file with appropriate headers for download
    return FileResponse(
        path=str(file_full_path),
        filename=filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# View Report (Admin + Investigator) - Opens in browser instead of downloading
@router.get("/{report_id}/view")
def view_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    View a report file in the browser (inline) instead of downloading.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Extract filename from file_path
    file_path = report.file_path
    if file_path.startswith("/reports/"):
        filename = file_path.replace("/reports/", "")
    elif file_path.startswith("reports/"):
        filename = file_path.replace("reports/", "")
    else:
        filename = os.path.basename(file_path)
    
    # Construct full path to the file
    current_file = Path(__file__)  # database/api/reports.py
    src_dir = current_file.parent.parent  # src/
    backend_dir = src_dir.parent  # FORESYTE_Backend/
    reports_dir = backend_dir / "reports"
    
    file_full_path = reports_dir / filename
    
    # Alternative: if running from different location, try relative path from src
    if not file_full_path.exists():
        file_full_path = Path("../reports") / filename
        file_full_path = file_full_path.resolve()
    
    # Check if file exists
    if not file_full_path.exists():
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Report file not found. Tried path: {file_full_path.absolute()}")
        logger.error(f"Reports directory exists: {reports_dir.exists()}")
        logger.error(f"Reports directory: {reports_dir.absolute()}")
        
        raise HTTPException(
            status_code=404, 
            detail=f"Report file not found: {filename}. The report record exists but the file hasn't been generated yet. Tried path: {file_full_path.absolute()}"
        )
    
    # Check if file is actually a text file (our dummy files)
    try:
        with open(file_full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # If it's a text file, serve as HTML-wrapped content
            if not content.startswith('%PDF'):  # Not a real PDF
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{filename}</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }}
                        pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap; }}
                        h1 {{ color: #333; }}
                    </style>
                </head>
                <body>
                    <h1>Report: {filename}</h1>
                    <pre>{content}</pre>
                </body>
                </html>
                """
                return HTMLResponse(content=html_content)
    except (UnicodeDecodeError, Exception):
        # If we can't read as text, assume it's a binary file (real PDF)
        pass
    
    # Determine media type based on file extension
    media_type = "application/pdf"
    if filename.endswith(".csv"):
        media_type = "text/csv"
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith(".json"):
        media_type = "application/json"
    
    # Serve the file with inline disposition for viewing
    return FileResponse(
        path=str(file_full_path),
        filename=filename,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )


# UPDATE (Admin Only)
@router.put("/{report_id}", response_model=ReportRead)
def update_report(
    report_id: UUID,
    updated: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can update reports.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update reports")

    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Validate updated relations if provided
    if updated.violation_id:
        violation = db.query(Violation).filter(Violation.violation_id == updated.violation_id).first()
        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")

    if updated.generated_by:
        investigator = db.query(Investigator).filter(Investigator.investigator_id == updated.generated_by).first()
        if not investigator:
            raise HTTPException(status_code=404, detail="Investigator not found")

    for key, value in updated.dict(exclude_unset=True).items():
        setattr(report, key, value)

    db.commit()
    db.refresh(report)
    return report


# DELETE (Admin Only)
@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Only admins can delete reports.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete reports")

    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()
    return None
