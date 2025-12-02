from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from database.db import get_db
from database.models import Admin, Invigilator, Investigator, Student
from database.auth import get_current_user, hash_password

router = APIRouter(prefix="/users", tags=["Users"])


# -------------------------
# Response Schemas
# -------------------------
class UserRead(BaseModel):
    id: str
    name: str
    email: str
    user_type: str
    status: Optional[str] = "active"
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    # User-type specific fields
    roll_number: Optional[str] = None  # For students
    designation: Optional[str] = None  # For investigators
    username: Optional[str] = None  # For admins

    model_config = {
        "from_attributes": True
    }


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    user_type: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    user_type: str
    password: str
    status: Optional[str] = "active"
    # Optional fields for specific user types
    username: Optional[str] = None  # For admin
    roll_number: Optional[str] = None  # For student
    designation: Optional[str] = None  # For investigator
    photo_url: Optional[str] = None  # For invigilator/student


class UserListResponse(BaseModel):
    users: List[UserRead]
    total: int
    page: int
    limit: int


# -------------------------
# Helper Functions
# -------------------------
def get_user_model(user_type: str):
    """Get the appropriate user model based on user type."""
    model_map = {
        "admin": Admin,
        "investigator": Investigator,
        "invigilator": Invigilator,
        "student": Student,
    }
    return model_map.get(user_type)


def get_user_id_field(user_type: str):
    """Get the ID field name for a user type."""
    field_map = {
        "admin": "admin_id",
        "investigator": "investigator_id",
        "invigilator": "invigilator_id",
        "student": "student_id",
    }
    return field_map.get(user_type)


def convert_user_to_read(user, user_type: str) -> UserRead:
    """Convert a user model instance to UserRead."""
    id_field = get_user_id_field(user_type)
    user_id = str(getattr(user, id_field))
    
    # Get user-type specific fields
    roll_number = getattr(user, "roll_number", None) if user_type == "student" else None
    designation = getattr(user, "designation", None) if user_type == "investigator" else None
    username = getattr(user, "username", None) if user_type == "admin" else None
    
    return UserRead(
        id=user_id,
        name=getattr(user, "name", getattr(user, "username", "Unknown")),
        email=user.email,
        user_type=user_type,
        status=getattr(user, "status", "active"),  # Get status from model or default to active
        created_at=getattr(user, "created_at", None),
        last_login=None,  # Can be added if last_login tracking is implemented
        roll_number=roll_number,
        designation=designation,
        username=username
    )


# -------------------------
# Get Current User
# -------------------------
@router.get("/me", response_model=UserRead)
def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current authenticated user's profile.
    """
    user_type = current_user.get("user_type")
    user_id = current_user.get("id")
    
    model = get_user_model(user_type)
    if not model:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    id_field = get_user_id_field(user_type)
    user = db.query(model).filter(getattr(model, id_field) == UUID(user_id)).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return convert_user_to_read(user, user_type)


# -------------------------
# Update Current User
# -------------------------
@router.put("/me", response_model=UserRead)
def update_current_user_profile(
    update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current authenticated user's profile.
    """
    user_type = current_user.get("user_type")
    user_id = current_user.get("id")
    
    model = get_user_model(user_type)
    if not model:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    id_field = get_user_id_field(user_type)
    user = db.query(model).filter(getattr(model, id_field) == UUID(user_id)).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if update.name is not None:
        if hasattr(user, "name"):
            user.name = update.name
        elif hasattr(user, "username"):
            user.username = update.name
    
    if update.email is not None:
        # Check if email is already taken
        existing = db.query(model).filter(model.email == update.email).first()
        if existing and str(getattr(existing, id_field)) != user_id:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = update.email
    
    db.commit()
    db.refresh(user)
    
    return convert_user_to_read(user, user_type)


