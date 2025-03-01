#!/bin/bash
# AILinux Startup Script
# This script starts the AILinux application with proper error handling and logging.

# Ensure proper error handling
set -euo pipefail

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define paths
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${BASE_DIR}/logs"
BACKEND_DIR="${BASE_DIR}/backend"
FRONTEND_DIR="${BASE_DIR}/frontend"
START_LOG="${LOG_DIR}/start.log"
BACKEND_LOG="${LOG_DIR}/backend.log"
FRONTEND_LOG="${LOG_DIR}/frontend.log"

# Define environment variables
export NODE_ENV=${NODE_ENV:-"production"}

# Process arguments
MODE="local"
if [ $# -ge 1 ]; then
    if [ "$1" == "remote" ] || [ "$1" == "local" ]; then
        MODE="$1"
    else
        echo -e "${RED}Invalid mode. Using default 'local' mode.${NC}"
    fi
fi

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Initialize log files with header
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
log_header="=== AILinux Startup Log - ${timestamp} ==="
echo "${log_header}" > "${START_LOG}"
echo "${log_header}" > "${BACKEND_LOG}"
echo "${log_header}" > "${FRONTEND_LOG}"

# Function to log messages
log_message() {
    local message="$1"
    local log_file="$2"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "${timestamp} - ${message}" >> "${log_file}"
    echo -e "${BLUE}[${timestamp}]${NC} ${message}"
}

# Function to check dependencies
check_dependencies() {
    log_message "Checking dependencies..." "${START_LOG}"
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        log_message "ERROR: Python 3 is not installed or not in PATH" "${START_LOG}"
        echo -e "${RED}ERROR: Python 3 is required but not found. Please install Python 3.${NC}"
        exit 1
    fi
    
    # Check for Node.js
    if ! command -v node &> /dev/null; then
        log_message "ERROR: Node.js is not installed or not in PATH" "${START_LOG}"
        echo -e "${RED}ERROR: Node.js is required but not found. Please install Node.js.${NC}"
        exit 1
    fi
    
    # Check for npm
    if ! command -v npm &> /dev/null; then
        log_message "ERROR: npm is not installed or not in PATH" "${START_LOG}"
        echo -e "${RED}ERROR: npm is required but not found. Please install npm.${NC}"
        exit 1
    fi
    
    # Check for required directories
    if [ ! -d "${BACKEND_DIR}" ]; then
        log_message "ERROR: Backend directory not found: ${BACKEND_DIR}" "${START_LOG}"
        echo -e "${RED}ERROR: Backend directory not found: ${BACKEND_DIR}${NC}"
        exit 1
    fi
    
    if [ ! -d "${FRONTEND_DIR}" ]; then
        log_message "ERROR: Frontend directory not found: ${FRONTEND_DIR}" "${START_LOG}"
        echo -e "${RED}ERROR: Frontend directory not found: ${FRONTEND_DIR}${NC}"
        exit 1
    fi
    
    # Check for required files
    if [ ! -f "${BACKEND_DIR}/app.py" ]; then
        log_message "ERROR: Backend app.py not found" "${START_LOG}"
        echo -e "${RED}ERROR: Backend app.py not found${NC}"
        exit 1
    fi
    
    if [ ! -f "${FRONTEND_DIR}/package.json" ]; then
        log_message "ERROR: Frontend package.json not found" "${START_LOG}"
        echo -e "${RED}ERROR: Frontend package.json not found${NC}"
        exit 1
    fi
    
    log_message "All dependencies satisfied" "${START_LOG}"
}

# Function to configure environment
configure_environment() {
    if [ "${MODE}" == "remote" ]; then
        export FLASK_HOST="derleiti.de"
        export FLASK_PORT="8081"
        export WS_SERVER_URL="wss://derleiti.de:8082"
        log_message "Running in REMOTE mode - connecting to derleiti.de" "${START_LOG}"
        echo -e "${YELLOW}Running in REMOTE mode - connecting to derleiti.de${NC}"
    else
        export FLASK_HOST="localhost"
        export FLASK_PORT="8081"
        export WS_SERVER_URL="ws://localhost:8082"
        log_message "Running in LOCAL mode - connecting to localhost" "${START_LOG}"
        echo -e "${GREEN}Running in LOCAL mode - connecting to localhost${NC}"
    fi
    
    # Log environment
    log_message "Configuration: Flask=${FLASK_HOST}:${FLASK_PORT}, WebSocket=${WS_SERVER_URL}" "${START_LOG}"
    
    # Log API key status
    if [ -n "${OPENAI_API_KEY:-}" ]; then
        log_message "OpenAI API Key: SET" "${START_LOG}"
    else
        log_message "OpenAI API Key: NOT SET" "${START_LOG}"
    fi
    
    if [ -n "${GEMINI_API_KEY:-}" ]; then
        log_message "Gemini API Key: SET" "${START_LOG}"
    else
        log_message "Gemini API Key: NOT SET" "${START_LOG}"
    fi
}

# Function to start the backend server
start_backend() {
    log_message "Starting backend server..." "${START_LOG}"
    echo -e "${BLUE}Starting backend server...${NC}"
    
    python3 "${BACKEND_DIR}/app.py" "${MODE}" > >(tee -a "${BACKEND_LOG}") 2> >(tee -a "${BACKEND_LOG}" >&2) &
    BACKEND_PID=$!
    
    # Wait for backend to start (up to 30 seconds)
    local max_attempts=30
    local attempt=0
    local backend_ready=false
    
    echo -ne "${YELLOW}Waiting for backend to start.${NC}"
    while [ $attempt -lt $max_attempts ]; do
        # Check if process is still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "\n${RED}Backend process died unexpectedly${NC}"
            log_message "ERROR: Backend process died unexpectedly" "${START_LOG}"
            exit 1
        fi
        
        # Check log for startup indication
        if grep -q "Running on" "${BACKEND_LOG}" || grep -q "Debugger PIN" "${BACKEND_LOG}"; then
            backend_ready=true
            break
        fi
        
        echo -ne "${YELLOW}.${NC}"
        sleep 1
        ((attempt++))
    done
    
    if [ "$backend_ready" = true ]; then
        echo -e "\n${GREEN}Backend server started successfully (PID: $BACKEND_PID)${NC}"
        log_message "Backend server started successfully (PID: $BACKEND_PID)" "${START_LOG}"
    else
        echo -e "\n${RED}Timed out waiting for backend to start${NC}"
        log_message "ERROR: Timed out waiting for backend to start" "${START_LOG}"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    
    # Export PID for cleanup
    export BACKEND_PID
}

# Function to start the frontend
start_frontend() {
    log_message "Starting frontend Electron app..." "${START_LOG}"
    echo -e "${BLUE}Starting frontend Electron app...${NC}"
    
    cd "${FRONTEND_DIR}"
    npm start > >(tee -a "${FRONTEND_LOG}") 2> >(tee -a "${FRONTEND_LOG}" >&2) &
    FRONTEND_PID=$!
    
    # Check if frontend started
    sleep 3
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}Frontend process failed to start${NC}"
        log_message "ERROR: Frontend process failed to start" "${START_LOG}"
        # Kill backend if frontend fails
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    
    echo -e "${GREEN}Frontend started successfully (PID: $FRONTEND_PID)${NC}"
    log_message "Frontend started successfully (PID: $FRONTEND_PID)" "${START_LOG}"
    
    # Export PID for cleanup
    export FRONTEND_PID
}

