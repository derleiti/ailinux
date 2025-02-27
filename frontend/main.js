const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const axios = require('axios');

let mainWindow;

// Function to log messages to frontend log file
function writeLog(message) {
    const logFilePath = path.join(app.getPath('userData'), 'frontend/frontend.log');
    const logEntry = `${new Date().toISOString()} - ${message}\n`;
    fs.appendFileSync(logFilePath, logEntry);
}

// Create the main application window
function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')  // Preload script for additional API interaction
        }
    });

    // Load the main HTML file
    mainWindow.loadFile('index.html');
    writeLog("Main window loaded");

    // Handle the closing of the main window
    mainWindow.on('closed', () => {
        mainWindow = null;
        writeLog("Main window closed");
    });
}

// When the app is ready, create the window
app.whenReady().then(() => {
    writeLog("App is ready to be launched");
    createMainWindow();
});

// Handle the event where frontend sends a chat message to the backend
ipcMain.handle('chat-message', async (event, message, modelType) => {
    try {
        // Make a POST request to the backend (Flask API)
        const response = await axios.post("http://127.0.0.1:8081/debug", {
            log: message,
            model: modelType
        });

        // Log the AI response
        const botResponse = response.data.analysis;
        writeLog(`Received AI response: ${botResponse}`);

        // Return the AI response to the frontend
        return botResponse;
    } catch (error) {
        // Log the error if communication with backend fails
        writeLog(`Error communicating with backend: ${error.message}`);
        return "⚠ AI server is not responding!";
    }
});
