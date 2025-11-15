#!/bin/bash
# Startup script for LM Studio LAN Gateway (Unix/Linux/MacOS)

# Set PYTHONPATH to include src directory
export PYTHONPATH=src

# Start the server
python -m uvicorn lmstudio_gateway.main:app --host 0.0.0.0 --port 8001
