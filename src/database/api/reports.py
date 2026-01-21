from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import json
import csv
from pathlib import Path

from database.db import get_db, SessionLocal
from database.models import Report, Violation, Investigator, StudentActivity, Exam
from database.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

# -------------------------
# Report Generation Utilities
# -------------------------
REPORTS_DIR = Path("uploads/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def generate_json_report(data: Dict[str, Any], file_path: str) -> bool:
    """Generate a JSON report file."""
    try:
        full_path = REPORTS_DIR / Path(file_path).name
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error generating JSON report: {e}")
        return False

def generate_csv_report(data: Dict[str, Any], file_path: str) -> bool:
    """Generate a CSV report file."""
    try:
        full_path = REPORTS_DIR / Path(file_path).name
        
        # Flatten the data structure for CSV
        rows = []
        if 'incidents' in data:
            for incident in data['incidents']:
                row = {
                    'incident_id': incident.get('id', ''),
                    'type': incident.get('type', ''),
                    'timestamp': incident.get('timestamp', ''),
                    'student_name': incident.get('student_name', ''),
                    'severity': incident.get('severity', ''),
                    'status': incident.get('status', '')
                }
                rows.append(row)
        elif 'activities' in data:
            for activity in data['activities']:
                row = {
                    'activity_id': activity.get('id', ''),
                    'type': activity.get('type', ''),
                    'timestamp': activity.get('timestamp', ''),
                    'student_id': activity.get('student_id', ''),
                    'description': activity.get('description', '')
                }
                rows.append(row)
        else:
            # Generic CSV from dict
            rows = [data] if isinstance(data, dict) else data
        
        if rows:
            with open(full_path, 'w', newline='', encoding='utf-8') as f:
                if rows:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
        return True
    except Exception as e:
        print(f"Error generating CSV report: {e}")
        return False

def generate_pdf_report(data: Dict[str, Any], file_path: str) -> bool:
    """Generate a simple PDF report file (text-based for now)."""
    try:
        full_path = REPORTS_DIR / Path(file_path).name.replace('.pdf', '.txt')
        
        # Create a simple text report (can be upgraded to actual PDF later)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            
            if 'title' in data:
                f.write(f"Title: {data['title']}\n\n")
            
            if 'summary' in data:
                f.write("SUMMARY\n")
                f.write("-" * 80 + "\n")
                for key, value in data['summary'].items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
            
            if 'incidents' in data:
                f.write("INCIDENTS\n")
                f.write("-" * 80 + "\n")
                for incident in data['incidents']:
                    f.write(f"ID: {incident.get('id', 'N/A')}\n")
                    f.write(f"Type: {incident.get('type', 'N/A')}\n")
                    f.write(f"Timestamp: {incident.get('timestamp', 'N/A')}\n")
                    f.write(f"Student: {incident.get('student_name', 'N/A')}\n")
                    f.write("\n")
            
            if 'activities' in data:
                f.write("ACTIVITIES\n")
                f.write("-" * 80 + "\n")
                for activity in data['activities']:
                    f.write(f"ID: {activity.get('id', 'N/A')}\n")
                    f.write(f"Type: {activity.get('type', 'N/A')}\n")
                    f.write(f"Timestamp: {activity.get('timestamp', 'N/A')}\n")
                    f.write("\n")
        
        # For now, we'll create a text file. In production, use a PDF library like reportlab
        return True
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        return False

async def generate_report_file_async(
    report_id: UUID,
    report_type: str,
    file_path: str,
    format_type: str,
    activities: List[StudentActivity] = None,
    exam: Exam = None,
    violation: Violation = None
):
    """Background task to generate the actual report file."""
    db = SessionLocal()
    try:
        # Prepare report data
        report_data = {
            'title': f"{report_type.title()} Report",
            'generated_at': datetime.utcnow().isoformat(),
            'report_type': report_type,
            'summary': {}
        }
        
        if activities:
            report_data['activities'] = [
                {
                    'id': str(act.activity_id),
                    'type': act.activity_type or 'Unknown',
                    'timestamp': act.timestamp.isoformat() if act.timestamp else '',
                    'student_id': str(act.student_id) if act.student_id else '',
                    'description': f"Activity detected: {act.activity_type}"
                }
                for act in activities
            ]
            report_data['summary']['total_activities'] = len(activities)
        
        if exam:
            report_data['exam'] = {
                'id': str(exam.exam_id),
                'name': exam.course or 'Unknown',
                'date': exam.exam_date.isoformat() if exam.exam_date else '',
            }
            report_data['summary']['exam_name'] = exam.course or 'Unknown'
        
        if violation:
            report_data['violation'] = {
                'id': str(violation.violation_id),
                'type': violation.violation_type or 'Unknown',
                'severity': violation.severity or 0,
                'status': violation.status or 'pending'
            }
        
        # Generate the file based on format
        success = False
        if format_type.lower() == 'json':
            success = generate_json_report(report_data, file_path)
        elif format_type.lower() == 'csv':
            success = generate_csv_report(report_data, file_path)
        elif format_type.lower() == 'pdf':
            success = generate_pdf_report(report_data, file_path)
        else:
            # Default to JSON
            success = generate_json_report(report_data, file_path)
        
        # Update report status
        report = db.query(Report).filter(Report.report_id == report_id).first()
        if report:
            if success:
                report.status = "completed"
                # Update file_path to actual generated file
                actual_file = REPORTS_DIR / Path(file_path).name
                if actual_file.exists():
                    report.file_path = f"/reports/{actual_file.name}"
            else:
                report.status = "failed"
            db.commit()
        
    except Exception as e:
        print(f"Error in background report generation: {e}")
        # Update status to failed
        try:
            report = db.query(Report).filter(Report.report_id == report_id).first()
            if report:
                report.status = "failed"
                db.commit()
        except:
            pass
    finally:
        db.close()

# -------------------------
# Helper Functions
# -------------------------
def get_investigator_id_for_report(current_user: dict, db: Session) -> UUID:
    """
    Get the appropriate investigator_id for report generation.
    If user is an investigator, use their ID. If admin, use a default investigator.
    Always returns a valid investigator_id - creates a system investigator if needed.
    """
    user_type = current_user.get("user_type")
    user_id = current_user.get("id")
    
    # Debug logging
    print(f"[REPORT DEBUG] get_investigator_id_for_report called - user_type: {user_type}, user_id: {user_id}")
    
    if user_type == "investigator":
        try:
            investigator_id = UUID(user_id)
            # Verify the investigator exists
            investigator = db.query(Investigator).filter(Investigator.investigator_id == investigator_id).first()
            if not investigator:
                print(f"[REPORT DEBUG] WARNING: Investigator {investigator_id} not found! Creating system investigator...")
                # Fall through to create system investigator
            else:
                print(f"[REPORT DEBUG] Using investigator ID: {investigator_id}")
                return investigator_id
        except (ValueError, TypeError) as e:
            print(f"[REPORT DEBUG] Invalid investigator ID format: {e}. Creating system investigator...")
            # Fall through to create system investigator
    
    # For admins OR if investigator not found, use/create a system investigator
    print(f"[REPORT DEBUG] Looking for default investigator...")
    default_investigator = db.query(Investigator).first()
    
    if default_investigator:
        print(f"[REPORT DEBUG] Found investigator ID: {default_investigator.investigator_id}")
        return default_investigator.investigator_id
    else:
        # Create a system investigator if none exists
        print(f"[REPORT DEBUG] No investigators found! Creating system investigator...")
        from database.auth import hash_password
        
        # Check again to avoid race condition (in case another request created one)
        default_investigator = db.query(Investigator).filter(Investigator.email == "system@foresyte.edu").first()
        if default_investigator:
            print(f"[REPORT DEBUG] System investigator already exists: {default_investigator.investigator_id}")
            return default_investigator.investigator_id
        
        system_investigator = Investigator(
            name="System Investigator",
            email="system@foresyte.edu",
            designation="System",
            password_hash=hash_password("System123!")
        )
        db.add(system_investigator)
        db.commit()
        db.refresh(system_investigator)
        print(f"[REPORT DEBUG] Created system investigator with ID: {system_investigator.investigator_id}")
        return system_investigator.investigator_id

# -------------------------
# Pydantic Schemas
# -------------------------
class ReportCreate(BaseModel):
    report_type: str
    file_path: str
    violation_id: UUID
    generated_by: UUID
    status: Optional[str] = "generating"  # Default to generating - reports need async processing


class ReportRead(BaseModel):
    report_id: UUID
    report_type: str
    generated_date: date
    file_path: str
    violation_id: Optional[UUID] = None  # Made optional since reports can exist without violations
    generated_by: UUID
    status: str = "generating"  # generating, completed, failed

    model_config = {
        "from_attributes": True
    }


class ReportUpdate(BaseModel):
    report_type: Optional[str] = None
    file_path: Optional[str] = None
    violation_id: Optional[UUID] = None
    generated_by: Optional[UUID] = None
    status: Optional[str] = None  # completed, generating, failed


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

    report_dict = report.dict()
    # Ensure status is set if not provided
    if 'status' not in report_dict:
        report_dict['status'] = 'generating'
    new_report = Report(**report_dict)
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
    background_tasks: BackgroundTasks,
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

    # Get investigator_id for report (handles both admin and investigator users)
    investigator_id = get_investigator_id_for_report(current_user, db)
    
    new_report = Report(
        report_type="incident",
        file_path=file_path,
        violation_id=violation.violation_id,
        generated_by=investigator_id,
        status="generating"  # Will be updated to "completed" by background task
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    # Start background task to generate the actual report file
    background_tasks.add_task(
        generate_report_file_async,
        report_id=new_report.report_id,
        report_type="incident",
        file_path=file_path,
        format_type=request.format,
        activities=activities,
        violation=violation
    )

    # Return report URL or file path
    return {
        "id": str(new_report.report_id),
        "file_path": file_path,
        "format": request.format,
        "status": "generating"
    }


# -------------------------
# Generate Exam Report
# -------------------------
@router.post("/exams/{exam_id}")
def generate_exam_report(
    exam_id: UUID,
    request: ExamReportRequest,
    background_tasks: BackgroundTasks,
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

    # Get investigator_id for report (handles both admin and investigator users)
    investigator_id = get_investigator_id_for_report(current_user, db)

    new_report = Report(
        report_type="exam",
        file_path=file_path,
        violation_id=violation.violation_id if violation else None,
        generated_by=investigator_id,
        status="generating"  # Will be updated to "completed" by background task
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    # Start background task to generate the actual report file
    background_tasks.add_task(
        generate_report_file_async,
        report_id=new_report.report_id,
        report_type="exam",
        file_path=file_path,
        format_type=request.format,
        activities=activities,
        exam=exam,
        violation=violation
    )

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
    Admins and Investigators can view all reports with pagination.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(Report)
    total = query.count()
    
    offset = (page - 1) * limit
    reports = query.order_by(Report.generated_date.desc()).offset(offset).limit(limit).all()

    return ReportListResponse(
        reports=reports,
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
    Admins and Investigators can view a specific report.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return report


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


# UPDATE Report Status (for async report generation)
@router.patch("/{report_id}/status", response_model=ReportRead)
def update_report_status(
    report_id: UUID,
    new_status: str = Query(..., regex="^(generating|completed|failed)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update report status (used by async report generation tasks).
    Allows updating status from 'generating' to 'completed' or 'failed'.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = new_status
    db.commit()
    db.refresh(report)
    return report
