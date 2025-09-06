from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import users_collection
from schema import *
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",  # React dev server
    "http://127.0.0.1:5173",
    # you can add other domains if needed
]

app = FastAPI(title="Auth API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # which domains can access
    allow_credentials=True,
    allow_methods=["*"],             # GET, POST, PUT, DELETE
    allow_headers=["*"],             # headers like Content-Type
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@app.post("/signup", response_model=UserCreateResponse)
def signup(user: User):
    existing_user = users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_dict = user.dict()
    user_dict["password"] = hash_password(user.password)
    users_collection.insert_one(user_dict)

    return UserCreateResponse(code=201, message="User created successfully", data=user)


@app.post("/login", response_model=UserGetResponse)
def login(data: LoginModel):
    user = users_collection.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    user_obj = User(**user)
    return UserGetResponse(code=200, message="Login successful", data=user_obj)
