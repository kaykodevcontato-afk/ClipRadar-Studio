#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo 'Instale ffmpeg primeiro'; exit 1; }
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn app:app --app-dir backend --host 127.0.0.1 --port 8765
