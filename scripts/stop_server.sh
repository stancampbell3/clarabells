#!/usr/bin/env bash
set -euo pipefail

# Stop the Clara FastAPI server started by start_server.sh
# Reads PID from ../run/server.pid and attempts to stop the process.
# Usage:
#   ./scripts/stop_server.sh      # stop background server and remove PID file
#   ./scripts/stop_server.sh -f   # force kill (SIGKILL)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/.."
PID_FILE="${PROJECT_ROOT}/run/server.pid"
LOG_DIR="${PROJECT_ROOT}/logs"
LOG_FILE="${LOG_DIR}/server.log"
FORCE=0

while getopts ":fh" opt; do
  case ${opt} in
    f )
      FORCE=1
      ;;
    h )
      echo "Usage: $0 [-f]"
      echo "  -f  Force kill the process (SIGKILL)"
      exit 0
      ;;
    \? )
      echo "Invalid Option: -$OPTARG" 1>&2
      exit 1
      ;;
  esac
done

if [ ! -f "$PID_FILE" ]; then
  echo "PID file not found: $PID_FILE" >&2
  echo "Is the server running?" >&2
  exit 1
fi

PID=$(cat "$PID_FILE" 2>/dev/null || true)
if [ -z "$PID" ]; then
  echo "PID file is empty or unreadable: $PID_FILE" >&2
  rm -f "$PID_FILE"
  exit 1
fi

if ! kill -0 "$PID" 2>/dev/null; then
  echo "Process $PID not running. Removing stale PID file." >&2
  rm -f "$PID_FILE"
  exit 0
fi

if [ "$FORCE" -eq 1 ]; then
  echo "Force killing process $PID"
  kill -9 "$PID" || true
else
  echo "Stopping process $PID"
  kill "$PID"
fi

# wait for process to exit (max 10s)
COUNT=0
while kill -0 "$PID" 2>/dev/null; do
  sleep 0.5
  COUNT=$((COUNT + 1))
  if [ "$COUNT" -ge 20 ]; then
    echo "Process did not stop within timeout. You can retry with -f to force kill." >&2
    exit 2
  fi
done

# remove pidfile
rm -f "$PID_FILE"

echo "Stopped process $PID and removed $PID_FILE"

# Optionally show last few log lines
if [ -f "$LOG_FILE" ]; then
  echo "--- Last 50 lines of $LOG_FILE ---"
  tail -n 50 "$LOG_FILE" || true
fi

