from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TranscriptBase(BaseModel):
    pass

class TranscriptCreate(TranscriptBase):
    pass 
    # File upload is handled via Form/UploadFile, not JSON body usually for the file itself.
    # But metadata can be passed.

class TranscriptResponse(BaseModel):
    id: int
    status: str
    media_url: str
    filename: Optional[str] = None
    transcript_text: Optional[str] = None
    created_at: datetime
    language: str
    project_id: Optional[int] = None
    gdrive_file_id: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class TranscriptReassignRequest(BaseModel):
    project_id: Optional[int] = None
