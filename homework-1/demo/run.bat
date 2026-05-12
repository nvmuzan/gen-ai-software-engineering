@echo off
cd /d "%~dp0.."
pip install -r requirements.txt
uvicorn src.app:app --reload --port 3000
