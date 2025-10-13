from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# -------------------------
# Import Routers
# -------------------------
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
from database.auth import router as auth_router
from app.seating_plan.upload_plan import router as upload_plan_router
# -------------------------
# FastAPI App
# -------------------------
app = FastAPI(
    title="ForeSyte API",
    description="Exam monitoring and management system",
    version="1.0.0"
)

# -------------------------
# CORS Middleware
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(auth_router)
app.include_router(upload_plan_router)
# -------------------------
# Root Endpoint
# -------------------------
@app.get("/")
def root():
    return {"message": "Welcome to the ForeSyte API!"}

