#!/bin/bash
# Fetch logs from the remote jacket-server via Tailscale

set -e

HOST="jacketserver"
USER="ubuntu"
APP_DIR="/opt/jacket-server"

# Default to last 100 lines, follow mode off
LINES="${1:-100}"
FOLLOW="${2:-}"

if [[ "$1" == "-f" || "$1" == "--follow" ]]; then
    # Follow mode
    ssh -t "$USER@$HOST" "cd $APP_DIR && docker compose logs -f"
elif [[ "$FOLLOW" == "-f" || "$FOLLOW" == "--follow" ]]; then
    # Lines + follow mode
    ssh -t "$USER@$HOST" "cd $APP_DIR && docker compose logs --tail=$LINES -f"
else
    # Just show last N lines
    ssh "$USER@$HOST" "cd $APP_DIR && docker compose logs --tail=$LINES"
fi
