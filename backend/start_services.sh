#!/bin/bash

echo "Starting Car Parking System Services..."
echo

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Redis is installed
if ! command_exists redis-server; then
    echo "Error: Redis is not installed or not in PATH"
    echo "Please install Redis and try again"
    exit 1
fi

# Check if Python is installed
if ! command_exists python3; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3 and try again"
    exit 1
fi

echo "1. Starting Redis Server..."
redis-server --daemonize yes
echo "   Redis started in background"

echo "2. Waiting for Redis to start..."
sleep 3

echo "3. Starting Celery Worker..."
gnome-terminal --title="Celery Worker" -- bash -c "celery -A celery_worker.celery worker --loglevel=info; exec bash" 2>/dev/null || \
xterm -title "Celery Worker" -e "celery -A celery_worker.celery worker --loglevel=info; bash" 2>/dev/null || \
echo "   Please start Celery Worker manually: celery -A celery_worker.celery worker --loglevel=info"

echo "4. Starting Celery Beat Scheduler..."
gnome-terminal --title="Celery Beat" -- bash -c "celery -A celery_worker.celery beat --loglevel=info; exec bash" 2>/dev/null || \
xterm -title "Celery Beat" -e "celery -A celery_worker.celery beat --loglevel=info; bash" 2>/dev/null || \
echo "   Please start Celery Beat manually: celery -A celery_worker.celery beat --loglevel=info"

echo "5. Starting Flask Application..."
gnome-terminal --title="Flask App" -- bash -c "python3 app.py; exec bash" 2>/dev/null || \
xterm -title "Flask App" -e "python3 app.py; bash" 2>/dev/null || \
echo "   Please start Flask App manually: python3 app.py"

echo
echo "All services started!"
echo
echo "Services running:"
echo "- Redis Server (Background)"
echo "- Celery Worker (Terminal 1)"
echo "- Celery Beat Scheduler (Terminal 2)"
echo "- Flask Application (Terminal 3)"
echo
echo "To stop Redis: redis-cli shutdown"
echo "To test the system: python3 test_monthly_report.py" 