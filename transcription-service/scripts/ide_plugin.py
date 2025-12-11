import requests
import sys
import os
import argparse
import json

# Configuration
API_URL = os.getenv("TRANSCRIPTION_API_URL", "https://service.8hats.ai") # Production Default -- or update based on real domain
# Fallback if domain not propagated yet:
# API_URL = "https://transcription-service-production-6161.up.railway.app" 

API_KEY = os.getenv("TRANSCRIPTION_API_KEY")

def get_headers():
    if not API_KEY:
        print("Error: TRANSCRIPTION_API_KEY environment variable is not set.")
        print("Please copy it from your Dashboard and run: set TRANSCRIPTION_API_KEY=your_key")
        sys.exit(1)
    return {'X-API-Key': API_KEY}

def list_transcripts():
    try:
        res = requests.get(f"{API_URL}/transcripts/", headers=get_headers())
        if res.status_code == 200:
            transcripts = res.json()
            print(f"{'ID':<5} {'Status':<12} {'Filename'}")
            print("-" * 40)
            for t in transcripts:
                print(f"{t['id']:<5} {t['status']:<12} {t['filename']}")
        else:
            print(f"Error listing transcripts: {res.text}")
    except Exception as e:
        print(f"Connection error: {e}")

def get_transcript(tid):
    try:
        res = requests.get(f"{API_URL}/transcripts/{tid}", headers=get_headers())
        if res.status_code == 200:
            data = res.json()
            if data['status'] == 'completed':
                print(data['transcript_text'])
            else:
                print(f"[Transcript not ready. Status: {data['status']}]")
                if data.get('error_message'):
                    print(f"Error: {data['error_message']}")
        else:
            print(f"Error fetching transcript {tid}: {res.text}")
    except Exception as e:
        print(f"Connection error: {e}")

def upload_file(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found")
        return

    print(f"Uploading {file_path}...")
    with open(file_path, 'rb') as f:
        files = {'file': f}
        try:
            res = requests.post(f"{API_URL}/transcripts/", headers=get_headers(), files=files)
            if res.status_code == 200:
                data = res.json()
                print(f"Success! Uploaded ID: {data['id']}")
            else:
                print(f"Error uploading: {res.text}")
        except Exception as e:
            print(f"Request failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Transcription Service CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List
    subparsers.add_parser("list", help="List all transcripts")

    # Get
    get_parser = subparsers.add_parser("get", help="Get transcript text")
    get_parser.add_argument("id", help="Transcript ID")

    # Upload
    upload_parser = subparsers.add_parser("upload", help="Upload a new file")
    upload_parser.add_argument("file", help="Path to audio file")

    args = parser.parse_args()

    if args.command == "list":
        list_transcripts()
    elif args.command == "get":
        get_transcript(args.id)
    elif args.command == "upload":
        upload_file(args.file)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
