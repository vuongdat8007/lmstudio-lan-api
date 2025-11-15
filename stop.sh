#!/bin/bash
# Stop script for LM Studio LAN Gateway (Unix/Linux/MacOS)

echo "Stopping LM Studio LAN Gateway..."

# Find process running on port 8001
PID=$(lsof -ti:8001 2>/dev/null)

if [ -z "$PID" ]; then
    echo "No server found running on port 8001"
    exit 0
fi

echo "Found server process: $PID"
echo "Sending SIGTERM signal..."
kill -TERM $PID

# Wait for graceful shutdown (max 5 seconds)
for i in {1..5}; do
    sleep 1
    if ! kill -0 $PID 2>/dev/null; then
        echo "Server stopped successfully"
        exit 0
    fi
    echo "Waiting for shutdown... ($i/5)"
done

# Force kill if still running
if kill -0 $PID 2>/dev/null; then
    echo "Server did not stop gracefully, forcing shutdown..."
    kill -9 $PID
    echo "Server forcefully stopped"
else
    echo "Server stopped successfully"
fi
