import requests
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.transcript import Transcript, TranscriptStatus
from app.utils.s3 import s3_client
from app.services.transcription import process_transcription
import uuid
import os

# Using Meta Cloud API (Graph API)
# Needs WHATSAPP_ACCESS_TOKEN and PHONE_NUMBER_ID in env

def get_whatsapp_user(phone_number: str, db: Session):
    # 1. Try to find user by Phone Number
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if user:
        return user

    # 2. KeyFallback: Try legacy email format (or create new)
    email = f"whatsapp_{phone_number}@bot.user"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        from app.core.security import get_password_hash
        user = User(
            email=email,
            phone_number=phone_number,
            hashed_password=get_password_hash(str(uuid.uuid4())),
            api_key=str(uuid.uuid4())
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def handle_whatsapp_update(data: dict, db: Session, background_tasks):
    # WhatsApp Webhook payload structure is deep
    entry = data.get("entry", [])[0]
    changes = entry.get("changes", [])[0]
    value = changes.get("value", {})
    messages = value.get("messages", [])
    
    if not messages:
        return

    message = messages[0]
    phone_number = message["from"]
    msg_type = message["type"]
    
    media_id = None
    if msg_type == "audio":
        media_id = message["audio"]["id"]
    elif msg_type == "video":
        media_id = message["video"]["id"]
    elif msg_type == "voice": # PTT
        media_id = message["voice"]["id"]
        
    if not media_id:
        # Maybe send text back saying "Send me audio"
        return

    # Download Media
    # 1. Get Media URL
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    media_url_res = requests.get(f"https://graph.facebook.com/v18.0/{media_id}", headers={"Authorization": f"Bearer {token}"})
    if media_url_res.status_code != 200:
        print(f"Error getting media url: {media_url_res.text}")
        return
        
    media_url = media_url_res.json().get("url")
    
    # 2. Download Content
    file_content_res = requests.get(media_url, headers={"Authorization": f"Bearer {token}"})
    content = file_content_res.content
    
    # 3. Upload to S3
    import io
    file_obj = io.BytesIO(content)
    # Guess extension? WhatsApp provides mime_type in original message usually.
    # For now, simplistic approach
    ext = ".ogg" if msg_type == "voice" else ".mp4"
    
    user = get_whatsapp_user(phone_number, db)
    s3_key = f"uploads/{user.id}/wa_{media_id}{ext}"
    
    s3_client.upload_file(file_obj, s3_key)
    
    # 4. Create Transcript
    new_transcript = Transcript(
        user_id=user.id,
        filename=f"whatsapp_{media_id}{ext}",
        media_url=s3_key,
        status=TranscriptStatus.PENDING
    )
    db.add(new_transcript)
    db.commit()
    db.refresh(new_transcript)
    
    background_tasks.add_task(process_transcription, new_transcript.id, s3_key, db)
    # Could reply "Processing..."
