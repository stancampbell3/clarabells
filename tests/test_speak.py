from pathlib import Path
from fastapi.testclient import TestClient
import shutil
from app.main import app
from app.tts import ChatterboxTTS

CLIENT = TestClient(app)
AUDIO_DIR = Path("./audio")
FALLBACK_WAV = AUDIO_DIR / "fallback.wav"


def setup_module(module):
    # Ensure audio dir exists (used by fallback test)
    AUDIO_DIR.mkdir(exist_ok=True)


def teardown_module(module):
    # Clean up the audio dir created for tests
    try:
        if FALLBACK_WAV.exists():
            FALLBACK_WAV.unlink()
        if AUDIO_DIR.exists():
            AUDIO_DIR.rmdir()
    except Exception:
        shutil.rmtree(AUDIO_DIR, ignore_errors=True)


def test_speak_tts_authorized():
    headers = {"Authorization": "Bearer mysecrettoken"}
    payload = {"text": "Hello Clara, this is a TTS test."}
    r = CLIENT.post("/clara/api/v1/speak", headers=headers, json=payload)
    assert r.status_code == 200
    # WAV files start with ASCII 'RIFF'
    assert r.content.startswith(b"RIFF")


def test_speak_fallback_wav():
    # create a fallback wav using the ChatterboxTTS
    ChatterboxTTS.synthesize_to_wav("fallback audio", str(FALLBACK_WAV))

    headers = {"Authorization": "Bearer mysecrettoken"}
    # POST without text to trigger fallback
    r = CLIENT.post("/clara/api/v1/speak", headers=headers, json={})
    assert r.status_code == 200
    assert r.content.startswith(b"RIFF")


def test_speak_wrong_token():
    headers = {"Authorization": "Bearer wrongtoken"}
    r = CLIENT.post("/clara/api/v1/speak", headers=headers, json={})
    assert r.status_code == 403


def test_speak_no_token():
    r = CLIENT.post("/clara/api/v1/speak", json={})
    # Missing bearer should produce 401/403 from security dependency
    assert r.status_code in (401, 403)
