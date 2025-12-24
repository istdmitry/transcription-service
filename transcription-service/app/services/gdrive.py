import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

from app.core.crypto import decrypt_data

def extract_service_account_email(json_creds: str):
    try:
        info = json.loads(json_creds)
        return info.get("client_email")
    except Exception:
        return None

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

def get_drive_service_from_json(json_creds: str):
    """
    Authenticates with Google Drive API using raw Service Account JSON content.
    """
    if not json_creds:
        return None, "missing_json"

    try:
        info = json.loads(json_creds)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/drive.file']
        )
        service = build('drive', 'v3', credentials=creds)
        return service, None
    except Exception as e:
        print(f"Error authenticating GDrive from JSON: {e}")
        return None, str(e)

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

def test_drive_upload(json_creds: str, folder_id: str, filename: str, content: str):
    """
    Attempts to upload a test file using raw JSON credentials and folder.
    Returns (ok: bool, error_message: Optional[str], file_id: Optional[str], service_account_email: Optional[str])
    """
    service, auth_err = get_drive_service_from_json(json_creds)
    if not service:
        return False, f"Invalid JSON key or auth error: {auth_err}", None, None

    sa_email = extract_service_account_email(json_creds)

    if not folder_id:
        return False, "Missing folder ID", None, sa_email

    try:
        file_metadata = {
            'name': filename,
            'parents': [folder_id],
            'mimeType': 'text/plain'
        }
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
        return True, None, file_id, sa_email
    except Exception as e:
        return False, str(e), None, sa_email

def test_drive_upload_encrypted(encrypted_creds: str, folder_id: str, filename: str, content: str):
    """
    Attempts to upload a test file using encrypted JSON credentials and folder.
    Returns (ok, error_message, file_id, service_account_email)
    """
    if not encrypted_creds:
        return False, "Missing credentials", None, None

    json_creds = decrypt_data(encrypted_creds)
    if not json_creds:
        return False, "Invalid JSON key or auth error", None, None

    sa_email = extract_service_account_email(json_creds)
    service = get_drive_service(encrypted_creds)
    if not service:
        return False, "Invalid JSON key or auth error", None, sa_email

    if not folder_id:
        return False, "Missing folder ID", None, sa_email

    try:
        file_metadata = {
            'name': filename,
            'parents': [folder_id],
            'mimeType': 'text/plain'
        }
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
        return True, None, file_id, sa_email
    except Exception as e:
        return False, str(e), None, sa_email

