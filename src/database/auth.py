from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from uuid import UUID
import os
import re
import logging
from database.db import get_db
from database.models import Admin, Invigilator, Investigator, Student
from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from starlette.responses import RedirectResponse
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class RoleRegisterRequest(BaseModel):
    email: str
    name: str
    role: str  # admin, invigilator, investigator

load_dotenv()
FRONTEND_URL = "http://localhost:5173"

oauth = OAuth()
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={
        200: {"description": "Success"},
        400: {"description": "Bad Request"},
        401: {"description": "Unauthorized"},
        404: {"description": "Not Found"},
    }
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
            "admin": (Admin, "admin_id"),
            "investigator": (Investigator, "investigator_id"),
            "invigilator": (Invigilator, "invigilator_id"),
            "student": (Student, "student_id"),
        }
        user_model_info = model_map.get(user_type)
        if not user_model_info:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user type")

        user_model, id_column = user_model_info
        # Use getattr to access the ID column dynamically
        user = db.query(user_model).filter(getattr(user_model, id_column) == UUID(user_id)).first()
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


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str  # student, admin, invigilator, investigator


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    id: str


class SignupResponse(BaseModel):
    access_token: str
    user_type: str
    id: str
    email: str
    name: str


@router.options("/signup")
async def signup_options(response: Response):
    """Handle preflight request for signup"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"message": "OK"}

@router.post("/signup", response_model=SignupResponse)
def signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    """
    User registration endpoint.
    Creates a new user account based on the selected role.
    """
    logger.info(f"Signup request received: email={user_data.email}, role={user_data.role}, name={user_data.name}")
    role = user_data.role.lower()
    email = user_data.email.lower()
    logger.info(f"Processing signup for email={email}, role={role}")
    
    # Validate role
    valid_roles = ["student", "admin", "invigilator", "investigator"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # Check if user already exists
    existing_admin = db.query(Admin).filter(Admin.email == email).first()
    existing_investigator = db.query(Investigator).filter(Investigator.email == email).first()
    existing_invigilator = db.query(Invigilator).filter(Invigilator.email == email).first()
    existing_student = db.query(Student).filter(Student.email == email).first()
    
    if existing_admin or existing_investigator or existing_invigilator or existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please login instead."
        )
    
    # Validate password
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Hash password
    password_hash = hash_password(user_data.password)
    
    # Create user based on role
    user = None
    user_id = None
    
    try:
        logger.info(f"Creating {role} user with email={email}")
        if role == "admin":
            # Admin model requires username, use email as username if not provided
            logger.info(f"Creating Admin user: email={email}, username={email}")
            user = Admin(
                email=email,
                username=email,  # Use email as username
                password_hash=password_hash,
                created_at=datetime.utcnow()
            )
            db.add(user)
            logger.info("Admin user added to session, committing...")
            db.commit()
            logger.info("Admin user committed, refreshing...")
            db.refresh(user)
            # Convert UUID to string properly
            user_id = str(user.admin_id) if user.admin_id else None
            logger.info(f"Admin user created successfully with ID: {user_id}")
            
        elif role == "invigilator":
            user = Invigilator(
                email=email,
                name=user_data.name,
                password_hash=password_hash,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            user_id = str(user.invigilator_id) if user.invigilator_id else None
            
        elif role == "investigator":
            user = Investigator(
                email=email,
                name=user_data.name,
                password_hash=password_hash,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            user_id = str(user.investigator_id) if user.investigator_id else None
            
        elif role == "student":
            user = Student(
                email=email,
                name=user_data.name,
                password_hash=password_hash,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            user_id = str(user.student_id) if user.student_id else None
        
        if not user_id:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user: User ID was not generated"
            )
        
        # Generate access token
        logger.info(f"Generating access token for user_id={user_id}, user_type={role}")
        access_token = create_access_token(
            user_id=user_id,
            user_type=role,
            expires_delta=timedelta(hours=1)
        )
        logger.info(f"Signup successful for email={email}, role={role}")
        
        return {
            "access_token": access_token,
            "user_type": role,
            "id": user_id,
            "email": email,
            "name": user_data.name
        }
        
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        logger.error(f"Database integrity error during signup: {error_msg}")
        
        # Check if it's a unique constraint violation
        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            if "email" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered. Please login instead."
                )
            elif "username" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken. Please use a different email."
                )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {error_msg}"
        )
        
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.error(f"Error during signup for {email} as {role}: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {error_msg}"
        )


@router.options("/login")
async def login_options(response: Response):
    """Handle preflight request for login"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"message": "OK"}

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = None
    user_type = None
    user_id = None

    # Check Admin
    admin = db.query(Admin).filter(Admin.email == credentials.email).first()
    if admin and admin.password_hash and verify_password(credentials.password, admin.password_hash):
        user, user_type, user_id = admin, "admin", str(admin.admin_id)

    # Check Investigator
    if not user:
        investigator = db.query(Investigator).filter(Investigator.email == credentials.email).first()
        if investigator and investigator.password_hash and verify_password(credentials.password, investigator.password_hash):
            user, user_type, user_id = investigator, "investigator", str(investigator.investigator_id)

    # Check Invigilator
    if not user:
        invigilator = db.query(Invigilator).filter(Invigilator.email == credentials.email).first()
        if invigilator and invigilator.password_hash and verify_password(credentials.password, invigilator.password_hash):
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

    # ✅ 1. Only allow NU domain emails
    if not (email.endswith("@nu.edu.pk") or email.endswith("@gmail.com")):
        raise HTTPException(
            status_code=403,
            detail="Access restricted to NU domain emails only.",
        )

    # ✅ 2. Detect student emails (like i22xxxx@nu.edu.pk)
    is_student_email = bool(re.match(r"i\d{2}\w{4}@(?:nu\.edu\.pk|isb\.nu\.edu\.pk)$", email, re.IGNORECASE))

    # ✅ 3. Look up user in database
    # Check in order: Investigator, Admin, Invigilator, Student
    # This ensures investigators are identified correctly
    investigator = db.query(Investigator).filter(Investigator.email == email).first()
    admin = db.query(Admin).filter(Admin.email == email).first()
    invigilator = db.query(Invigilator).filter(Invigilator.email == email).first()
    student = db.query(Student).filter(Student.email == email).first()

    user = investigator or admin or invigilator or student
    user_type = None
    user_id = None

    if user:
        # ✅ Existing user - Check investigator FIRST to avoid misidentification
        if investigator:
            user_type, user_id = "investigator", str(investigator.investigator_id)
        elif admin:
            user_type, user_id = "admin", str(admin.admin_id)
        elif invigilator:
            user_type, user_id = "invigilator", str(invigilator.invigilator_id)
        elif student:
            user_type, user_id = "student", str(student.student_id)

    else:
        # ✅ 4. New user — handle based on email type
        if is_student_email:
            # Auto-register student
            new_student = Student(
                email=email,
                name=name,
                created_at=datetime.utcnow(),
            )
            db.add(new_student)
            db.commit()
            db.refresh(new_student)
            user_type = "student"
            user_id = str(new_student.student_id)

        else:
            # Redirect to frontend for role selection
            select_role_url = f"{FRONTEND_URL}/select-role?email={email}&name={name}"
            return RedirectResponse(url=select_role_url)

    # ✅ 5. Create access token and redirect to dashboard
    access_token = create_access_token(user_id=user_id, user_type=user_type)
    frontend_url = f"{FRONTEND_URL}/login-success?token={access_token}&user_type={user_type}&id={user_id}"

    print("-----------------------------------")
    print(frontend_url)
    print("-----------------------------------")

    return RedirectResponse(url=frontend_url)


@router.post("/register-role")
def register_role(data: RoleRegisterRequest, db: Session = Depends(get_db)):
    role = data.role.lower()
    email = data.email
    name = data.name

    # Check if already exists
    existing = (
        db.query(Admin).filter(Admin.email == email).first()
        or db.query(Invigilator).filter(Invigilator.email == email).first()
        or db.query(Investigator).filter(Investigator.email == email).first()
        or db.query(Student).filter(Student.email == email).first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User already registered.")

    # Create the appropriate record
    if role == "admin":
        user = Admin(email=email, name=name, created_at=datetime.utcnow())
        db.add(user)
    elif role == "invigilator":
        user = Invigilator(email=email, name=name, created_at=datetime.utcnow())
        db.add(user)
    elif role == "investigator":
        user = Investigator(email=email, name=name, created_at=datetime.utcnow())
        db.add(user)
    else:
        raise HTTPException(status_code=400, detail="Invalid role selected.")

    db.commit()
    db.refresh(user)

    user_id = str(
        getattr(user, f"{role}_id")
    )
    access_token = create_access_token(user_id=user_id, user_type=role)

    return {
        "access_token": access_token,
        "user_type": role,
        "id": user_id,
    }