# Cleanup function to ensure all processes are terminated
cleanup() {
    log_message "Shutting down AILinux..." "${START_LOG}"
    echo -e "${YELLOW}Shutting down AILinux...${NC}"
    
    # Kill frontend
    if [ -n "${FRONTEND_PID:-}" ]; then
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            log_message "Stopping frontend (PID: $FRONTEND_PID)" "${START_LOG}"
            kill $FRONTEND_PID 2>/dev/null || true
        fi
    fi
    
    # Kill backend
    if [ -n "${BACKEND_PID:-}" ]; then
        if kill -0 $BACKEND_PID 2>/dev/null; then
            log_message "Stopping backend (PID: $BACKEND_PID)" "${START_LOG}"
            kill $BACKEND_PID 2>/dev/null || true
        fi
    fi
    
    log_message "AILinux shutdown complete" "${START_LOG}"
    echo -e "${GREEN}AILinux shutdown complete${NC}"
}

# Set up signal handling for graceful shutdown
trap cleanup SIGINT SIGTERM EXIT

# Main execution flow
echo -e "${GREEN}=== Starting AILinux ===
Mode: ${MODE}
Base directory: ${BASE_DIR}
Logs directory: ${LOG_DIR}${NC}"

log_message "Starting AILinux in ${MODE} mode" "${START_LOG}"

# Check dependencies
check_dependencies

# Configure environment
configure_environment

# Start backend and wait for it to be ready
start_backend

# Start frontend
start_frontend

# Show how to stop the application
echo -e "${GREEN}AILinux is running. Press Ctrl+C to stop all processes.${NC}"
log_message "AILinux started successfully. Press Ctrl+C to stop." "${START_LOG}"

# Keep script running until manually interrupted
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Backend process died unexpectedly${NC}"
        log_message "ERROR: Backend process died unexpectedly" "${START_LOG}"
        # Trigger cleanup
        exit 1
    fi
    
    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}Frontend process died unexpectedly${NC}"
        log_message "ERROR: Frontend process died unexpectedly" "${START_LOG}"
        # Trigger cleanup
        exit 1
    fi
    
    sleep 2
done
