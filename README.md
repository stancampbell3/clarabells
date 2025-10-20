# Clara — Minimal FastAPI service

This repository contains a minimal FastAPI app with a single health check endpoint.

Quick start (install dev dependencies and run tests):

```bash
cd /home/stanc/Development/clara
python -m pip install -r requirements-dev.txt
pytest -q
```

Run the server locally:

```bash
cd /home/stanc/Development/clara
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health endpoint:
GET /health -> { "status": "ok" }

