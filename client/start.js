/**
 * AILinux Start Script (Optimized)
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

// Set up logging with explicit app name configuration
electronLog.transports.file.level = 'info';
electronLog.transports.console.level = 'info';
electronLog.transports.file.resolvePathFn = () => path.join(process.cwd(), 'logs', 'electron.log');

// Process command line arguments
const args = process.argv.slice(2);
const mode = args[0] || 'local'; // Default to local mode if not specified
const pythonPath = args[1] || process.env.PYTHON_PATH || 'python3'; // Use Python path from args or env

// Define directories and paths
const baseDir = process.cwd();
const logDir = path.join(baseDir, 'logs');
const backendDir = path.join(baseDir, 'backend');
const frontendDir = path.join(baseDir, 'frontend');
const backendLogPath = path.join(logDir, 'backend.log');
const frontendLogPath = path.join(logDir, 'frontend.log');
const startLogPath = path.join(logDir, 'start.log');

// Store process handles for proper cleanup
const processes = {
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
  logMessage(`API Keys: OpenAI=${process.env.OPENAI_API_KEY ? 'SET' : 'NOT SET'}, Gemini=${process.env.GEMINI_API_KEY ? 'SET' : 'NOT SET'}, HuggingFace=${process.env.HUGGINGFACE_API_KEY ? 'SET' : 'NOT SET'}`, startLogPath);
  logMessage(`Using Python interpreter: ${pythonPath}`, startLogPath);

  return { flaskHost, flaskPort, wsServerUrl };
}

/**
 * Check Python environment and dependencies
 * @returns {Promise<boolean>} Resolves to true if environment is valid
 */
async function checkPythonEnvironment() {
  return new Promise((resolve, reject) => {
    electronLog.info('Checking Python environment...');
    logMessage('Checking Python environment...', startLogPath);

    // Check that python path exists and is executable
    try {
      // Use spawn with a simple command to check if Python is executable
      const pythonCheck = spawn(pythonPath, ['-c', 'print("Python check succeeded")']);
      
      pythonCheck.on('error', (error) => {
        const errorMsg = `Python interpreter error: ${error.message}`;
        electronLog.error(errorMsg);
        logMessage(`ERROR: ${errorMsg}`, startLogPath);
        reject(new Error(errorMsg));
      });
      
      pythonCheck.on('close', (code) => {
        if (code !== 0) {
          const errorMsg = `Python interpreter check failed with code ${code}`;
          electronLog.error(errorMsg);
          logMessage(`ERROR: ${errorMsg}`, startLogPath);
          reject(new Error(errorMsg));
        } else {
          electronLog.info('Python interpreter is available');
          
          // Now check for Flask module
          const checkFlask = spawn(pythonPath, [
            '-c', 
            `
try:
    import flask
    print(f"Flask version: {flask.__version__}")
    exit(0)
except ImportError:
    print("Flask not installed")
    exit(1)
except SyntaxError as e:
    print(f"Flask syntax error: {e}")
    exit(2)
except Exception as e:
    print(f"Flask import error: {e}")
    exit(3)
            `
          ]);
          
          let flaskOutput = '';
          let flaskErrorOutput = '';
          
          checkFlask.stdout.on('data', (data) => {
            const output = data.toString().trim();
            flaskOutput += output;
            electronLog.info(`Flask check: ${output}`);
            logMessage(`Flask check: ${output}`, startLogPath);
          });

          checkFlask.stderr.on('data', (data) => {
            const output = data.toString().trim();
            flaskErrorOutput += output;
            electronLog.error(`Flask check error: ${output}`);
            logMessage(`Flask check error: ${output}`, startLogPath);
          });

          checkFlask.on('error', (error) => {
            const errorMsg = `Error running Flask check: ${error.message}`;
            electronLog.error(errorMsg);
            logMessage(`ERROR: ${errorMsg}`, startLogPath);
            reject(new Error(errorMsg));
          });

          checkFlask.on('close', (flaskCode) => {
            if (flaskCode === 0) {
              electronLog.info('Flask module is available');
              logMessage('Flask module is available', startLogPath);
              resolve(true);
            } else if (flaskCode === 1) {
              const errorMsg = 'Flask module not found. Please install Flask: pip install flask flask-cors';
              electronLog.error(errorMsg);
              logMessage(`ERROR: ${errorMsg}`, startLogPath);
              resolve(false); // We resolve with false to allow startup without Flask
            } else if (flaskCode === 2) {
              const errorMsg = `Flask module has syntax errors with this Python version. Try using Python 3.9-3.11.`;
              electronLog.error(errorMsg);
              logMessage(`ERROR: ${errorMsg}`, startLogPath);
              resolve(false); // We resolve with false to allow startup without Flask
            } else {
              const errorMsg = `Flask check failed with code ${flaskCode}: ${flaskErrorOutput || flaskOutput || 'Unknown error'}`;
              electronLog.error(errorMsg);
              logMessage(`ERROR: ${errorMsg}`, startLogPath);
              resolve(false); // We resolve with false to allow startup without Flask
            }
          });
        }
      });
    } catch (error) {
      const errorMsg = `Failed to run Python check: ${error.message}`;
      electronLog.error(errorMsg);
      logMessage(`ERROR: ${errorMsg}`, startLogPath);
      reject(new Error(errorMsg));
    }
  });
}

/**
 * Start the backend server
 * @returns {Promise} Resolves when backend is ready or after timeout
 */
