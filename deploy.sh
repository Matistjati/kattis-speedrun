#!/usr/bin/env bash
# Git-based deploy for the po host (dev.progolymp.se).
#
# From your laptop:
#   ssh -A po 'cd ~/dev/kattis-speedrun && ./deploy.sh'
#
# Pulls the latest committed code from origin/master, installs any new
# dependencies into the venv, and restarts the systemd service. The live DB
# (instance/) and Kattis token (.kattisrc) are gitignored, so they are never
# touched by the pull.
set -euo pipefail
cd "$(dirname "$0")"

echo "[deploy] fetching + fast-forwarding origin/master..."
git pull --ff-only origin master

echo "[deploy] syncing dependencies..."
./venv/bin/pip install -q -r requirements.txt

echo "[deploy] restarting service..."
sudo systemctl restart kattis-speedrun

sleep 2
echo "[deploy] service is now: $(systemctl is-active kattis-speedrun)"
