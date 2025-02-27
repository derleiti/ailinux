require('dotenv').config();  // Load environment variables from .env file
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Define log file paths
const backendLogPath = path.join(__dirname, 'backend', 'backend.log');
const frontendLogPath = path.join(__dirname, 'frontend', 'frontend.log');
const startLogPath = path.join(__dirname, 'start.log');

// Function to initialize and overwrite log files
function initializeLog(filePath) {
  fs.writeFileSync(filePath, '');  // Clear the log file to overwrite
  console.log(`Log file initialized: ${filePath}`);
}

// Initialize logs
initializeLog(startLogPath);
initializeLog(backendLogPath);
initializeLog(frontendLogPath);

// Function to log messages to files
function logMessage(message, logPath) {
  const timestamp = new Date().toISOString();
  const logEntry = `${timestamp} - ${message}\n`;
  fs.appendFileSync(logPath, logEntry);
}

// Log initialization message in start log
logMessage('Initialization started', startLogPath);

// Fetch and log the API Key (useful for debugging)
const apiKey = process.env.API_KEY;
logMessage(`Your API key is: ${apiKey}`, startLogPath);

// Start the backend process
const backend = spawn('node', [path.join(__dirname, 'backend', 'app.js')]);

// Start the frontend process (Electron)
const frontend = spawn('electron', [path.join(__dirname, 'frontend', 'main.js')]);

// Log the start of backend process
logMessage('Starting backend process', startLogPath);

// Handle backend process exit
backend.on('exit', (code) => {
  const message = `Backend process exited with code ${code}`;
  console.error(message);
  logMessage(message, backendLogPath); // Log backend exit in backend log
  frontend.kill();  // Kill frontend if backend exits
  process.exit(code);  // Exit the whole script if backend fails
});

// Log when the frontend process starts
logMessage('Starting frontend process', startLogPath);

// Handle frontend process exit
frontend.on('exit', (code) => {
  const message = `Frontend process exited with code ${code}`;
  console.error(message);
  logMessage(message, frontendLogPath); // Log frontend exit in frontend log
  backend.kill();  // Kill backend if frontend fails
  process.exit(code);  // Exit the whole script if frontend fails
});

// Additional logging for LLaMA bot (debug logs)
const llamaLogPath = path.join(__dirname, 'backend', 'llama_debug.log');
function logLlamaDebug(message) {
  const timestamp = new Date().toISOString();
  const logEntry = `${timestamp} - LLaMA Bot Debug: ${message}\n`;
  fs.appendFileSync(llamaLogPath, logEntry);
}

// Example logging for LLaMA bot
logLlamaDebug('LLaMA Bot initialized and ready to process');
