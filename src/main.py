from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
from pathlib import Path
from database.api.admins import router as admin_router
from database.api.invigilators import router as invigilator_router
from database.api.investigators import router as investigator_router
from database.api.students import router as student_router
from database.api.exams import router as exam_router
from database.api.rooms import router as room_router
from database.api.seats import router as seat_router
from database.api.student_activities import router as student_activity_router
from database.api.invigilator_activities import router as invigilator_activity_router
from database.api.violations import router as violation_router
from database.api.reports import router as report_router
from database.api.dashboard import router as dashboard_router
from database.api.incidents import router as incidents_router
from database.api.monitoring import router as monitoring_router
from database.api.users import router as users_router
from database.api.seating_plans import router as seating_plans_router
from database.api.notifications import router as notifications_router
from database.auth import router as auth_router
from app.seating_plan.upload_plan import router as upload_plan_router
from database.api.video_streams import router as video_stream_router
# -------------------------
# FastAPI App
# -------------------------
app = FastAPI(
    title="ForeSyte API",
    description="Exam monitoring and management system",
    version="1.0.0"
)
load_dotenv()

# -------------------------
# Static Files (for serving videos and frames to frontend)
# -------------------------
# Create uploads directory if it doesn't exist
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Mount static files for frontend access
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# -------------------------
# CORS Middleware
# -------------------------
app.add_middleware(
    CORSMiddleware,
   
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_headers=["*"],
)


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "supersecret_session_key"),  # change to strong random key
)

# -------------------------
# Include Routers
# -------------------------
app.include_router(admin_router)
app.include_router(invigilator_router)
app.include_router(investigator_router)
app.include_router(student_router)
app.include_router(exam_router)
app.include_router(room_router)
app.include_router(seat_router)
app.include_router(student_activity_router)
app.include_router(invigilator_activity_router)
app.include_router(violation_router)
app.include_router(report_router)
app.include_router(dashboard_router)
app.include_router(incidents_router)
app.include_router(monitoring_router)
app.include_router(users_router)
app.include_router(seating_plans_router)
app.include_router(notifications_router)
app.include_router(auth_router)
app.include_router(upload_plan_router)
app.include_router(video_stream_router)
# -------------------------
# Root Endpoint
# -------------------------
@app.get("/")
def root():
    return {"message": "Welcome to the ForeSyte API!"}

