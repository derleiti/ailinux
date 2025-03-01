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

# Set up environment
echo -e "${BLUE}Setting up environment...${NC}"

# Configure the Python path to find Flask
export PYTHONPATH="/home/zombie/client/lib/python3.12/site-packages:$PYTHONPATH"

# Configure electron-log app name
export ELECTRON_APP_NAME="ailinux"

# Load existing .env file if it exists, or create a new one
if [ -f .env ]; then
    # Load the HUGGINGFACE_API_KEY from existing .env
    export $(grep -v '^#' .env | xargs)
    # Make sure ELECTRON_APP_NAME is set in the .env file
    if ! grep -q "ELECTRON_APP_NAME=" .env; then
        echo "ELECTRON_APP_NAME=ailinux" >> .env
    fi
else
    # Create new .env file with app name for Node.js
    echo "ELECTRON_APP_NAME=ailinux" > .env
    echo "# Add your HUGGINGFACE_API_KEY here if not already set" >> .env
fi

# Report API key status
if [ -n "$HUGGINGFACE_API_KEY" ]; then
    echo -e "${GREEN}Hugging Face API key is set${NC}"
else
    echo -e "${YELLOW}Warning: Hugging Face API key is not set in .env file${NC}"
fi

# Check if we should verify Flask installation
if [ "$2" == "--check-deps" ]; then
    echo -e "${BLUE}Checking dependencies...${NC}"
    PYTHON_PATH="/home/zombie/client/bin/python3"
    
    # Check if the Python interpreter exists
    if [ ! -f "$PYTHON_PATH" ]; then
        echo -e "${RED}Error: Python interpreter not found at $PYTHON_PATH${NC}"
        echo -e "${YELLOW}Falling back to system Python${NC}"
        PYTHON_PATH="python3"
    fi
    
    # Check if Flask is installed
    if ! $PYTHON_PATH -c "import flask" 2>/dev/null; then
        echo -e "${RED}Error: Flask module not found!${NC}"
        echo -e "${YELLOW}Please make sure Flask is installed:${NC}"
        echo -e "${GREEN}  pip install flask flask-cors${NC}"
        exit 1
    else
        FLASK_VERSION=$($PYTHON_PATH -c "import flask; print(flask.__version__)" 2>/dev/null)
        echo -e "${GREEN}Flask version $FLASK_VERSION is installed${NC}"
    fi
fi

# Start the optimized application
echo -e "${BLUE}Starting AILinux...${NC}"
node start.js "$MODE"

# Exit status
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}AILinux exited successfully${NC}"
else
    echo -e "${RED}AILinux exited with error code $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
