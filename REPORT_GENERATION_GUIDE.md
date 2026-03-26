# Comprehensive Report Generation Guide

## Overview

The ForeSyte system now includes a comprehensive report generation system that creates detailed violation reports in multiple formats (PDF, CSV, JSON) with full async processing and download capabilities.

## Features

### ✅ Detailed Violation Reporting
- **Student Information**: Names, roll numbers, student IDs
- **Activity Details**: Type, timestamp, severity, confidence scores
- **Violation Tracking**: Violation types, severity levels, status
- **Evidence Links**: URLs to evidence files
- **Exam Context**: Full exam information including date, time, course

### ✅ Multiple Export Formats

#### 1. PDF Reports
- Professional layout with branded colors (#6e5ae6)
- Executive summary with key metrics
- Severity breakdown (low, medium, high, critical)
- Detailed violation table with all information
- Supports up to 100 violations per report
- Proper pagination and formatting

#### 2. CSV Reports
- Spreadsheet-compatible format
- All violation details in columns:
  - Activity_ID, Student_Name, Roll_Number
  - Activity_Type, Timestamp, Severity
  - Confidence, Evidence_URL
  - Violation_ID, Violation_Type, Violation_Severity, Violation_Status
  - Exam_Name, Exam_Date
- Perfect for data analysis and Excel import

#### 3. JSON Reports
- Structured data format
- Complete hierarchy:
  ```json
  {
    "report_metadata": {...},
    "summary": {...},
    "exam_information": {...},
    "activities_and_violations": [...],
    "primary_violation": {...}
  }
  ```
- Ideal for programmatic access and integrations

### ✅ Asynchronous Processing
- Reports generate in the background
- Status tracking: `generating` → `completed` or `failed`
- Frontend polls for status updates every 3 seconds
- No blocking of API requests

### ✅ Download & View Functionality
- **View Button**: Opens report in new browser tab
- **Download Button**: Downloads with proper filename
- **Status Checking**: Only works for completed reports
- **Error Handling**: Clear user feedback for all states

## API Endpoints

### Generate Exam Report
```http
POST /reports/exams/{exam_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "format": "pdf",  // or "csv", "json"
  "include_statistics": true,
  "include_video_links": true
}
```

**Response:**
```json
{
  "id": "report-uuid",
  "file_path": "/reports/exam_report_xxx.pdf",
  "format": "pdf",
  "status": "generating"
}
```

### Download Report
```http
GET /reports/{report_id}/download
Authorization: Bearer <token>
```

**Response:** Binary file with proper MIME type

### Get Report Status
```http
GET /reports/
Authorization: Bearer <token>
```

Returns list of all reports with current status.

## Database Schema

### Report Status Column
```sql
ALTER TABLE reports ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'generating';
```

**Possible values:**
- `generating`: Report is being created
- `completed`: Report is ready for download
- `failed`: Report generation failed

### Violation Information
All reports now pull complete violation data including:
- Violation type
- Severity (1-4: low, medium, high, critical)
- Status (pending, under_review, resolved)
- Linked student activities

## Usage Instructions

### 1. Add Violations to Exam
```bash
cd Foresyte-backend/ForeSyte_Backend
python scripts/add_exam_violations.py
```

This will:
- Find exams in your database
- Create student activities (incidents)
- Generate violations linked to activities
- Provide a summary of created data

### 2. Test Report Generation
```bash
python scripts/test_report_generation.py
```

This will:
- List exams with violations
- Generate test reports in all formats
- Verify file creation
- Display file sizes and paths

### 3. Generate Reports via API

**Frontend (ReportsPage.tsx):**
- Click "Generate Report" button
- Select exam from dropdown
- Choose format (PDF, CSV, JSON)
- Wait for status to change to "completed"
- Click view (eye icon) or download icon

**Backend Processing:**
1. API receives request
2. Creates report record with status="generating"
3. Starts background task
4. Background task:
   - Queries all violations for exam
   - Gathers student information
   - Counts severities
   - Generates file in requested format
   - Updates status to "completed"
5. Frontend polling detects status change
6. User can now view/download

### 4. View and Download Reports

**View Report:**
- Opens in new browser tab
- Uses `/reports/{id}/download` endpoint
- Displays PDF in browser or downloads CSV/JSON

**Download Report:**
- Downloads file with proper filename
- Extracts name from Content-Disposition header
- Saves to user's Downloads folder

## File Locations

Reports are stored in:
```
Foresyte-backend/ForeSyte_Backend/src/uploads/reports/
```

Naming convention:
- Exam reports: `exam_report_{exam_id}_{timestamp}.{format}`
- Incident reports: `incident_report_{timestamp}.{format}`

## Troubleshooting

### Report Status Stuck on "Generating"

**Solution 1: Check backend logs**
```bash
# Look for errors in console output
```

**Solution 2: Run status fix script**
```bash
python scripts/fix_report_status.py
```

### PDF Generation Not Working

**Check reportlab installation:**
```bash
pip install reportlab==4.2.5
```

**Restart backend server after installing**

### No Violations in Reports

**Add violations to exam:**
```bash
python scripts/add_exam_violations.py
```

### Download Button Not Working

**Check:**
1. Report status is "completed"
2. File exists in `uploads/reports/`
3. Backend endpoint `/reports/{id}/download` is accessible
4. Frontend has proper authentication token

## Report Content Details

### Executive Summary Includes:
- Total activities detected
- Total violations
- Unique students flagged
- Exam name and date
- Severity breakdown (low/medium/high/critical counts)

### Detailed Violation Table Includes:
- Student name and roll number
- Activity type (Looking Away, Device Detected, etc.)
- Exact timestamp
- Severity level
- Confidence score
- Violation type
- Violation status
- Evidence URL

### Example Violations:
- **Looking Away**: Low severity, distraction
- **Device Detected**: High severity, unauthorized device
- **Cheating Attempt**: Critical severity, academic dishonesty
- **Talking to Neighbor**: Medium severity, communication
- **Multiple Faces**: High severity, impersonation risk

## Performance Considerations

- Reports limited to 100 violations in PDF (for readability)
- CSV and JSON include all violations
- Background processing prevents API timeouts
- File size typically:
  - PDF: 50-200 KB for 50-100 violations
  - CSV: 10-50 KB
  - JSON: 20-100 KB

## Security

- All endpoints require authentication
- Only admin and investigator users can generate reports
- Report files are protected by backend authentication
- Download endpoint validates user permissions

## Future Enhancements

Potential additions:
- [ ] Email reports to stakeholders
- [ ] Scheduled report generation
- [ ] Report templates customization
- [ ] Bulk report generation
- [ ] Report archiving and retention
- [ ] Advanced filtering options
- [ ] Custom report layouts

## Support

For issues or questions:
1. Check backend logs
2. Run test script: `python scripts/test_report_generation.py`
3. Verify database has violations
4. Check file permissions in `uploads/reports/`
5. Restart backend after changes

## Summary

The report generation system now provides:
✅ Comprehensive violation data
✅ Professional PDF reports
✅ CSV exports for analysis
✅ JSON for integrations
✅ Async processing with status tracking
✅ View and download functionality
✅ Error handling and user feedback

All features are production-ready and fully tested.
