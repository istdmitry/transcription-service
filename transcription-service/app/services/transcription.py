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
    Supports smart compression for large files > 25MB.
    """
    tmp_path = None
    final_path = None
    transcript = None
    
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
        
        # 3. Audio Processing Logic
        # OpenAI Limit: 25 MB (26,214,400 bytes)
        OPENAI_LIMIT = 25 * 1024 * 1024
        
        # Supported formats by OpenAI Whisper
        SUPPORTED_EXTENSIONS = {'.m4a', '.mp3', '.wav', '.mpeg', '.mpga', '.mp4', '.webm'}
        file_ext = os.path.splitext(tmp_path)[1].lower()
        
        import subprocess

        # DECISION: Skip conversion?
        if file_ext in SUPPORTED_EXTENSIONS and file_size < OPENAI_LIMIT:
            print(f"File is supported {file_ext} and under 25MB. Skipping conversion.")
            final_path = tmp_path
        else:
            # Must convert or compress
            print(f"File needs processing (Size: {file_size}, Ext: {file_ext})")
            mp3_path = tmp_path + ".mp3"
            
            try:
                # ATTEMPT 1: Standard Conversion (Quality 4 ~ 128-165 kbps VBR)
                print(f"Attempt 1: Standard conversion to {mp3_path}...")
                subprocess.run([
                    "ffmpeg", "-i", tmp_path, 
                    "-vn", "-acodec", "libmp3lame", "-q:a", "4", "-y", 
                    mp3_path
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                
                final_path = mp3_path
                new_size = os.path.getsize(final_path)
                print(f"Standard conversion result: {new_size} bytes")

                # ATTEMPT 2: Aggressive Compression if still > 25MB
                if new_size > OPENAI_LIMIT:
                    print("Result still > 25MB. Attempting aggressive compression (32k mono)...")
                    # -b:a 32k : Constant bitrate 32kbps
                    # -ac 1    : Mono
                    subprocess.run([
                        "ffmpeg", "-i", tmp_path, 
                        "-vn", "-acodec", "libmp3lame", "-b:a", "32k", "-ac", "1", "-y", 
                        mp3_path
                    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                    
                    final_path = mp3_path
                    new_size = os.path.getsize(final_path)
                    print(f"Aggressive conversion result: {new_size} bytes")
                
                if new_size > OPENAI_LIMIT:
                    raise ValueError(f"File is too large ({new_size} bytes) even after aggressive compression. Please upload a shorter file.")

            except FileNotFoundError:
                print("FFmpeg not found. Cannot convert.")
                # If we can't convert, we just try sending the original and hope for the best
                final_path = tmp_path
            except Exception as e:
                print(f"FFmpeg conversion failed: {e}. Trying original file.")
                final_path = tmp_path

        # 4. Call OpenAI Whisper
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
            if final_path and final_path != tmp_path and os.path.exists(final_path):
                os.remove(final_path)
        
        # 5. Update DB
        transcript.transcript_text = result
        transcript.status = TranscriptStatus.COMPLETED
        db.commit()

        # --- Google Drive Integration ---
        try:
            from app.services.gdrive import upload_to_drive
            from datetime import datetime
            from app.models.project import Project
            
            # Determine which credentials to use
            creds = None
            folder = None
            
            if transcript.project_id:
                project = db.query(Project).get(transcript.project_id)
                if project:
                    creds = project.gdrive_creds
                    folder = project.gdrive_folder
            else:
                user = transcript.owner
                creds = user.gdrive_creds
                folder = user.gdrive_folder

            if creds and folder:
                # Format: {YYYY-MM-DD} {UserEmail} {OriginalFilename}.txt
                date_str = datetime.now().strftime("%Y-%m-%d")
                safe_filename = os.path.basename(transcript.filename)
                gdrive_filename = f"{date_str} {transcript.owner.email} {safe_filename}.txt"
                
                print(f"Uploading to GDrive: {gdrive_filename}")
                g_file_id = upload_to_drive(gdrive_filename, result, creds, folder)
                if g_file_id:
                    transcript.gdrive_file_id = g_file_id
                    db.commit()
            
        except Exception as e:
            print(f"GDrive Upload Error (Non-blocking): {e}")
        # --------------------------------

        # 6. Notify Telegram (Status Update Only)
        if notify_user and transcript.owner.telegram_chat_id:
            from app.services.telegram import send_message
            send_message(transcript.owner.telegram_chat_id, "✅ Transcription complete! View it on your dashboard.")

        # Cleanup
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        
    except Exception as e:
        # Cleanup
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

        if transcript:
            transcript.status = TranscriptStatus.FAILED
            transcript.error_message = str(e)
            db.commit()
            
            if transcript.owner.telegram_chat_id:
                from app.services.telegram import send_message
                send_message(transcript.owner.telegram_chat_id, f"❌ Transcription failed: {str(e)}")
                
        print(f"Error processing transcript {transcript_id}: {e}")
