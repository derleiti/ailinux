#!/bin/bash
# Start AILinux with virtual environment
source "/home/zombie/Downloads/ailinux/client/venv/bin/activate"

# Install Flask if needed
if ! python -c "import flask" 2>/dev/null; then
  echo "Installing Flask and dependencies..."
  pip install flask flask-cors
fi

# Start the application
node start.js local "/home/zombie/Downloads/ailinux/client/venv/bin/python"
