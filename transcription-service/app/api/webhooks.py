from fastapi import APIRouter, Request, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.services.telegram import handle_telegram_update

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

from app.services.whatsapp import handle_whatsapp_update
import os

@router.post("/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    update = await request.json()
    try:
        handle_telegram_update(update, db, background_tasks)
    except Exception as e:
        print(f"Error handling webhook: {e}") 
    return {"status": "ok"}

@router.get("/whatsapp")
def verify_whatsapp(mode: str = "", token: str = "", challenge: str = ""):
    # WhatsApp verification challenge
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "myverifytoken")
    if mode == "subscribe" and token == verify_token:
        return int(challenge)
    return {"status": "error"}

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    data = await request.json()
    try:
        handle_whatsapp_update(data, db, background_tasks)
    except Exception as e:
        print(f"Error handling whatsapp webhook: {e}")
    return {"status": "ok"}
