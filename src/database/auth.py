from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
import os
import re
from database.db import get_db
from database.models import Admin, Invigilator, Investigator, Student
from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from starlette.responses import RedirectResponse
from dotenv import load_dotenv

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

        user = db.query(user_model).filter(user_model._table_.columns[0] == user_id).first()
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


@router.post("/signup", response_model=SignupResponse)
def signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    """
    User registration endpoint.
    Creates a new user account based on the selected role.
    """
    role = user_data.role.lower()
    email = user_data.email.lower()
    
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
        if role == "admin":
            # Admin model requires username, use email as username if not provided
            user = Admin(
                email=email,
                username=email,  # Use email as username
                password_hash=password_hash,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            user_id = str(user.admin_id)
            
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
            user_id = str(user.invigilator_id)
            
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
            user_id = str(user.investigator_id)
            
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
            user_id = str(user.student_id)
        
        # Generate access token
        access_token = create_access_token(
            user_id=user_id,
            user_type=role,
            expires_delta=timedelta(hours=1)
        )
        
        return {
            "access_token": access_token,
            "user_type": role,
            "id": user_id,
            "email": email,
            "name": user_data.name
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


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
    student = db.query(Student).filter(Student.email == email).first()
    admin = db.query(Admin).filter(Admin.email == email).first()
    investigator = db.query(Investigator).filter(Investigator.email == email).first()
    invigilator = db.query(Invigilator).filter(Invigilator.email == email).first()

    user = admin or investigator or invigilator or student
    user_type = None
    user_id = None

    if user:
        # ✅ Existing user
        if admin:
            user_type, user_id = "admin", str(admin.admin_id)
        elif investigator:
            user_type, user_id = "investigator", str(investigator.investigator_id)
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