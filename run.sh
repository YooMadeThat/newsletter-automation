#!/bin/bash
# Allen + Clarke Intel — Newsletter runner
# Called by launchd every Monday at 8am.
# Logs are written to logs/run_YYYYMMDD.log

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/run_$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

echo "=== Allen + Clarke Intel — $(date) ===" >> "$LOG_FILE"

cd "$SCRIPT_DIR" || exit 1

"$SCRIPT_DIR/.venv/bin/python" orchestrator.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: orchestrator.py exited with code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "=== Done $(date) ===" >> "$LOG_FILE"
