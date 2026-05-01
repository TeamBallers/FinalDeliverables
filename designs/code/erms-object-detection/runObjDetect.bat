@echo off
echo    RUNNING ERMS YOLO Object Detection Server


:: Get the directory where this batch file is located
set ROOT=%~dp0

:: Check if venv exists, create if not
if not exist "%ROOT%server\yolo_env\Scripts\activate" (
    echo Creating virtual environment...
    cd /d "%ROOT%server"
    python -m venv yolo_env
    call yolo_env\Scripts\activate
    pip install -r requirements.txt
    echo Virtual environment ready!
)

:: Start YOLO server
echo Starting YOLO server on port 8000...
cd /d "%ROOT%server"
call yolo_env\Scripts\activate
uvicorn yolo_api:app --host 0.0.0.0 --port 8000