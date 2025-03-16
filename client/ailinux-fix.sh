#!/bin/bash
# Simple AILinux Fix Script
# This script fixes the two most critical issues:
# 1. Fixes the incomplete start.js file
# 2. Creates a Python virtual environment for dependencies

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE_DIR"
echo -e "${BLUE}Working in directory:${NC} $BASE_DIR"

# Step 1: Fix start.js
echo -e "${BLUE}Fixing start.js file...${NC}"
START_JS="$BASE_DIR/start.js"

# Create backup
cp "$START_JS" "$START_JS.bak" 2>/dev/null
echo "Created backup at $START_JS.bak"

# Write the fixed start.js file (a minimal working version)
cat > "$START_JS" << 'ENDOFJS'
/**
 * AILinux Startup Script - Fixed Version
 */
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Ensure log directory exists
const logDir = path.join(__dirname, 'logs');
try {
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }
} catch (error) {
  console.error(`Error creating log directory: ${error.message}`);
}

console.log('=== AILinux Startup Script ===');

// Get Python path from command line or use default
const pythonPath = process.argv[3] || 'python3';
console.log(`Using Python: ${pythonPath}`);

// Get mode from command line
const mode = process.argv[2] || 'local';
console.log(`Mode: ${mode}`);

// Find backend directory
let backendPath = '';
const possibleBackendPaths = [
  path.join(__dirname, 'backend', 'app.py'),
  path.join(__dirname, 'client', 'backend', 'app.py')
];

for (const testPath of possibleBackendPaths) {
  if (fs.existsSync(testPath)) {
    backendPath = testPath;
    break;
  }
}

if (!backendPath) {
  console.error('Error: Backend app.py not found!');
  process.exit(1);
}

// Start backend server
console.log(`Starting backend server: ${backendPath}`);
const backendProcess = spawn(pythonPath, [backendPath], {
  env: {
    ...process.env,
    FLASK_HOST: mode === 'local' ? 'localhost' : '0.0.0.0',
    FLASK_PORT: process.env.FLASK_PORT || '8081'
  }
});

// Log backend output
backendProcess.stdout.on('data', (data) => {
  console.log(`Backend: ${data.toString().trim()}`);
});

backendProcess.stderr.on('data', (data) => {
  console.error(`Backend error: ${data.toString().trim()}`);
});

// Handle backend exit
backendProcess.on('exit', (code) => {
  console.log(`Backend exited with code ${code}`);
  process.exit(code);
});

// Handle main process exit
process.on('SIGINT', () => {
  console.log('Shutting down backend server...');
  backendProcess.kill();
  process.exit(0);
});

console.log('Backend server started. Press Ctrl+C to exit.');
console.log(`Backend URL: http://localhost:${process.env.FLASK_PORT || 8081}`);
ENDOFJS

echo -e "${GREEN}✓ Fixed start.js file${NC}"

# Step 2: Create virtual environment
echo -e "${BLUE}Setting up Python virtual environment...${NC}"
VENV_DIR="$BASE_DIR/venv"

# Check if venv already exists
if [ -d "$VENV_DIR" ]; then
  echo "Virtual environment already exists at $VENV_DIR"
else
  echo "Creating virtual environment at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
  if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to create virtual environment${NC}"
    echo "Make sure python3-venv is installed:"
    echo "sudo apt install python3-venv"
    exit 1
  fi
  echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Create activation script
ACTIVATE_SCRIPT="$BASE_DIR/activate.sh"
cat > "$ACTIVATE_SCRIPT" << EOL
#!/bin/bash
# Activate AILinux virtual environment
source "$VENV_DIR/bin/activate"
EOL
chmod +x "$ACTIVATE_SCRIPT"
echo -e "${GREEN}✓ Created activation script at $ACTIVATE_SCRIPT${NC}"

# Create start with venv script
START_VENV_SCRIPT="$BASE_DIR/start_venv.sh"
cat > "$START_VENV_SCRIPT" << EOL
#!/bin/bash
# Start AILinux with virtual environment
source "$VENV_DIR/bin/activate"

# Install Flask if needed
if ! python -c "import flask" 2>/dev/null; then
  echo "Installing Flask and dependencies..."
  pip install flask flask-cors
fi

# Start the application
node start.js local "$VENV_DIR/bin/python"
EOL
chmod +x "$START_VENV_SCRIPT"
echo -e "${GREEN}✓ Created start script with virtual environment at $START_VENV_SCRIPT${NC}"

echo
echo -e "${GREEN}=== Fixes applied successfully ===${NC}"
echo "To start AILinux with the virtual environment, run:"
echo -e "${BLUE}./start_venv.sh${NC}"
echo
