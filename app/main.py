from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
import logging
import os

app = FastAPI(title="Clara API", version="0.1.0")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bearer token authentication
bearer_scheme = HTTPBearer()

# Dummy token for illustration; in practice, use a secure method to manage tokens
FAKE_TOKEN = "mysecrettoken"


@app.get("/health")
async def health():
    """
    Health check endpoint.
    Returns JSON { "status": "ok" } with HTTP 200.
    """
    return {"status": "ok"}


@app.post("/clara/api/v1/speak")
async def speak(
    auth: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """
    Endpoint to process speech requests.
    Authenticates using a bearer token and streams back an audio response.
    """
    # Token verification (in practice, verify the token properly)
    if auth.credentials != FAKE_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    logger.info("Received request with token: %s", auth.credentials)

    # Find the first mp3 file in the audio directory
    audio_path = "./audio"
    for file in os.listdir(audio_path):
        if file.endswith(".mp3"):
            file_path = os.path.join(audio_path, file)
            logger.info("Streaming audio file: %s", file_path)
            return StreamingResponse(open(file_path, "rb"), media_type="audio/mpeg")

    logger.warning("No audio files found in directory: %s", audio_path)
    return {"error": "No audio files found"}, 404
