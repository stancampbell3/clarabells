from audioread import audio_open
from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
from contextlib import asynccontextmanager
import asyncio
import logging
import os
import time
from typing import Optional, List, Dict, Any

from app.tts import ChatterboxTTS
from app.cerebrum_client import CerebrumClient
from app.config import config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting Clara server on {config.host}:{config.port}")
    logger.info(f"Audio cache TTL: {config.audio_cache_ttl_seconds}s")
    logger.info(f"Audio cache cleanup interval: {config.audio_cache_cleanup_interval_seconds}s")

    cleanup_task = None
    if config.audio_cache_ttl_seconds > 0:
        cleanup_task = asyncio.create_task(cleanup_expired_audio_files())
        logger.info("Audio cleanup background task started")
    else:
        logger.info("Audio cleanup disabled (TTL = 0)")

    yield

    # Shutdown
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    logger.info("Clara server shutting down")


app = FastAPI(title="Clara API", version="0.1.0", lifespan=lifespan)

# Audio cache directory
audio_cache_dir = Path("audio")
audio_cache_dir.mkdir(exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bearer token authentication
bearer_scheme = HTTPBearer()


# Initialize TTS with the voice sample for cloning (optional)
sample_path = "./app/assets/clara_sample.wav"
if not os.path.exists(sample_path):
    logger.warning("Voice sample not found at %s; continuing without cloned voice sample", sample_path)

class SpeakRequest(BaseModel):
    text: Optional[str] = None

class PromptRequest(BaseModel):
    """Request model for /prompt endpoint."""
    query: str
    facts: Optional[List[str]] = None
    rules: Optional[str] = None
    use_clips: bool = True

class PromptResponse(BaseModel):
    """Response model for /prompt endpoint."""
    query: str
    response: str
    reasoning: Optional[Dict[str, Any]] = None
    clips_output: Optional[str] = None

# List to hold connected WebSocket clients
connected_clients: List[WebSocket] = []

# Global CLIPS session for logic-informed responses
_cerebrum_client: Optional[CerebrumClient] = None
_cerebrum_session = None

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
    Otherwise stream the first .wav found in `./audio` if available, or synthesize a short fallback.
    """
    # Token verification (in practice, verify the token properly)
    if auth.credentials != config.bearer_token:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    logger.info("Received /speak request. text present=%s", bool(payload.text))
    if not payload.text:
        fallback_path = Path("./app/assets/masters_of_the_earth.wav")
        return FileResponse(fallback_path, media_type="audio/wav")
    else:
        # Generate a GUID for the text (simple hash for caching; use actual hash if needed)
        text_hash = str(hash(payload.text))
        cached_file = audio_cache_dir / f"{text_hash}.wav"

        if not cached_file.exists():
            try:
                ChatterboxTTS.synthesize_to_wav(payload.text, str(cached_file))
            except Exception as e:
                logger.error("TTS synthesis failed: %s. Falling back to masters_of_the_earth.wav", e)
                # Fall back to masters_of_the_earth.wav
                fallback_file = Path("./app/assets/masters_of_the_earth.wav")
                if fallback_file.exists():
                    logger.info("Using fallback audio: masters_of_the_earth.wav")
                    return FileResponse(fallback_file, media_type="audio/wav")
                else:
                    logger.error("Fallback file not found: %s", fallback_file)
                    raise HTTPException(status_code=500, detail="TTS synthesis failed and fallback audio not available")

        # Broadcast the new audio GUID to connected WebSocket clients
        # Await the broadcast so tests can receive notifications synchronously
        await broadcast_message(text_hash)
        # Include the GUID in a response header so external clients can reference it
        headers = {"X-Clara-Audio-GUID": text_hash}
        return FileResponse(cached_file, media_type="audio/wav", headers=headers)

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
            # Keep the connection alive; receive_text will block until client sends something
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        try:
            connected_clients.remove(websocket)
        except ValueError:
            pass

async def broadcast_message(message: str):
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            pass


async def _get_cerebrum_session():
    """Get or create a persistent CLIPS session."""
    global _cerebrum_client, _cerebrum_session

    try:
        if _cerebrum_client is None:
            cerebrum_url = os.getenv("CEREBRUM_API_URL", "http://localhost:8080")
            _cerebrum_client = CerebrumClient(base_url=cerebrum_url)

        if _cerebrum_session is None:
            _cerebrum_session = await _cerebrum_client.create_session(user_id="clara-voice")
            logger.info(f"Created CLIPS session: {_cerebrum_session.session_id}")

        return _cerebrum_session
    except Exception as e:
        logger.error(f"Failed to get CLIPS session: {e}")
        raise


@app.post("/clara/api/v1/prompt", response_model=PromptResponse)
async def prompt(
    payload: PromptRequest,
    auth: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """
    POST /clara/api/v1/prompt

    Accept a natural language query and optionally facts/rules.
    Use the CLIPS expert system to reason about the query and provide a logic-informed response.

    Request body:
    {
        "query": "What is the capital of France?",
        "facts": ["(country france capital paris)"],
        "rules": "(defrule find-capital (country ?name capital ?city) => ...)",
        "use_clips": true
    }
    """
    if auth.credentials != config.bearer_token:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    logger.info(f"Received /prompt request: {payload.query}")

    try:
        session = await _get_cerebrum_session()

        # Build CLIPS script with optional facts and rules
        clips_script_parts = []

        # Add user-provided rules
        if payload.rules:
            clips_script_parts.append(payload.rules)

        # Add user-provided facts
        if payload.facts:
            for fact in payload.facts:
                if not fact.startswith("("):
                    fact = f"({fact})"
                clips_script_parts.append(f"(assert {fact})")

        # Add a query to find relevant information
        # This is a simple approach - assert the query as a fact to trigger rules
        clips_script_parts.append(f"(assert (query \"{payload.query}\"))")

        # Run inference
        clips_script_parts.append("(run)")

        clips_script = "\n".join(clips_script_parts)

        logger.debug(f"CLIPS script:\n{clips_script}")

        clips_result = await session.eval(clips_script)
        clips_output = clips_result.get("stdout", "")

        logger.info(f"CLIPS evaluation completed. Output length: {len(clips_output)}")

        # Parse the query context for reasoning explanation
        reasoning = {
            "approach": "CLIPS expert system",
            "session_id": session.session_id,
            "has_facts": bool(payload.facts),
            "has_rules": bool(payload.rules),
            "clips_output_length": len(clips_output)
        }

        # Generate a response based on CLIPS output
        if clips_output.strip():
            response = f"Based on the expert system reasoning: {clips_output[:200]}"
            if len(clips_output) > 200:
                response += "..."
        else:
            response = "The expert system could not derive a conclusive answer based on the provided facts and rules."

        return PromptResponse(
            query=payload.query,
            response=response,
            reasoning=reasoning,
            clips_output=clips_output if len(clips_output) < 1000 else clips_output[:1000] + "..."
        )

    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process prompt: {str(e)}"
        )


async def cleanup_expired_audio_files():
    """Background task to periodically clean up expired audio files."""
    while True:
        try:
            await asyncio.sleep(config.audio_cache_cleanup_interval_seconds)

            if config.audio_cache_ttl_seconds <= 0:
                # TTL disabled
                continue

            now = time.time()
            ttl = config.audio_cache_ttl_seconds
            deleted_count = 0

            for audio_file in audio_cache_dir.glob("*.wav"):
                try:
                    # Skip protected files in assets directory
                    if "assets" in str(audio_file):
                        continue

                    # Check file age
                    file_age = now - audio_file.stat().st_mtime
                    if file_age > ttl:
                        audio_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted expired audio file: {audio_file.name} (age: {file_age:.0f}s)")
                except Exception as e:
                    logger.error(f"Failed to delete {audio_file}: {e}")

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired audio file(s)")

        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")

