#!/bin/bash
# AILinux Startup Script
# This script starts the AILinux application with proper environment setup

# Ensure proper error handling
set -e

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"

echo -e "${BLUE}=== AILinux Startup Script ===${NC}"

# Process arguments
MODE="local"
if [ $# -ge 1 ]; then
    if [ "$1" == "remote" ] || [ "$1" == "local" ]; then
        MODE="$1"
    else
        echo -e "${YELLOW}Invalid mode. Using default 'local' mode.${NC}"
    fi
fi

echo -e "${GREEN}Running in $MODE mode${NC}"

# Find compatible Python version
echo -e "${BLUE}Finding compatible Python version...${NC}"

find_compatible_python() {
    # Check for Python 3.9-3.11 explicitly
    for version in "3.9" "3.10" "3.11"; do
        if command -v python$version &> /dev/null; then
            echo "python$version"
            return 0
        fi
    done
    
    # Fall back to checking default python3
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" = "3" ] && [ "$PYTHON_MINOR" -ge 9 ] && [ "$PYTHON_MINOR" -le 11 ]; then
        echo "python3"
        return 0
    fi
    
    # Check for specific Python installations
    if [ -f "/home/zombie/client/bin/python3.9" ]; then
        echo "/home/zombie/client/bin/python3.9"
        return 0
    elif [ -f "/home/zombie/client/bin/python3.10" ]; then
        echo "/home/zombie/client/bin/python3.10"
        return 0
    elif [ -f "/home/zombie/client/bin/python3.11" ]; then
        echo "/home/zombie/client/bin/python3.11"
        return 0
    fi
    
    # No compatible version found, return the system default as fallback
    echo "python3"
    return 1
}

# Get compatible Python
PYTHON_PATH=$(find_compatible_python)
PYTHON_OK=$?

# Test the Python path
if [ -n "$PYTHON_PATH" ]; then
    echo -e "${GREEN}Found Python at: $PYTHON_PATH${NC}"
    PYTHON_VERSION=$($PYTHON_PATH --version 2>&1)
    echo -e "${GREEN}$PYTHON_VERSION${NC}"
else
    echo -e "${RED}No Python interpreter found. Please install Python.${NC}"
    exit 1
fi

# Check if Python version is compatible (3.9-3.11)
if [ $PYTHON_OK -ne 0 ]; then
    echo -e "${YELLOW}Warning: Python version might not be compatible with Flask.${NC}"
    echo -e "${YELLOW}Recommended Python version: 3.9-3.11${NC}"
    
    # Ask user whether to continue or abort
    read -p "Do you want to continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Aborting startup due to Python compatibility issues.${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Continuing despite compatibility warnings...${NC}"
fi

# Set up environment
echo -e "${BLUE}Setting up environment...${NC}"

# Set PYTHONPATH to find modules
export PYTHON_PATH
export PYTHONPATH="$BASE_DIR:$PYTHONPATH"

# Configure the electron-log app name
export ELECTRON_APP_NAME="ailinux"

# Check if we have a .env file, create one if not
if [ -f "$BASE_DIR/.env" ]; then
    # Source the .env file to get environment variables
    set -a
    source "$BASE_DIR/.env"
    set +a
    
    # Make sure ELECTRON_APP_NAME is set in the .env file
    if ! grep -q "ELECTRON_APP_NAME=" "$BASE_DIR/.env"; then
        echo "ELECTRON_APP_NAME=ailinux" >> "$BASE_DIR/.env"
    fi
else
    # Create new .env file with app name for Node.js
    cat > "$BASE_DIR/.env" << EOF
ELECTRON_APP_NAME=ailinux
FLASK_HOST=localhost
FLASK_PORT=8081
WS_SERVER_URL=ws://localhost:8082
# Add API keys below
# OPENAI_API_KEY=
# GEMINI_API_KEY=
# HUGGINGFACE_API_KEY=
EOF
    echo -e "${GREEN}Created new .env file${NC}"
    
    # Source the new .env file
    set -a
    source "$BASE_DIR/.env"
    set +a
fi

# Ensure logs directory exists
mkdir -p "$BASE_DIR/logs"

# Check Flask installation
echo -e "${BLUE}Checking Flask installation...${NC}"
if ! $PYTHON_PATH -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}Flask is not installed or cannot be found.${NC}"
    echo -e "${YELLOW}Attempting to install Flask...${NC}"
    
    # Try to install Flask for the selected Python version
    $PYTHON_PATH -m pip install flask flask-cors werkzeug 2>/dev/null || true
    
    # Check again
    if ! $PYTHON_PATH -c "import flask" 2>/dev/null; then
        echo -e "${RED}Failed to install Flask. Please install it manually:${NC}"
        echo -e "${YELLOW}  $PYTHON_PATH -m pip install flask flask-cors werkzeug${NC}"
        # Continue anyway, as start.js will handle this error
    else
        echo -e "${GREEN}Flask installed successfully${NC}"
    fi
else
    FLASK_VERSION=$($PYTHON_PATH -c "import flask; print(flask.__version__)" 2>/dev/null)
    echo -e "${GREEN}Flask version $FLASK_VERSION is installed${NC}"
fi

# Start AILinux with the selected Python version
echo -e "${BLUE}Starting AILinux...${NC}"
NODE_OPTIONS=--max-old-space-size=4096 node start.js "$MODE" "$PYTHON_PATH"

# Exit status
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}AILinux exited successfully${NC}"
else
    echo -e "${RED}AILinux exited with error code $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
