# Transcription Service CLI Guide

Use this script to upload files and retrieve transcripts directly from your Cursor terminal.

## 1. Setup

### Install Requirements
You need the `requests` library to talk to the API.
```bash
pip install requests
```

### Set API Key
1. Go to your Web Dashboard.
2. Copy the **API Key** from the top right.
3. Set it in your terminal:

**Windows (PowerShell):**
```powershell
$env:TRANSCRIPTION_API_KEY="your-api-key-here"
```

**Mac/Linux:**
```bash
export TRANSCRIPTION_API_KEY="your-api-key-here"
```

## 2. Usage

### List All Transcripts
Shows IDs, Status, and Filenames.
```bash
python scripts/ide_plugin.py list
```

### 🆕 Filter by Date
List only today's transcripts:
```bash
python scripts/ide_plugin.py list --today
```

List for a specific date:
```bash
python scripts/ide_plugin.py list --date 2023-12-11
```

### Get Transcript Text
Retrieves the full text for a specific ID.
```bash
python scripts/ide_plugin.py get <ID>
```
*Example: `python scripts/ide_plugin.py get 15`*

### Upload a File
Uploads an audio/video file for processing.
```bash
python scripts/ide_plugin.py upload "path/to/meeting.mp3"
```

## Cursor AI Tip
You can paste this file into Cursor's Chat to teach it how to use the tool for you!
Just type: *"Read CLI_GUIDE.md and use the script to list my transcripts."*
