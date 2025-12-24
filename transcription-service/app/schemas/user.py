from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    api_key: Optional[str] = None
    is_admin: bool = False
    gdrive_folder: Optional[str] = None
    has_gdrive_creds: bool = False

    class Config:
        from_attributes = True
