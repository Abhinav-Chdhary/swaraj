const BACKEND_URL = "http://localhost:8000";

const recordBtn = document.getElementById("recordBtn");
const btnText = document.getElementById("btnText");
const timerEl = document.getElementById("timer");
const statusEl = document.getElementById("status");
const resultArea = document.getElementById("resultArea");
const transcriptionEl = document.getElementById("transcription");
const copyBtn = document.getElementById("copyBtn");
const errorEl = document.getElementById("error");

let mediaRecorder = null;
let audioChunks = [];
let timerInterval = null;
let startTime = null;

recordBtn.addEventListener("click", toggleRecording);
copyBtn.addEventListener("click", copyText);

async function toggleRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    stopRecording();
  } else {
    await startRecording();
  }
}

async function startRecording() {
  hideError();

  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        noiseSuppression: true,
        echoCancellation: true,
      },
    });
  } catch (err) {
    showError("Microphone access denied. Please allow microphone permission.");
    return;
  }

  audioChunks = [];

  const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
    ? "audio/webm;codecs=opus"
    : "audio/webm";

  mediaRecorder = new MediaRecorder(stream, { mimeType });

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) {
      audioChunks.push(e.data);
    }
  };

  mediaRecorder.onstop = () => {
    stream.getTracks().forEach((t) => t.stop());
    clearInterval(timerInterval);
    handleRecordingComplete();
  };

  mediaRecorder.start();

  recordBtn.classList.add("recording");
  btnText.textContent = "Stop Recording";
  timerEl.classList.remove("hidden");
  startTime = Date.now();
  updateTimer();
  timerInterval = setInterval(updateTimer, 1000);
  setStatus("");
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
  }
}

function updateTimer() {
  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  const mins = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const secs = String(elapsed % 60).padStart(2, "0");
  timerEl.textContent = `${mins}:${secs}`;
}

async function handleRecordingComplete() {
  recordBtn.classList.remove("recording");
  btnText.textContent = "Start Recording";
  timerEl.classList.add("hidden");

  const blob = new Blob(audioChunks, { type: mediaRecorder.mimeType });

  if (blob.size < 1000) {
    showError("Recording too short. Please try again.");
    return;
  }

  setStatus("Transcribing...");

  const formData = new FormData();
  formData.append("file", blob, "recording.webm");

  try {
    const response = await fetch(`${BACKEND_URL}/transcribe`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => null);
      throw new Error(errData?.detail || `Server error (${response.status})`);
    }

    const data = await response.json();

    if (!data.text || data.text.trim() === "") {
      setStatus("No speech detected. Try again.");
      return;
    }

    transcriptionEl.textContent = data.text;
    resultArea.classList.remove("hidden");
    setStatus(`Done — ${data.duration}s of audio`);
  } catch (err) {
    if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
      showError("Cannot reach backend. Is the server running on localhost:8000?");
    } else {
      showError(err.message);
    }
  }
}

async function copyText() {
  const text = transcriptionEl.textContent;
  if (!text) return;

  try {
    await navigator.clipboard.writeText(text);
    copyBtn.textContent = "Copied!";
    setTimeout(() => {
      copyBtn.textContent = "Copy Text";
    }, 1500);
  } catch {
    showError("Failed to copy. Try selecting the text manually.");
  }
}

function setStatus(msg) {
  statusEl.textContent = msg;
}

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove("hidden");
}

function hideError() {
  errorEl.classList.add("hidden");
  errorEl.textContent = "";
}
