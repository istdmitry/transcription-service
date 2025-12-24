from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.transcript import Transcript
from app.models.project import Project, ProjectMember
from app.api.auth import get_current_user

router = APIRouter()

def check_admin(user: User):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

class UserAdminResponse(BaseModel):
    id: int
    email: str
    phone_number: Optional[str]
    created_at: datetime
    is_admin: bool
    projects: List[str]
    last_transcript_at: Optional[datetime]
    total_transcripts: int
    deleted_at: Optional[datetime] = None
    delete_after: Optional[datetime] = None

@router.get("/users", response_model=List[UserAdminResponse])
def list_users_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    
    users = db.query(User).all()
    results = []
    
    for user in users:
        # Get projects
        proj_names = db.query(Project.name).join(ProjectMember).filter(ProjectMember.user_id == user.id).all()
        proj_list = [p[0] for p in proj_names]
        
        # Get stats
        stats = db.query(
            func.count(Transcript.id),
            func.max(Transcript.created_at)
        ).filter(Transcript.user_id == user.id).first()
        
        results.append(UserAdminResponse(
            id=user.id,
            email=user.email,
            phone_number=user.phone_number,
            created_at=user.created_at,
            is_admin=user.is_admin,
            projects=proj_list,
            last_transcript_at=stats[1],
            total_transcripts=stats[0] or 0,
            deleted_at=user.deleted_at,
            delete_after=user.delete_after
        ))
        
    return results

@router.get("/stats")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    
    total_users = db.query(func.count(User.id)).scalar()
    total_transcripts = db.query(func.count(Transcript.id)).scalar()
    total_projects = db.query(func.count(Project.id)).scalar()
    
    return {
        "total_users": total_users,
        "total_transcripts": total_transcripts,
        "total_projects": total_projects
    }

@router.delete("/users/{user_id}")
def soft_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    user.is_active = False
    user.deleted_at = now
    user.delete_after = now + timedelta(days=10)
    # scrub personal integrations
    user.api_key = None
    user.phone_number = None
    user.telegram_chat_id = None
    user.gdrive_creds = None
    user.gdrive_folder = None
    user.gdrive_email = None

    db.add(user)
    db.commit()
    return {"message": "User marked for deletion", "delete_after": user.delete_after}
