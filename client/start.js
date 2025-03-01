/**
 * AILinux Start Script
 * 
 * This script starts both the backend Flask server and frontend Electron app.
 * It manages environment configuration for local or remote server connections.
 */

require('dotenv').config();
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Process command line arguments
const args = process.argv.slice(2);
const mode = args[0] || 'local'; // Default to local mode if not specified

// Define log file paths
const baseDir = __dirname;
const logDir = path.join(baseDir, 'logs');
const backendLogPath = path.join(baseDir, 'backend', 'backend.log');
const frontendLogPath = path.join(baseDir, 'frontend', 'frontend.log');
const startLogPath = path.join(baseDir, 'start.log');

// Ensure log directory exists
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

// Initialize log files
function initializeLog(filePath) {
  try {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(filePath, '');
    console.log(`Log file initialized: ${filePath}`);
  } catch (error) {
    console.error(`Error initializing log file: ${filePath}`, error);
  }
}

// Write messages to log files
function logMessage(message, logPath) {
  try {
    const timestamp = new Date().toISOString();
    const logEntry = `${timestamp} - ${message}\n`;
    fs.appendFileSync(logPath, logEntry);
  } catch (error) {
    console.error('Error writing to log file:', error);
  }
}

// Initialize logs
initializeLog(startLogPath);
initializeLog(backendLogPath);
initializeLog(frontendLogPath);

// Configure environment based on selected mode
let flaskHost, flaskPort, wsServerUrl;

if (mode === 'remote') {
  // Remote configuration (derleiti.de)
  flaskHost = 'derleiti.de';
  flaskPort = 8081;
  wsServerUrl = 'wss://derleiti.de:8082';
  
  // Set environment variables for processes
  process.env.FLASK_HOST = flaskHost;
  process.env.FLASK_PORT = flaskPort;
  process.env.WS_SERVER_URL = wsServerUrl;
  
  console.log('Running in REMOTE mode - connecting to derleiti.de');
  logMessage('Running in REMOTE mode - connecting to derleiti.de', startLogPath);
} else {
  // Local configuration
  flaskHost = 'localhost';
  flaskPort = 8081;
  wsServerUrl = 'ws://localhost:8082';
  
  // Set environment variables for processes
  process.env.FLASK_HOST = flaskHost;
  process.env.FLASK_PORT = flaskPort;
  process.env.WS_SERVER_URL = wsServerUrl;
  
  console.log('Running in LOCAL mode - connecting to localhost');
  logMessage('Running in LOCAL mode - connecting to localhost', startLogPath);
}

// Log configuration
logMessage(`Configuration: Flask=${flaskHost}:${flaskPort}, WebSocket=${wsServerUrl}`,
startLogPath);
logMessage(`API Keys: OpenAI=${process.env.OPENAI_API_KEY ? 'SET' : 'NOT SET'},
Gemini=${process.env.GEMINI_API_KEY ? 'SET' : 'NOT SET'}`, startLogPath);

// Start the backend process with the selected mode
const backendProcess = spawn('python3', [
  path.join(baseDir, 'backend', 'app.py'),
  mode // Pass mode to backend script
]);

// Log backend start
logMessage('Backend process started', startLogPath);

// Start the frontend process
const frontendProcess = spawn('npm', ['start'], {
  cwd: path.join(baseDir, 'frontend'),
  env: { 
    ...process.env,
    FLASK_HOST: flaskHost,
    FLASK_PORT: flaskPort,
    WS_SERVER_URL: wsServerUrl
  }
});

// Log frontend start
logMessage('Frontend process started', startLogPath);

// Handle backend process outputs
backendProcess.stdout.on('data', (data) => {
  const output = data.toString().trim();
  logMessage(`Backend output: ${output}`, backendLogPath);
  console.log(`[Backend] ${output}`);
});

backendProcess.stderr.on('data', (data) => {
  const output = data.toString().trim();
  logMessage(`Backend error: ${output}`, backendLogPath);
  console.error(`[Backend ERROR] ${output}`);
});

// Handle frontend process outputs
frontendProcess.stdout.on('data', (data) => {
  const output = data.toString().trim();
  logMessage(`Frontend output: ${output}`, frontendLogPath);
  console.log(`[Frontend] ${output}`);
});

frontendProcess.stderr.on('data', (data) => {
  const output = data.toString().trim();
  logMessage(`Frontend error: ${output}`, frontendLogPath);
  console.error(`[Frontend ERROR] ${output}`);
});

// Handle process exit
backendProcess.on('close', (code) => {
  logMessage(`Backend process exited with code: ${code}`, startLogPath);
  console.log(`Backend process exited with code: ${code}`);
  
  // When backend exits, terminate frontend as well
  if (frontendProcess) {
    frontendProcess.kill();
  }
});

frontendProcess.on('close', (code) => {
  logMessage(`Frontend process exited with code: ${code}`, startLogPath);
  console.log(`Frontend process exited with code: ${code}`);
  
  // When frontend exits, terminate backend as well
  if (backendProcess) {
    backendProcess.kill();
  }
});

// Handle script termination
process.on('SIGINT', () => {
  logMessage('Received SIGINT. Shutting down all processes...', startLogPath);
  console.log('Shutting down all processes...');
  
  if (backendProcess) backendProcess.kill();
  if (frontendProcess) frontendProcess.kill();
  
  process.exit(0);
});

console.log(`AILinux started in ${mode.toUpperCase()} mode. Press Ctrl+C to stop.`);
