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

# Check Python compatibility
echo -e "${BLUE}Checking Python compatibility...${NC}"
# Modify python-fix.py execution to capture exit code properly
python3 -c "
import sys
sys.path.append('$BASE_DIR')
from python-fix import check_python_compatibility

if not check_python_compatibility():
    print('${YELLOW}WARNING: Python compatibility issues detected!${NC}')
    print('${YELLOW}Flask may not work correctly with this Python version.${NC}')
    sys.exit(1)
sys.exit(0)
"
PY_COMPAT_STATUS=$?

if [ $PY_COMPAT_STATUS -ne 0 ]; then
    echo -e "${YELLOW}Python compatibility check failed!${NC}"
    echo -e "${YELLOW}The system may experience issues with Flask due to Python version incompatibility.${NC}"
    echo -e "${YELLOW}Recommended: Use Python 3.9-3.11 instead of Python 3.12+${NC}"
    
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

# Configure the Python path based on compatibility check
# If compatibility failed, try looking for Python 3.11 or 3.10 first
if [ $PY_COMPAT_STATUS -ne 0 ]; then
    echo -e "${YELLOW}Attempting to find compatible Python version...${NC}"
    if command -v python3.11 &> /dev/null; then
        export PYTHON_PATH="$(command -v python3.11)"
        echo -e "${GREEN}Found Python 3.11: $PYTHON_PATH${NC}"
    elif command -v python3.10 &> /dev/null; then
        export PYTHON_PATH="$(command -v python3.10)"
        echo -e "${GREEN}Found Python 3.10: $PYTHON_PATH${NC}"
    elif command -v python3.9 &> /dev/null; then
        export PYTHON_PATH="$(command -v python3.9)"
        echo -e "${GREEN}Found Python 3.9: $PYTHON_PATH${NC}"
    else
        echo -e "${YELLOW}No alternative Python version found. Using default path.${NC}"
        export PYTHON_PATH="/home/zombie/client/bin/python3"
    fi
else
    # Compatibility passed, use the standard path
    export PYTHON_PATH="/home/zombie/client/bin/python3"
fi

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

# Modify node start.js to use our potentially updated PYTHON_PATH
echo -e "${BLUE}Starting AILinux...${NC}"
PYTHON_PATH="$PYTHON_PATH" node start.js "$MODE"

# Exit status
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}AILinux exited successfully${NC}"
else
    echo -e "${RED}AILinux exited with error code $EXIT_CODE${NC}"
fi

exit $EXIT_CODE
