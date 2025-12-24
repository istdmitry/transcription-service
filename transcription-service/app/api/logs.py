from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.models.user import User
import os

router = APIRouter()

@router.get("/", response_model=list[str])
def get_logs(lines: int = 50, current_user: User = Depends(get_current_user)):
    """
    Retrieve the last N lines of the server log.
    Only accessible to authenticated users.
    """
    log_file = "server.log"
    if not os.path.exists(log_file):
        return ["Log file not found."]

    try:
        with open(log_file, "r") as f:
            all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
