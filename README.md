# Swaraj — Hindi Voice-to-Text

Chrome extension that records Hindi speech and transcribes it to text using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) running locally.

## Prerequisites

- Python 3.9+
- Google Chrome
- ffmpeg (`brew install ffmpeg` on macOS)

## Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

The first run downloads the `base` whisper model (~150 MB) from HuggingFace. This is cached for subsequent runs.

Verify the server is running:

```bash
curl http://localhost:8000/health
```

## Extension Setup

1. Open `chrome://extensions/` in Chrome
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** and select the `extension/` folder
4. The Swaraj icon (orange circle) appears in your toolbar

## Usage

1. Make sure the backend server is running
2. Click the Swaraj extension icon
3. Click **Start Recording** and speak in Hindi
4. Click **Stop Recording** when done
5. Wait for the transcription to appear
6. Click **Copy Text** to copy to clipboard

## Architecture

```
Chrome Extension (popup)             Local Python Backend
┌──────────────────────┐   HTTP POST   ┌──────────────────────┐
│ MediaRecorder API    │─────────────>│ FastAPI /transcribe   │
│ Records mic audio    │  audio/webm  │ faster-whisper model  │
│ (webm/opus)          │<─────────────│ Hindi (lang="hi")     │
│                      │  JSON {text} │ "base" model, int8    │
└──────────────────────┘              └──────────────────────┘
```

## Notes

- The popup closes if you click outside it (Chrome limitation) — any in-progress recording is lost
- Audio is processed entirely on your local machine; nothing is sent to external servers
- Uses `int8` quantization for efficient CPU inference on macOS
