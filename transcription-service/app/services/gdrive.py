import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

from app.core.crypto import decrypt_data

def get_drive_service(encrypted_creds: str):
    """
    Authenticates with Google Drive API using decrypted Service Account JSON.
    """
    if not encrypted_creds:
        return None

    json_creds = decrypt_data(encrypted_creds)
    if not json_creds:
        return None

    try:
        # Parse JSON string
        info = json.loads(json_creds)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/drive.file']
        )
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error authenticating GDrive: {e}")
        return None

def upload_to_drive(filename: str, content: str, encrypted_creds: str, folder_id: str):
    """
    Uploads text content to Google Drive using provided credentials and folder.
    """
    if not encrypted_creds or not folder_id:
        return None

    service = get_drive_service(encrypted_creds)
    if not service:
        return None

    try:
        file_metadata = {
            'name': filename,
            'parents': [folder_id],
            'mimeType': 'text/plain'
        }
        
        # Create media from string
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode('utf-8')),
            mimetype='text/plain',
            resumable=True
        )

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        print(f"File ID: {file_id} uploaded to GDrive as {filename}")
        return file_id

    except Exception as e:
        print(f"Failed to upload to GDrive: {e}")
        return None

