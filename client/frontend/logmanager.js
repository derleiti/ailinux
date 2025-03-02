const { ipcMain } = require('electron');
const { createWriteStream, existsSync, mkdirSync } = require('fs');
const path = require('path');

// Configuration for log management
const MAX_LOG_FILES = 5;
const MAX_LOG_SIZE = 10 * 1024 * 1024; // 10 MB
const LOG_DIRECTORY = path.join(__dirname, 'logs');

// Initialize log directory
if (!existsSync(LOG_DIRECTORY)) {
  mkdirSync(LOG_DIRECTORY, { recursive: true });
}

class LogManager {
  constructor() {
    this.logs = [];
    this.currentFile = null;
  }

  /**
   * Write log entry to file and memory
   * @param {string} level - Log level (info, warn, error)
   * @param {string} message - Log message
   * @param {Object} [metadata] - Additional metadata
   */
  log(level, message, metadata = {}) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level: level.toUpperCase(),
      message,
      ...metadata
    };

    // Store in memory logs
    this.logs.push(logEntry);

    // Limit in-memory logs
    if (this.logs.length > 1000) {
      this.logs.shift();
    }

    // Write to log file
    this.writeToLogFile(JSON.stringify(logEntry));
  }

  /**
   * Write log entry to file with rotation
   * @param {string} entry - Log entry to write
   */
  writeToLogFile(entry) {
    const logFilePath = path.join(LOG_DIRECTORY, `ailinux-${new Date().toISOString().split('T')[0]}.log`);
    
    try {
      const writeStream = createWriteStream(logFilePath, { flags: 'a' });
      writeStream.write(entry + '\n');
      writeStream.end();
    } catch (error) {
      console.error('Error writing log file:', error);
    }
  }

  /**
   * Get recent logs
   * @param {number} [limit=50] - Number of logs to retrieve
   * @returns {Array} Recent log entries
   */
  getLogs(limit = 50) {
    return this.logs.slice(-limit);
  }

  /**
   * Clear in-memory logs
   */
  clearLogs() {
    this.logs = [];
  }
}

// Create singleton LogManager
const logManager = new LogManager();

/**
 * Register IPC handlers for log management
 * @param {Electron.BrowserWindow} mainWindow - Main application window
 */
function setupLogHandlers(mainWindow) {
  // Log from renderer
  ipcMain.handle('log', (event, { level, message, metadata }) => {
    logManager.log(level, message, metadata);
  });

  // Get logs
  ipcMain.handle('get-logs', (event, limit) => {
    return logManager.getLogs(limit);
  });

  // Clear logs
  ipcMain.handle('clear-logs', () => {
    logManager.clearLogs();
    return true;
  });
}

module.exports = {
  logManager,
  setupLogHandlers
};
