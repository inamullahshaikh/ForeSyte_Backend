from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import os
import re

from database.db import get_db
from database.models import Admin, Invigilator, Investigator, Student

# -------------------------
# Initialization
# -------------------------
router = APIRouter(prefix="/auth", tags=["Auth"])
load_dotenv()
FRONTEND_URL = "http://localhost:5173"

# OAuth Setup
oauth = OAuth()
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# -------------------------
# Config
# -------------------------
SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# Schemas
# -------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = None


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str  # admin | invigilator | investigator | student


class RoleRegisterRequest(BaseModel):
    email: str
    name: str
    role: str  # admin, invigilator, investigator


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    user_id: str


# -------------------------
# Utility Functions
# -------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, user_type: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT with consistent naming: 'user_id' and 'user_type'
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"user_id": user_id, "user_type": user_type, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -------------------------
# Get Current User
# -------------------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
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

        primary_key = list(user_model.__table__.primary_key.columns)[0]
        user = db.query(user_model).filter(primary_key == user_id).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return {"user_type": user_type, "user_id": user_id, "user": user}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


# -------------------------
# Login
# -------------------------
@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = None
    user_type = None
    user_id = None

    # Admin
    admin = db.query(Admin).filter(Admin.email == credentials.email).first()
    if admin and verify_password(credentials.password, admin.password_hash):
        user, user_type, user_id = admin, "admin", str(admin.admin_id)

    # Investigator
    if not user:
        investigator = db.query(Investigator).filter(Investigator.email == credentials.email).first()
        if investigator and hasattr(investigator, "password_hash") and verify_password(credentials.password, investigator.password_hash):
            user, user_type, user_id = investigator, "investigator", str(investigator.investigator_id)

    # Invigilator
    if not user:
        invigilator = db.query(Invigilator).filter(Invigilator.email == credentials.email).first()
        if invigilator and hasattr(invigilator, "password_hash") and verify_password(credentials.password, invigilator.password_hash):
            user, user_type, user_id = invigilator, "invigilator", str(invigilator.invigilator_id)

    # Student
    if not user:
        student = db.query(Student).filter(Student.email == credentials.email).first()
        if student and student.password_hash and verify_password(credentials.password, student.password_hash):
            user, user_type, user_id = student, "student", str(student.student_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(user_id=user_id, user_type=user_type, expires_delta=timedelta(hours=1))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": user_type,
        "user_id": user_id
    }


# -------------------------
# Signup
# -------------------------
@router.post("/signup", response_model=TokenResponse)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    role = data.role.lower().strip()
    email = data.email
    name = data.name
    password = data.password

    # Check existing user
    existing_user = (
        db.query(Admin).filter(Admin.email == email).first()
        or db.query(Invigilator).filter(Invigilator.email == email).first()
        or db.query(Investigator).filter(Investigator.email == email).first()
        or db.query(Student).filter(Student.email == email).first()
    )
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # Validate role
    if role not in ["admin", "invigilator", "investigator", "student"]:
        raise HTTPException(status_code=400, detail="Invalid role provided.")

    hashed_password = hash_password(password)

    if role == "admin":
        user = Admin(email=email, name=name, password_hash=hashed_password, created_at=datetime.utcnow())
    elif role == "invigilator":
        user = Invigilator(email=email, name=name, password_hash=hashed_password, created_at=datetime.utcnow())
    elif role == "investigator":
        user = Investigator(email=email, name=name, password_hash=hashed_password, created_at=datetime.utcnow())
    else:
        user = Student(email=email, name=name, password_hash=hashed_password, created_at=datetime.utcnow())

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = str(getattr(user, f"{role}_id"))
    access_token = create_access_token(user_id=user_id, user_type=role)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": role,
        "user_id": user_id
    }


# -------------------------
# Google OAuth
# -------------------------
@router.get("/google")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    token = await google.authorize_access_token(request)
    user_info = token.get("userinfo")

    if not user_info:
        raise HTTPException(status_code=400, detail="Google login failed")

    email = user_info["email"]
    name = user_info.get("name")

    # Restrict access
    if not (email.endswith("@nu.edu.pk") or email.endswith("@gmail.com")):
        raise HTTPException(status_code=403, detail="Access restricted to NU or Gmail accounts.")

    is_student_email = bool(re.match(r"i\d{2}\w{4}@(?:nu\.edu\.pk|isb\.nu\.edu\.pk)$", email, re.IGNORECASE))

    student = db.query(Student).filter(Student.email == email).first()
    admin = db.query(Admin).filter(Admin.email == email).first()
    investigator = db.query(Investigator).filter(Investigator.email == email).first()
    invigilator = db.query(Invigilator).filter(Invigilator.email == email).first()

    user = admin or investigator or invigilator or student
    user_type, user_id = None, None

    if user:
        if admin:
            user_type, user_id = "admin", str(admin.admin_id)
        elif investigator:
            user_type, user_id = "investigator", str(investigator.investigator_id)
        elif invigilator:
            user_type, user_id = "invigilator", str(invigilator.invigilator_id)
        else:
            user_type, user_id = "student", str(student.student_id)
    else:
        if is_student_email:
            new_student = Student(email=email, name=name, created_at=datetime.utcnow())
            db.add(new_student)
            db.commit()
            db.refresh(new_student)
            user_type = "student"
            user_id = str(new_student.student_id)
        else:
            select_role_url = f"{FRONTEND_URL}/select-role?email={email}&name={name}"
            return RedirectResponse(url=select_role_url)
    print(f"User Type: {user_type}, User ID: {user_id}")
    access_token = create_access_token(user_id=user_id, user_type=user_type)
    frontend_url = f"{FRONTEND_URL}/login-success?token={access_token}&user_type={user_type}&user_id={user_id}"

    return RedirectResponse(url=frontend_url)


# -------------------------
# Register Role (for non-student users)
# -------------------------
@router.post("/register-role", response_model=TokenResponse)
def register_role(data: RoleRegisterRequest, db: Session = Depends(get_db)):
    role = data.role.lower()
    email = data.email
    name = data.name

    existing = (
        db.query(Admin).filter(Admin.email == email).first()
        or db.query(Invigilator).filter(Invigilator.email == email).first()
        or db.query(Investigator).filter(Investigator.email == email).first()
        or db.query(Student).filter(Student.email == email).first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User already registered.")

    if role == "admin":
        user = Admin(email=email, name=name, created_at=datetime.utcnow())
    elif role == "invigilator":
        user = Invigilator(email=email, name=name, created_at=datetime.utcnow())
    elif role == "investigator":
        user = Investigator(email=email, name=name, created_at=datetime.utcnow())
    else:
        raise HTTPException(status_code=400, detail="Invalid role selected.")

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = str(getattr(user, f"{role}_id"))
    access_token = create_access_token(user_id=user_id, user_type=role)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_type": role,
        "user_id": user_id
    }
