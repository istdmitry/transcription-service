import requests
import sys
import os
import argparse
import json
from datetime import datetime

# Configuration
API_URL = os.getenv("TRANSCRIPTION_API_URL", "https://service.8hats.ai")
# Fallback if domain not propagated yet:
# API_URL = "https://enchanting-insight-production.up.railway.app"
API_KEY = os.getenv("TRANSCRIPTION_API_KEY")

def get_headers():
    if not API_KEY:
        print("Error: TRANSCRIPTION_API_KEY environment variable is not set.")
        print("Please copy it from your Dashboard and run: set TRANSCRIPTION_API_KEY=your_key")
        sys.exit(1)
    return {'X-API-Key': API_KEY}

def list_transcripts(date_filter=None):
    try:
        res = requests.get(f"{API_URL}/transcripts/", headers=get_headers())
        if res.status_code == 200:
            transcripts = res.json()
            
            # Filter by date if requested
            if date_filter:
                filtered = []
                target_date = date_filter
                if target_date == "today":
                    target_date = datetime.now().strftime("%Y-%m-%d")
                
                print(f"Filtering for date: {target_date}")
                
                for t in transcripts:
                    # Created_at format: 2023-12-11T12:34:56.789Z (ISO)
                    if t.get('created_at', '').startswith(target_date):
                        filtered.append(t)
                transcripts = filtered

            if not transcripts:
                print("No transcripts found.")
                return

            print(f"{'ID':<5} {'Date':<12} {'Status':<12} {'Filename'}")
            print("-" * 60)
            for t in transcripts:
                date_str = t.get('created_at', '')[:10]
                filename = t.get('filename', 'Unknown')
                print(f"{t['id']:<5} {date_str:<12} {t['status']:<12} {filename}")
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

def get_server_logs(lines):
    try:
        res = requests.get(f"{API_URL}/logs/?lines={lines}", headers=get_headers())
        if res.status_code == 200:
            logs = res.json()
            print(f"--- Server Logs (Last {lines} lines) ---")
            for line in logs:
                print(line)
        else:
            print(f"Error fetching logs: {res.text}")
    except Exception as e:
        print(f"Connection error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Transcription Service CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List
    list_parser = subparsers.add_parser("list", help="List all transcripts")
    list_parser.add_argument("--date", help="Filter by date (YYYY-MM-DD)")
    list_parser.add_argument("--today", action="store_true", help="Filter for today only")

    # Get
    get_parser = subparsers.add_parser("get", help="Get transcript text")
    get_parser.add_argument("id", help="Transcript ID")

    # Upload
    upload_parser = subparsers.add_parser("upload", help="Upload a new file")
    upload_parser.add_argument("file", help="Path to audio file")

    # Logs
    logs_parser = subparsers.add_parser("logs", help="Get server logs")
    logs_parser.add_argument("--lines", type=int, default=50, help="Number of lines to retrieve")

    args = parser.parse_args()

    if getattr(args, 'command', None) == "list":
        filter_date = args.date
        if args.today:
            filter_date = "today"
        list_transcripts(filter_date)
    elif getattr(args, 'command', None) == "get":
        get_transcript(args.id)
    elif getattr(args, 'command', None) == "upload":
        upload_file(args.file)
    elif getattr(args, 'command', None) == "logs":
        get_server_logs(args.lines)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
