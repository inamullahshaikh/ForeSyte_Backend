from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from collections import defaultdict
from pydantic import BaseModel
import os
import json
import csv
import logging
import html
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError as e:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not installed: %s. PDF generation will create text files. Install with: pip install reportlab", e)

from database.db import get_db, SessionLocal
from database.models import Report, Violation, Investigator, StudentActivity, Exam, Student, InvigilatorActivity, Invigilator, Room
from database.auth import get_current_user
from database.severity_logic import severity_from_int

router = APIRouter(prefix="/reports", tags=["Reports"])

# -------------------------
# Report Generation Utilities
# -------------------------
REPORTS_DIR = Path("uploads/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def generate_json_report(data: Dict[str, Any], file_path: str) -> bool:
    """Generate a comprehensive JSON report file with all details."""
    full_path = REPORTS_DIR / Path(file_path).name
    logger.info("generate_json_report: starting, file_path=%s, full_path=%s", file_path, full_path)
    try:
        # Ensure all data is JSON serializable
        json_data = {
            'report_metadata': {
                'title': data.get('title', 'Report'),
                'generated_at': data.get('generated_at', datetime.utcnow().isoformat()),
                'report_type': data.get('report_type', 'N/A'),
                'violation_view': data.get('violation_view', 'all'),
            },
            'summary': data.get('summary', {}),
            'exam_information': data.get('exam', {}),
            'activities_and_violations': data.get('activities', []),
            'aggregated_violations': data.get('aggregated_violations', []),
            'primary_violation': data.get('primary_violation', None),
        }
        
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        logger.info("generate_json_report: success, path=%s", full_path)
        return True
    except Exception as e:
        logger.exception("generate_json_report failed: file_path=%s, error=%s", file_path, e)
        return False

def generate_csv_report(data: Dict[str, Any], file_path: str) -> bool:
    """Generate a comprehensive CSV report file with detailed violation information."""
    full_path = REPORTS_DIR / Path(file_path).name
    logger.info("generate_csv_report: starting, file_path=%s, full_path=%s", file_path, full_path)
    try:
        # Prepare rows for CSV with all details
        rows = []
        if data.get('violation_view') == 'summary' and data.get('aggregated_violations'):
            for row in data['aggregated_violations']:
                urls = row.get('evidence_urls') or []
                rows.append({
                    'Student_Name': row.get('student_name', ''),
                    'Roll_Number': row.get('student_roll_number', ''),
                    'Violation_Type': row.get('activity_type', ''),
                    'Severity': row.get('severity', ''),
                    'Frequency': row.get('frequency', 0),
                    'Evidence_URLs': '; '.join(str(u) for u in urls) if urls else '',
                })
        elif 'incidents' in data:
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
            if data.get('report_type') == 'invigilator':
                for activity in data['activities']:
                    row = {
                        'Invigilator_Name': activity.get('invigilator_name', ''),
                        'Room': activity.get('room_name', ''),
                        'Timestamp': activity.get('timestamp', ''),
                        'Activity_Type': activity.get('activity_type', ''),
                        'Notes': activity.get('notes', '') or '',
                    }
                    rows.append(row)
            else:
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
                    'Description': activity.get('description', ''),
                    'Exam_Name': activity.get('exam_name', data['exam'].get('name', '') if 'exam' in data else ''),
                    'Exam_Date': activity.get('exam_date', data['exam'].get('date', '') if 'exam' in data else ''),
                    }
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
        
        logger.info("generate_csv_report: success, path=%s, rows=%s", full_path, len(rows))
        return True
    except Exception as e:
        logger.exception("generate_csv_report failed: file_path=%s, error=%s", file_path, e)
        return False

# Severity colors for PDF (background, text) - appealing tag-style colors
def _truncate_cell(text: str, max_len: int = 16) -> str:
    """Truncate text for table cells to prevent overflow."""
    if not text:
        return "N/A"
    s = str(text).strip()
    # Strip any trailing time pattern like :20:00 or :11:20:00 that may have been concatenated
    if ":" in s and len(s) > 10:
        parts = s.rsplit(":", 2)
        if len(parts) == 3 and all(p.isdigit() for p in parts[-2:]):
            s = parts[0].strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def _severity_pdf_colors(severity: str) -> tuple:
    """Return (background_hex, text_hex) for severity level for use in PDF."""
    s = (severity or "").lower().strip()
    if s == "critical":
        return ("#fecaca", "#991b1b")  # red
    if s == "high":
        return ("#fed7aa", "#9a3412")  # orange
    if s == "medium":
        return ("#fef3c7", "#92400e")  # amber
    if s == "low":
        return ("#dcfce7", "#166534")  # green
    return ("#f1f5f9", "#475569")  # slate/gray for N/A


