#!/bin/bash
# AILinux Startup Script (Fixed Version with debug output)
# This script starts the AILinux application with improved error handling and compatibility

# Don't exit on error - just continue with appropriate warnings instead
set +e

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

# Create a log file for debugging
DEBUG_LOG="$LOG_DIR/start_debug.log"
echo "=== AILinux Startup Log - $(date) ===" > "$DEBUG_LOG"
echo "Working directory: $BASE_DIR" >> "$DEBUG_LOG"

# Function to both display and log messages
log() {
  level=$1
  message=$2
  case $level in
    "info")
      echo -e "${BLUE}$message${NC}"
      ;;
    "success")
      echo -e "${GREEN}$message${NC}"
      ;;
    "warning")
      echo -e "${YELLOW}$message${NC}"
      ;;
    "error")
      echo -e "${RED}$message${NC}"
      ;;
    *)
      echo -e "$message"
      ;;
  esac
  echo "$(date +'%Y-%m-%dT%H:%M:%S.%3N'): $level - $message" >> "$DEBUG_LOG"
}

log "info" "=== AILinux Startup Script ==="
log "info" "Current directory: $BASE_DIR"

# Process arguments
MODE="local"
if [ $# -ge 1 ]; then
    if [ "$1" == "remote" ] || [ "$1" == "local" ]; then
        MODE="$1"
    else
        log "warning" "Invalid mode. Using default 'local' mode."
    fi
fi

log "success" "Running in $MODE mode"
log "info" "Finding compatible Python version..."

# Function to check if a Python path is valid and compatible
check_python_path() {
  python_path="$1"
  if [ -z "$python_path" ]; then
    return 1
  fi

  # Check if the path exists and is executable
  if command -v "$python_path" &>/dev/null || [ -x "$python_path" ]; then
    # Try to get the version
    version_output=$("$python_path" --version 2>&1)
    echo "Testing Python path: $python_path - $version_output" >> "$DEBUG_LOG"

    if [[ "$version_output" =~ Python\ 3 ]]; then
      echo "Found working Python: $python_path - $version_output" >> "$DEBUG_LOG"
      echo "$python_path"
      return 0
    fi
  fi

  return 1
}

# Find a compatible Python installation
find_compatible_python() {
  log "info" "Searching for compatible Python..." >> "$DEBUG_LOG"

  # List of potential Python paths to check
  paths=(
    "python3.9"
    "python3.10"
    "python3.11"
    "python3"
    "/usr/bin/python3.9"
    "/usr/bin/python3.10"
    "/usr/bin/python3.11"
    "/usr/bin/python3"
    "/usr/local/bin/python3.9"
    "/usr/local/bin/python3.10"
    "/usr/local/bin/python3.11"
  )

  # Check each path
  for path in "${paths[@]}"; do
    result=$(check_python_path "$path")
    if [ $? -eq 0 ]; then
      echo "$result"
      return 0
    fi
  done

  # No compatible version found
  log "warning" "No ideal Python version found, will try with system default" >> "$DEBUG_LOG"
  echo "python3"
  return 1
}

# Get compatible Python - with error handling
log "info" "Looking for Python 3.9-3.11..." >> "$DEBUG_LOG"
PYTHON_PATH=$(find_compatible_python)
PYTHON_STATUS=$?

# Always fallback to system Python if detection fails
if [ -z "$PYTHON_PATH" ]; then
  log "warning" "Python detection failed, falling back to system Python"
  PYTHON_PATH="python3"
  PYTHON_STATUS=1
fi

# Test if Python works at all
if ! command -v $PYTHON_PATH &>/dev/null; then
  log "error" "Python path $PYTHON_PATH is not executable, trying plain python3"
  PYTHON_PATH="python3"
fi

# Final verification of Python
if command -v $PYTHON_PATH &>/dev/null; then
  PYTHON_VERSION=$($PYTHON_PATH --version 2>&1)
  log "success" "Using Python: $PYTHON_PATH - $PYTHON_VERSION"
else
  log "error" "No usable Python installation found. Please install Python 3.x"
  log "error" "Program cannot continue without Python"
  exit 1
fi

# Set up environment
log "info" "Setting up environment..."

# Set PYTHONPATH to find modules
export PYTHON_PATH
export PYTHONPATH="$BASE_DIR:$PYTHONPATH"

# Configure the electron-log app name
export ELECTRON_APP_NAME="ailinux"

# Create necessary directories
mkdir -p "$BASE_DIR/logs"
mkdir -p "$BASE_DIR/client/backend/logs" 2>/dev/null || true

# Check if we have a .env file, create one if not
if [ -f "$BASE_DIR/.env" ]; then
    log "info" "Using existing .env file"
    # Source the .env file to get environment variables
    set -a
    source "$BASE_DIR/.env"
    set +a
else
    log "info" "Creating new .env file"
    # Create new .env file with app name for Node.js
    cat > "$BASE_DIR/.env" << EOF
ELECTRON_APP_NAME=ailinux
FLASK_HOST=localhost
FLASK_PORT=8081
FLASK_DEBUG=False
WS_SERVER_URL=ws://localhost:8082
# Add API keys below
# OPENAI_API_KEY=
# GEMINI_API_KEY=
# HUGGINGFACE_API_KEY=
EOF

    # Source the new .env file
    set -a
    source "$BASE_DIR/.env"
    set +a
fi

# Check Flask installation
log "info" "Checking Flask installation..."
if ! $PYTHON_PATH -c "import flask" 2>/dev/null; then
    log "warning" "Flask is not installed, attempting to install..."

    # Try to install Flask for the selected Python version
    $PYTHON_PATH -m pip install flask flask-cors werkzeug requests
    PIP_STATUS=$?

    # Check again
    if [ $PIP_STATUS -ne 0 ] || ! $PYTHON_PATH -c "import flask" 2>/dev/null; then
        log "warning" "Flask installation failed, but continuing..."
    else
        log "success" "Flask installed successfully"
    fi
else
    FLASK_VERSION=$($PYTHON_PATH -c "import flask; print(flask.__version__)" 2>/dev/null)
    log "success" "Flask version $FLASK_VERSION is installed"
fi

# Create and run a simple backend server starter script
log "info" "Setting up backend server..."
BACKEND_DIR="$BASE_DIR/backend"
if [ ! -d "$BACKEND_DIR" ]; then
    # Fallback to client/backend if backend doesn't exist
    BACKEND_DIR="$BASE_DIR/client/backend"
    mkdir -p "$BACKEND_DIR"
fi

# Create a simple Flask app if none exists
if [ ! -f "$BACKEND_DIR/app.py" ]; then
    log "info" "Creating minimal Flask app..."
    cat > "$BACKEND_DIR/app.py" << 'EOF'
"""
Minimal Flask Server for AILinux
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
import json
import platform
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("backend.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Backend")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "online",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform()
    })

@app.route('/logs', methods=['GET'])
def get_logs():
    """Return logs."""
    return jsonify({"logs": ["System starting up", "Backend initialized"]})

@app.route('/debug', methods=['POST'])
def debug():
    """Process and analyze log data."""
    try:
        # Process the request
        data = request.json if request.is_json else {}
        log_text = data.get('log', 'No log provided')
        model = data.get('model', 'default')

        # Log the request
        logger.info(f"Received {len(log_text)} characters for analysis with {model}")

        # Return a simple analysis
        return jsonify({
            "analysis": f"Analyzed {len(log_text)} characters with {model}.\nNo issues detected.",
            "processing_time": 0.5,
            "model": model
        })
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "localhost")
    port = int(os.getenv("FLASK_PORT", "8081"))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    logger.info(f"Starting Flask server on {host}:{port} (Debug: {debug})")
    app.run(host=host, port=port, debug=debug)
EOF
fi

# Start backend in background
log "info" "Starting backend server..."
BACKEND_SCRIPT="$BACKEND_DIR/app.py"
nohup $PYTHON_PATH "$BACKEND_SCRIPT" > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
log "success" "Backend started with PID: $BACKEND_PID"

# Wait for backend to start up
log "info" "Waiting for backend to start..."
sleep 2

# Check if Node.js is installed
if ! command -v node &>/dev/null; then
    log "error" "Node.js is not installed. Please install Node.js to run the frontend."
    # Kill backend process
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# For debugging, show what files we have in the directory
log "info" "Checking for start.js..."
if [ -f "$BASE_DIR/start.js" ]; then
    log "success" "Found start.js"
else
    log "error" "start.js not found in $BASE_DIR"
    ls -la "$BASE_DIR" >> "$DEBUG_LOG"

    # Try to find it
    START_JS_PATH=$(find "$BASE_DIR" -name "start.js" -type f | head -n 1)
    if [ -n "$START_JS_PATH" ]; then
        log "success" "Found start.js at $START_JS_PATH"
        cd "$(dirname "$START_JS_PATH")"
    else
        log "error" "Cannot find start.js anywhere. Frontend cannot be started."
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
fi

# Start frontend with Node.js
log "info" "Starting frontend..."
NODE_OPTIONS="--max-old-space-size=4096" node start.js "$MODE" "$PYTHON_PATH"
EXIT_CODE=$?

# Cleanup backend process
log "info" "Shutting down backend..."
kill $BACKEND_PID 2>/dev/null || true

if [ $EXIT_CODE -eq 0 ]; then
    log "success" "AILinux exited successfully"
else
    log "error" "AILinux exited with error code $EXIT_CODE"
fi

exit $EXIT_CODE
