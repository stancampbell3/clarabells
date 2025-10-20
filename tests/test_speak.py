from pathlib import Path
from fastapi.testclient import TestClient
import shutil
from app.main import app

CLIENT = TestClient(app)
AUDIO_DIR = Path("./audio")
SAMPLE_FILE = AUDIO_DIR / "sample.mp3"
FAKE_BYTES = b"FAKE_MP3_CONTENT"


def setup_module(module):
    # Ensure audio dir exists and contains a sample mp3
    AUDIO_DIR.mkdir(exist_ok=True)
    with open(SAMPLE_FILE, "wb") as f:
        f.write(FAKE_BYTES)


def teardown_module(module):
    # Clean up the audio dir created for tests
    try:
        if SAMPLE_FILE.exists():
            SAMPLE_FILE.unlink()
        if AUDIO_DIR.exists():
            AUDIO_DIR.rmdir()
    except Exception:
        # best-effort cleanup
        shutil.rmtree(AUDIO_DIR, ignore_errors=True)


def test_speak_authorized():
    headers = {"Authorization": "Bearer mysecrettoken"}
    r = CLIENT.post("/clara/api/v1/speak", headers=headers)
    assert r.status_code == 200
    assert r.content == FAKE_BYTES


def test_speak_wrong_token():
    headers = {"Authorization": "Bearer wrongtoken"}
    r = CLIENT.post("/clara/api/v1/speak", headers=headers)
    assert r.status_code == 403


def test_speak_no_token():
    r = CLIENT.post("/clara/api/v1/speak")
    # Missing bearer should produce 401/403 from security dependency
    assert r.status_code in (401, 403)
