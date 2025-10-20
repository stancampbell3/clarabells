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


# Docker

This project includes a `Dockerfile` and `docker-compose.yml` for running the app in a container.

Important: model storage should be mounted from the host to avoid filling the container image/layers. The compose setup mounts `./models` on the host into `/models` inside the container.

Quick Docker commands:

```bash
# create a local models dir (if you plan to persist models on host)
mkdir -p ./models

# build the image (first time or after changes)
docker compose build

# run in foreground
docker compose up

# run detached
docker compose up -d

# stop and remove containers
docker compose down
```

Notes:
- Building the image will install the libraries in `requirements.txt`, which may include heavy ML packages (PyTorch, Transformers). Building may take a long time and require sufficient disk space.
- If you want a faster dev iteration loop, consider using a lightweight `requirements-dev.txt` for building the image and mounting source or using a multi-stage approach to avoid installing large model libraries on every build.
