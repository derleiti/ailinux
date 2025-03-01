/**
 * AILinux Electron Main Process
 * 
 * This file handles the main process of the Electron application,
 * creating windows, managing IPC communication, and handling application events.
 */

const { app, BrowserWindow, ipcMain, dialog, Menu, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const url = require('url');
const axios = require('axios');
const electronLog = require('electron-log');
const Store = require('electron-store');
require('dotenv').config();

// Configure logging
electronLog.transports.file.level = 'info';
electronLog.transports.console.level = 'debug';
electronLog.info('Application starting...');

// Initialize configuration store
const store = new Store({
  name: 'user-preferences',
  defaults: {
    windowSize: { width: 1200, height: 900 },
    serverUrl: process.env.SERVER_URL || 'http://localhost:8081',
    wsServerUrl: process.env.WS_SERVER_URL || 'ws://localhost:8082',
    theme: 'light',
    defaultModel: 'gpt4all',
    recentLogs: []
  }
});

// Global reference to the main window
let mainWindow = null;
let settingsWindow = null;

// Keep track of WebSocket connection status
let wsConnected = false;

/**
 * Create the main application window
 */
function createMainWindow() {
  const { width, height } = store.get('windowSize');
  
  mainWindow = new BrowserWindow({
    width,
    height,
    minWidth: 900,
    minHeight: 600,
    title: 'AILinux - AI-Powered Log Analysis',
    icon: path.join(__dirname, 'assets/icons/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load the main HTML file
  mainWindow.loadFile('index.html');

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Save window dimensions when closing
  mainWindow.on('close', () => {
    store.set('windowSize', mainWindow.getBounds());
  });

  // Create application menu
  createApplicationMenu();

  // Open DevTools if in development mode
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  // Log window creation
  electronLog.info('Main window created');
}

/**
 * Create the settings window
 */
function createSettingsWindow() {
  if (settingsWindow) {
    settingsWindow.focus();
    return;
  }

  settingsWindow = new BrowserWindow({
    width: 800,
    height: 700,
    parent: mainWindow,
    modal: true,
    title: 'AILinux Settings',
    icon: path.join(__dirname, 'assets/icons/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load the settings HTML file
  settingsWindow.loadFile('settings.html');

  // Ensure the window is properly cleaned up on close
  settingsWindow.on('closed', () => {
    settingsWindow = null;
  });

  // Log settings window creation
  electronLog.info('Settings window created');
}

/**
 * Create the application menu
 */
function createApplicationMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Log File',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            await openLogFile();
          }
        },
        {
          label: 'Save Analysis',
          accelerator: 'CmdOrCtrl+S',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.send('save-analysis');
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Settings',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            createSettingsWindow();
          }
        },
        { type: 'separator' },
        { 
          label: 'Exit', 
          role: 'quit' 
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Toggle Theme',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.send('toggle-theme');
            }
          }
        },
        { type: 'separator' },
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'AI Models',
      submenu: [
        {
          label: 'Local Models',
          submenu: [
            {
              label: 'GPT4All',
              click: () => {
                if (mainWindow) {
                  mainWindow.webContents.send('set-model', 'gpt4all');
                }
              }
            },
            {
              label: 'Hugging Face',
              click: () => {
                if (mainWindow) {
                  mainWindow.webContents.send('set-model', 'huggingface');
                }
              }
            }
          ]
        },
        {
          label: 'Cloud Models',
          submenu: [
            {
              label: 'OpenAI',
              click: () => {
                if (mainWindow) {
                  mainWindow.webContents.send('set-model', 'openai');
                }
              }
            },
            {
              label: 'Google Gemini',
              click: () => {
                if (mainWindow) {
                  mainWindow.webContents.send('set-model', 'gemini');
                }
              }
            }
          ]
        },
        { type: 'separator' },
        {
          label: 'Manage Models',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.send('open-model-manager');
            }
          }
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: async () => {
            await shell.openExternal('https://github.com/derleiti/ailinux/wiki');
          }
        },
        {
          label: 'About AILinux',
          click: () => {
            showAboutDialog();
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * Show the About dialog
 */
function showAboutDialog() {
  dialog.showMessageBox(mainWindow, {
    title: 'About AILinux',
    message: 'AILinux - AI-Powered Log Analysis',
    detail: `Version: 1.0.0\n\nAn innovative tool for log analysis using multiple AI models.\n\nMIT License\nCopyright © 2025`,
    buttons: ['OK'],
    icon: path.join(__dirname, 'assets/icons/icon.png')
  });
}

/**
 * Open a log file and send its contents to the renderer
 */
async function openLogFile() {
  try {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile'],
      filters: [
        { name: 'Log Files', extensions: ['log', 'txt'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });

    if (!result.canceled && result.filePaths.length > 0) {
      const filePath = result.filePaths[0];
      const fileContent = fs.readFileSync(filePath, 'utf8');
      
      // Add to recent logs
      const recentLogs = store.get('recentLogs');
      const newRecentLogs = [
        { path: filePath, name: path.basename(filePath), timestamp: Date.now() },
        ...recentLogs.filter(item => item.path !== filePath).slice(0, 9)
      ];
      store.set('recentLogs', newRecentLogs);
      
      // Send to renderer
      mainWindow.webContents.send('log-file-opened', {
        content: fileContent,
        path: filePath,
        name: path.basename(filePath)
      });
      
      electronLog.info(`Opened log file: ${filePath}`);
    }
  } catch (error) {
    electronLog.error('Error opening log file:', error);
    dialog.showErrorBox(
      'Error Opening File',
      `Could not open the file: ${error.message}`
    );
  }
}

/**
 * Save analysis results to a file
 */
async function saveAnalysisToFile(content) {
  try {
    const result = await dialog.showSaveDialog(mainWindow, {
      filters: [
        { name: 'Text Files', extensions: ['txt'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });

    if (!result.canceled && result.filePath) {
      fs.writeFileSync(result.filePath, content, 'utf8');
      electronLog.info(`Analysis saved to: ${result.filePath}`);
      
      return { success: true, filePath: result.filePath };
    }
    
    return { success: false, cancelled: true };
  } catch (error) {
    electronLog.error('Error saving analysis:', error);
    dialog.showErrorBox(
      'Error Saving File',
      `Could not save the file: ${error.message}`
    );
    
    return { success: false, error: error.message };
  }
}

/**
 * Initialize IPC communication channels
 */
function initializeIPC() {
  // Chat message to AI model
  ipcMain.handle('chat-message', async (event, message, modelType) => {
    try {
      const serverUrl = store.get('serverUrl');
      electronLog.info(`Sending message to ${modelType} model`);
      
      const response = await axios.post(`${serverUrl}/debug`, {
        log: message,
        model: modelType
      });
      
      return response.data.analysis;
    } catch (error) {
      electronLog.error('Error sending chat message:', error);
      return `Error: ${error.message}`;
    }
  });

  // Fetch logs from the backend
  ipcMain.handle('fetch-logs', async () => {
    try {
      const serverUrl = store.get('serverUrl');
      const response = await axios.get(`${serverUrl}/logs`);
      return response.data.logs;
    } catch (error) {
      electronLog.error('Error fetching logs:', error);
      return [];
    }
  });

  // Save application settings
  ipcMain.handle('save-settings', async (event, settings) => {
    try {
      // Save local settings
      if (settings.serverUrl) store.set('serverUrl', settings.serverUrl);
      if (settings.wsServerUrl) store.set('wsServerUrl', settings.wsServerUrl);
      if (settings.theme) store.set('theme', settings.theme);
      if (settings.defaultModel) store.set('defaultModel', settings.defaultModel);
      
      // Save settings to backend
      const serverUrl = store.get('serverUrl');
      await axios.post(`${serverUrl}/settings`, settings);
      
      electronLog.info('Settings saved successfully');
      return { success: true };
    } catch (error) {
      electronLog.error('Error saving settings:', error);
      return { success: false, error: error.message };
    }
  });

  // Get current application settings
  ipcMain.handle('get-settings', async () => {
    try {
      // Get local settings
      const localSettings = {
        serverUrl: store.get('serverUrl'),
        wsServerUrl: store.get('wsServerUrl'),
        theme: store.get('theme'),
        defaultModel: store.get('defaultModel'),
        recentLogs: store.get('recentLogs')
      };
      
      // Try to get server settings
      try {
        const response = await axios.get(`${localSettings.serverUrl}/settings`);
        return { ...localSettings, ...response.data };
      } catch (serverError) {
        electronLog.warn('Could not fetch server settings:', serverError);
        return localSettings;
      }
    } catch (error) {
      electronLog.error('Error getting settings:', error);
      return {};
    }
  });

  // Open settings window
  ipcMain.on('open-settings', () => {
    createSettingsWindow();
  });

  // Save analysis to file
  ipcMain.handle('save-analysis-to-file', async (event, content) => {
    return await saveAnalysisToFile(content);
  });

  // Open log file
  ipcMain.on('open-log-file', async () => {
    await openLogFile();
  });
  
  // Get backend status
  ipcMain.handle('check-backend-status', async () => {
    try {
      const serverUrl = store.get('serverUrl');
      const response = await axios.get(`${serverUrl}/health`, { timeout: 5000 });
      return { 
        online: true, 
        wsConnected: wsConnected,
        serverInfo: response.data 
      };
    } catch (error) {
      electronLog.warn('Backend server appears to be offline:', error.message);
      return { online: false, wsConnected: false };
    }
  });

  // Get available models
  ipcMain.handle('get-available-models', async () => {
    try {
      const serverUrl = store.get('serverUrl');
      const response = await axios.get(`${serverUrl}/models`);
      return response.data.models;
    } catch (error) {
      electronLog.error('Error getting available models:', error);
      return [];
    }
  });
}

/**
 * Setup WebSocket connection status listeners
 */
function setupWebSocketStatusListeners() {
  // Listen for WebSocket connection status updates from renderer
  ipcMain.on('websocket-status-update', (event, status) => {
    wsConnected = status.connected;
    electronLog.info(`WebSocket connection status updated: ${wsConnected ? 'Connected' : 'Disconnected'}`);
  });
}

// Initialize the app
app.whenReady().then(() => {
  // Create the main window
  createMainWindow();
  
  // Initialize IPC handlers
  initializeIPC();
  
  // Setup WebSocket status listeners
  setupWebSocketStatusListeners();
  
  // On macOS, recreate the window when dock icon is clicked
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
  
  electronLog.info('Application ready and initialized');
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Handle any uncaught exceptions
process.on('uncaughtException', (error) => {
  electronLog.error('Uncaught Exception:', error);
  dialog.showErrorBox(
    'Error',
    `An unexpected error occurred: ${error.message}\n\nThe application will now close.`
  );
  app.quit();
});
