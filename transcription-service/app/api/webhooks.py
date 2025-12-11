from fastapi import APIRouter, Request, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.services.telegram import handle_telegram_update

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    update = await request.json()
    # Process synchronously or background?
    # Telegram expects quick 200 OK. Background is better.
    # However, `handle_telegram_update` needs a DB session. 
    # Passing DB session to background task can be tricky due to thread safety/closing.
    # Better to process the lightweight logic here or create a new session in the task.
    # For MVP, we'll run it directly but fast.
    
    # Actually, let's just await it if it's fast, or use background tasks with a wrapper that creates a new session.
    # But `dbsession` dependency is per-request.
    # Let's run `handle_telegram_update` here.
    
    try:
        handle_telegram_update(update, db, background_tasks)
    except Exception as e:
        print(f"Error handling webhook: {e}")
        
    return {"status": "ok"}
