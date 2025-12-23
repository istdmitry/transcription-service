from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    telegram_chat_id = Column(BigInteger, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Personal GDrive (Encrypted)
    gdrive_creds = Column(Text, nullable=True)
    gdrive_folder = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
