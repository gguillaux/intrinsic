#!/bin/bash

# Exit on error
set -e

echo "Starting Intrinsic Pro v3.0..."

# Clean up any existing processes on ports 8000 and 3000
echo "Cleaning up any existing processes on ports 8000 and 3000..."
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3000/tcp 2>/dev/null || true
sleep 1

# Ensure we are in the project root
cd "$(dirname "$0")"
source venv/bin/activate

# Auto cache-bust app.js with content hash (R10)
HASH=$(md5sum frontend/app.js | cut -c1-8)
sed -i "s/app\.js?v=[a-z0-9]*/app.js?v=${HASH}/" frontend/index.html
echo "Cache-busted app.js → v=${HASH}"

# Start Backend
echo "Starting Backend (uvicorn) on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend (python http.server) on port 3000..."
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!

echo ""
echo "====================================================="
echo "Application started successfully!"
echo "Backend API is running at http://localhost:8000"
echo "Frontend Dashboard is running at http://localhost:3000"
echo "Press Ctrl+C to stop both servers."
echo "====================================================="
echo ""

# Trap Ctrl+C to kill both background processes
trap "echo -e '\nStopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" SIGINT SIGTERM

# Wait for both processes
wait $BACKEND_PID
wait $FRONTEND_PID
