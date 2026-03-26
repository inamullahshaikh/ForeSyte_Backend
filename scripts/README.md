# Database Scripts

This directory contains utility scripts for database management operations.

## Available Scripts

### `create_invigilators.py`

Creates or updates the required invigilator accounts for the invigilator portal.

**Creates these accounts:**
- Ms. Saira Qamar (`saira.qamar@invigilator.foresyte.local`)
- Mr. Inam Ullah Shaikh (`inam.shaikh@invigilator.foresyte.local`)
- Ms. Aden Sial (`aden.sial@invigilator.foresyte.local`)
- Ms. Emaan Fatima (`emaan.fatima@invigilator.foresyte.local`)

**Usage:**
```bash
python scripts/create_invigilators.py
python scripts/create_invigilators.py --password "StrongPassword123!"
```

**Default password:**
- `Invigilator@123` (or `DEFAULT_INVIGILATOR_PASSWORD` from environment)

---

### `delete_all_students.py`

Deletes all students from the database along with their related records.

**⚠️ WARNING: This script permanently deletes data. Always backup your database before running!**

**What it does:**
- Deletes all student records
- Removes student activities
- Deletes violations linked to student activities
- Deletes reports linked to student violations
- Removes student assignments from seats (sets student_id to NULL)

**Usage:**

```bash
# Interactive mode (will ask for confirmation)
python scripts/delete_all_students.py

# Non-interactive mode (skip confirmation - useful for automation)
python scripts/delete_all_students.py --yes

# Show help
python scripts/delete_all_students.py --help
```

**Requirements:**
- Database connection configured in `.env` file
- All required Python packages from `requirements.txt` installed

**Example Output:**
```
============================================================
STUDENT DELETION SUMMARY
============================================================
Total students to delete: 150

Related records that will be affected:
  - Seat assignments: 45 (student_id will be set to NULL)
  - Student activities: 230
  - Violations: 15
  - Reports: 5
============================================================

Are you sure you want to delete ALL 150 students? (yes/no):
```

## Running Scripts

Make sure you're in the `ForeSyte_Backend` directory when running scripts:

```bash
cd ForeSyte_Backend
python scripts/delete_all_students.py
```

Or use the full path from the project root:

```bash
python ForeSyte_Backend/scripts/delete_all_students.py
```

---

### `import_students_from_pdf.py`

Imports students from a seating plan PDF file into the database.

**Features:**
- Extracts student information (roll number, name, seat number) from PDF tables
- Generates email addresses automatically based on roll number pattern
- Follows the Student model schema from the database
- Handles duplicates (can skip or update existing students)
- Provides detailed progress reporting and error handling

**Email Pattern:**
- Roll number format: `XXY-AAAA` (e.g., `22I-0857`)
- Email format: `YXXAAAA@nu.edu.pk` (e.g., `i220857@nu.edu.pk`)
  - `Y` = letter from roll number (lowercased)
  - `XX` = first 2 digits from roll number
  - `AAAA` = last 4 digits from roll number
  - No prefix needed - starts with the lowercase letter

**Usage:**

```bash
# Import from default PDF location (scripts/seating_plan.pdf)
python scripts/import_students_from_pdf.py

# Import from specific PDF file
python scripts/import_students_from_pdf.py --pdf path/to/seating_plan.pdf

# Import with custom password
python scripts/import_students_from_pdf.py --password MyPassword123

# Update existing students instead of skipping them
python scripts/import_students_from_pdf.py --update-existing

# Show help
python scripts/import_students_from_pdf.py --help
```

**Arguments:**
- `--pdf, -p`: Path to the seating plan PDF file (default: `scripts/seating_plan.pdf`)
- `--password`: Default password for students (default: `Student@123`)
- `--update-existing`: Update existing students instead of skipping them

**Requirements:**
- Database connection configured in `.env` file
- `pdfplumber` library installed (included in requirements.txt)
- PDF file must contain a table with columns: Roll No, Name, Seat No

