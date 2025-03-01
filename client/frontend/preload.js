/**
 * Preload script for AILinux Log Analysis
 * 
 * This script provides a secure bridge between the renderer process 
 * and backend for log analysis and processing.
 */

const { contextBridge, ipcRenderer } = require('electron');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

// Logging setup
const log = require('electron-log');
log.transports.file.level = 'info';
log.transports.console.level = 'debug';

// AI Analysis Child Process Management
let analysisProcess = null;

contextBridge.exposeInMainWorld('ailinuxAPI', {
    /**
     * Send log for AI analysis
     * @param {string} logText - Log text to analyze 
     * @param {string} modelType - AI model to use
     * @returns {Promise<string>} Analysis result
     */
    sendChatMessage: async (logText, modelType) => {
        try {
            // Spawn a Python subprocess for log analysis
            return new Promise((resolve, reject) => {
                const pythonPath = path.join(process.cwd(), 'venv', 'bin', 'python');
                const scriptPath = path.join(process.cwd(), 'backend', 'log_analysis.py');

                // Ensure clean subprocess handling
                if (analysisProcess) {
                    analysisProcess.kill();
                }

                analysisProcess = spawn(pythonPath, [
                    scriptPath, 
                    '--model', modelType, 
                    '--log', logText
                ]);

                let outputData = '';
                let errorData = '';

                analysisProcess.stdout.on('data', (data) => {
                    outputData += data.toString();
                });

                analysisProcess.stderr.on('data', (data) => {
                    errorData += data.toString();
                });

                analysisProcess.on('close', (code) => {
                    if (code === 0) {
                        resolve(outputData.trim());
                    } else {
                        reject(new Error(errorData || `Analysis process exited with code ${code}`));
                    }
                });

                analysisProcess.on('error', (error) => {
                    log.error('AI analysis process error:', error);
                    reject(error);
                });
            });
        } catch (error) {
            log.error('Log analysis error:', error);
            throw error;
        }
    },

    /**
     * Get system information for diagnostics
     * @returns {Object} System information
     */
    getSystemInfo: () => {
        return {
            platform: process.platform,
            arch: process.arch,
            cpus: os.cpus(),
            totalMemory: os.totalmem(),
            freeMemory: os.freemem(),
            homeDir: os.homedir(),
            tempDir: os.tmpdir()
        };
    },

    /**
     * Log diagnostic information
     * @param {string} level - Log level (info, warn, error)
     * @param {string} message - Log message
     */
    log: (level, message) => {
        switch(level) {
            case 'info':
                log.info(message);
                break;
            case 'warn':
                log.warn(message);
                break;
            case 'error':
                log.error(message);
                break;
            default:
                log.info(message);
        }
    }
});
