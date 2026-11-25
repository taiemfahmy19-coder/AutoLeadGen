@echo off
title AutoLeadGen V3 - FastAPI & WebSocket Server
color 0B
echo ============================================================
echo      AutoLeadGen V3 - FastAPI REST & WebSocket Backend
echo      Runs on port 8502 (Local & Tailscale Remote Control)
echo ============================================================
echo.
cd /d "%~dp0"
call "C:\Python314\python.exe" -m uvicorn api.main:app --host 0.0.0.0 --port 8502
pause
