# ForeSyte Investigator Portal

## Overview

The Investigator Portal is a comprehensive interface for discipline committee members and investigators to review, manage, and take action on violations detected by the ForeSyte AI Exam Surveillance System.

## Features Implemented

Based on the requirements from the thesis document, the following features have been fully implemented:

### 1. Dashboard (UC-01: View & Manage Reports/Dashboard)
- **Real-time Statistics**: Display of key metrics including total violations, pending reviews, resolved cases, and active exams
- **Period Filters**: View data for Today, This Week, or This Month
- **Recent Activities**: Quick view of the latest violations and suspicious activities
- **Severity Indicators**: Color-coded badges for high, medium, and low severity violations
- **Status Tracking**: Visual indicators for pending, confirmed, and dismissed cases

### 2. Violations Management (UC-03: Generate Detection Reports & UC-06: Monitor Student Behaviour)
- **Comprehensive Filtering**:
  - Search by Student ID, Name, Seat Number, or Violation Type
  - Filter by Status (Pending, Confirmed, Dismissed)
  - Filter by Severity Level (High, Medium, Low)
  - Filter by Violation Type
- **Detailed Violation View**:
  - Student information (Name, ID, Seat, Room)
  - Violation details (Type, Timestamp, Severity, Status)
  - Evidence URLs for supporting materials
- **Action Capabilities** (FR-14, FR-30):
  - Confirm violations
  - Dismiss violations
  - View evidence (video snippets, screenshots)

### 3. Student Activities Monitoring (UC-06: Monitor Student Behaviour)
- **Activity Tracking**:
  - All detected student activities with timestamps
  - Activity types (Phone Usage, Looking Around, Hand Gestures, etc.)
  - Confidence scores from AI detection
  - Evidence links for each activity
- **Filtering Options**:
  - Search by student information
  - Filter by severity
  - Filter by activity type

### 4. Invigilator Activities Monitoring (UC-05: Monitor Invigilator Activity)
- **Invigilator Tracking** (FR-21, FR-22, FR-23, FR-24, FR-25):
  - Monitor invigilator presence
  - Detect prolonged absences
  - Identify unauthorized phone usage
  - Track idle periods
- **Activity Types**:
  - Entered Room
  - Walking Around
  - Absent from Zone
  - Phone Usage
  - Idle Period
- **Detailed Notes**: Each activity includes notes explaining the context

### 5. Reports Management (UC-01, UC-03: Generate Detection Reports)
- **Report Generation** (FR-11, FR-12, FR-15):
  - Create Incident Reports
  - Create Exam Reports
  - Multiple export formats (PDF, Excel, CSV)
  - Include video evidence links option
  - Date range selection
- **Report History**:
  - View all previously generated reports
  - Filter by report type
  - Search by exam name or author
  - Download reports
  - View report details (violation count, date, author)

### 6. Settings & Profile Management (UC-02: Manage User Profiles)
- **Profile Settings**:
  - Update name, email, designation
  - View Investigator ID
- **Password Management**:
  - Change password securely
  - Password strength validation
- **Notification Preferences**:
  - Email notifications toggle
  - Violation alerts
  - Report ready notifications
  - Weekly digest option

## Technical Implementation

### Components Structure
```
investigator-portal/
├── components/
│   ├── InvestigatorHeader.tsx    # Header with notifications and profile
│   └── InvestigatorSidebar.tsx   # Navigation sidebar
├── InvestigatorDashboard.tsx     # Main dashboard
├── ViolationsPage.tsx            # Violations management
├── StudentActivitiesPage.tsx     # Student activities monitoring
├── InvigilatorActivitiesPage.tsx # Invigilator activities monitoring
├── ReportsPage.tsx               # Reports generation and management
├── SettingsPage.tsx              # Profile and settings
└── routes.tsx                    # Route configuration
```

### API Integration
All pages are integrated with the backend API through `src/services/api.ts` with the following investigator-specific endpoints:

- `/violations` - Get, confirm, dismiss violations
- `/student-activities` - Fetch student activities
- `/invigilator-activities` - Fetch invigilator activities
- `/reports` - Generate and download reports
- `/investigators/me` - Get/update investigator profile

### Routing
The investigator portal is accessible at the following routes:
- `/investigator/dashboard` - Main dashboard
- `/investigator/violations` - Violations management
- `/investigator/student-activities` - Student activities
- `/investigator/invigilator-activities` - Invigilator activities
- `/investigator/reports` - Reports management
- `/investigator/settings` - Settings and profile

## Functional Requirements Coverage

### FR-01 to FR-05: Dashboard & Reports Access ✅
- Authorized login and access control
- Real-time and historical reports display
- Filtering by student ID, seat number, violation type, timestamp
- Export to PDF and Excel formats
- Role-based access enforcement

### FR-11 to FR-15: Report Generation ✅
- Automatic report generation on violation flagging
- Timestamps, seat numbers, and violation types included
- Database storage of reports
- Review and approval workflow
- Export functionality

### FR-26 to FR-30: Student Behavior Monitoring ✅
- Real-time activity analysis
- Detection of suspicious behaviors
- Differentiation between normal and abnormal behaviors
- Logging with seat ID, timestamp, and evidence
- Review and confirmation workflow

### FR-21 to FR-25: Invigilator Monitoring ✅
- Monitoring during exam sessions
- Presence tracking in defined zones
- Unauthorized activity detection
- Negligence event logging with timestamp and location
- Activity logs accessible to investigators

## Non-Functional Requirements Coverage

### Usability (USE-1, USE-2, USE-3) ✅
- Simple 3-click violation report generation
- Intuitive dashboard with clear navigation
- Tabular format with comprehensive filters

### Performance (PER-3) ✅
- Efficient data loading with pagination
- Quick filtering and search
- Optimized rendering for large datasets

### Security (SEC-1, SEC-2, SEC-3) ✅
- Protected routes requiring authentication
- Role-based access control (investigator role required)
- Session-based authentication with tokens

## User Workflow

1. **Login**: Investigator logs in via email or Google OAuth
2. **Dashboard**: View overview of violations and activities
3. **Review Violations**: Navigate to violations page, filter and search
4. **Take Action**: Confirm or dismiss violations with evidence review
5. **Generate Reports**: Create detailed reports with custom filters
6. **Export**: Download reports in preferred format
7. **Monitor Activities**: Track both student and invigilator activities
8. **Manage Profile**: Update personal information and preferences

## Future Enhancements

- Real-time WebSocket notifications for new violations
- Advanced analytics and trend visualization
- Bulk actions for violations
- Integration with university student database
- Mobile-responsive design improvements
- Video evidence preview directly in the interface

## Access & Permissions

The investigator portal enforces strict access control:
- Only users with `user_type: investigator` can access these pages
- All routes are protected with `ProtectedRoute` component
- JWT token validation on every API request
- Audit logs for all investigator actions

## Support

For technical issues or feature requests, contact the development team.

