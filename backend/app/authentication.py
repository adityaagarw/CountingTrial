# backend/app/authentication.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import sys
import os
from db.schema import User
from db.db_service import DBService
from passlib.context import CryptContext
from pydantic import BaseModel

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Hash password
def get_password_hash(password):
    return pwd_context.hash(password)

# Authenticate user
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

class UserSignupInDB(BaseModel):
    username: str
    password: str
    isAdmin: bool

class UserInDB(BaseModel):
    username: str
    password: str

# User login route
@router.post("/login")
def login(form_data: UserInDB):
    db = DBService().get_session()
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    # Return user details
    return {"username": user.email, "is_admin": user.is_admin}


# User signup route
# def signup(form_data: OAuth2PasswordRequestForm = Depends()):

@router.post("/signup")
def signup(form_data: UserSignupInDB):
    # Access username and password from the request body directly
    db = DBService().get_session()
    user = db.query(User).filter(User.email == form_data.username).first()
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    # Create new user
    hashed_password = get_password_hash(form_data.password)
    new_user = User(email=form_data.username, hashed_password=hashed_password, is_admin=form_data.isAdmin)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"username": new_user.email, "is_admin": new_user.is_admin}