/**
 * Preload script for Electron frontend.
 * 
 * This script provides a secure bridge between the renderer process and 
 * the main process through contextBridge. It exposes a limited set of
 * APIs that the renderer can use to communicate with the main process.
 */

const { contextBridge, ipcRenderer } = require('electron');
const os = require('os');
const packageInfo = require('./package.json');

// Expose protected API to renderer
contextBridge.exposeInMainWorld('ailinuxAPI', {
    /**
     * Send a chat message to the AI model
     * @param {string} message - The message to send
     * @param {string} modelType - The AI model to use (gpt4all, openai, gemini, huggingface)
     * @returns {Promise<string>} - The AI's response
     */
    sendChatMessage: (message, modelType) => 
        ipcRenderer.invoke('chat-message', message, modelType),
    
    /**
     * Fetch logs from the backend
     * @returns {Promise<string[]>} - Array of log entries
     */
    fetchLogs: () => 
        ipcRenderer.invoke('fetch-logs'),
    
    /**
     * Save application settings
     * @param {Object} settings - Settings object to save
     * @returns {Promise<Object>} - Result of the save operation
     */
    saveSettings: (settings) => 
        ipcRenderer.invoke('save-settings', settings),
    
    /**
     * Get current application settings
     * @returns {Promise<Object>} - Current settings
     */
    getSettings: () => 
        ipcRenderer.invoke('get-settings'),
    
    /**
     * Open the settings window
     */
    openSettings: () => 
        ipcRenderer.send('open-settings'),
    
    /**
     * Open a log file dialog
     */
    openLogFile: () => 
        ipcRenderer.send('open-log-file'),
    
    /**
     * Save analysis results to a file
     * @param {string} content - The content to save
     * @returns {Promise<Object>} - Result of the save operation
     */
    saveAnalysisToFile: (content) => 
        ipcRenderer.invoke('save-analysis-to-file', content),
    
    /**
     * Check backend server status
     * @returns {Promise<Object>} - Server status information
     */
    checkBackendStatus: () => 
        ipcRenderer.invoke('check-backend-status'),
    
    /**
     * Get available AI models
     * @returns {Promise<Array>} - Array of available models and their status
     */
    getAvailableModels: () => 
        ipcRenderer.invoke('get-available-models'),
    
    /**
     * Update WebSocket connection status
     * @param {boolean} connected - Whether the WebSocket is connected
     */
    updateWebSocketStatus: (connected) => 
        ipcRenderer.send('websocket-status-update', { connected }),
    
    /**
     * Register a callback for when a log file is opened
     * @param {Function} callback - Function to call when a log file is opened
     * @returns {Function} - Function to remove the listener
     */
    onLogFileOpened: (callback) => {
        const subscription = (event, fileData) => callback(fileData);
        ipcRenderer.on('log-file-opened', subscription);
        return () => ipcRenderer.removeListener('log-file-opened', subscription);
    },
    
    /**
     * Register a callback for save analysis requests
     * @param {Function} callback - Function to call when save is requested
     * @returns {Function} - Function to remove the listener
     */
    onSaveAnalysis: (callback) => {
        const subscription = () => callback();
        ipcRenderer.on('save-analysis', subscription);
        return () => ipcRenderer.removeListener('save-analysis', subscription);
    },
    
    /**
     * Register a callback for theme toggle requests
     * @param {Function} callback - Function to call when theme toggle is requested
     * @returns {Function} - Function to remove the listener
     */
    onToggleTheme: (callback) => {
        const subscription = () => callback();
        ipcRenderer.on('toggle-theme', subscription);
        return () => ipcRenderer.removeListener('toggle-theme', subscription);
    },
    
    /**
     * Register a callback for model setting requests
     * @param {Function} callback - Function to call when model setting is requested
     * @returns {Function} - Function to remove the listener
     */
    onSetModel: (callback) => {
        const subscription = (event, model) => callback(model);
        ipcRenderer.on('set-model', subscription);
        return () => ipcRenderer.removeListener('set-model', subscription);
    },
    
    /**
     * Register a callback for opening the model manager
     * @param {Function} callback - Function to call when model manager should open
     * @returns {Function} - Function to remove the listener
     */
    onOpenModelManager: (callback) => {
        const subscription = () => callback();
        ipcRenderer.on('open-model-manager', subscription);
        return () => ipcRenderer.removeListener('open-model-manager', subscription);
    },
    
    /**
     * Get system information
     * @returns {Object} - System information
     */
    getSystemInfo: () => ({
        platform: process.platform,
        arch: process.arch,
        version: packageInfo.version,
        electronVersion: process.versions.electron,
        nodeVersion: process.versions.node,
        chromeVersion: process.versions.chrome,
        cpus: os.cpus(),
        totalMemory: os.totalmem(),
        freeMemory: os.freemem()
    })
});

