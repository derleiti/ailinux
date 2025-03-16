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
