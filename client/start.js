/**
 * AILinux Startup Script
 * Enhanced with Python compatibility checks and error handling
 */

const { spawn, exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs');
const path = require('path');
const os = require('os');
const execAsync = promisify(exec);

// Configure logging
let electronLog;
try {
  electronLog = require('electron-log');
  electronLog.transports.file.level = 'info';
  electronLog.transports.console.level = 'debug';
} catch (error) {
  console.warn('electron-log not available, using console', error);
  // Create a minimal replacement
  electronLog = {
    info: console.log,
    warn: console.warn,
    error: console.error,
    debug: console.debug
  };
}

// Global configuration
const startLogPath = path.join(__dirname, 'logs', 'start.log');
let pythonPath = 'python3'; // Default, will be overridden
const