function startBackend() {
  return new Promise((resolve, reject) => {
    electronLog.info('Starting backend server...');
    logMessage('Starting backend server...', startLogPath);

    // Start the backend process using the specified Python interpreter
    const backendProcess = spawn(pythonPath, [
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
        const warningMsg = 'Backend server taking longer than expected, continuing startup...';
        electronLog.warn(warningMsg);
        logMessage(warningMsg, startLogPath);
        // Resolve anyway to allow frontend to start
        resolve(false);
      }
    }, 10000); // 10 second timeout - reduced to make startup faster
    
    // Handle stdout (normal output)
    backendProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      logMessage(output, backendLogPath);
      electronLog.info(`[Backend] ${output}`);
      
      // Check for backend ready indicators
      if (output.includes('Running on') || output.includes('Debugger PIN')) {
        backendStarted = true;
        clearTimeout(startTimeout);
        electronLog.info('Backend server is running');
        logMessage('Backend server started successfully', startLogPath);
        resolve(true);
      }
    });

    // Handle stderr (error output)
    backendProcess.stderr.on('data', (data) => {
      const output = data.toString().trim();
      logMessage(output, backendLogPath);
      electronLog.error(`[Backend] ${output}`);
      
      // Don't treat all stderr as fatal - Flask outputs to stderr sometimes
      if (output.includes('Running on') || output.includes('Debugger PIN')) {
        backendStarted = true;
        clearTimeout(startTimeout);
        electronLog.info('Backend server is running (from stderr output)');
        logMessage('Backend server started successfully', startLogPath);
        resolve(true);
      }
    });

    // Handle process exit
    backendProcess.on('close', (code) => {
      if (!shuttingDown) {
        logMessage(`Backend process exited with code: ${code}`, startLogPath);
        electronLog.warn(`Backend process exited with code: ${code}`);
        
        if (!backendStarted) {
          clearTimeout(startTimeout);
          // Just warn, don't reject to allow frontend to start
          electronLog.warn(`Backend failed to start properly. Will continue with frontend only.`);
          logMessage('Backend failed to start properly. Will continue with frontend only.', startLogPath);
          resolve(false);
        }
      }
    });

    // Handle process errors
    backendProcess.on('error', (error) => {
      logMessage(`Backend process error: ${error.message}`, startLogPath);
      electronLog.error('Backend process error:', error);
      clearTimeout(startTimeout);
      // Just warn, don't reject to allow frontend to start
      resolve(false);
    });
  });
}

/**
 * Start the frontend Electron app
 * @returns {Promise} Resolves when frontend process is started
 */
function startFrontend() {
  return new Promise((resolve, reject) => {
    electronLog.info('Starting frontend Electron app...');
    logMessage('Starting frontend Electron app...', startLogPath);

    // Create frontend environment with server variables
    const frontendEnv = {
      ...process.env,
      FLASK_HOST: process.env.FLASK_HOST,
      FLASK_PORT: process.env.FLASK_PORT,
      WS_SERVER_URL: process.env.WS_SERVER_URL,
      ELECTRON_APP_NAME: 'ailinux' // Explicitly set app name for Electron
    };

    // Check if we're running from within the frontend directory
    const frontendPackageJsonPath = path.join(frontendDir, 'package.json');
    if (!fs.existsSync(frontendPackageJsonPath)) {
      electronLog.warn(`Frontend package.json not found at ${frontendPackageJsonPath}`);
      
      // Try to find package.json in parent directory
      const parentPackageJsonPath = path.join(baseDir, 'package.json');
      if (fs.existsSync(parentPackageJsonPath)) {
        electronLog.info(`Found package.json in parent directory, using direct Electron startup`);
        
        // Direct Electron startup
        const electronPath = electron;
        const mainFile = path.join(frontendDir, 'main.js');
        
        if (fs.existsSync(mainFile)) {
          const frontendProcess = spawn(electronPath, [mainFile], {
            env: frontendEnv
          });

          processes.frontend = frontendProcess;
          setupFrontendListeners(frontendProcess);
          resolve(true);
        } else {
          electronLog.error(`Main file not found at ${mainFile}`);
          reject(new Error(`Main file not found at ${mainFile}`));
        }
      } else {
        electronLog.error('Could not find package.json for frontend');
        reject(new Error('Could not find package.json for frontend'));
      }
    } else {
      // Use npm start in the frontend directory
      const frontendProcess = spawn('npm', ['start'], {
        cwd: frontendDir,
        env: frontendEnv,
        shell: true // Use shell for npm command
      });

      processes.frontend = frontendProcess;
      setupFrontendListeners(frontendProcess);
      resolve(true);
    }
  });

  function setupFrontendListeners(frontendProcess) {
    // Handle stdout
    frontendProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      logMessage(output, frontendLogPath);
      electronLog.info(`[Frontend] ${output}`);
    });

    // Handle stderr
    frontendProcess.stderr.on('data', (data) => {
      const output = data.toString().trim();
      logMessage(output, frontendLogPath);
      electronLog.error(`[Frontend] ${output}`);
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
    
    // Check Python environment and dependencies
    const pythonOk = await checkPythonEnvironment();
    if (!pythonOk) {
      logMessage('Warning: Python environment check failed, but will attempt to continue', startLogPath);
      electronLog.warn('Python environment check failed, but will attempt to continue');
    }
    
    // Start backend and wait for it to be ready
    const backendStarted = await startBackend();
    if (!backendStarted) {
      logMessage('Warning: Backend did not start properly, continuing with frontend only', startLogPath);
      electronLog.warn('Backend did not start properly, continuing with frontend only');
    }
    
    // Start frontend
    await startFrontend();
    
    electronLog.info(`AILinux started in ${mode.toUpperCase()} mode. Press Ctrl+C to stop.`);
    console.log(`AILinux started in ${mode.toUpperCase()} mode. Press Ctrl+C to stop.`);
    
  } catch (error) {
    electronLog.error('Error starting AILinux:', error);
    logMessage(`Startup error: ${error.message}`, startLogPath);
    console.error(`Error starting AILinux: ${error.message}`);
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
