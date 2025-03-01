/**
 * AILinux Start Script
 * 
 * This script starts both the backend Flask server and frontend Electron app.
 * It manages environment configuration for local or remote server connections,
 * with robust error handling and process management.
 */

require('dotenv').config();
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const electron = require('electron');
const electronLog = require('electron-log');

// Set up logging
electronLog.transports.file.level = 'info';
electronLog.transports.console.level = 'info';

// Process command line arguments
const args = process.argv.slice(2);
const mode = args[0] || 'local'; // Default to local mode if not specified

// Define directories and paths
const baseDir = __dirname;
const logDir = path.join(baseDir, 'logs');
const backendDir = path.join(baseDir, 'backend');
const frontendDir = path.join(baseDir, 'frontend');
const backendLogPath = path.join(logDir, 'backend.log');
const frontendLogPath = path.join(logDir, 'frontend.log');
const startLogPath = path.join(logDir, 'start.log');

// Store process handles for proper cleanup
let processes = {
  backend: null,
  frontend: null
};

// Flag to track if shutdown is in progress
let shuttingDown = false;

/**
 * Initialize logging environment
 */
function initializeLogging() {
  try {
    // Ensure log directory exists
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    
    // Initialize log files with headers
    const timestamp = new Date().toISOString();
    const logHeader = `=== AILinux Startup Log - ${timestamp} ===\n`;
    
    fs.writeFileSync(startLogPath, logHeader);
    fs.writeFileSync(backendLogPath, logHeader);
    fs.writeFileSync(frontendLogPath, logHeader);
    
    electronLog.info('Logging initialized successfully');
    logMessage('Logging system initialized', startLogPath);
  } catch (error) {
    console.error(`Error initializing logging: ${error.message}`);
    electronLog.error('Failed to initialize logging', error);
    process.exit(1);
  }
}

/**
 * Write message to specified log file
 * @param {string} message - Message to log
 * @param {string} logPath - Path to log file
 */
function logMessage(message, logPath) {
  try {
    const timestamp = new Date().toISOString();
    const logEntry = `${timestamp} - ${message}\n`;
    fs.appendFileSync(logPath, logEntry);
  } catch (error) {
    console.error('Error writing to log file:', error);
    electronLog.error(`Failed to write to log file: ${logPath}`, error);
  }
}

/**
 * Configure environment based on selected mode
 * @returns {Object} Environment configuration
 */
function configureEnvironment() {
  let flaskHost, flaskPort, wsServerUrl;

  if (mode === 'remote') {
    // Remote configuration (derleiti.de)
    flaskHost = 'derleiti.de';
    flaskPort = 8081;
    wsServerUrl = 'wss://derleiti.de:8082';
    
    electronLog.info('Running in REMOTE mode - connecting to derleiti.de');
    logMessage('Running in REMOTE mode - connecting to derleiti.de', startLogPath);
  } else {
    // Local configuration
    flaskHost = 'localhost';
    flaskPort = 8081;
    wsServerUrl = 'ws://localhost:8082';
    
    electronLog.info('Running in LOCAL mode - connecting to localhost');
    logMessage('Running in LOCAL mode - connecting to localhost', startLogPath);
  }

  // Set environment variables for processes
  process.env.FLASK_HOST = flaskHost;
  process.env.FLASK_PORT = flaskPort;
  process.env.WS_SERVER_URL = wsServerUrl;
  
  // Log configuration
  logMessage(`Configuration: Flask=${flaskHost}:${flaskPort}, WebSocket=${wsServerUrl}`, startLogPath);
  logMessage(`API Keys: OpenAI=${process.env.OPENAI_API_KEY ? 'SET' : 'NOT SET'}, Gemini=${process.env.GEMINI_API_KEY ? 'SET' : 'NOT SET'}`, startLogPath);

  return { flaskHost, flaskPort, wsServerUrl };
}

/**
 * Start the backend server
 * @returns {Promise} Resolves when backend is ready
 */
function startBackend() {
  return new Promise((resolve, reject) => {
    electronLog.info('Starting backend server...');
    logMessage('Starting backend server...', startLogPath);

    // Check if Python is available
    try {
      const pythonVersionCheck = spawn('python3', ['--version']);
      pythonVersionCheck.on('error', (err) => {
        electronLog.error('Python3 not found. Please ensure Python 3 is installed and in your PATH.');
        reject(new Error('Python3 not found'));
      });
    } catch (error) {
      electronLog.error('Failed to check Python version', error);
      reject(error);
      return;
    }

    // Start the backend process
    const backendProcess = spawn('python3', [
      path.join(backendDir, 'app.py'),
      mode // Pass mode to backend script
    ], {
      env: process.env
    });

    // Store process reference
    processes.backend = backendProcess;

    // Flag to track if backend has started successfully
    let backendStarted = false;
    let startTimeout = setTimeout(() => {
      if (!backendStarted) {
        electronLog.error('Backend server failed to start within timeout period');
        logMessage('ERROR: Backend server start timed out', startLogPath);
        reject(new Error('Backend start timeout'));
      }
    }, 30000); // 30 second timeout
    
    // Handle stdout (normal output)
    backendProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      logMessage(`Backend output: ${output}`, backendLogPath);
      electronLog.info(`[Backend] ${output}`);
      
      // Check for backend ready indicators
      if (output.includes('Running on') || output.includes('Debugger PIN')) {
        backendStarted = true;
        clearTimeout(startTimeout);
        electronLog.info('Backend server is running');
        logMessage('Backend server started successfully', startLogPath);
        resolve();
      }
    });

    // Handle stderr (error output)
    backendProcess.stderr.on('data', (data) => {
      const output = data.toString().trim();
      logMessage(`Backend error: ${output}`, backendLogPath);
      electronLog.error(`[Backend ERROR] ${output}`);
      
      // Don't treat all stderr as fatal - Flask outputs to stderr sometimes
      if (output.includes('Running on') || output.includes('Debugger PIN')) {
        backendStarted = true;
        clearTimeout(startTimeout);
        electronLog.info('Backend server is running (from stderr output)');
        logMessage('Backend server started successfully', startLogPath);
        resolve();
      }
    });

    // Handle process exit
    backendProcess.on('close', (code) => {
      if (!shuttingDown) {
        logMessage(`Backend process exited with code: ${code}`, startLogPath);
        electronLog.warn(`Backend process exited with code: ${code}`);
        
        if (!backendStarted) {
          clearTimeout(startTimeout);
          reject(new Error(`Backend process exited prematurely with code ${code}`));
        } else if (code !== 0) {
          // If backend was running but exited with error
          shutdownAll(`Backend process crashed with code ${code}`);
        }
      }
    });

    // Handle process errors
    backendProcess.on('error', (error) => {
      logMessage(`Backend process error: ${error.message}`, startLogPath);
      electronLog.error('Backend process error:', error);
      clearTimeout(startTimeout);
      reject(error);
    });
  });
}

