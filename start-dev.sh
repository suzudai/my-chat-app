#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Start the backend server in the background
echo "Starting backend server with hot-reload..."
cd /app/backend
python3 app.py &

# Start the frontend server in the foreground
echo "Starting frontend server with hot-reload..."
cd /app/frontend
npm run dev -- --host 