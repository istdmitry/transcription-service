# Transcription Service - User Guide

Welcome to the Transcription Service! This guide will help you register, upload files, and use our CLI tools.

## 1. Registration

### Web Registration
1. Visit the web dashboard at [https://enchanting-insight-production.up.railway.app](https://enchanting-insight-production.up.railway.app).
2. Click on **Register**.
3. Enter your **Email** and **Password**.
4. Once registered, you will be logged in and can access your **API Key** from the dashboard. You will need this key for the CLI.

### Telegram Registration (Optional)
You can also use the service via Telegram.
1. Start a chat with the bot [@EightHatsAI_bot](https://t.me/EightHatsAI_bot).
2. Send `/start`.
3. Click the **Link Account** button and share your contact to link your Telegram account with your web account.
   - *Note: If you don't link, a guest account might be created for you, but you won't see those files on the web dashboard unless the email matches.*

## 2. Sending Audio/Video for Processing

### Method A: Web Dashboard
1. Log in to the dashboard.
2. Click the **Upload** button.
3. Select an audio or video file from your computer.
4. The file will be uploaded and processing will start automatically.
5. You can view the status in the transcripts list.

### Method B: Telegram Bot
1. Open the chat with [@EightHatsAI_bot](https://t.me/EightHatsAI_bot).
2. Simply **send an audio or video file** (or forward a voice message) to the chat.
   - The bot will download the file and start transcription.
3. You will receive a confirmation message.
4. Once finished, you can view the result on the web dashboard (if accounts are linked).

## 3. Using the CLI (Command Line Interface)

We provide a Python script to interact with the service directly from your terminal.

### Setup
1. Ensure you have Python installed.
2. Set your API Key as an environment variable:
   ```bash
   # Windows (CMD)
   set TRANSCRIPTION_API_KEY=your_api_key_here

   # PowerShell
   $env:TRANSCRIPTION_API_KEY="your_api_key_here"
   
   # Mac/Linux
   export TRANSCRIPTION_API_KEY=your_api_key_here
   ```
   *(You can find your API Key in the web dashboard)*

### Commands

The CLI script is located at `scripts/ide_plugin.py`. You can run it as follows:

**1. Upload a File**
```bash
python scripts/ide_plugin.py upload "path/to/audio.mp3"
```

**2. List Transcripts**
```bash
python scripts/ide_plugin.py list
```
*Options:*
- `--date YYYY-MM-DD`: Filter by specific date.
- `--today`: Show only today's transcripts.

**3. Get Transcript Text**
```bash
python scripts/ide_plugin.py get <TRANSCRIPT_ID>
```

**4. View Server Logs**
```bash
python scripts/ide_plugin.py logs --lines 50
```
