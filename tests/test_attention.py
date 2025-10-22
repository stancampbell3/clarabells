from fastapi.testclient import TestClient
from app.main import app


def test_attention_notification_and_audio():
    """Connect to websocket, post a speak request and verify notification and audio retrieval."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws/notify") as ws:
            headers = {"Authorization": "Bearer mysecrettoken"}
            # Trigger synthesis which will broadcast the GUID
            r = client.post("/clara/api/v1/speak", headers=headers, json={"text": "notify test"})
            assert r.status_code == 200

            # Receive the GUID from websocket
            guid = ws.receive_text()
            assert isinstance(guid, str) and guid

            # Retrieve the audio via the audio endpoint
            r2 = client.get(f"/audio/{guid}")
            assert r2.status_code == 200
            assert r2.content.startswith(b"RIFF")

