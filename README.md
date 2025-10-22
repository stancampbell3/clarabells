# Clara — Minimal FastAPI service

This repository contains a minimal FastAPI app with a single health check endpoint.

## Configuration

Clara uses a `clara_config.json` file for server configuration. Copy the example and customize:

```bash
cp clara_config.json.example clara_config.json
# Edit clara_config.json to set host, port, audio TTL, and bearer token
```

See **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** for detailed configuration options.

## Quick Start

Install dev dependencies and run tests:

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

Or use the provided scripts:
```bash
# Start in background
./scripts/start_server.sh

# Start in foreground (shows logs)
./scripts/start_server.sh --foreground

# Stop the server
./scripts/stop_server.sh
```

Health endpoint:
GET /health -> { "status": "ok" }

# Audio Playback Setup

Clara uses external audio players for reliable playback. Check your system setup:

```bash
./scripts/check_audio_setup.sh
```

**Recommended players** (in priority order):
- **Linux**: `mpv` (most reliable), `ffplay`, `aplay`, `mpg123`, `sox`
- **macOS**: `afplay` (built-in), `mpv`, `ffplay`
- **Windows**: Uses built-in `cmd` (no installation needed)

**Quick install** (Linux):
```bash
sudo apt-get install mpv ffmpeg alsa-utils
```

**Quick install** (macOS):
```bash
brew install mpv ffmpeg
```

For detailed troubleshooting and configuration, see: **[docs/AUDIO_PLAYBACK.md](docs/AUDIO_PLAYBACK.md)**

## Using Clara

**Test the speak endpoint** (without playback):
```bash
python clarasvoice/speak.py --text "Hello world" --host 127.0.0.1
```

**Test with audio playback**:
```bash
python clarasvoice/speak.py --text "Hello world" --host 127.0.0.1 --outloud
```

**Run attention listener** (receives WebSocket notifications):
```bash
python clarasattention/attention.py --host 127.0.0.1 --port 8000
```


# Docker

This project includes a `Dockerfile` and `docker-compose.yml` for running the app in a container.

Important: model storage should be mounted from the host to avoid filling the container image/layers. The compose setup mounts `./models` on the host into `/models` inside the container.

Quick Docker commands (dev-friendly):

```bash
# create a local models dir (if you plan to persist models on host)
mkdir -p ./models

# Build using the dev requirements (faster; avoids heavy ML libs)
docker compose build --build-arg REQUIREMENTS=requirements-dev.txt

# Start the app (detached)
docker compose up -d

# Confirm container is running
docker compose ps

# Probe the health endpoint (should return {"status":"ok"})
curl -sS http://127.0.0.1:8000/health

# When done, stop everything
docker compose down
```

Notes:
- Building with `requirements.txt` will install heavy ML packages (Transformers, PyTorch) and may take a long time and large disk space. For development, use `requirements-dev.txt` as shown above.
- The compose file mounts `./models` -> `/models` so large models live on the host filesystem and don't bloat the image or commit history.

# Push to GitHub (create `clarabells` repo)

You can create and push this repository to GitHub under the name `clarabells`. Two options are shown below.

Option A — Using GitHub CLI (`gh`) (recommended if you have `gh` installed and authenticated):

```bash
cd /home/stanc/Development/clara
# create a public repo on GitHub, set remote origin, and push the current main branch
gh repo create clarabells --public --source=. --remote=origin --push
```

Option B — Manual (use if you don't have `gh`):

1. Create an empty repo named `clarabells` on GitHub through the web UI: https://github.com/new
   - Name: clarabells
   - Visibility: Public

2. Add the remote and push:

```bash
cd /home/stanc/Development/clara
# replace <your-username> with your GitHub username
git remote add origin git@github.com:<your-username>/clarabells.git
git push -u origin main
```

If you don't use SSH keys, use the HTTPS remote instead:

```bash
git remote add origin https://github.com/<your-username>/clarabells.git
git push -u origin main
```

# After pushing
- The GitHub Actions workflow at `.github/workflows/ci.yml` will run on push/PR to `main` and execute tests.
- Optionally add a status badge to the top of this README once CI runs successfully:

```markdown
![CI](https://github.com/<your-username>/clarabells/actions/workflows/ci.yml/badge.svg)
```


--

If you'd like, I can attempt to create and push the `clarabells` repo from this environment for you (will use `gh` if available, otherwise I'll try the git remote push). If you prefer to handle the GitHub repo creation yourself, tell me and I'll stop after committing the README change.
