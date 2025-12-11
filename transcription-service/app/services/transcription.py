import openai
from sqlalchemy.orm import Session
from app.models.transcript import Transcript, TranscriptStatus
from app.core.config import settings
from app.utils.s3 import s3_client
import os
import tempfile

def process_transcription(transcript_id: int, s3_key: str, db: Session):
    """
    Background task to process transcription using OpenAI Whisper.
    """
    try:
        # 1. Fetch transcript record
        transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
        if not transcript:
            return

        transcript.status = TranscriptStatus.PROCESSING
        db.commit()

        # 2. Download from S3 to Temp File
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(s3_key)[1]) as tmp_file:
            s3_client.s3.download_fileobj(s3_client.bucket, s3_key, tmp_file)
            tmp_path = tmp_file.name

        # 3. Call OpenAI Whisper
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        with open(tmp_path, "rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text"
            )
        
        # 4. Update DB
        transcript.transcript_text = result
        transcript.status = TranscriptStatus.COMPLETED
        db.commit()

        # 5. Notify Telegram (Status Update Only)
        if transcript.user.telegram_chat_id:
            from app.services.telegram import send_message
            send_message(transcript.user.telegram_chat_id, "✅ Transcription complete! View it on your dashboard.")

        # Cleanup
        os.remove(tmp_path)
        
    except Exception as e:
        if transcript:
            transcript.status = TranscriptStatus.FAILED
            transcript.error_message = str(e)
            db.commit()
            
            if transcript.user.telegram_chat_id:
                from app.services.telegram import send_message
                send_message(transcript.user.telegram_chat_id, f"❌ Transcription failed: {str(e)}")
                
        print(f"Error processing transcript {transcript_id}: {e}")
