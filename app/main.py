from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import os
import tempfile
from typing import Optional

from app.tts import ChatterboxTTS

app = FastAPI(title="Clara API", version="0.1.0")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bearer token authentication
bearer_scheme = HTTPBearer()

# Dummy token for illustration; in practice, use a secure method to manage tokens
FAKE_TOKEN = "mysecrettoken"


class SpeakRequest(BaseModel):
    text: Optional[str] = None


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

    # If text provided, synthesize to temp wav and stream it
    if payload.text:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_path = tmp.name
        tmp.close()
        try:
            ChatterboxTTS.synthesize_to_wav(payload.text, tmp_path)
            return StreamingResponse(_file_streamer(tmp_path, remove_after=True), media_type="audio/wav")
        except Exception:
            logger.exception("TTS synthesis failed")
            # ensure cleanup
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            raise HTTPException(status_code=500, detail="TTS synthesis failed")

    # No text: attempt to stream an existing wav file from ./audio
    audio_dir = "./audio"
    if os.path.isdir(audio_dir):
        for fn in os.listdir(audio_dir):
            if fn.lower().endswith('.wav'):
                file_path = os.path.join(audio_dir, fn)
                logger.info("Streaming existing audio file: %s", file_path)
                return StreamingResponse(_file_streamer(file_path, remove_after=False), media_type="audio/wav")

    logger.warning("No text provided and no .wav files found in %s", audio_dir)
    raise HTTPException(status_code=404, detail="No audio available")
