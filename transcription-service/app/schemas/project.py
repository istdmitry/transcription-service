from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    gdrive_folder: Optional[str] = None

class ProjectCreate(ProjectBase):
    gdrive_creds: Optional[str] = None # Plain JSON input, will be encrypted by API

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    gdrive_folder: Optional[str] = None
    gdrive_creds: Optional[str] = None

class ProjectMemberBase(BaseModel):
    user_id: int
    role: str = "member"

class ProjectMemberResponse(ProjectMemberBase):
    id: int
    email: str
    
    class Config:
        from_attributes = True

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    has_gdrive_creds: bool = False
    
    class Config:
        from_attributes = True

class ProjectDetailResponse(ProjectResponse):
    members: List[ProjectMemberResponse] = []
    # gdrive_creds is NOT returned for security (or only returned if needed by admin)
