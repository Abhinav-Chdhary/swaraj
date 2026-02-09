# Swaraj — Hindi Voice-to-Text

Chrome extension that records Hindi speech and transcribes it to Devanagari text using [AI4Bharat IndicConformer](https://huggingface.co/ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large) running locally.

## Prerequisites

- [conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- ffmpeg (`brew install ffmpeg` on macOS)
- Google Chrome

## Backend Setup

```bash
cd backend
bash setup.sh
conda activate swaraj
uvicorn main:app --port 8000
```

The first run downloads the IndicConformer Hindi model (~120M params) from HuggingFace. This is cached for subsequent runs.

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
│ Records mic audio    │  audio/webm  │ IndicConformer model  │
│ (webm/opus)          │<─────────────│ Hindi CTC decoder     │
│                      │  JSON {text} │ Devanagari output     │
└──────────────────────┘              └──────────────────────┘
```

## Notes

- The popup closes if you click outside it (Chrome limitation) — any in-progress recording is lost
- Audio is processed entirely on your local machine; nothing is sent to external servers
- Uses AI4Bharat's IndicConformer (hybrid CTC/RNNT) for accurate Devanagari Hindi transcription
