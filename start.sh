#!/bin/bash

# Set environment variables (add as needed)
export FLASK_APP="/home/zombie/ailinux/backend/app.py"
export FLASK_ENV="production"
export PORT=8081
export NODE_ENV="production"

# Log files
LOG_DIR="/home/zombie/ailinux/logs"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
DEBUG_LOG="$LOG_DIR/debug.log"

# Create the log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to start backend (Flask)
start_backend() {
    echo "Starting backend (Flask)..."
    cd /home/zombie/ailinux/backend
    nohup python3 app.py > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
}

# Function to start frontend (Electron)
start_frontend() {
    echo "Starting frontend (Electron)..."
    cd /home/zombie/ailinux/frontend
    nohup electron main.js > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    echo "Frontend started with PID: $FRONTEND_PID"
}

# Function to stop backend
stop_backend() {
    if [ -n "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        wait $BACKEND_PID 2>/dev/null
        echo "Backend stopped."
    else
        echo "Backend is not running."
    fi
}

# Function to stop frontend
stop_frontend() {
    if [ -n "$FRONTEND_PID" ]; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        wait $FRONTEND_PID 2>/dev/null
        echo "Frontend stopped."
    else
        echo "Frontend is not running."
    fi
}

# Function to gracefully handle exit
graceful_exit() {
    echo "Gracefully shutting down services..."
    stop_backend
    stop_frontend
    echo "All services stopped."
    exit 0
}

# Trap signals for graceful shutdown (e.g., CTRL+C or kill)
trap graceful_exit SIGINT SIGTERM

# Start the backend and frontend
start_backend
start_frontend

# Wait for services to terminate (so the script doesn't exit immediately)
wait $BACKEND_PID
wait $FRONTEND_PID
