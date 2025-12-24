from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import get_current_user
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
import uuid
from pydantic import BaseModel
from typing import Optional
from app.core.crypto import encrypt_data
from app.api.deps import get_current_user

router = APIRouter()

class UserGDriveUpdate(BaseModel):
    gdrive_creds: Optional[str] = None
    gdrive_folder: Optional[str] = None

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate a random API key for the user
    api_key = str(uuid.uuid4())
    
    hashed_pw = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        phone_number=user.phone_number,
        hashed_password=hashed_pw,
        api_key=api_key
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    # Build explicit response to add computed flags without mutating the model instance
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        phone_number=current_user.phone_number,
        is_active=current_user.is_active,
        api_key=current_user.api_key,
        is_admin=current_user.is_admin,
        gdrive_folder=current_user.gdrive_folder,
        has_gdrive_creds=bool(current_user.gdrive_creds)
    )

@router.patch("/me/gdrive", response_model=UserResponse)
def update_personal_gdrive(
    payload: UserGDriveUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Connect or update a user's personal Google Drive settings.
    Credentials are encrypted before storing.
    """
    if payload.gdrive_creds is not None:
        current_user.gdrive_creds = encrypt_data(payload.gdrive_creds) if payload.gdrive_creds else None
    if payload.gdrive_folder is not None:
        current_user.gdrive_folder = payload.gdrive_folder

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    current_user.has_gdrive_creds = bool(current_user.gdrive_creds)
    return current_user