/**
 * Start the frontend Electron app
 */
function startFrontend() {
  electronLog.info('Starting frontend Electron app...');
  logMessage('Starting frontend Electron app...', startLogPath);

  // Create frontend environment with server variables
  const frontendEnv = {
    ...process.env,
    FLASK_HOST: process.env.FLASK_HOST,
    FLASK_PORT: process.env.FLASK_PORT,
    WS_SERVER_URL: process.env.WS_SERVER_URL
  };

  // Start the frontend process with npm start (which should run electron)
  const frontendProcess = spawn('npm', ['start'], {
    cwd: frontendDir,
    env: frontendEnv,
    shell: true // Use shell for npm command
  });

  // Store process reference
  processes.frontend = frontendProcess;

  // Handle stdout
  frontendProcess.stdout.on('data', (data) => {
    const output = data.toString().trim();
    logMessage(`Frontend output: ${output}`, frontendLogPath);
    electronLog.info(`[Frontend] ${output}`);
  });

  // Handle stderr
  frontendProcess.stderr.on('data', (data) => {
    const output = data.toString().trim();
    logMessage(`Frontend error: ${output}`, frontendLogPath);
    electronLog.error(`[Frontend ERROR] ${output}`);
  });

  // Handle process exit
  frontendProcess.on('close', (code) => {
    if (!shuttingDown) {
      logMessage(`Frontend process exited with code: ${code}`, startLogPath);
      electronLog.info(`Frontend process exited with code: ${code}`);
      
      // Frontend exit should trigger full app shutdown
      shutdownAll('Frontend process exited');
    }
  });

  // Handle process errors
  frontendProcess.on('error', (error) => {
    logMessage(`Frontend process error: ${error.message}`, startLogPath);
    electronLog.error('Frontend process error:', error);
    shutdownAll(`Frontend error: ${error.message}`);
  });

  electronLog.info('Frontend process started');
  logMessage('Frontend process started', startLogPath);
}

/**
 * Shutdown all processes gracefully
 * @param {string} reason - Reason for shutdown
 */
function shutdownAll(reason = 'Normal shutdown') {
  // Prevent multiple shutdown attempts
  if (shuttingDown) return;
  shuttingDown = true;
  
  electronLog.info(`Shutting down all processes: ${reason}`);
  logMessage(`Shutting down all processes: ${reason}`, startLogPath);

  // Kill frontend first
  if (processes.frontend) {
    try {
      processes.frontend.kill();
      electronLog.info('Frontend process terminated');
    } catch (error) {
      electronLog.error('Error terminating frontend process:', error);
    }
  }

  // Kill backend
  if (processes.backend) {
    try {
      processes.backend.kill();
      electronLog.info('Backend process terminated');
    } catch (error) {
      electronLog.error('Error terminating backend process:', error);
    }
  }

  // Final logging
  logMessage('All processes shut down', startLogPath);
  electronLog.info('All processes shut down');
  
  // Allow some time for logging to finish
  setTimeout(() => {
    process.exit(0);
  }, 1000);
}

/**
 * Main function to start the application
 */
async function main() {
  try {
    // Initialize logging
    initializeLogging();
    
    // Configure environment
    configureEnvironment();
    
    // Start backend and wait for it to be ready
    await startBackend();
    
    // Start frontend
    startFrontend();
    
    electronLog.info(`AILinux started in ${mode.toUpperCase()} mode. Press Ctrl+C to stop.`);
    console.log(`AILinux started in ${mode.toUpperCase()} mode. Press Ctrl+C to stop.`);
    
  } catch (error) {
    electronLog.error('Error starting AILinux:', error);
    logMessage(`Startup error: ${error.message}`, startLogPath);
    console.error('Error starting AILinux:', error.message);
    process.exit(1);
  }
}

// Handle process termination signals
process.on('SIGINT', () => shutdownAll('Received SIGINT'));
process.on('SIGTERM', () => shutdownAll('Received SIGTERM'));
process.on('uncaughtException', (error) => {
  electronLog.error('Uncaught exception:', error);
  shutdownAll(`Uncaught exception: ${error.message}`);
});
process.on('unhandledRejection', (reason) => {
  electronLog.error('Unhandled rejection:', reason);
  shutdownAll(`Unhandled promise rejection: ${reason}`);
});

// Start the application
main();
