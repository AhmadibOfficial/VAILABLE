#!/usr/bin/env bash
# Installs a DAILY 09:30 user-local runner after explicit invocation.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [[ ! -d "$ROOT/.git" ]]; then
  echo "STOP: Initialize a regular VAILABLE Git repo first." >&2
  exit 2
fi
if [[ "$ROOT" == *$'\n'* || "$ROOT" == *' '* ]]; then
  echo "STOP: Move the project to a path without spaces or newlines." >&2
  exit 2
fi
command -v systemctl >/dev/null || { echo "STOP: systemd unavailable" >&2; exit 2; }
command -v python3 >/dev/null || { echo "STOP: Python missing" >&2; exit 2; }
command -v codex >/dev/null || { echo "STOP: Codex CLI missing" >&2; exit 2; }
command -v gh >/dev/null || { echo "STOP: GitHub CLI missing" >&2; exit 2; }
python3 "$ROOT/scripts/auto_dev.py" plan
mkdir -p -- "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/vailable-dev.service" <<UNIT
[Unit]
Description=VAILABLE one-task-per-run autonomous development
[Service]
Type=oneshot
WorkingDirectory=$ROOT
ExecStart=/usr/bin/python3 $ROOT/scripts/auto_dev.py once --publish
TimeoutStartSec=7500
UNIT
cat > "$HOME/.config/systemd/user/vailable-dev.timer" <<'UNIT'
[Unit]
Description=Daily VAILABLE task proposal
[Timer]
OnCalendar=*-*-* 09:30:00
Persistent=true
Unit=vailable-dev.service
[Install]
WantedBy=timers.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now vailable-dev.timer
echo "Enabled daily task at 09:30 local time. Review changes before merge."
echo "Status: systemctl --user status vailable-dev.timer"
echo "Disable: systemctl --user disable --now vailable-dev.timer"
