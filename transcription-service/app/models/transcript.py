import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class TranscriptStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Metadata
    filename = Column(String)
    media_url = Column(String, nullable=False) # S3 URL or path
    media_type = Column(String) # audio/wav, video/mp4 etc.
    
    # Content
    transcript_text = Column(Text, nullable=True)
    language = Column(String, default="en") # en, ru
    
    # Status
    status = Column(Enum(TranscriptStatus), default=TranscriptStatus.PENDING)
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("app.models.user.User", backref="transcripts")
