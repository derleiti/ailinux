const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const electronLog = require('electron-log');
const Store = require('electron-store');

// Configure electron-log
electronLog.transports.file.resolvePathFn = () => path.join(__dirname, 'frontend.log');
electronLog.transports.file.level = 'debug';
electronLog.transports.console.level = 'debug';

// Initialize config store
const store = new Store({
  name: 'ailinux-config',
  defaults: {
    apiKeys: {
      openai: '',
      gemini: '',
      llama: ''
    },
    settings: {
      aiEnabled: true,
      loggingEnabled: true,
      computationMode: 'cpu',
      backend: {
        host: 'http://127.0.0.1',
        port: 8081
      }
    }
  }
});

let mainWindow;
let aiModelsWindow;

/**
 * Creates the main application window
 */
function createMainWindow() {
  electronLog.info('Creating main window');
  
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png')
  });

  // Load the index.html file
  mainWindow.loadFile(path.join(__dirname, 'index.html'));
  
  // Open DevTools in development mode
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  // Handle window close
  mainWindow.on('closed', () => {
    electronLog.info('Main window closed');
    mainWindow = null;
  });
}

/**
 * Creates a window to display AI model settings
 */
function createAIModelsWindow() {
  electronLog.info('Creating AI models window');
  
  aiModelsWindow = new BrowserWindow({
    width: 800,
    height: 600,
    parent: mainWindow,
    modal: true,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  aiModelsWindow.loadFile(path.join(__dirname, 'settings.html'));
  
  aiModelsWindow.on('closed', () => {
    electronLog.info('AI models window closed');
    aiModelsWindow = null;
  });
}

/**
 * Handles the chat message request to the backend
 * @param {string} message - The user message to process
 * @param {string} modelType - The AI model to use
 * @returns {Promise<string>} - The AI response
 */
async function handleChatMessage(message, modelType) {
  try {
    const { host, port } = store.get('settings.backend');
    const endpoint = `${host}:${port}/debug`;
    
    electronLog.info(`Sending message to backend at ${endpoint}`);
    electronLog.debug(`Message: ${message.substring(0, 50)}...`);
    
    const response = await axios.post(endpoint, {
      log: message,
      model: modelType
    });

    electronLog.info('Received response from backend');
    return response.data.analysis;
  } catch (error) {
    electronLog.error(`Error in handleChatMessage: ${error.message}`, error);
    
    // If we can't reach the backend, provide a useful error message
    if (error.code === 'ECONNREFUSED') {
      return "⚠️ Cannot connect to the backend server. Please make sure the backend is running.";
    }
    
    return `⚠️ Error: ${error.message}`;
  }
}

/**
 * Saves the application settings
 * @param {Object} settings - The settings to save
 * @returns {Object} - Status of the save operation
 */
function saveSettings(settings) {
  try {
    // Update API keys
    if (settings.apiKeys) {
      store.set('apiKeys', settings.apiKeys);
    }
    
    // Update general settings
    if (settings.aiEnabled !== undefined) {
      store.set('settings.aiEnabled', settings.aiEnabled);
    }
    
    if (settings.loggingEnabled !== undefined) {
      store.set('settings.loggingEnabled', settings.loggingEnabled);
    }
    
    if (settings.computationMode) {
      store.set('settings.computationMode', settings.computationMode);
    }
    
    electronLog.info('Settings saved successfully');
    return { success: true };
  } catch (error) {
    electronLog.error(`Error saving settings: ${error.message}`, error);
    return { success: false, error: error.message };
  }
}

/**
 * Gets the current application settings
 * @returns {Object} - The current settings
 */
function getSettings() {
  try {
    return {
      apiKeys: store.get('apiKeys'),
      aiEnabled: store.get('settings.aiEnabled'),
      loggingEnabled: store.get('settings.loggingEnabled'),
      computationMode: store.get('settings.computationMode')
    };
  } catch (error) {
    electronLog.error(`Error getting settings: ${error.message}`, error);
    return { error: error.message };
  }
}

// Initialize the app
app.whenReady().then(() => {
  electronLog.info('Application starting up');
  
  // Register IPC handlers
  ipcMain.handle('chat-message', async (event, message, modelType) => {
    return await handleChatMessage(message, modelType);
  });
  
  ipcMain.handle('get-settings', () => {
    return getSettings();
  });
  
  ipcMain.handle('save-settings', (event, settings) => {
    return saveSettings(settings);
  });
  
  ipcMain.handle('open-settings', () => {
    if (!aiModelsWindow) {
      createAIModelsWindow();
    } else {
      aiModelsWindow.focus();
    }
  });
  
  // Create the main window
  createMainWindow();
  
  // Handle macOS app activation
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

// Quit when all windows are closed except on macOS
app.on('window-all-closed', () => {
  electronLog.info('All windows closed');
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Log any unhandled exceptions
process.on('uncaughtException', (error) => {
  electronLog.error('Uncaught Exception:', error);
  dialog.showErrorBox(
    'An error occurred',
    `Uncaught Exception: ${error.message}\n\nSee the log for more details.`
  );
});
