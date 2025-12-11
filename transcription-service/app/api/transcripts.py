from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.base import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.transcript import Transcript, TranscriptStatus
from app.schemas.transcript import TranscriptResponse
from app.utils.s3 import s3_client
from app.services.transcription import process_transcription
import uuid
import os

router = APIRouter(prefix="/transcripts", tags=["transcripts"])

@router.post("/", response_model=TranscriptResponse)
def upload_transcript(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Upload to S3
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    s3_key = f"uploads/{current_user.id}/{unique_filename}"
    
    try:
        s3_client.upload_file(file.file, s3_key, content_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    # 2. Create DB Record
    # For MVP, we presume S3 URL or just store key. Let's store key or pre-signed URL base.
    # Storing key is better.
    new_transcript = Transcript(
        user_id=current_user.id,
        filename=file.filename,
        media_url=s3_key,
        media_type=file.content_type,
        status=TranscriptStatus.PENDING
    )
    db.add(new_transcript)
    db.commit()
    db.refresh(new_transcript)
    
    # 3. Trigger Background Task
    # Issue: Background task needs the file to send to OpenAI.
    # If we uploaded to S3, the background task needs to download it back.
    # Or we can pass the temp file (Web servers usually store uploads in temp).
    # Ideally: Worker downloads from S3.
    # For now, we'll setup the background task to handle it.
    background_tasks.add_task(process_transcription, new_transcript.id, s3_key, db, notify_user=False)
    
    return new_transcript

@router.get("/", response_model=List[TranscriptResponse])
def list_transcripts(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transcripts = db.query(Transcript).filter(Transcript.user_id == current_user.id).offset(skip).limit(limit).all()
    return transcripts

@router.get("/{transcript_id}", response_model=TranscriptResponse)
def get_transcript(
    transcript_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id, Transcript.user_id == current_user.id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript

@router.delete("/{transcript_id}", status_code=204)
def delete_transcript(
    transcript_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id, Transcript.user_id == current_user.id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # 1. Delete from S3
    if transcript.media_url:
        try:
            # Check if media_url is full URL or key. Our code stores key.
            # But if we store full URL, we might need to parse.
            # Current implementation: s3_key = f"uploads/..." -> This is the key.
            s3_client.delete_file(transcript.media_url)
        except Exception as e:
            print(f"Warning: Failed to delete S3 file {transcript.media_url}: {e}")
            # We continue to delete the DB record even if S3 fails (orphan file is better than broken UI)

    # 2. Delete from DB
    db.delete(transcript)
    db.commit()
    return