**Example Output:**
```
============================================================
PARSING PDF FILE
============================================================
Reading PDF file: scripts/seating_plan.pdf
PDF has 1 page(s)
Processing page 1...
  Found table 1 with 34 rows
Parsed 33 students from PDF

Sample of parsed data:
  1. Roll: 22I-0839, Name: Muhammad Talha, Email: i220839@nu.edu.pk
  2. Roll: 22I-0842, Name: Shah Abdullah, Email: i220842@nu.edu.pk
  3. Roll: 22I-0857, Name: Inam Ullah, Email: i220857@nu.edu.pk
  ... and 30 more

============================================================
IMPORTING TO DATABASE
============================================================
[1/33] Created: Muhammad Talha (22I-0839) - yi220839@nu.edu.pk
[2/33] Created: Shah Abdullah (22I-0842) - yi220842@nu.edu.pk
...

============================================================
IMPORT SUMMARY
============================================================
Total students parsed: 33
Successfully created: 33
Skipped (already exist): 0
Errors: 0
============================================================
```

**Note:** The script automatically:
- Generates unique email addresses based on roll numbers
- Hashes passwords securely
- Handles database constraint violations gracefully
- Skips students that already exist (by roll number or email)

---

### `add_dummy_data.py`

Populates the database with comprehensive dummy data for all tables. Useful for testing and development.

**Features:**
- Creates dummy data for all user types (Admin, Invigilator, Investigator, Student)
- Populates all related tables respecting foreign key constraints
- Generates realistic relationships between entities
- Handles database constraints gracefully
- Provides detailed progress reporting

**What it creates:**
- **Users:**
  - 5 Admins
  - 5 Invigilators
  - 5 Investigators
  - 15 Students (3x admins count)
  
- **Exams:** 10 exams with various courses and dates
  
- **Rooms:** 2 rooms per exam with cameras and streams
  
- **Seats:** Seat assignments linking students to rooms
  
- **Activities:**
  - 50 Student activities (incidents)
  - 30 Invigilator activities
  
- **Violations:** 20 violations linked to student activities
  
- **Reports:** 10 reports generated by investigators
  
- **Notifications:** 100+ notifications across all user types
  
- **Video Streams:** 20 video streams with processing status
  
- **Processing Jobs:** 15 processing jobs linked to streams
  
- **Frame Logs:** 50 frame logs from processing jobs

**Usage:**

```bash
# Interactive mode (will ask for confirmation)
python scripts/add_dummy_data.py
```

**Requirements:**
- Database connection configured in `.env` file
- All required Python packages from `requirements.txt` installed

**Default Password:**
All created users will have the default password: `Password123!`

**Important Notes:**
- The script respects foreign key constraints by creating data in the correct order
- If users already exist, it will skip duplicates and continue
- All passwords are securely hashed using bcrypt
- The script creates a realistic interconnected dataset for testing

**Example Output:**
```
============================================================
DUMMY DATA GENERATION SCRIPT
============================================================

This script will populate the database with sample data.
All users will have the default password: Password123!

Warning: This will add data to your database.

Do you want to continue? (yes/no): yes

=== Adding Dummy Users ===
Creating 5 admins...
  ✓ Created admin: Ahmed Khan (admin1_ahmed@admin.nu.edu.pk)
  ...

=== Adding Dummy Exams ===
  ✓ Created exam: Calculus I on 2024-12-15
  ...

=== Adding Dummy Rooms ===
  ✓ Created room: A 101 for Calculus I
  ...

✅ DUMMY DATA GENERATION COMPLETED SUCCESSFULLY!
============================================================

Summary:
  - Admins: 5
  - Invigilators: 5
  - Investigators: 5
  - Students: 15
  - Exams: 10
  - Rooms: 20
  - Student Activities: 50
  - Violations: 20

Default password for all users: Password123!
```

**Database Table Order (respects foreign keys):**
1. Users (Admin, Invigilator, Investigator, Student) - no dependencies
2. Exams - no dependencies
3. Rooms - depends on Exams
4. Seats - depends on Rooms and Students
5. StudentActivities - depends on Students and Exams
6. InvigilatorActivities - depends on Invigilators and Rooms
7. Violations - depends on StudentActivities
8. Reports - depends on Violations and Investigators
9. Notifications - depends on all Users
10. VideoStreams - depends on Rooms and Exams
11. ProcessingJobs - depends on VideoStreams
12. FrameLogs - depends on ProcessingJobs
