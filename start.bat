@echo off
REM Startup script for LM Studio LAN Gateway (Windows)

REM Set PYTHONPATH to include src directory
set PYTHONPATH=src

REM Start the server
python -m uvicorn lmstudio_gateway.main:app --host 0.0.0.0 --port 8001
