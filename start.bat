@echo off
REM Start script for Trend & Viral Engine Pro (Windows)

echo Starting Trend ^& Viral Engine Pro...

REM Check if .env exists
if not exist .env (
    echo .env file not found. Creating from .env.example...
    copy .env.example .env
    echo Please edit .env with your API keys before continuing.
    exit /b 1
)

REM Create directories
echo Creating directories...
if not exist data\raw mkdir data\raw
if not exist data\features mkdir data\features
if not exist data\labels mkdir data\labels
if not exist data\feedback mkdir data\feedback
if not exist models mkdir models
if not exist outputs mkdir outputs
if not exist logs mkdir logs
if not exist mlruns mkdir mlruns

REM Start Docker services
echo Starting Docker services...
docker-compose up -d

REM Wait for services
echo Waiting for services to be ready...
timeout /t 10

echo All services are up and running!
echo.
echo Access points:
echo    - API: http://localhost:8000
echo    - API Docs: http://localhost:8000/docs
echo    - Grafana: http://localhost:3000 (admin/admin)
echo    - MLflow: http://localhost:5000
echo.
echo View logs: docker-compose logs -f
echo Stop services: docker-compose down
