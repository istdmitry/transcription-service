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
import json

def get_telegram_user(chat_id: int, db: Session):
    # 1. Try to find user by explicitly linked Telegram Chat ID
    user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
    if user:
        return user
    
    # 2. KeyFallback: Legacy auto-user (only if NO other match likely)
    # Ideally, we should prompt them to link instead of creating random users immediately.
    # But for backward compatibility with previous steps:
    email = f"telegram_{chat_id}@bot.user"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        from app.core.security import get_password_hash
        user = User(
            email=email,
            hashed_password=get_password_hash(str(uuid.uuid4())),
            api_key=str(uuid.uuid4()),
            telegram_chat_id=chat_id # Auto-link new ghost users
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

    # Handle /start command
    text = message.get("text", "")
    if text == "/start":
        send_welcome_screen(chat_id)
        return

    # Handle Contact Sharing (Account Linking)
    if "contact" in message:
        contact = message["contact"]
        # Ensure the contact belongs to the sender
        if contact.get("user_id") == message.get("from", {}).get("id"):
            phone = contact.get("phone_number")
            # Telegram might return phone with or without '+'
            if not phone.startswith("+"):
                phone = f"+{phone}"
            
            # Find user by phone
            user = db.query(User).filter(User.phone_number == phone).first()
            if user:
                user.telegram_chat_id = chat_id
                db.commit()
                send_message(chat_id, f"✅ Account linked successfully!\nUser: {user.email}\n\nYou can now send files to transcribe.")
            else:
                send_message(chat_id, "❌ No account found with this phone number. Please register on the website first.")
        else:
            send_message(chat_id, "❌ Please share your own contact.")
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
        send_message(chat_id, "Please send an audio or video file to transcribe, or share your contact to link account.")
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

def send_welcome_screen(chat_id):
    # Send a button to request contact
    keyboard = {
        "keyboard": [[{
            "text": "📱 Link Account",
            "request_contact": True
        }]],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }
    
    data = {
        "chat_id": chat_id,
        "text": "Welcome! 👋\n\nTo save transcripts to your web account, please link it by sharing your phone number.\n\nOr just send an audio file to use as a guest.",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=data)