def generate_pdf_report(data: Dict[str, Any], file_path: str) -> bool:
    """Generate a professional PDF report file using reportlab."""
    full_path = REPORTS_DIR / Path(file_path).name
    logger.info("generate_pdf_report: starting, file_path=%s, full_path=%s", file_path, full_path)
    try:
        if not full_path.suffix.lower() == '.pdf':
            full_path = full_path.with_suffix('.pdf')
        
        if not REPORTLAB_AVAILABLE:
            logger.error("generate_pdf_report: reportlab not available. Install with: pip install reportlab==4.2.5")
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
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            wordWrap='CJK',
        )

        def _cell_para(s: Any) -> Any:
            """Wrap text in a Paragraph so it wraps in table cells; no truncation."""
            if s is None or (isinstance(s, str) and not s.strip()):
                return Paragraph("—", cell_style)
            return Paragraph(html.escape(str(s).strip()), cell_style)

        # Title
        title = data.get('title', 'Report')
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Report metadata (use Paragraph for values so long exam names wrap)
        metadata_data = [
            ['Generated:', _cell_para(datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))],
            ['Report Type:', _cell_para(data.get('report_type', 'N/A'))],
        ]
        if 'exam' in data:
            exam_info = data['exam']
            metadata_data.append(['Exam:', _cell_para(exam_info.get('name', 'N/A'))])
            metadata_data.append(['Exam Date:', _cell_para(exam_info.get('date', 'N/A'))])

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
        
        # Summary section (full text with wrapping; no truncation)
        if 'summary' in data and data['summary']:
            story.append(Paragraph("Executive Summary", heading_style))
            summary_data = [[_cell_para('Metric'), _cell_para('Value')]]

            summary = data['summary']
            if 'total_activities' in summary:
                summary_data.append([_cell_para('Total Activities Detected'), _cell_para(str(summary['total_activities']))])
            if 'total_violations' in summary:
                summary_data.append([_cell_para('Total Violations'), _cell_para(str(summary['total_violations']))])
            if 'unique_students_flagged' in summary:
                summary_data.append([_cell_para('Unique Students Flagged'), _cell_para(str(summary['unique_students_flagged']))])
            if 'exam_name' in summary:
                summary_data.append([_cell_para('Exam Name'), _cell_para(summary['exam_name'])])
            if 'exam_date' in summary:
                summary_data.append([_cell_para('Exam Date'), _cell_para(summary['exam_date'])])

            severity_breakdown_start_row = None
            if 'severity_breakdown' in summary:
                severity = summary['severity_breakdown']
                story.append(Spacer(1, 0.1*inch))
                summary_data.append([_cell_para('--- Severity Breakdown ---'), _cell_para('')])
                severity_breakdown_start_row = len(summary_data)
                for level, count in severity.items():
                    if count > 0:
                        summary_data.append([_cell_para(f'{level.title()} Severity'), _cell_para(str(count))])

            summary_style_commands = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6e5ae6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]
            if severity_breakdown_start_row is not None and summary.get('severity_breakdown'):
                for idx, (level, count) in enumerate(summary['severity_breakdown'].items()):
                    if count <= 0:
                        continue
                    r = severity_breakdown_start_row + 1 + idx
                    if "critical" in level.lower():
                        bg, tx = _severity_pdf_colors("critical")
                    elif "high" in level.lower():
                        bg, tx = _severity_pdf_colors("high")
                    elif "medium" in level.lower():
                        bg, tx = _severity_pdf_colors("medium")
                    elif "low" in level.lower():
                        bg, tx = _severity_pdf_colors("low")
                    else:
                        continue
                    summary_style_commands.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor(bg)))
                    summary_style_commands.append(('TEXTCOLOR', (0, r), (-1, r), colors.HexColor(tx)))
            summary_table = Table(summary_data, colWidths=[2.5*inch, 4*inch])
            summary_table.setStyle(TableStyle(summary_style_commands))
            story.append(summary_table)
            story.append(Spacer(1, 0.4*inch))
        
        # Detailed Activities and Violations section
        if 'activities' in data and data['activities']:
            if data.get('report_type') == 'invigilator':
                story.append(Paragraph("Invigilator Activities", heading_style))
                story.append(Spacer(1, 0.1*inch))
                inv_headers = [[_cell_para('Invigilator'), _cell_para('Room'), _cell_para('Time'), _cell_para('Activity Type'), _cell_para('Notes')]]
                inv_col_widths = [1.4*inch, 1.1*inch, 0.9*inch, 1.2*inch, 2*inch]
                for activity in data['activities'][:100]:
                    ts = activity.get('timestamp', 'N/A')
                    if isinstance(ts, str) and len(ts) > 12:
                        ts = ts[-8:]
                    inv_headers.append([
                        _cell_para(activity.get('invigilator_name') or 'N/A'),
                        _cell_para(activity.get('room_name') or 'N/A'),
                        ts,
                        _cell_para(activity.get('activity_type') or 'N/A'),
                        _cell_para((activity.get('notes') or '').strip() or '—'),
                    ])
                if len(data['activities']) > 100:
                    inv_headers.append(['...', f'{len(data["activities"]) - 100} more', '', '', ''])
                inv_table = Table(inv_headers, colWidths=inv_col_widths)
                inv_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6e5ae6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(inv_table)
                story.append(Spacer(1, 0.3*inch))
            elif data.get('violation_view') == 'summary' and data.get('aggregated_violations'):
                story.append(Paragraph("Violations by student (type, severity, frequency)", heading_style))
                story.append(Spacer(1, 0.1*inch))
                agg_headers = [[_cell_para('Student'), _cell_para('Roll No'), _cell_para('Violation Type'), _cell_para('Severity'), _cell_para('Frequency'), _cell_para('Evidence (video links)')]]
                agg_col_widths = [1.3*inch, 0.75*inch, 1.4*inch, 0.65*inch, 0.55*inch, 1.8*inch]
                for row in data['aggregated_violations']:
                    urls = row.get('evidence_urls') or []
                    links_str = ", ".join(str(u) for u in urls[:3]) if urls else "—"
                    agg_headers.append([
                        _cell_para(row.get('student_name') or 'N/A'),
                        _cell_para(row.get('student_roll_number') or 'N/A'),
                        _cell_para(row.get('activity_type') or 'N/A'),
                        (row.get('severity') or 'N/A'),
                        str(row.get('frequency', 0)),
                        _cell_para(links_str),
                    ])
                agg_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6e5ae6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]
                for r in range(1, len(agg_headers)):
                    if len(agg_headers[r]) > 3:
                        sev = (agg_headers[r][3] or "N/A").strip()
                        bg, tx = _severity_pdf_colors(sev)
                        agg_style.append(('BACKGROUND', (3, r), (3, r), colors.HexColor(bg)))
                        agg_style.append(('TEXTCOLOR', (3, r), (3, r), colors.HexColor(tx)))
                agg_table = Table(agg_headers, colWidths=agg_col_widths)
                agg_table.setStyle(TableStyle(agg_style))
                story.append(agg_table)
                story.append(Spacer(1, 0.3*inch))
            else:
                story.append(Paragraph("Detailed Violation Report", heading_style))
                story.append(Spacer(1, 0.1*inch))
            
                # Create detailed table with violations (include Exam for student reports, Evidence link)
                has_per_activity_exam = any(a.get('exam_name') for a in data['activities'][:1])
                if has_per_activity_exam:
                    activities_data = [[
                        'Student', 'Roll No', 'Exam', 'Activity Type', 'Time', 'Severity', 'Violation Type', 'Status', 'Evidence'
                    ]]
                    col_widths = [1.0*inch, 0.6*inch, 1.0*inch, 1.0*inch, 0.5*inch, 0.5*inch, 0.9*inch, 0.6*inch, 0.5*inch]
                else:
                    activities_data = [[
                        'Student', 'Roll No', 'Activity Type', 'Time', 'Severity', 'Violation Type', 'Status', 'Evidence'
                    ]]
                    col_widths = [1.2*inch, 0.8*inch, 1.3*inch, 0.7*inch, 0.6*inch, 1.1*inch, 0.8*inch, 0.5*inch]
            
                for activity in data['activities'][:100]:  # Show up to 100 activities
                    violation_info = activity.get('violation', {})
                    student_name = activity.get('student_name', 'Unknown')
                    if len(student_name) > 20:
                        student_name = student_name[:17] + '...'
                    exam_display = (activity.get('exam_name') or '') + (' ' + (activity.get('exam_date') or '') if activity.get('exam_date') else '')
                    if len(exam_display) > 14:
                        exam_display = exam_display[:11] + '...'
                    ev_url = activity.get('evidence_url') or 'N/A'
                    if ev_url and ev_url != 'N/A' and (ev_url.startswith('http://') or ev_url.startswith('https://')):
                        evidence_cell = Paragraph(f'<a href="{ev_url}" color="#0066cc">View</a>', styles['Normal'])
                    else:
                        evidence_cell = ev_url[:8] + '...' if ev_url and len(str(ev_url)) > 8 else (ev_url or '-')
                    ts = activity.get('timestamp') or 'N/A'
                    time_str = (ts[-8:] if isinstance(ts, str) and len(ts) >= 8 else ts) if ts != 'N/A' else 'N/A'
                    row = [
                        _cell_para(student_name),
                        _cell_para(activity.get('student_roll_number') or 'N/A'),
                        _cell_para(activity.get('activity_type') or 'N/A'),
                        _cell_para(time_str),
                        str(activity.get('severity', 'N/A')),
                        violation_info.get('type', 'N/A') if violation_info else 'N/A',
                        violation_info.get('status', 'N/A') if violation_info else 'N/A',
                        evidence_cell
                    ]
                    if has_per_activity_exam:
                        row.insert(2, _cell_para(exam_display))
                    activities_data.append(row)
            
                if len(data['activities']) > 100:
                    pad_len = len(activities_data[0])
                    pad = ['...', f'{len(data["activities"]) - 100} more'] + ([''] * (pad_len - 2))
                    activities_data.append(pad[:pad_len])
            
                severity_col = 5 if has_per_activity_exam else 4
                act_style_commands = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6e5ae6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]
                # Colored severity cells (tag-style)
                for r in range(1, len(activities_data)):
                    if severity_col < len(activities_data[r]):
                        sev = (activities_data[r][severity_col] or "N/A").strip()
                        bg, tx = _severity_pdf_colors(sev)
                        act_style_commands.append(('BACKGROUND', (severity_col, r), (severity_col, r), colors.HexColor(bg)))
                        act_style_commands.append(('TEXTCOLOR', (severity_col, r), (severity_col, r), colors.HexColor(tx)))
                activities_table = Table(activities_data, colWidths=col_widths)
                activities_table.setStyle(TableStyle(act_style_commands))
                story.append(activities_table)
                story.append(Spacer(1, 0.3*inch))
        
        # Violation section (primary_violation from report_data)
        viol_data = data.get('primary_violation') or data.get('violation')
        if viol_data:
            story.append(Paragraph("Violation Details", heading_style))
            violation = viol_data
            ev_url = violation.get('evidence_url') or 'N/A'
            evidence_row = ['Evidence:', ev_url]
            if ev_url and ev_url != 'N/A' and (str(ev_url).startswith('http://') or str(ev_url).startswith('https://')):
                evidence_row[1] = Paragraph(f'<a href="{ev_url}" color="#0066cc">View evidence image</a>', styles['Normal'])
            sev_val = str(violation.get('severity', 'N/A'))
            violation_data = [
                ['Violation ID:', violation.get('id', 'N/A')],
                ['Type:', violation.get('type', 'N/A')],
                ['Severity:', sev_val],
                ['Status:', violation.get('status', 'N/A')],
                evidence_row,
            ]
            vbg, vtx = _severity_pdf_colors(sev_val)
            violation_table = Table(violation_data, colWidths=[2*inch, 4*inch])
            violation_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('BACKGROUND', (1, 2), (1, 2), colors.HexColor(vbg)),
                ('TEXTCOLOR', (1, 2), (1, 2), colors.HexColor(vtx)),
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
        logger.info("generate_pdf_report: success, path=%s", full_path)
        return True
        
    except Exception as e:
        logger.exception("generate_pdf_report failed: file_path=%s, error=%s", file_path, e)
        return False

