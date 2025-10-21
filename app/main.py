from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import asyncio
import logging
import os
import tempfile
import uuid
from typing import Optional, List

from app.tts import ChatterboxTTS

app = FastAPI(title="Clara API", version="0.1.0")

# Audio cache directory
audio_cache_dir = Path("audio")
audio_cache_dir.mkdir(exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bearer token authentication
bearer_scheme = HTTPBearer()

# Dummy token for illustration; in practice, use a secure method to manage tokens
FAKE_TOKEN = "mysecrettoken"

# Initialize TTS with the voice sample for cloning
sample_path = "./app/assets/clara_sample.wav"
if not os.path.exists(sample_path):
    raise RuntimeError(f"Voice sample not found at {sample_path}")
tts_engine = ChatterboxTTS()  # our TTS wrapper instance, we manage the voice internally

class SpeakRequest(BaseModel):
    text: Optional[str] = None

# List to hold connected WebSocket clients
connected_clients: List[WebSocket] = []

@app.get("/health")
async def health():
    """
    Health check endpoint.
    Returns JSON { "status": "ok" } with HTTP 200.
    """
    return {"status": "ok"}

def _file_streamer(path: str, remove_after: bool = False):
    """Return a generator that yields file chunks and optionally removes the file after streaming."""
    def _gen():
        try:
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    yield chunk
        finally:
            if remove_after:
                try:
                    os.remove(path)
                except Exception:
                    logger.exception("Failed to remove temporary file: %s", path)
    return _gen()

@app.post("/clara/api/v1/speak")
async def speak(payload: SpeakRequest, auth: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    POST /clara/api/v1/speak
    Accept JSON payload { "text": "..." }.
    If `text` is provided, synthesize a WAV via ChatterboxTTS and stream it back.
    Otherwise stream the first .wav found in `./audio` if available.
    """
    # Token verification (in practice, verify the token properly)
    if auth.credentials != FAKE_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    logger.info("Received /speak request. text present=%s", bool(payload.text))
    if not payload.text:
        raise HTTPException(status_code=400, detail="No text provided for synthesis")
    else:
        # Generate a GUID for the text (simple hash for caching; use actual hash if needed)
        text_hash = str(hash(payload.text))
        cached_file = audio_cache_dir / f"{text_hash}.wav"

        if not cached_file.exists():
            ChatterboxTTS.synthesize_to_wav(payload.text, str(cached_file))

        # Broadcast the new audio GUID to connected WebSocket clients
        asyncio.create_task(broadcast_message(text_hash))
        return FileResponse(cached_file, media_type="audio/wav")

@app.get("/audio/{guid}")
async def get_audio(guid: str):
    cached_file = audio_cache_dir / f"{guid}.wav"
    if not cached_file.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(cached_file, media_type="audio/wav")

@app.websocket("/ws/notify")
async def websocket_notify(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # Keep the connection alive; no need to receive messages from clients
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        connected_clients.remove(websocket)

async def broadcast_message(message: str):
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            pass