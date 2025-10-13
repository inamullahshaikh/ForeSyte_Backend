from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
import os

from database.db import get_db
from database.models import Admin, Invigilator, Investigator, Student

router = APIRouter(prefix="/auth", tags=["Auth"])

# -------------------------
# Config
# -------------------------
SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# Utilities
# -------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: str, user_type: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"id": user_id, "user_type": user_type, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# -------------------------
# Get current user
# -------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        user_type: str = payload.get("user_type")
        if not user_id or not user_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        model_map = {
            "admin": Admin,
            "investigator": Investigator,
            "invigilator": Invigilator,
            "student": Student,
        }
        user_model = model_map.get(user_type)
        if not user_model:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user type")

        user = db.query(user_model).filter(user_model.__table__.columns[0] == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return {"user_type": user_type, "id": user_id, "user": user}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

# -------------------------
# Request & Response Schemas
# -------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None  # password required for all except maybe some students


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    id: str


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = None
    user_type = None
    user_id = None

    # Check Admin
    admin = db.query(Admin).filter(Admin.email == credentials.email).first()
    if admin and verify_password(credentials.password, admin.password_hash):
        user, user_type, user_id = admin, "admin", str(admin.admin_id)

    # Check Investigator
    if not user:
        investigator = db.query(Investigator).filter(Investigator.email == credentials.email).first()
        if investigator and hasattr(investigator, "password_hash") and verify_password(credentials.password, investigator.password_hash):
            user, user_type, user_id = investigator, "investigator", str(investigator.investigator_id)

    # Check Invigilator
    if not user:
        invigilator = db.query(Invigilator).filter(Invigilator.email == credentials.email).first()
        if invigilator and hasattr(invigilator, "password_hash") and verify_password(credentials.password, invigilator.password_hash):
            user, user_type, user_id = invigilator, "invigilator", str(invigilator.invigilator_id)

    # Check Student (password)
    if not user:
        student = db.query(Student).filter(Student.email == credentials.email).first()
        if student and student.password_hash and verify_password(credentials.password, student.password_hash):
            user, user_type, user_id = student, "student", str(student.student_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Generate JWT using your function
    access_token = create_access_token(
        user_id=user_id,
        user_type=user_type,
        expires_delta=timedelta(hours=1)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": user_type,
        "id": user_id
    }