/**
 * Enhanced Python Environment Check Function
 * Addresses Flask SyntaxError issue
 */
async function checkPythonEnvironment() {
  return new Promise((resolve, reject) => {
    electronLog.info('Checking Python environment...');
    logMessage('Checking Python environment...', startLogPath);

    // Check that python path exists and is executable
    if (!fs.existsSync(pythonPath)) {
      const errorMsg = `Python interpreter not found at: ${pythonPath}`;
      electronLog.error(errorMsg);
      logMessage(`ERROR: ${errorMsg}`, startLogPath);
      return reject(new Error(errorMsg));
    }

    // First check Python version to ensure compatibility
    const checkPythonVersion = spawn(pythonPath, ['-c', 'import sys; print(sys.version_info[0], sys.version_info[1])']);
    
    let pythonVersionOutput = '';
    
    checkPythonVersion.stdout.on('data', (data) => {
      pythonVersionOutput += data.toString().trim();
    });

    checkPythonVersion.on('close', (code) => {
      if (code === 0) {
        const [major, minor] = pythonVersionOutput.split(' ').map(Number);
        
        // Log Python version info
        electronLog.info(`Python version: ${major}.${minor}`);
        logMessage(`Python version: ${major}.${minor}`, startLogPath);
        
        // Check if Python version is compatible (we want 3.9+ but < 3.12)
        if (major === 3 && (minor < 9 || minor >= 12)) {
          const versionWarnMsg = `Warning: Python ${major}.${minor} detected. This application works best with Python 3.9-3.11.`;
          electronLog.warn(versionWarnMsg);
          logMessage(versionWarnMsg, startLogPath);
        }
        
        // Check for Flask module (with error handling)
        const checkFlask = spawn(pythonPath, [
          '-c', 
          `
try:
    import flask
    print(f"Flask version: {flask.__version__}")
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

        checkFlask.on('close', (flaskCode) => {
          if (flaskCode === 0) {
            electronLog.info('Flask module is available');
            logMessage('Flask module is available', startLogPath);
            resolve(true);
          } else if (flaskCode === 1) {
            const errorMsg = 'Flask module not found. Please install Flask: pip install flask flask-cors';
            electronLog.error(errorMsg);
            logMessage(`ERROR: ${errorMsg}`, startLogPath);
            reject(new Error(errorMsg));
          } else if (flaskCode === 2) {
            const errorMsg = `Flask module has syntax errors with Python ${major}.${minor}. Try using Python 3.9-3.11.`;
            electronLog.error(errorMsg);
            logMessage(`ERROR: ${errorMsg}`, startLogPath);
            reject(new Error(errorMsg));
          } else {
            const errorMsg = `Flask check failed with code ${flaskCode}: ${flaskErrorOutput || flaskOutput || 'Unknown error'}`;
            electronLog.error(errorMsg);
            logMessage(`ERROR: ${errorMsg}`, startLogPath);
            reject(new Error(errorMsg));
          }
        });
        
      } else {
        const errorMsg = `Failed to check Python version: exit code ${code}`;
        electronLog.error(errorMsg);
        logMessage(`ERROR: ${errorMsg}`, startLogPath);
        reject(new Error(errorMsg));
      }
    });
  });
}
