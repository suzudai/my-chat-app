#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# 既存の8000番ポートのプロセスを自動でkill
PIDS=$(lsof -t -i:8000)
if [ -n "$PIDS" ]; then
  echo "Killing processes on port 8000: $PIDS"
  kill -9 $PIDS
fi

# Start the backend server in the background
echo "Starting backend server with hot-reload..."
PYTHONPATH=backend uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload &

# Start the frontend server in the foreground
echo "Starting frontend server with hot-reload..."
cd frontend
npm run dev -- --host 0.0.0.0 