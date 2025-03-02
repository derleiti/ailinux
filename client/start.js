// Enhanced Python version checking and selection
// Add this to the start.js file after the configureEnvironment function

/**
 * Find a compatible Python version (3.9-3.11)
 * @returns {Promise<string>} Path to compatible Python or default
 */
async function findCompatiblePython() {
  const { exec } = require('child_process');
  const util = require('util');
  const execAsync = util.promisify(exec);
  
  // Check for explicit Python versions first
  const versionsToCheck = ['python3.9', 'python3.10', 'python3.11'];
  
  for (const version of versionsToCheck) {
    try {
      await execAsync(`${version} --version`);
      electronLog.info(`Found compatible Python version: ${version}`);
      logMessage(`Found compatible Python version: ${version}`, startLogPath);
      return version;
    } catch (error) {
      // This version is not available, try the next one
    }
  }
  
  // Check system python3 version
  try {
    const { stdout } = await execAsync('python3 --version');
    const match = stdout.match(/Python (\d+)\.(\d+)\.\d+/);
    
    if (match) {
      const major = parseInt(match[1]);
      const minor = parseInt(match[2]);
      
      if (major === 3 && minor >= 9 && minor <= 11) {
        electronLog.info(`System Python3 version is compatible: ${stdout.trim()}`);
        logMessage(`System Python3 version is compatible: ${stdout.trim()}`, startLogPath);
        return 'python3';
      } else {
        electronLog.warn(`System Python3 version may not be compatible: ${stdout.trim()}`);
        logMessage(`Warning: System Python3 version may not be compatible: ${stdout.trim()}`, startLogPath);
      }
    }
  } catch (error) {
    // Python3 not found or cannot be executed
  }
  
  // Check specific paths that might contain compatible Python
  const specificPaths = [
    '/home/zombie/client/bin/python3.9',
    '/home/zombie/client/bin/python3.10',
    '/home/zombie/client/bin/python3.11',
    '/usr/bin/python3.9',
    '/usr/bin/python3.10',
    '/usr/bin/python3.11',
    '/usr/local/bin/python3.9',
    '/usr/local/bin/python3.10',
    '/usr/local/bin/python3.11'
  ];
  
  for (const path of specificPaths) {
    try {
      const { stdout } = await execAsync(`${path} --version`);
      electronLog.info(`Found Python at specific path: ${path} (${stdout.trim()})`);
      logMessage(`Found Python at specific path: ${path} (${stdout.trim()})`, startLogPath);
      return path;
    } catch (error) {
      // This path is not available, try the next one
    }
  }
  
  // If no compatible version found, return the provided default
  electronLog.warn(`No compatible Python version found, using default: ${pythonPath}`);
  logMessage(`Warning: No compatible Python version found, using default: ${pythonPath}`, startLogPath);
  return pythonPath;
}

// Modified main function to use compatible Python
async function main() {
  try {
    // Initialize logging
    initializeLogging();
    
    // Configure environment
    configureEnvironment();
    
    // Find a compatible Python version (3.9-3.11)
    const compatiblePython = await findCompatiblePython();
    // Override the pythonPath with a compatible version
    global.pythonPath = compatiblePython;
    
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