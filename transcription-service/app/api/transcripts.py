from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db

from app.api.deps import get_current_user
from app.models.user import User
from app.models.transcript import Transcript, TranscriptStatus
from app.schemas.transcript import TranscriptResponse, TranscriptReassignRequest
from app.utils.s3 import s3_client
from app.services.transcription import process_transcription
from app.models.project import Project, ProjectMember
import uuid
import os

router = APIRouter()

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

from typing import List, Optional

@router.get("/", response_model=List[TranscriptResponse])
def list_transcripts(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    sort_by: Optional[str] = "created_at_desc", # created_at_asc, filename_asc, etc.
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Transcript).filter(Transcript.user_id == current_user.id)
    
    if status:
        query = query.filter(Transcript.status == status)
        
    if project_id:
        query = query.filter(Transcript.project_id == project_id)
        
    # Sorting
    if sort_by == "created_at_desc":
        query = query.order_by(Transcript.created_at.desc())
    elif sort_by == "created_at_asc":
        query = query.order_by(Transcript.created_at.asc())
    elif sort_by == "filename_asc":
        query = query.order_by(Transcript.filename.asc())
    elif sort_by == "filename_desc":
        query = query.order_by(Transcript.filename.desc())
        
    transcripts = query.offset(skip).limit(limit).all()
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

@router.patch("/{transcript_id}/reassign", response_model=TranscriptResponse)
def reassign_transcript(
    transcript_id: int,
    payload: TranscriptReassignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")

    if not current_user.is_admin and transcript.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this transcript")

    # Validate project membership if assigning to a project
    if payload.project_id:
        project = db.query(Project).filter(Project.id == payload.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if not current_user.is_admin:
            membership = db.query(ProjectMember).filter(
                ProjectMember.project_id == payload.project_id,
                ProjectMember.user_id == current_user.id
            ).first()
            if not membership:
                raise HTTPException(status_code=403, detail="Not a member of this project")

        transcript.project_id = payload.project_id
    else:
        transcript.project_id = None

    db.commit()
    db.refresh(transcript)
    return transcript
