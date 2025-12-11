import openai
from sqlalchemy.orm import Session
from app.models.transcript import Transcript, TranscriptStatus
from app.core.config import settings
from app.utils.s3 import s3_client
import os
import tempfile

def process_transcription(transcript_id: int, s3_key: str, db: Session, notify_user: bool = True):
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

        # Validate File
        file_size = os.path.getsize(tmp_path)
        print(f"Processing Transcript {transcript_id}: Downloaded {s3_key} ({file_size} bytes)")
        
        if file_size == 0:
            raise ValueError("Downloaded file is empty (0 bytes). Upload might have failed.")
        
        # 3. Convert to MP3 if needed (FFmpeg)
        # OpenAI Whisper limit is 25MB. Audio conversion usually shrinks video significantly.
        # We always convert to mp3 for consistency and size reduction.
        
        import subprocess
        mp3_path = tmp_path + ".mp3"
        
        try:
            print(f"Converting {tmp_path} to {mp3_path}...")
            # ffmpeg -i input -vn -acodec libmp3lame -q:a 4 output.mp3
            # -vn: disable video
            # -y: overwrite
            # -ac 1: mono (optional, good for speech)
            subprocess.run([
                "ffmpeg", "-i", tmp_path, 
                "-vn", "-acodec", "libmp3lame", "-q:a", "4", "-y", 
                mp3_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            
            # Use the new MP3 file
            final_path = mp3_path
            print(f"Conversion successful. New size: {os.path.getsize(final_path)} bytes")
            
        except FileNotFoundError:
            print("FFmpeg not found. Skipping conversion (sending original file).")
            final_path = tmp_path
        except Exception as e:
            print(f"FFmpeg conversion failed: {e}. Trying original file.")
            final_path = tmp_path

        # 3. Call OpenAI Whisper
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        try:
            with open(final_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    response_format="text"
                )
        finally:
            # Cleanup extra file if created
            if final_path != tmp_path and os.path.exists(final_path):
                os.remove(final_path)
        
        # 4. Update DB
        transcript.transcript_text = result
        transcript.status = TranscriptStatus.COMPLETED
        db.commit()

        # 5. Notify Telegram (Status Update Only)
        if notify_user and transcript.owner.telegram_chat_id:
            from app.services.telegram import send_message
            send_message(transcript.owner.telegram_chat_id, "✅ Transcription complete! View it on your dashboard.")

        # Cleanup
        os.remove(tmp_path)
        
    except Exception as e:
        if transcript:
            transcript.status = TranscriptStatus.FAILED
            transcript.error_message = str(e)
            db.commit()
            
            if transcript.owner.telegram_chat_id:
                from app.services.telegram import send_message
                send_message(transcript.owner.telegram_chat_id, f"❌ Transcription failed: {str(e)}")
                
        print(f"Error processing transcript {transcript_id}: {e}")