# -------------------------
# Get All Users (Admin Only)
# -------------------------
@router.get("/", response_model=UserListResponse)
def get_all_users(
    role: Optional[str] = Query(None, regex="^(admin|investigator|invigilator|student)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all users with filtering and pagination (Admin only).
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view all users")
    
    all_users = []
    
    # Get users based on role filter
    user_types = [role] if role else ["admin", "investigator", "invigilator", "student"]
    
    for user_type in user_types:
        model = get_user_model(user_type)
        if model:
            users = db.query(model).all()
            for user in users:
                all_users.append(convert_user_to_read(user, user_type))
    
    # Apply pagination
    total = len(all_users)
    offset = (page - 1) * limit
    paginated_users = all_users[offset:offset + limit]
    
    return UserListResponse(
        users=paginated_users,
        total=total,
        page=page,
        limit=limit
    )


# -------------------------
# Create User (Admin Only)
# -------------------------
@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new user (Admin only).
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create users")
    
    user_type = user_data.user_type.lower()
    if user_type not in ["admin", "investigator", "invigilator", "student"]:
        raise HTTPException(status_code=400, detail="Invalid user type. Must be one of: admin, investigator, invigilator, student")
    
    model = get_user_model(user_type)
    if not model:
        raise HTTPException(status_code=400, detail="Invalid user type")
    
    # Check if email already exists across ALL user types
    email_lower = user_data.email.lower()
    existing_admin = db.query(Admin).filter(Admin.email == email_lower).first()
    existing_investigator = db.query(Investigator).filter(Investigator.email == email_lower).first()
    existing_invigilator = db.query(Invigilator).filter(Invigilator.email == email_lower).first()
    existing_student = db.query(Student).filter(Student.email == email_lower).first()
    
    if existing_admin or existing_investigator or existing_invigilator or existing_student:
        raise HTTPException(status_code=400, detail="Email already registered with another user account")
    
    # Import hash_password from auth
    from database.auth import hash_password
    
    # Validate required fields based on user type
    if user_type == "admin":
        # For admin, use name as username if username is not provided
        username = user_data.username or user_data.name or user_data.email
        if not username:
            raise HTTPException(status_code=400, detail="Username, name, or email is required for admin users")
        
        # Check if username already exists for admin users
        existing_username = db.query(Admin).filter(Admin.username == username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken by another admin")
    elif user_type in ["invigilator", "investigator", "student"]:
        if not user_data.name:
            raise HTTPException(status_code=400, detail="Name is required for this user type")
    
    # Validate password
    if not user_data.password or len(user_data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
    
    # Create user based on type
    if user_type == "admin":
        username = user_data.username or user_data.name or user_data.email
        new_user = Admin(
            username=username,
            email=user_data.email.lower(),
            password_hash=hash_password(user_data.password),
            created_at=datetime.utcnow()
            # status field will be available after database migration
            # status=user_data.status or "active"
        )
    elif user_type == "invigilator":
        new_user = Invigilator(
            name=user_data.name.strip(),
            email=user_data.email.lower(),
            password_hash=hash_password(user_data.password),
            photo_url=user_data.photo_url,
            created_at=datetime.utcnow()
            # status field will be available after database migration
            # status=user_data.status or "active"
        )
    elif user_type == "investigator":
        new_user = Investigator(
            name=user_data.name.strip(),
            email=user_data.email.lower(),
            designation=user_data.designation.strip() if user_data.designation else None,
            password_hash=hash_password(user_data.password),
            created_at=datetime.utcnow()
            # status field will be available after database migration
            # status=user_data.status or "active"
        )
    elif user_type == "student":
        if not user_data.roll_number:
            raise HTTPException(status_code=400, detail="roll_number is required for students")
        
        # Check if roll_number already exists for students
        existing_roll = db.query(Student).filter(Student.roll_number == user_data.roll_number.strip()).first()
        if existing_roll:
            raise HTTPException(status_code=400, detail="A student with this roll number already exists")
        
        new_user = Student(
            name=user_data.name.strip(),
            email=user_data.email.lower(),
            roll_number=user_data.roll_number.strip(),
            photo_url=user_data.photo_url,
            password_hash=hash_password(user_data.password),
            created_at=datetime.utcnow()
            # status field will be available after database migration
            # status=user_data.status or "active"
        )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return convert_user_to_read(new_user, user_type)


# -------------------------
# Get User by ID
# -------------------------
@router.get("/{user_id}", response_model=UserRead)
def get_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a user by ID (Admin only).
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view user details")
    
    # Try to find user in each model
    for user_type in ["admin", "investigator", "invigilator", "student"]:
        model = get_user_model(user_type)
        if not model:
            continue
        
        id_field = get_user_id_field(user_type)
        try:
            user = db.query(model).filter(getattr(model, id_field) == UUID(user_id)).first()
            if user:
                return convert_user_to_read(user, user_type)
        except ValueError:
            continue
    
    raise HTTPException(status_code=404, detail="User not found")


# -------------------------
# Update User (Admin Only)
# -------------------------
@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: str,
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a user (Admin only).
    Admins cannot update other admin users.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update users")
    
    # Find user
    user = None
    user_type = None
    for ut in ["admin", "investigator", "invigilator", "student"]:
        model = get_user_model(ut)
        if not model:
            continue
        
        id_field = get_user_id_field(ut)
        try:
            found_user = db.query(model).filter(getattr(model, id_field) == UUID(user_id)).first()
            if found_user:
                user = found_user
                user_type = ut
                break
        except ValueError:
            continue
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admins from editing other admins
    if user_type == "admin":
        raise HTTPException(status_code=403, detail="Admins cannot edit other admin users")
    
    # Update fields
    if update.name is not None:
        if hasattr(user, "name"):
            user.name = update.name
        elif hasattr(user, "username"):
            user.username = update.name
    
    if update.email is not None:
        # Check if email is already taken
        model = get_user_model(user_type)
        existing = db.query(model).filter(model.email == update.email).first()
        if existing and str(getattr(existing, get_user_id_field(user_type))) != user_id:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = update.email
    
    if update.status is not None:
        # Update status field
        if hasattr(user, "status"):
            user.status = update.status
    
    if update.password is not None:
        # Update password
        from database.auth import hash_password
        user.password_hash = hash_password(update.password)
    
    if update.user_type is not None and update.user_type != user_type:
        # User type change would require migration - implement if needed
        raise HTTPException(status_code=400, detail="User type cannot be changed")
    
    db.commit()
    db.refresh(user)
    
    return convert_user_to_read(user, user_type)


# -------------------------
# Delete User (Admin Only)
# -------------------------
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a user (Admin only).
    Admins cannot delete other admin users.
    """
    if current_user.get("user_type") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")
    
    # Find and delete user
    user_type = None
    for ut in ["admin", "investigator", "invigilator", "student"]:
        model = get_user_model(ut)
        if not model:
            continue
        
        id_field = get_user_id_field(ut)
        try:
            user = db.query(model).filter(getattr(model, id_field) == UUID(user_id)).first()
            if user:
                user_type = ut
                # Prevent admins from deleting other admins
                if ut == "admin":
                    raise HTTPException(status_code=403, detail="Admins cannot delete other admin users")
                db.delete(user)
                db.commit()
                return None
        except ValueError:
            continue
    
    raise HTTPException(status_code=404, detail="User not found")

