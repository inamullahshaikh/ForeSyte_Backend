from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import json
import csv
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF generation will create text files. Install with: pip install reportlab")

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
    """Generate a comprehensive JSON report file with all details."""
    try:
        full_path = REPORTS_DIR / Path(file_path).name
        
        # Ensure all data is JSON serializable
        json_data = {
            'report_metadata': {
                'title': data.get('title', 'Report'),
                'generated_at': data.get('generated_at', datetime.utcnow().isoformat()),
                'report_type': data.get('report_type', 'N/A')
            },
            'summary': data.get('summary', {}),
            'exam_information': data.get('exam', {}),
            'activities_and_violations': data.get('activities', []),
            'primary_violation': data.get('primary_violation', None)
        }
        
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        print(f"JSON report generated successfully: {full_path}")
        return True
    except Exception as e:
        print(f"Error generating JSON report: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_csv_report(data: Dict[str, Any], file_path: str) -> bool:
    """Generate a comprehensive CSV report file with detailed violation information."""
    try:
        full_path = REPORTS_DIR / Path(file_path).name
        
        # Prepare rows for CSV with all details
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
                violation_info = activity.get('violation', {})
                row = {
                    'Activity_ID': activity.get('activity_id', ''),
                    'Student_Name': activity.get('student_name', ''),
                    'Roll_Number': activity.get('student_roll_number', ''),
                    'Activity_Type': activity.get('activity_type', ''),
                    'Timestamp': activity.get('timestamp', ''),
                    'Severity': activity.get('severity', ''),
                    'Confidence': activity.get('confidence', ''),
                    'Evidence_URL': activity.get('evidence_url', ''),
                    'Violation_ID': violation_info.get('violation_id', 'N/A') if violation_info else 'N/A',
                    'Violation_Type': violation_info.get('type', 'N/A') if violation_info else 'N/A',
                    'Violation_Severity': violation_info.get('severity', 'N/A') if violation_info else 'N/A',
                    'Violation_Status': violation_info.get('status', 'N/A') if violation_info else 'N/A',
                    'Description': activity.get('description', '')
                }
                
                # Add exam info if available
                if 'exam' in data:
                    row['Exam_Name'] = data['exam'].get('name', '')
                    row['Exam_Date'] = data['exam'].get('date', '')
                
                rows.append(row)
        else:
            # Generic CSV from dict
            rows = [data] if isinstance(data, dict) else data
        
        # If no activities, create a summary row
        if not rows and 'summary' in data:
            rows = [{
                'Report_Type': data.get('report_type', ''),
                'Generated_At': data.get('generated_at', ''),
                'Total_Activities': data['summary'].get('total_activities', 0),
                'Total_Violations': data['summary'].get('total_violations', 0),
                'Unique_Students': data['summary'].get('unique_students_flagged', 0)
            }]
        
        if rows:
            with open(full_path, 'w', newline='', encoding='utf-8') as f:
                if rows:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
        
        print(f"CSV report generated successfully: {full_path}")
        return True
    except Exception as e:
        print(f"Error generating CSV report: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_pdf_report(data: Dict[str, Any], file_path: str) -> bool:
    """Generate a professional PDF report file using reportlab."""
    try:
        full_path = REPORTS_DIR / Path(file_path).name
        if not full_path.suffix.lower() == '.pdf':
            full_path = full_path.with_suffix('.pdf')
        
        if not REPORTLAB_AVAILABLE:
            # Fallback to text file if reportlab is not available
            print("ERROR: reportlab not available!")
            print("Install with: pip install reportlab==4.2.5")
            print("Then restart the backend server.")
            return False
        
        # Create PDF document
        doc = SimpleDocTemplate(str(full_path), pagesize=A4,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        story = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#6e5ae6'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Title
        title = data.get('title', 'Report')
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Report metadata
        metadata_data = [
            ['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')],
            ['Report Type:', data.get('report_type', 'N/A')],
        ]
        
        if 'exam' in data:
            exam_info = data['exam']
            metadata_data.append(['Exam:', exam_info.get('name', 'N/A')])
            metadata_data.append(['Exam Date:', exam_info.get('date', 'N/A')])
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Summary section
        if 'summary' in data and data['summary']:
            story.append(Paragraph("Executive Summary", heading_style))
            summary_data = [['Metric', 'Value']]
            
            # Format summary data with better presentation
            summary = data['summary']
            if 'total_activities' in summary:
                summary_data.append(['Total Activities Detected', str(summary['total_activities'])])
            if 'total_violations' in summary:
                summary_data.append(['Total Violations', str(summary['total_violations'])])
            if 'unique_students_flagged' in summary:
                summary_data.append(['Unique Students Flagged', str(summary['unique_students_flagged'])])
            if 'exam_name' in summary:
                summary_data.append(['Exam Name', summary['exam_name']])
            if 'exam_date' in summary:
                summary_data.append(['Exam Date', summary['exam_date']])
            
            # Add severity breakdown if available
            if 'severity_breakdown' in summary:
                severity = summary['severity_breakdown']
                story.append(Spacer(1, 0.1*inch))
                summary_data.append(['--- Severity Breakdown ---', ''])
                for level, count in severity.items():
                    if count > 0:
                        summary_data.append([f'{level.title()} Severity', str(count)])
            
            summary_table = Table(summary_data, colWidths=[3.5*inch, 2.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6e5ae6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 0.4*inch))
        
        # Detailed Activities and Violations section
        if 'activities' in data and data['activities']:
            story.append(Paragraph("Detailed Violation Report", heading_style))
            story.append(Spacer(1, 0.1*inch))
            
            # Create detailed table with violations
            activities_data = [[
                'Student',
                'Roll No',
                'Activity Type',
                'Time',
                'Severity',
                'Violation Type',
                'Status'
            ]]
            
            for activity in data['activities'][:100]:  # Show up to 100 activities
                violation_info = activity.get('violation', {})
                
                # Determine row color based on severity
                student_name = activity.get('student_name', 'Unknown')
                if len(student_name) > 20:
                    student_name = student_name[:17] + '...'
                
                activities_data.append([
                    student_name,
                    activity.get('student_roll_number', 'N/A'),
                    activity.get('activity_type', 'N/A'),
                    activity.get('timestamp', 'N/A')[-8:] if activity.get('timestamp') else 'N/A',  # Time only
                    str(activity.get('severity', 'N/A')),
                    violation_info.get('type', 'N/A') if violation_info else 'N/A',
                    violation_info.get('status', 'N/A') if violation_info else 'N/A'
                ])
            
            if len(data['activities']) > 100:
                activities_data.append([
                    '...', 
                    f'{len(data["activities"]) - 100} more',
                    '', '', '', '', ''
                ])
            
            activities_table = Table(
                activities_data,
                colWidths=[1.2*inch, 0.8*inch, 1.3*inch, 0.7*inch, 0.6*inch, 1.1*inch, 0.8*inch]
            )
            activities_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6e5ae6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(activities_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Violation section
        if 'violation' in data and data['violation']:
            story.append(Paragraph("Violation Details", heading_style))
            violation = data['violation']
            violation_data = [
                ['Violation ID:', violation.get('id', 'N/A')],
                ['Type:', violation.get('type', 'N/A')],
                ['Severity:', str(violation.get('severity', 'N/A'))],
                ['Status:', violation.get('status', 'N/A')],
            ]
            
            violation_table = Table(violation_data, colWidths=[2*inch, 4*inch])
            violation_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(violation_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"Generated by ForeSyte System | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        story.append(Paragraph(footer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        print(f"PDF report generated successfully: {full_path}")
        return True
        
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        import traceback
        traceback.print_exc()
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
    """Background task to generate the actual report file with detailed information."""
    db = SessionLocal()
    try:
        from database.models import Student, Violation as ViolationModel
        
        # Prepare comprehensive report data
        report_data = {
            'title': f"{report_type.title()} Report",
            'generated_at': datetime.utcnow().isoformat(),
            'report_type': report_type,
            'summary': {}
        }
        
        # Collect detailed violation information
        violations_list = []
        unique_students = set()
        severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        if activities:
            # Build detailed activities with student info and violations
            detailed_activities = []
            
            for act in activities:
                # Get student information
                student = db.query(Student).filter(Student.student_id == act.student_id).first()
                student_name = f"{student.name}" if student else "Unknown Student"
                student_roll = student.roll_number if student else "N/A"
                unique_students.add(str(act.student_id))
                
                # Get associated violation
                act_violation = db.query(ViolationModel).filter(
                    ViolationModel.activity_id == act.activity_id
                ).first()
                
                # Determine severity category
                if act.severity:
                    if act.severity in ['low', 'medium', 'high', 'critical']:
                        severity_counts[act.severity] += 1
                    elif isinstance(act.severity, int):
                        if act.severity <= 1:
                            severity_counts['low'] += 1
                        elif act.severity == 2:
                            severity_counts['medium'] += 1
                        elif act.severity == 3:
                            severity_counts['high'] += 1
                        else:
                            severity_counts['critical'] += 1
                
                activity_detail = {
                    'activity_id': str(act.activity_id),
                    'activity_type': act.activity_type or 'Unknown',
                    'timestamp': act.timestamp.strftime('%Y-%m-%d %H:%M:%S') if act.timestamp else '',
                    'student_id': str(act.student_id) if act.student_id else '',
                    'student_name': student_name,
                    'student_roll_number': student_roll,
                    'severity': str(act.severity) if act.severity else 'N/A',
                    'confidence': f"{act.confidence * 100:.1f}%" if act.confidence else 'N/A',
                    'evidence_url': act.evidence_url or 'N/A',
                    'description': f"{act.activity_type} detected at {act.timestamp.strftime('%H:%M:%S') if act.timestamp else 'unknown time'}"
                }
                
                # Add violation information if exists
                if act_violation:
                    activity_detail['violation'] = {
                        'violation_id': str(act_violation.violation_id),
                        'type': act_violation.violation_type or 'N/A',
                        'severity': act_violation.severity or 0,
                        'status': act_violation.status or 'pending',
                        'timestamp': act_violation.timestamp.strftime('%Y-%m-%d %H:%M:%S') if act_violation.timestamp else ''
                    }
                    violations_list.append(activity_detail['violation'])
                else:
                    activity_detail['violation'] = None
                
                detailed_activities.append(activity_detail)
            
            report_data['activities'] = detailed_activities
            report_data['summary']['total_activities'] = len(activities)
            report_data['summary']['total_violations'] = len(violations_list)
            report_data['summary']['unique_students_flagged'] = len(unique_students)
            report_data['summary']['severity_breakdown'] = severity_counts
        
        if exam:
            report_data['exam'] = {
                'id': str(exam.exam_id),
                'name': exam.course or 'Unknown',
                'course_code': exam.course or 'N/A',
                'date': exam.exam_date.strftime('%Y-%m-%d') if exam.exam_date else '',
                'start_time': exam.start_time.strftime('%H:%M:%S') if exam.start_time else 'N/A',
                'end_time': exam.end_time.strftime('%H:%M:%S') if exam.end_time else 'N/A',
            }
            report_data['summary']['exam_name'] = exam.course or 'Unknown'
            report_data['summary']['exam_date'] = exam.exam_date.strftime('%Y-%m-%d') if exam.exam_date else 'N/A'
        
        if violation:
            report_data['primary_violation'] = {
                'id': str(violation.violation_id),
                'type': violation.violation_type or 'Unknown',
                'severity': violation.severity or 0,
                'status': violation.status or 'pending',
                'timestamp': violation.timestamp.strftime('%Y-%m-%d %H:%M:%S') if violation.timestamp else '',
                'evidence_url': violation.evidence_url or 'N/A'
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
                # Check what file was actually created
                base_name = Path(file_path).stem
                
                # Try to find the actual file
                possible_extensions = []
                if format_type.lower() == 'pdf':
                    possible_extensions = ['.pdf', '.txt']  # Fallback for PDF
                elif format_type.lower() == 'csv':
                    possible_extensions = ['.csv']
                elif format_type.lower() == 'json':
                    possible_extensions = ['.json']
                
                actual_file = None
                for ext in possible_extensions:
                    test_file = REPORTS_DIR / f"{base_name}{ext}"
                    if test_file.exists():
                        actual_file = test_file
                        break
                
                if actual_file:
                    report.file_path = f"/reports/{actual_file.name}"
                    print(f"Report file saved: {actual_file.name}")
                else:
                    print(f"Warning: Generated file not found for {base_name}")
                    report.status = "failed"
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


# DOWNLOAD Report File
@router.get("/{report_id}/download")
def download_report(
    report_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Download a report file."""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if report is completed
    if report.status != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Report is not ready for download. Current status: {report.status}"
        )
    
    # Get the file path - it's stored as /reports/filename.ext
    if not report.file_path:
        raise HTTPException(status_code=404, detail="Report file path not found")
    
    # Extract filename from path
    filename = Path(report.file_path).name
    file_full_path = REPORTS_DIR / filename
    
    # If file doesn't exist, try alternative extensions (for backwards compatibility)
    if not file_full_path.exists():
        # Try alternative extensions
        base_name = file_full_path.stem
        possible_extensions = ['.pdf', '.txt', '.csv', '.json']
        
        found = False
        for ext in possible_extensions:
            alternative_path = REPORTS_DIR / f"{base_name}{ext}"
            if alternative_path.exists():
                file_full_path = alternative_path
                filename = alternative_path.name
                found = True
                break
        
        if not found:
            raise HTTPException(
                status_code=404, 
                detail=f"Report file not found on server: {filename} (checked all extensions)"
            )
    
    # Determine media type based on file extension
    extension = file_full_path.suffix.lower()
    media_type_map = {
        '.pdf': 'application/pdf',
        '.csv': 'text/csv',
        '.json': 'application/json',
        '.txt': 'text/plain'
    }
    media_type = media_type_map.get(extension, 'application/octet-stream')
    
    # Return file as download
    return FileResponse(
        path=str(file_full_path),
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
