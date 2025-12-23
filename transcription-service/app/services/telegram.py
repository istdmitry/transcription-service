import requests
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.transcript import Transcript, TranscriptStatus
from app.models.project import Project, ProjectMember, PendingInteraction
from app.utils.s3 import s3_client
from app.services.transcription import process_transcription
from app.core.config import settings
import uuid
import os
import json

TELEGRAM_API_URL = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}"

def handle_telegram_update(update: dict, db: Session, background_tasks):
    # Determine if it's a message or a callback query
    if "message" in update:
        handle_message(update["message"], db, background_tasks)
    elif "callback_query" in update:
        handle_callback(update["callback_query"], db, background_tasks)

def handle_message(message: dict, db: Session, background_tasks):
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return

    # 1. Handle Commands
    text = message.get("text", "")
    if text == "/start":
        # Check if linked
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if user:
            send_message(chat_id, f"✅ Connected as: {user.email}\nYou can send audio/video files to transcribe.")
        else:
            send_welcome_screen(chat_id)
        return

    # 2. Handle Contact Sharing (Link Account)
    if "contact" in message:
        handle_contact_link(message, db)
        return

    # 3. Handle File Uploads
    file_id = None
    if "voice" in message:
        file_id = message["voice"]["file_id"]
    elif "audio" in message:
        file_id = message["audio"]["file_id"]
    elif "video" in message:
        file_id = message["video"]["file_id"]
    elif "document" in message:
        file_id = message["document"]["file_id"]

    if file_id:
        process_file_upload(chat_id, file_id, db, background_tasks)
    else:
        # Check if linked anyway to provide context
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if not user:
            send_message(chat_id, "❌ Please link your account first by sharing your contact.")
            send_welcome_screen(chat_id)
        else:
            send_message(chat_id, "Please send an audio or video file to transcribe.")

def handle_contact_link(message: dict, db: Session):
    chat_id = message["chat"]["id"]
    contact = message["contact"]
    if contact.get("user_id") == message.get("from", {}).get("id"):
        phone = contact.get("phone_number")
        if not phone.startswith("+"): phone = f"+{phone}"
        
        user = db.query(User).filter(User.phone_number == phone).first()
        if user:
            user.telegram_chat_id = chat_id
            db.commit()
            send_message(chat_id, f"✅ Account linked successfully!\nUser: {user.email}\n\nYou can now send files.")
        else:
            send_message(chat_id, "❌ No account found with this phone number. Please register on the website first.")
    else:
        send_message(chat_id, "❌ Please share your own contact.")

def process_file_upload(chat_id: int, file_id: str, db: Session, background_tasks):
    # Verify link
    user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
    if not user:
        send_message(chat_id, "❌ Registration required. Please link your account first.")
        send_welcome_screen(chat_id)
        return

    # Get user projects
    projects = db.query(Project).join(ProjectMember).filter(ProjectMember.user_id == user.id).all()
    
    if not projects:
        # Direct processing for personal
        start_transcription_task(chat_id, user, file_id, None, db, background_tasks)
    else:
        # Create Pending Interaction
        pending = PendingInteraction(user_id=user.id, telegram_file_id=file_id)
        db.add(pending)
        db.commit()
        db.refresh(pending)
        
        # Send project selection keyboard
        send_project_selection(chat_id, pending.id, projects)

def handle_callback(callback: dict, db: Session, background_tasks):
    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]
    data = callback.get("data", "")
    
    # Format: proj_{interaction_id}_{project_id or 'personal'}
    if not data.startswith("proj_"):
        return
        
    parts = data.split("_")
    interaction_id = int(parts[1])
    target = parts[2] # 'personal' or ID
    
    pending = db.query(PendingInteraction).get(interaction_id)
    if not pending:
        send_message(chat_id, "❌ This request has expired or was already processed.")
        return
        
    user = db.query(User).get(pending.user_id)
    project_id = int(target) if target != "personal" else None
    
    # Update message to show choice
    choice_text = "Personal" if target == "personal" else db.query(Project.name).filter(Project.id == project_id).scalar()
    edit_message(chat_id, message_id, f"✅ Selected: {choice_text}. Starting transcription...")
    
    # Start task
    start_transcription_task(chat_id, user, pending.telegram_file_id, project_id, db, background_tasks)
    
    # Cleanup
    db.delete(pending)
    db.commit()

def start_transcription_task(chat_id, user, file_id, project_id, db, background_tasks):
    try:
        # 1. Get File Path
        file_path_res = requests.get(f"{TELEGRAM_API_URL}/getFile?file_id={file_id}")
        if file_path_res.status_code != 200:
            send_message(chat_id, "Error getting file info from Telegram.")
            return
            
        file_path = file_path_res.json()["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/{file_path}"
        
        # 2. Download and Upload to S3
        file_content = requests.get(download_url).content
        import io
        file_ext = os.path.splitext(file_path)[1]
        s3_key = f"uploads/{user.id}/{uuid.uuid4()}{file_ext}"
        s3_client.upload_file(io.BytesIO(file_content), s3_key)
        
        # 3. Create Transcript Record
        new_transcript = Transcript(
            user_id=user.id,
            project_id=project_id,
            filename=f"telegram_upload_{file_id[:8]}{file_ext}",
            media_url=s3_key,
            status=TranscriptStatus.PENDING
        )
        db.add(new_transcript)
        db.commit()
        db.refresh(new_transcript)
        
        if not project_id:
            send_message(chat_id, "File received! Transcription started (Personal).")
        
        # 4. Trigger Processing
        background_tasks.add_task(process_transcription, new_transcript.id, s3_key, db)
        
    except Exception as e:
        send_message(chat_id, f"Error starting transcription: {str(e)}")

def send_project_selection(chat_id, interaction_id, projects):
    # Buttons: Personal (BOLD simulated with text), then Projects
    buttons = [
        [{"text": "➡ PERSONAL NOTE", "callback_data": f"proj_{interaction_id}_personal"}]
    ]
    for p in projects:
        buttons.append([{"text": f"📁 {p.name}", "callback_data": f"proj_{interaction_id}_{p.id}"}])
        
    keyboard = {"inline_keyboard": buttons}
    data = {
        "chat_id": chat_id,
        "text": "Where should this transcript be assigned?",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=data)

def send_message(chat_id, text):
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})

def edit_message(chat_id, message_id, text):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text}
    requests.post(f"{TELEGRAM_API_URL}/editMessageText", json=data)

def send_welcome_screen(chat_id):
    keyboard = {
        "keyboard": [[{"text": "📱 Link Account", "request_contact": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }
    data = {
        "chat_id": chat_id,
        "text": "Welcome! 👋\n\nPlease link your account by sharing your contact to start transcribing files.",
        "reply_markup": json.dumps(keyboard)
    }
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=data)
