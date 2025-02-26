const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const config = require('./config.json');

let mainWindow;
const logFilePath = path.join(app.getPath('userData'), 'bot.log');

// Helper function to write logs
const writeLog = (message) => {
    const logEntry = `${new Date().toISOString()} - ${message}\n`;
    fs.appendFileSync(logFilePath, logEntry);
};

// Setup the main application window
const createMainWindow = () => {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
        },
    });

    mainWindow.loadFile('index.html');
    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    writeLog('Main window created');
};

// Handle AI chat messages
ipcMain.handle('chat-message', async (event, message, modelType) => {
    try {
        const response = await axios.post("http://127.0.0.1:8081/debug", {
            log: message,
            use_chatgpt: modelType === "chatgpt"
        });
        const botResponse = response.data.analysis;
        writeLog(`Bot response: ${botResponse}`);
        return botResponse;
    } catch (error) {
        writeLog(`Error: ${error.message}`);
        return "⚠ AI server is not responding!";
    }
});

// Electron App Ready
app.whenReady().then(() => {
    createMainWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createMainWindow();
        }
    });

    writeLog('App is ready');
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
    writeLog('All windows closed');
});