// Expose WebSocket API to the renderer
contextBridge.exposeInMainWorld('webSocketAPI', {
    /**
     * Initialize WebSocket with proper error handling
     * @param {string} url - WebSocket server URL
     * @param {Object} callbacks - Callback functions for WebSocket events
     * @returns {Object} - WebSocket control functions
     */
    createConnection: (url, callbacks = {}) => {
        let socket = null;
        let reconnectTimeout = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;
        const reconnectDelayMs = 3000;
        
        // Initialize WebSocket
        const initialize = () => {
            try {
                // Clear any existing reconnect timeout
                if (reconnectTimeout) {
                    clearTimeout(reconnectTimeout);
                    reconnectTimeout = null;
                }
                
                // Create the WebSocket
                socket = new WebSocket(url);
                
                // Set up event handlers
                socket.onopen = (event) => {
                    console.log('WebSocket connection established');
                    reconnectAttempts = 0;
                    
                    // Update status in main process
                    ipcRenderer.send('websocket-status-update', { connected: true });
                    
                    // Call user callback if provided
                    if (callbacks.onOpen) callbacks.onOpen(event);
                };
                
                socket.onmessage = (event) => {
                    // Call user callback if provided
                    if (callbacks.onMessage) callbacks.onMessage(event);
                };
                
                socket.onerror = (event) => {
                    console.error('WebSocket error:', event);
                    
                    // Call user callback if provided
                    if (callbacks.onError) callbacks.onError(event);
                };
                
                socket.onclose = (event) => {
                    console.log(`WebSocket connection closed: ${event.code} ${event.reason}`);
                    
                    // Update status in main process
                    ipcRenderer.send('websocket-status-update', { connected: false });
                    
                    // Call user callback if provided
                    if (callbacks.onClose) callbacks.onClose(event);
                    
                    // Attempt to reconnect if not closed cleanly and within max attempts
                    if (event.code !== 1000 && event.code !== 1001) {
                        if (reconnectAttempts < maxReconnectAttempts) {
                            reconnectAttempts++;
                            console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
                            
                            reconnectTimeout = setTimeout(() => {
                                initialize();
                            }, reconnectDelayMs * reconnectAttempts);
                        } else {
                            console.error(`Failed to reconnect after ${maxReconnectAttempts} attempts`);
                        }
                    }
                };
                
                return true;
            } catch (error) {
                console.error('Error initializing WebSocket:', error);
                
                // Call user callback if provided
                if (callbacks.onError) callbacks.onError(error);
                
                return false;
            }
        };
        
        // Initialize immediately
        initialize();
        
        // Return control functions
        return {
            // Send a message through the WebSocket
            send: (message) => {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    // If message is an object, convert to JSON
                    if (typeof message === 'object') {
                        socket.send(JSON.stringify(message));
                    } else {
                        socket.send(message);
                    }
                    return true;
                }
                return false;
            },
            
            // Close the WebSocket connection
            close: () => {
                if (socket) {
                    socket.close();
                    
                    // Clear any reconnect timeout
                    if (reconnectTimeout) {
                        clearTimeout(reconnectTimeout);
                        reconnectTimeout = null;
                    }
                    
                    return true;
                }
                return false;
            },
            
            // Check if the WebSocket is connected
            isConnected: () => {
                return socket && socket.readyState === WebSocket.OPEN;
            },
            
            // Force reconnection
            reconnect: () => {
                if (socket) {
                    socket.close();
                }
                
                // Clear any reconnect timeout
                if (reconnectTimeout) {
                    clearTimeout(reconnectTimeout);
                    reconnectTimeout = null;
                }
                
                // Reset reconnect attempts
                reconnectAttempts = 0;
                
                // Initialize again
                return initialize();
            }
        };
    }
});

// Log that preload script has loaded
console.log('AILinux preload script loaded successfully');
