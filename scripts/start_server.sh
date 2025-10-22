#!/usr/bin/env bash
set -euo pipefail

# Start the Clara FastAPI server.
# Writes PID to ../run/server.pid and logs to ../logs/server.log when started in background.
# Usage:
#   ./scripts/start_server.sh            # start in background (default port 8000)
#   ./scripts/start_server.sh -f         # start in foreground (show logs, do not write PID)
#   ./scripts/start_server.sh -p 9000    # start on custom port
#   PORT=9000 ./scripts/start_server.sh # or set env var PORT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."
PID_DIR="${PROJECT_ROOT}/run"
PID_FILE="${PID_DIR}/server.pid"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/server.log"

# Try to read host/port from clara_config.json if it exists
CONFIG_FILE="${PROJECT_ROOT}/clara_config.json"
if [ -f "$CONFIG_FILE" ] && command -v python3 &> /dev/null; then
  CONFIG_HOST=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('host', '0.0.0.0'))" 2>/dev/null || echo "0.0.0.0")
  CONFIG_PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('port', 8000))" 2>/dev/null || echo "8000")
else
  CONFIG_HOST="0.0.0.0"
  CONFIG_PORT="8000"
fi

HOST="${HOST:-$CONFIG_HOST}"
PORT="${PORT:-$CONFIG_PORT}"
FOREGROUND=0

show_help() {
  cat <<EOF
Usage: $0 [-f] [-p PORT]
  -f   Run in foreground (logs printed to console). No PID file is written in this mode.
  -p   Port to bind (default: 8000 or use PORT env var)
EOF
}

while getopts ":fp:h" opt; do
  case ${opt} in
    f )
      FOREGROUND=1
      ;;
    p )
      PORT="$OPTARG"
      ;;
    h )
      show_help
      exit 0
      ;;
    \? )
      echo "Invalid Option: -$OPTARG" 1>&2
      show_help
      exit 1
      ;;
  esac
done

# Ensure project root is an absolute path
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

# If not foreground, ensure run/log directories
if [ "$FOREGROUND" -eq 0 ]; then
  mkdir -p "$PID_DIR"
  mkdir -p "$LOG_DIR"
fi

# If PID file exists and process is running, don't start another
if [ -f "$PID_FILE" ]; then
  PID_EXISTING=$(cat "$PID_FILE" 2>/dev/null || true)
  if [ -n "$PID_EXISTING" ] && kill -0 "$PID_EXISTING" 2>/dev/null; then
    echo "Server appears to already be running (pid $PID_EXISTING). Aborting." >&2
    echo "If this is stale, remove $PID_FILE and try again." >&2
    exit 1
  else
    # stale pidfile
    rm -f "$PID_FILE"
  fi
fi

UVICORN_CMD=(python -m uvicorn app.main:app --host "$HOST" --port "$PORT")

if [ "$FOREGROUND" -eq 1 ]; then
  echo "Starting server in foreground (host=$HOST port=$PORT)"
  exec "${UVICORN_CMD[@]}"
else
  echo "Starting server in background (host=$HOST port=$PORT). Logs: $LOG_FILE"
  nohup "${UVICORN_CMD[@]}" >>"$LOG_FILE" 2>&1 &
  PID=$!
  # Give the process a moment to start
  sleep 0.5
  if kill -0 "$PID" 2>/dev/null; then
    echo "$PID" > "$PID_FILE"
    echo "Started server (pid $PID). PID written to $PID_FILE"
  else
    echo "Failed to start server; check $LOG_FILE for errors." >&2
    exit 2
  fi
fi

