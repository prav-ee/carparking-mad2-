@echo off
echo Starting Car Parking System Services...
echo.

echo 1. Starting Redis Server...
start "Redis Server" redis-server

echo 2. Waiting for Redis to start...
timeout /t 3 /nobreak > nul

echo 3. Starting Celery Worker...
start "Celery Worker" cmd /k "celery -A celery_worker.celery worker --loglevel=info"

echo 4. Starting Celery Beat Scheduler...
start "Celery Beat" cmd /k "celery -A celery_worker.celery beat --loglevel=info"

echo 5. Starting Flask Application...
start "Flask App" cmd /k "python app.py"

echo.
echo All services started!
echo.
echo Services running:
echo - Redis Server (Background)
echo - Celery Worker (Terminal 1)
echo - Celery Beat Scheduler (Terminal 2)
echo - Flask Application (Terminal 3)
echo.
echo Press any key to exit this script...
pause > nul 