/**
 * Preload script for Electron frontend.
 * 
 * This script provides a secure bridge between the renderer process and 
 * the main process through contextBridge. It exposes a limited set of
 * APIs that the renderer can use to communicate with the main process.
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose API to renderer
contextBridge.exposeInMainWorld('ailinuxAPI', {
    /**
     * Send a chat message to the AI model
     * @param {string} message - The message to send
     * @param {string} modelType - The AI model to use (gpt4all, chatgpt, gemini)
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
     * Register a callback for backend status updates
     * @param {Function} callback - Function to call when backend status changes
     */
    onBackendStatusChange: (callback) => {
        const subscription = (event, status) => callback(status);
        ipcRenderer.on('backend-status', subscription);
        
        // Return a function to remove the listener
        return () => {
            ipcRenderer.removeListener('backend-status', subscription);
        };
    },
    
    /**
     * Get the version of the application
     * @returns {string} - Application version
     */
    getAppVersion: () => {
        return require('electron').app.getVersion();
    }
});

// Log that preload script has finished loading
console.log('Preload script loaded successfully');
