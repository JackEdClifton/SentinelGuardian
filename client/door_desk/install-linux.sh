#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="doordesk.service"

python -m venv "$SCRIPT_DIR/venv" --system-site-packages
"$SCRIPT_DIR/venv/bin/pip" install --upgrade pip
"$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

mkdir -p "$HOME/.config/systemd/user"

echo "
[Unit]
Description=Door Desk
After=network.target

[Service]
Type=simple
WorkingDirectory="$SCRIPT_DIR"
ExecStart="$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/door_desk.pyw"
Restart=on-failure
RestartSec=5
KillSignal=SIGKILL
TimeoutStopSec=1
KillMode=control-group

[Install]
WantedBy=default.target
" > "$HOME/.config/systemd/user/$SERVICE_NAME"

systemctl --user daemon-reload
systemctl --user enable $SERVICE_NAME
systemctl --user start $SERVICE_NAME
