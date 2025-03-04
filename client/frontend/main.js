/**
 * AILinux Electron Main Process
 * Combines features from existing implementation with enhanced security
 */
const { app, BrowserWindow, ipcMain, dialog, Menu, shell } = require('electron');
const path = require('path');
const fs = require('fs').promises;
const axios = require('axios');
const electronLog = require('electron-log');
const dotenv = require('dotenv');

// Dynamically import electron-store with a wrapper
const createStore = async () => {
  try {
    const Store = await import('electron-store');
    return new Store.default({
      name: 'ailinux-app-state',
      defaults: {
        windowBounds: { width: 1200, height: 900 },
        theme: 'system',
        serverUrl: process.env.SERVER_URL || 'http://localhost:8081',
        wsServerUrl: process.env.WS_SERVER_URL || 'ws://localhost:8082',
        recentLogs: [],
        defaultModel: process.env.DEFAULT_MODEL || 'gpt4all'
      }
    });
  } catch (error) {
    electronLog.error('Failed to load electron-store:', error);
    throw error;
  }
};

// Load environment variables
dotenv.config();

// Configure logging
electronLog.transports.file.level = 'info';
electronLog.transports.console.level = 'debug';
electronLog.initialize({ deep: true });

// Global reference to main window and store
let mainWindow = null;
let settingsWindow = null;
let store = null;

/**
 * Create the main application window
 */
async function createMainWindow() {
  // Ensure store is initialized
  if (!store) {
    store = await createStore();
  }

  const { width, height } = store.get('windowBounds');
  
  mainWindow = new BrowserWindow({
    width,
    height,
    minWidth: 900,
    minHeight: 600,
    title: 'AILinux',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      enableRemoteModule: false,
      worldSafeExecuteJavaScript: true,
      sandbox: true
    }
  });

  // Load the main HTML file
  mainWindow.loadFile('index.html');

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  // Save window dimensions
  mainWindow.on('resize', () => {
    store.set('windowBounds', mainWindow.getBounds());
  });

  // DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }
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
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  settingsWindow.loadFile('settings.html');

  settingsWindow.on('closed', () => {
    settingsWindow = null;
  });
}

/**
 * Setup IPC handlers for inter-process communication
 */
function setupIpcHandlers() {
  // Fetch logs from backend
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

  // Get system status
  ipcMain.handle('get-system-status', async () => {
    try {
      const serverUrl = store.get('serverUrl');
      const response = await axios.get(`${serverUrl}/system`);
      return response.data;
    } catch (error) {
      electronLog.error('Error getting system status:', error);
      return null;
    }
  });

  // Manage API keys
  ipcMain.handle('update-api-key', (event, { service, key }) => {
    try {
      const config = store.get('ai.models') || {};
      config[service] = { apiKey: key, enabled: !!key };
      store.set('ai.models', config);
      return true;
    } catch (error) {
      electronLog.error('API key update error:', error);
      return false;
    }
  });

  // Check backend health
  ipcMain.handle('check-backend', async () => {
    try {
      const serverUrl = store.get('serverUrl');
      const response = await axios.get(`${serverUrl}/health`, { timeout: 5000 });
      return { 
        online: true, 
        details: response.data 
      };
    } catch (error) {
      electronLog.warn('Backend health check failed:', error.message);
      return { 
        online: false, 
        error: error.message 
      };
    }
  });
}

/**
 * Create application menu
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
            try {
              const { filePaths } = await dialog.showOpenDialog({
                properties: ['openFile'],
                filters: [{ name: 'Log Files', extensions: ['log', 'txt'] }]
              });
              
              if (filePaths && filePaths.length > 0) {
                const logContent = await fs.readFile(filePaths[0], 'utf-8');
                electronLog.info(`Opened log file: ${filePaths[0]}`);
                mainWindow.webContents.send('log-file-opened', logContent);
              }
            } catch (error) {
              electronLog.error('Error opening log file:', error);
              dialog.showErrorBox('Error', 'Could not open log file');
            }
          }
        },
        { type: 'separator' },
        { 
          label: 'Settings', 
          accelerator: 'CmdOrCtrl+,',
          click: createSettingsWindow 
        },
        { role: 'quit' }
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
        { role: 'paste' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * Initialize application lifecycle
 */
async function initializeApp() {
  app.on('ready', async () => {
    try {
      // Initialize store before other operations
      store = await createStore();
      
      createMainWindow();
      setupIpcHandlers();
      createApplicationMenu();
    } catch (error) {
      electronLog.error('Initialization error:', error);
      app.quit();
    }
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });

  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createMainWindow();
    }
  });
}

/**
 * Setup error handling
 */
function setupErrorHandling() {
  process.on('uncaughtException', (error) => {
    electronLog.error('Uncaught Exception:', error);
    dialog.showErrorBox('Unhandled Error', error.message);
  });

  process.on('unhandledRejection', (reason, promise) => {
    electronLog.error('Unhandled Rejection:', reason);
  });
}

// Initialize the application
async function main() {
  setupErrorHandling();
  await initializeApp();
}

main().catch(error => {
  console.error('Failed to start application:', error);
  process.exit(1);
});

module.exports = {
  mainWindow,
  store,
  electronLog
};
