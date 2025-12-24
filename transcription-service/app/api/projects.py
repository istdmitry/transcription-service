from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse, ProjectMemberBase
from app.api.auth import get_current_user
from app.core.crypto import encrypt_data
from app.services.gdrive import test_drive_upload, test_drive_upload_encrypted
import time
from pydantic import BaseModel

router = APIRouter()


def check_admin(user: User):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

@router.get("/", response_model=List[ProjectResponse])
def list_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all projects the current user is a member of."""
    if current_user.is_admin:
        return db.query(Project).all()
        
    projects = db.query(Project).join(ProjectMember).filter(ProjectMember.user_id == current_user.id).all()
    return projects

@router.get("/admin", response_model=List[ProjectDetailResponse])
def list_all_projects_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin-only list of all projects with member details."""
    check_admin(current_user)
    return db.query(Project).all()

@router.post("/", response_model=ProjectResponse)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    
    encrypted_creds = encrypt_data(project_in.gdrive_creds) if project_in.gdrive_creds else None
    
    db_project = Project(
        name=project_in.name,
        description=project_in.description,
        gdrive_folder=project_in.gdrive_folder,
        gdrive_creds=encrypted_creds,
        gdrive_email=project_in.gdrive_email
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if not current_user.is_admin:
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        ).first()
        if not is_member:
            raise HTTPException(status_code=403, detail="Not a member of this project")
            
    return db_project

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    update_data = project_in.dict(exclude_unset=True)
    if "gdrive_creds" in update_data and update_data["gdrive_creds"]:
        update_data["gdrive_creds"] = encrypt_data(update_data["gdrive_creds"])
        
    for field, value in update_data.items():
        setattr(db_project, field, value)
        
    db.commit()
    db.refresh(db_project)
    return db_project

@router.post("/{project_id}/members")
def add_member(
    project_id: int,
    member_in: ProjectMemberBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    
    # Check if user exists
    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if already member
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == member_in.user_id
    ).first()
    if existing:
        return {"message": "User already a member"}
        
    db_member = ProjectMember(
        project_id=project_id,
        user_id=member_in.user_id,
        role=member_in.role
    )
    db.add(db_member)
    db.commit()
    return {"message": "Member added"}

class ProjectGDriveTest(BaseModel):
    gdrive_creds: Optional[str] = None
    gdrive_folder: str
    gdrive_email: Optional[str] = None

@router.post("/{project_id}/gdrive/test")
def test_project_gdrive(
    project_id: int,
    payload: ProjectGDriveTest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin(current_user)
    if not payload.gdrive_folder:
        raise HTTPException(status_code=400, detail="Missing folder ID")

    ts = int(time.time())
    filename = f"test_transcription_service_{ts}.txt"
    content = f"Test upload from Transcription Service at {ts}. If you see this file, integration works."
    if payload.gdrive_creds:
        ok, err, file_id, sa_email = test_drive_upload(payload.gdrive_creds, payload.gdrive_folder, filename, content)
    else:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.gdrive_creds:
            raise HTTPException(status_code=400, detail={"ok": False, "message": "Missing credentials. Paste JSON or save credentials first."})
        ok, err, file_id, sa_email = test_drive_upload_encrypted(project.gdrive_creds, payload.gdrive_folder, filename, content)
    if ok:
        return {"ok": True, "file_id": file_id, "filename": filename}

    hint = None
    if sa_email:
        hint = f"Share the folder with service account: {sa_email}"
    raise HTTPException(status_code=400, detail={"ok": False, "message": err, "hint": hint})
