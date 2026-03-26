import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Date, Time, DateTime, Text,
    ForeignKey, Float, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# -------------------------------
#  USER MODELS
# -------------------------------

class Admin(Base):
    __tablename__ = "admins"
    admin_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=True)
    # Status column - commented out until database migration is run
    # After running migration to add status column, uncomment the line below:
    # status = Column(String, default="active")  # active, suspended, inactive
    created_at = Column(DateTime, default=datetime.utcnow)


class Invigilator(Base):
    __tablename__ = "invigilators"
    invigilator_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    photo_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    password_hash = Column(String, nullable=True)
    # Status column - commented out until database migration is run
    # After running migration to add status column, uncomment the line below:
    # status = Column(String, default="active")  # active, suspended, inactive

    activities = relationship("InvigilatorActivity", back_populates="invigilator")


class Investigator(Base):
    __tablename__ = "investigators"
    investigator_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    designation = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    password_hash = Column(String, nullable=True)
    # Status column - commented out until database migration is run
    # After running migration to add status column, uncomment the line below:
    # status = Column(String, default="active")  # active, suspended, inactive


class Student(Base):
    __tablename__ = "students"
    student_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    roll_number = Column(String, unique=True)
    photo_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    password_hash = Column(String, nullable=True)
    # Status column - commented out until database migration is run
    # After running migration to add status column, uncomment the line below:
    # status = Column(String, default="active")  # active, suspended, inactive
    activities = relationship("StudentActivity", back_populates="student")
    seat_assignment = relationship("Seat", back_populates="student", uselist=False)


# -------------------------------
#  EXAM / ROOM / SEATING
# -------------------------------

class Exam(Base):
    __tablename__ = "exams"
    exam_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course = Column(String, nullable=False)
    exam_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    rooms = relationship("Room", back_populates="exam")
    activities = relationship("StudentActivity", back_populates="exam")


class Room(Base):
    __tablename__ = "rooms"
    room_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_number = Column(String, nullable=False)
    block = Column(String)
    total_seats = Column(Integer)
    camera_id = Column(String)
    stream_url = Column(Text)  # IP Webcam stream URL (e.g., http://192.168.1.100:8080/video.mjpeg)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.exam_id"))

    exam = relationship("Exam", back_populates="rooms")
    seats = relationship("Seat", back_populates="room")
    invigilator_activities = relationship("InvigilatorActivity", back_populates="room")


class Seat(Base):
    __tablename__ = "seats"
    seat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    seat_number = Column(String, nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.room_id"))
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"))

    room = relationship("Room", back_populates="seats")
    student = relationship("Student", back_populates="seat_assignment")


# -------------------------------
#  ACTIVITY / VIOLATION / REPORT
# -------------------------------

class StudentActivity(Base):
    __tablename__ = "student_activities"
    activity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.student_id"))
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.exam_id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    activity_type = Column(String)
    severity = Column(String)
    confidence = Column(Float)
    evidence_url = Column(Text)

    student = relationship("Student", back_populates="activities")
    exam = relationship("Exam", back_populates="activities")
    violation = relationship("Violation", back_populates="activity", uselist=False)


class InvigilatorActivity(Base):
    __tablename__ = "invigilator_activities"
    activity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invigilator_id = Column(UUID(as_uuid=True), ForeignKey("invigilators.invigilator_id"))
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.room_id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    activity_type = Column(String)
    notes = Column(Text)

    invigilator = relationship("Invigilator", back_populates="activities")
    room = relationship("Room", back_populates="invigilator_activities")


class Violation(Base):
    __tablename__ = "violations"
    violation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("student_activities.activity_id"))
    violation_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    severity = Column(Integer)
    status = Column(String, default="pending")
    evidence_url = Column(Text)

    activity = relationship("StudentActivity", back_populates="violation")
    report = relationship("Report", back_populates="violation", uselist=False)


class Report(Base):
    __tablename__ = "reports"
    report_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)  # User-defined display name (e.g. "Midterm CS101 - Room D302")
    report_type = Column(String)
    generated_date = Column(Date, default=datetime.utcnow)
    file_path = Column(Text)
    violation_id = Column(UUID(as_uuid=True), ForeignKey("violations.violation_id"), nullable=True)  # Reports can exist without violations
    generated_by = Column(UUID(as_uuid=True), ForeignKey("investigators.investigator_id"))
    status = Column(String, default="generating")  # generating, completed, failed

    violation = relationship("Violation", back_populates="report")
    investigator = relationship("Investigator")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    user_type = Column(String, nullable=False)  # admin, investigator, invigilator, student
    type = Column(String, nullable=False)  # incident, exam, system, etc.
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# -------------------------------
#  VIDEO PROCESSING MODELS
# -------------------------------

class VideoStream(Base):
    __tablename__ = "video_streams"
    stream_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.room_id"))
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.exam_id"))
    stream_type = Column(String, nullable=False)  # 'live' or 'recorded'
    source_url = Column(Text)  # Camera URL or file path
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    room = relationship("Room")
    exam = relationship("Exam")
    processing_jobs = relationship("ProcessingJob", back_populates="video_stream")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stream_id = Column(UUID(as_uuid=True), ForeignKey("video_streams.stream_id"))
    status = Column(String, default="queued")  # queued, processing, completed, failed
    progress = Column(Float, default=0.0)
    total_frames = Column(Integer)
    processed_frames = Column(Integer, default=0)
    detected_activities = Column(Integer, default=0)
    detected_violations = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    video_stream = relationship("VideoStream", back_populates="processing_jobs")
    frame_logs = relationship("FrameLog", back_populates="job")


class FrameLog(Base):
    __tablename__ = "frame_logs"
    frame_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("processing_jobs.job_id"))
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    detected_objects = Column(Text)  # JSON string of detected objects
    activity_detected = Column(String)
    confidence_score = Column(Float)
    frame_path = Column(Text)  # Path to saved frame image
    
    job = relationship("ProcessingJob", back_populates="frame_logs")
