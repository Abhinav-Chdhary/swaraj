import os
import subprocess
import tempfile
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

model = None
device = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, device
    import nemo.collections.asr as nemo_asr

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading IndicConformer Hindi model on {device}...")
    model = nemo_asr.models.ASRModel.from_pretrained(
        "ai4bharat/indicconformer_stt_hi_hybrid_ctc_rnnt_large"
    )
    model.freeze()
    model = model.to(device)
    print("Model loaded successfully.")
    yield
    model = None


app = FastAPI(title="Swaraj — Hindi Voice-to-Text", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or "audio.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    wav_path = tmp_path + ".wav"
    try:
        # Convert uploaded audio to 16kHz mono WAV using ffmpeg
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", tmp_path,
                "-ar", "16000", "-ac", "1", "-f", "wav", wav_path,
            ],
            check=True,
            capture_output=True,
        )

        # Transcribe with CTC decoder
        model.cur_decoder = "ctc"
        transcriptions = model.transcribe(
            [wav_path], batch_size=1, logprobs=False, language_id="hi"
        )

        # NeMo returns a list of strings (or list of Hypothesis objects)
        if isinstance(transcriptions, tuple):
            transcriptions = transcriptions[0]

        text = transcriptions[0] if transcriptions else ""
        if hasattr(text, "text"):
            text = text.text

        # Get audio duration via ffprobe
        duration = 0.0
        try:
            probe = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    wav_path,
                ],
                capture_output=True, text=True,
            )
            duration = round(float(probe.stdout.strip()), 2)
        except (ValueError, FileNotFoundError):
            pass

        return {"text": text, "duration": duration}
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        if os.path.exists(wav_path):
            os.unlink(wav_path)
