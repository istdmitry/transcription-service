import requests
import sys
import os

# Usage examples:
# python transcribe.py /path/to/audio.mp3
# Or called from Cursor extension

API_URL = "http://localhost:8000/transcripts/" # or production URL
API_KEY = os.getenv("TRANSCRIPTION_API_KEY")

def upload_file(file_path):
    if not API_KEY:
        print("Error: TRANSCRIPTION_API_KEY env var not set")
        return

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return

    print(f"Uploading {file_path}...")
    
    with open(file_path, 'rb') as f:
        headers = {'X-API-Key': API_KEY}
        files = {'file': f}
        try:
            response = requests.post(API_URL, headers=headers, files=files)
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Transcript ID: {data['id']}")
                print(f"Status: {data['status']}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <file_path>")
    else:
        upload_file(sys.argv[1])
