import requests
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.transcript import Transcript, TranscriptStatus
from app.utils.s3 import s3_client
from app.services.transcription import process_transcription
from app.core.config import settings
import uuid
import os

TELEGRAM_API_URL = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}"

def get_telegram_user(chat_id: int, db: Session):
    # This is a simplification. Ideally, we link Telegram ID to User ID.
    # For now, we can create a user based on Telegram ID or lookup by a stored telegram_id field.
    # We didn't add telegram_id to User model yet. We should. 
    # Or we just use `telegram_{chat_id}@bot.user` as email.
    email = f"telegram_{chat_id}@bot.user"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create auto-user
        from app.core.security import get_password_hash
        user = User(
            email=email,
            hashed_password=get_password_hash(str(uuid.uuid4())), # Random password
            api_key=str(uuid.uuid4())
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def handle_telegram_update(update: dict, db: Session, background_tasks):
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    
    if not chat_id:
        return

    # 1. Check for Audio/Voice/Video
    file_id = None
    if "voice" in message:
        file_id = message["voice"]["file_id"]
    elif "audio" in message:
        file_id = message["audio"]["file_id"]
    elif "video" in message:
        file_id = message["video"]["file_id"]
    elif "document" in message:
        # Check mime type?
        file_id = message["document"]["file_id"]
    
    if not file_id:
        send_message(chat_id, "Please send an audio or video file to transcribe.")
        return

    # 2. Get File Path from Telegram
    file_path_res = requests.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}")
    if file_path_res.status_code != 200:
        send_message(chat_id, "Error getting file info.")
        return
    
    file_path = file_path_res.json()["result"]["file_path"]
    download_url = f"https://api.telegram.org/file/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/{file_path}"
    
    # 3. Download and Upload to S3
    # Note: Telegram limits bot downloads to 20MB. For larger, need TdLib or Local API Server.
    # Assuming small files for MVP.
    
    try:
        file_content = requests.get(download_url).content
        import io
        file_obj = io.BytesIO(file_content)
        
        user = get_telegram_user(chat_id, db)
        file_ext = os.path.splitext(file_path)[1]
        s3_key = f"uploads/{user.id}/{uuid.uuid4()}{file_ext}" # file_path usually has ext
        
        s3_client.upload_file(file_obj, s3_key)
        
        # 4. Create Transcript Record
        new_transcript = Transcript(
            user_id=user.id,
            filename=f"telegram_upload_{file_id}{file_ext}",
            media_url=s3_key,
            status=TranscriptStatus.PENDING
        )
        db.add(new_transcript)
        db.commit()
        db.refresh(new_transcript)
        
        send_message(chat_id, "File received! Transcription started.")
        
        # 5. Trigger Processing
        background_tasks.add_task(process_transcription, new_transcript.id, s3_key, db)
        
    except Exception as e:
        send_message(chat_id, f"Error processing file: {str(e)}")

def send_message(chat_id, text):
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})