async def generate_report_file_async(
    report_id: UUID,
    report_type: str,
    file_path: str,
    format_type: str,
    activities: List[StudentActivity] = None,
    exam: Exam = None,
    violation: Violation = None,
    violation_view: str = "all",  # "all" | "summary" (summary = per-student: student, type, severity, frequency + evidence_urls)
):
    """Background task to generate the actual report file with detailed information."""
    logger.info(
        "generate_report_file_async: start report_id=%s report_type=%s file_path=%s format=%s activities_count=%s exam=%s has_violation=%s REPORTS_DIR=%s exists=%s",
        report_id, report_type, file_path, format_type,
        len(activities) if activities else 0,
        exam.exam_id if exam else None,
        violation is not None,
        REPORTS_DIR.resolve(),
        REPORTS_DIR.exists(),
    )
    db = SessionLocal()
    try:
        from database.models import Student, Violation as ViolationModel
        from app.storage.b2_storage import download_evidence_for_report

        # Collect all evidence URLs and download from B2 to uploads/downloads/evidence
        evidence_urls = []
        if activities:
            evidence_urls.extend(a.evidence_url for a in activities if a.evidence_url and a.evidence_url != "N/A")
        if violation and violation.evidence_url and violation.evidence_url != "N/A":
            evidence_urls.append(violation.evidence_url)
        evidence_url_map = download_evidence_for_report(str(report_id), list(set(evidence_urls)))

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
                
                # Per-activity exam info (for student report: violations across different exams)
                exam_for_act = db.query(Exam).filter(Exam.exam_id == act.exam_id).first() if act.exam_id else None
                activity_detail_exam_name = (exam_for_act.course or "N/A") if exam_for_act else "N/A"
                activity_detail_exam_date = (exam_for_act.exam_date.strftime("%Y-%m-%d") if exam_for_act and exam_for_act.exam_date else "N/A")
                
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
                
                # Use localhost link from downloads folder when available
                orig_evidence = act.evidence_url or "N/A"
                evidence_display = evidence_url_map.get(orig_evidence, orig_evidence) if orig_evidence != "N/A" else "N/A"
                activity_detail = {
                    'activity_id': str(act.activity_id),
                    'activity_type': act.activity_type or 'Unknown',
                    'timestamp': act.timestamp.strftime('%Y-%m-%d %H:%M:%S') if act.timestamp else '',
                    'student_id': str(act.student_id) if act.student_id else '',
                    'student_name': student_name,
                    'student_roll_number': student_roll,
                    'exam_name': activity_detail_exam_name,
                    'exam_date': activity_detail_exam_date,
                    'severity': str(act.severity) if act.severity else 'N/A',
                    'confidence': f"{act.confidence * 100:.1f}%" if act.confidence else 'N/A',
                    'evidence_url': evidence_display,
                    'description': f"{act.activity_type} detected at {act.timestamp.strftime('%H:%M:%S') if act.timestamp else 'unknown time'}"
                }
                
                # Add violation information if exists
                if act_violation:
                    activity_detail['violation'] = {
                        'violation_id': str(act_violation.violation_id),
                        'type': act_violation.violation_type or 'N/A',
                        'severity': severity_from_int(act_violation.severity or 1),
                        'status': act_violation.status or 'pending',
                        'timestamp': act_violation.timestamp.strftime('%Y-%m-%d %H:%M:%S') if act_violation.timestamp else '',
                        'evidence_url': act_violation.evidence_url or ''
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
            report_data['violation_view'] = violation_view or "all"
            if violation_view == "summary":
                # Group by (student_id, student_name, roll, activity_type, severity) so report is per-student
                agg = defaultdict(lambda: {"count": 0, "evidence_urls": []})
                for d in detailed_activities:
                    sid = d.get("student_id") or ""
                    sname = (d.get("student_name") or "Unknown").strip()
                    sroll = (d.get("student_roll_number") or "N/A").strip()
                    atype = d.get("activity_type") or "Unknown"
                    sev = d.get("severity") or "N/A"
                    key = (sname, sroll, sid, atype, sev)
                    agg[key]["count"] += 1
                    u1 = d.get("evidence_url")
                    if u1 and str(u1).strip() and str(u1) != "N/A":
                        if u1 not in agg[key]["evidence_urls"]:
                            agg[key]["evidence_urls"].append(u1)
                    vio = d.get("violation") or {}
                    u2 = vio.get("evidence_url")
                    if u2 and str(u2).strip() and str(u2) != "N/A":
                        if u2 not in agg[key]["evidence_urls"]:
                            agg[key]["evidence_urls"].append(u2)
                report_data["aggregated_violations"] = [
                    {
                        "student_id": k[2],
                        "student_name": k[0],
                        "student_roll_number": k[1],
                        "activity_type": k[3],
                        "severity": k[4],
                        "frequency": v["count"],
                        "evidence_urls": v["evidence_urls"],
                    }
                    for k, v in sorted(agg.items(), key=lambda x: (x[0][0], -x[1]["count"], x[0][3]))
                ]
                logger.info("generate_report_file_async: built %s aggregated violation groups (per student) for report_id=%s", len(report_data["aggregated_violations"]), report_id)
            logger.info("generate_report_file_async: built %s activities for report_id=%s", len(detailed_activities), report_id)
        else:
            report_data['violation_view'] = violation_view or "all"
            logger.info("generate_report_file_async: no activities, report_id=%s", report_id)
        
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
            orig_viol_evidence = violation.evidence_url or "N/A"
            viol_evidence_display = evidence_url_map.get(orig_viol_evidence, orig_viol_evidence) if orig_viol_evidence != "N/A" else "N/A"
            report_data['primary_violation'] = {
                'id': str(violation.violation_id),
                'type': violation.violation_type or 'Unknown',
                'severity': severity_from_int(violation.severity or 1),
                'status': violation.status or 'pending',
                'timestamp': violation.timestamp.strftime('%Y-%m-%d %H:%M:%S') if violation.timestamp else '',
                'evidence_url': viol_evidence_display
            }
        
        logger.info(
            "generate_report_file_async: report_data ready report_id=%s summary_keys=%s activities_len=%s",
            report_id, list(report_data.get('summary', {}).keys()), len(report_data.get('activities', [])),
        )
        
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
            logger.info("generate_report_file_async: unknown format %s, defaulting to JSON", format_type)
            success = generate_json_report(report_data, file_path)
        
        logger.info("generate_report_file_async: format generation finished report_id=%s success=%s", report_id, success)
        
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
                    logger.info("generate_report_file_async: report completed report_id=%s file=%s", report_id, actual_file.name)
                else:
                    logger.warning("generate_report_file_async: generated file not found report_id=%s base_name=%s checked=%s", report_id, base_name, possible_extensions)
                    report.status = "failed"
            else:
                logger.warning("generate_report_file_async: generation returned False report_id=%s", report_id)
                report.status = "failed"
            db.commit()
        else:
            logger.error("generate_report_file_async: report record not found report_id=%s", report_id)
        
    except Exception as e:
        logger.exception("generate_report_file_async failed: report_id=%s error=%s", report_id, e)
        # Update status to failed
        try:
            report = db.query(Report).filter(Report.report_id == report_id).first()
            if report:
                report.status = "failed"
                db.commit()
                logger.info("generate_report_file_async: marked report_id=%s as failed", report_id)
        except Exception as commit_err:
            logger.exception("generate_report_file_async: failed to update report status to failed: %s", commit_err)
    finally:
        db.close()
        logger.info("generate_report_file_async: done report_id=%s", report_id)


async def generate_invigilator_report_file_async(
    report_id: UUID,
    file_path: str,
    format_type: str,
):
    """Background task to generate invigilator report file (all invigilator activities)."""
    logger.info("generate_invigilator_report_file_async: start report_id=%s file_path=%s format=%s", report_id, file_path, format_type)
    db = SessionLocal()
    try:
        activities = (
            db.query(InvigilatorActivity)
            .order_by(InvigilatorActivity.timestamp.desc())
            .all()
        )
        detailed = []
        for act in activities:
            inv = db.query(Invigilator).filter(Invigilator.invigilator_id == act.invigilator_id).first()
            room = db.query(Room).filter(Room.room_id == act.room_id).first()
            room_display = room.room_number if room else "N/A"
            detailed.append({
                'activity_id': str(act.activity_id),
                'invigilator_name': inv.name if inv else 'N/A',
                'room_name': room_display,
                'timestamp': act.timestamp.strftime('%Y-%m-%d %H:%M:%S') if act.timestamp else '',
                'activity_type': act.activity_type or 'N/A',
                'notes': act.notes or '',
            })
        report_data = {
            'title': 'Invigilator Report',
            'generated_at': datetime.utcnow().isoformat(),
            'report_type': 'invigilator',
            'activities': detailed,
            'summary': {'total_activities': len(detailed)},
        }
        success = False
        if format_type.lower() == 'json':
            success = generate_json_report(report_data, file_path)
        elif format_type.lower() == 'csv':
            success = generate_csv_report(report_data, file_path)
        elif format_type.lower() == 'pdf':
            success = generate_pdf_report(report_data, file_path)
        else:
            success = generate_json_report(report_data, file_path)
        report = db.query(Report).filter(Report.report_id == report_id).first()
        if report:
            if success:
                report.status = "completed"
                base_name = Path(file_path).stem
                for ext in ['.pdf', '.txt', '.csv', '.json']:
                    test_file = REPORTS_DIR / f"{base_name}{ext}"
                    if test_file.exists():
                        report.file_path = f"/reports/{test_file.name}"
                        break
            else:
                report.status = "failed"
            db.commit()
    except Exception as e:
        logger.exception("generate_invigilator_report_file_async failed: report_id=%s error=%s", report_id, e)
        try:
            r = db.query(Report).filter(Report.report_id == report_id).first()
            if r:
                r.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
        logger.info("generate_invigilator_report_file_async: done report_id=%s", report_id)


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
    
    logger.info("get_investigator_id_for_report: user_type=%s user_id=%s", user_type, user_id)
    
    if user_type == "investigator":
        try:
            investigator_id = UUID(user_id)
            # Verify the investigator exists
            investigator = db.query(Investigator).filter(Investigator.investigator_id == investigator_id).first()
            if not investigator:
                logger.warning("get_investigator_id_for_report: investigator %s not found, using default", investigator_id)
                # Fall through to create system investigator
            else:
                logger.info("get_investigator_id_for_report: using investigator_id=%s", investigator_id)
                return investigator_id
        except (ValueError, TypeError) as e:
            logger.warning("get_investigator_id_for_report: invalid investigator ID %s: %s", user_id, e)
            # Fall through to create system investigator
    
    # For admins OR if investigator not found, use/create a system investigator
    default_investigator = db.query(Investigator).first()
    
    if default_investigator:
        logger.info("get_investigator_id_for_report: using default investigator_id=%s", default_investigator.investigator_id)
        return default_investigator.investigator_id
    else:
        # Create a system investigator if none exists
        logger.info("get_investigator_id_for_report: no investigators found, creating system investigator")
        from database.auth import hash_password
        
        # Check again to avoid race condition (in case another request created one)
        default_investigator = db.query(Investigator).filter(Investigator.email == "system@foresyte.edu").first()
        if default_investigator:
            logger.info("get_investigator_id_for_report: system investigator exists id=%s", default_investigator.investigator_id)
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
        logger.info("get_investigator_id_for_report: created system investigator id=%s", system_investigator.investigator_id)
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
    name: Optional[str] = None  # User-defined display name
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
    name: Optional[str] = None  # Rename report
    report_type: Optional[str] = None
    file_path: Optional[str] = None
    violation_id: Optional[UUID] = None
    generated_by: Optional[UUID] = None
    status: Optional[str] = None  # completed, generating, failed


class ReportRenameRequest(BaseModel):
    name: str  # New display name for the report


class IncidentReportRequest(BaseModel):
    incident_ids: List[str]
    format: str  # pdf, csv, json
    include_video_links: bool
    violation_view: Optional[str] = "all"  # "all" = every violation row; "summary" = per-student rows (student, type, severity, frequency + evidence links)


class ExamReportRequest(BaseModel):
    format: str  # pdf, csv, json
    include_statistics: bool
    violation_view: Optional[str] = "all"  # "all" | "summary"


class StudentReportRequest(BaseModel):
    format: str  # pdf, csv, json
    include_statistics: Optional[bool] = True
    violation_view: Optional[str] = "all"  # "all" | "summary"


class InvigilatorReportRequest(BaseModel):
    format: str  # pdf, csv, json
    include_statistics: Optional[bool] = True


class ReportListItem(BaseModel):
    """Report row for list endpoint: includes generated_by_email for display."""
    report_id: UUID
    name: Optional[str] = None
    report_type: str
    generated_date: date
    file_path: str
    violation_id: Optional[UUID] = None
    generated_by: UUID
    generated_by_email: Optional[str] = None
    status: str = "generating"

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: List[ReportListItem]
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
    logger.info("generate_incident_report: request incident_ids=%s format=%s", request.incident_ids, request.format)
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
        except ValueError as e:
            logger.warning("generate_incident_report: invalid incident_id=%s %s", incident_id, e)
            continue

    if not activities:
        logger.warning("generate_incident_report: no valid incidents found for ids=%s", request.incident_ids)
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
    
    initial_name = f"Incident Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    new_report = Report(
        name=initial_name,
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
    logger.info(
        "generate_incident_report: adding background task report_id=%s file_path=%s format=%s",
        new_report.report_id, file_path, request.format,
    )
    background_tasks.add_task(
        generate_report_file_async,
        report_id=new_report.report_id,
        report_type="incident",
        file_path=file_path,
        format_type=request.format,
        activities=activities,
        violation=violation,
        violation_view=getattr(request, "violation_view", None) or "all",
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
    logger.info("generate_exam_report: exam_id=%s format=%s", exam_id, request.format)
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    exam = db.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        logger.warning("generate_exam_report: exam not found exam_id=%s", exam_id)
        raise HTTPException(status_code=404, detail="Exam not found")

    # Generate report file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"exam_report_{exam_id}_{timestamp}.{request.format}"
    file_path = os.path.join("reports", filename)

    # Get violations/incidents for this exam
    activities = db.query(StudentActivity).filter(
        StudentActivity.exam_id == exam_id
    ).all()
    logger.info("generate_exam_report: exam_id=%s activities_count=%s", exam_id, len(activities))

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

    initial_name = f"Exam Report - {exam.course or 'Exam'} - {exam.exam_date.strftime('%Y-%m-%d') if exam.exam_date else 'N/A'}"
    new_report = Report(
        name=initial_name,
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
    logger.info(
        "generate_exam_report: adding background task report_id=%s file_path=%s format=%s violation_id=%s",
        new_report.report_id, file_path, request.format, new_report.violation_id,
    )
    background_tasks.add_task(
        generate_report_file_async,
        report_id=new_report.report_id,
        report_type="exam",
        file_path=file_path,
        format_type=request.format,
        activities=activities,
        exam=exam,
        violation=violation,
        violation_view=getattr(request, "violation_view", None) or "all",
    )

    return {
        "id": str(new_report.report_id),
        "file_path": file_path,
        "format": request.format,
        "status": "generating"
    }


# -------------------------
# Generate Invigilator Report
# -------------------------
@router.post("/invigilators", status_code=status.HTTP_201_CREATED)
def generate_invigilator_report(
    request: InvigilatorReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate a report of all invigilator activities."""
    logger.info("generate_invigilator_report: format=%s", request.format)
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"invigilator_report_{timestamp}.{request.format}"
    file_path = os.path.join("reports", filename)
    investigator_id = get_investigator_id_for_report(current_user, db)
    initial_name = f"Invigilator Report - {datetime.utcnow().strftime('%Y-%m-%d')}"
    new_report = Report(
        name=initial_name,
        report_type="invigilator",
        file_path=file_path,
        violation_id=None,
        generated_by=investigator_id,
        status="generating"
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    background_tasks.add_task(
        generate_invigilator_report_file_async,
        report_id=new_report.report_id,
        file_path=file_path,
        format_type=request.format,
    )
    return {
        "id": str(new_report.report_id),
        "file_path": file_path,
        "format": request.format,
        "status": "generating"
    }


# -------------------------
# Generate Student Violations Report (one student, all exams)
# -------------------------
@router.post("/students/{student_id}")
def generate_student_report(
    student_id: UUID,
    request: StudentReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a report for a single student showing their violations across all exams.
    """
    logger.info("generate_student_report: student_id=%s format=%s", student_id, request.format)
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        logger.warning("generate_student_report: student not found student_id=%s", student_id)
        raise HTTPException(status_code=404, detail="Student not found")

    # All activities (violations/incidents) for this student, any exam, newest first
    activities = (
        db.query(StudentActivity)
        .filter(StudentActivity.student_id == student_id)
        .order_by(StudentActivity.timestamp.desc())
        .all()
    )
    logger.info("generate_student_report: student_id=%s activities_count=%s", student_id, len(activities))

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"student_report_{student_id}_{timestamp}.{request.format}"
    file_path = os.path.join("reports", filename)

    violation = None
    if activities:
        violation = db.query(Violation).filter(
            Violation.activity_id == activities[0].activity_id
        ).first()
    if not violation and activities:
        violation = Violation(
            activity_id=activities[0].activity_id,
            violation_type="Student Report",
            severity=1,
            status="pending"
        )
        db.add(violation)
        db.commit()
        db.refresh(violation)

    investigator_id = get_investigator_id_for_report(current_user, db)
    initial_name = f"Student Report - {student.name or 'Student'} ({student.roll_number or student_id}) - Violations across exams"
    new_report = Report(
        name=initial_name,
        report_type="student",
        file_path=file_path,
        violation_id=violation.violation_id if violation else None,
        generated_by=investigator_id,
        status="generating"
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    logger.info(
        "generate_student_report: adding background task report_id=%s student_id=%s format=%s",
        new_report.report_id, student_id, request.format,
    )
    background_tasks.add_task(
        generate_report_file_async,
        report_id=new_report.report_id,
        report_type="student",
        file_path=file_path,
        format_type=request.format,
        activities=activities,
        exam=None,
        violation=violation,
        violation_view=getattr(request, "violation_view", None) or "all",
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
    Returns generated_by_email for display (By: email).
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(Report)
    total = query.count()

    offset = (page - 1) * limit
    reports = query.order_by(Report.generated_date.desc()).offset(offset).limit(limit).all()

    items = []
    for report in reports:
        investigator = db.query(Investigator).filter(Investigator.investigator_id == report.generated_by).first()
        generated_by_email = investigator.email if investigator else None
        items.append(ReportListItem(
            report_id=report.report_id,
            name=report.name,
            report_type=report.report_type,
            generated_date=report.generated_date,
            file_path=report.file_path or "",
            violation_id=report.violation_id,
            generated_by=report.generated_by,
            generated_by_email=generated_by_email,
            status=report.status or "generating",
        ))

    return ReportListResponse(reports=items, total=total)


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


# RENAME Report (Admin + Investigator)
@router.patch("/{report_id}/name", response_model=ReportRead)
def rename_report(
    report_id: UUID,
    body: ReportRenameRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Rename a report. The new name is stored in the database.
    Admins and Investigators can rename reports.
    """
    if current_user.get("user_type") not in ["admin", "investigator"]:
        raise HTTPException(status_code=403, detail="Access denied")

    report = db.query(Report).filter(Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    new_name = (body.name or "").strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Report name cannot be empty")

    report.name = new_name
    db.commit()
    db.refresh(report)
    logger.info("rename_report: report_id=%s new_name=%s", report_id, new_name)
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
