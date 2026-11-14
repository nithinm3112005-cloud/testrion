#!/bin/bash
# Testrion - one-command launcher (builds the frontend if needed, then starts the app on :8000)
set -e
cd "$(dirname "$0")"

if [ ! -d backend/.venv ]; then
  echo "▶ Creating Python environment..."
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -q -r backend/requirements.txt
fi

if [ ! -d frontend/dist ]; then
  echo "▶ Building frontend..."
  (cd frontend && npm install --silent && npm run build)
fi

echo "✔ Testrion running at http://127.0.0.1:8000"
cd backend && exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
