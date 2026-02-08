import os
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel

model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print("Loading faster-whisper 'base' model (int8)...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    print("Model loaded successfully.")
    yield
    model = None


app = FastAPI(title="Swaraj - Hindi Voice-to-Text", lifespan=lifespan)

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

    try:
        segments_iter, info = model.transcribe(
            tmp_path,
            language="hi",
            vad_filter=True,
        )

        segments = []
        full_text_parts = []
        for segment in segments_iter:
            segments.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip(),
            })
            full_text_parts.append(segment.text.strip())

        return {
            "text": " ".join(full_text_parts),
            "segments": segments,
            "duration": round(info.duration, 2),
        }
    finally:
        os.unlink(tmp_path)
