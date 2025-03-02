/**
 * Unified Configuration System for AILinux
 * Enhanced for Electron Compatibility and Security
 */
const { contextBridge, ipcRenderer } = require('electron');
const Store = require('electron-store');
const dotenv = require('dotenv');
const electronLog = require('electron-log');

// Load environment variables
dotenv.config();

// Configure logging
electronLog.transports.file.level = 'info';
electronLog.transports.console.level = 'debug';

// Create a persistent configuration store with enhanced defaults
const store = new Store({
  name: 'ailinux-user-preferences',
  defaults: {
    // AI Model Configuration
    ai: {
      defaultModel: process.env.DEFAULT_MODEL || 'gpt4all',
      models: {
        gpt4all: { 
          enabled: true, 
          path: process.env.GPTALL_MODEL_PATH || 'default/model/path' 
        },
        openai: { 
          enabled: !!process.env.OPENAI_API_KEY, 
          apiKey: process.env.OPENAI_API_KEY || '' 
        },
        gemini: { 
          enabled: !!process.env.GEMINI_API_KEY, 
          apiKey: process.env.GEMINI_API_KEY || '' 
        },
        huggingface: { 
          enabled: !!process.env.HUGGINGFACE_API_KEY, 
          apiKey: process.env.HUGGINGFACE_API_KEY || '' 
        }
      }
    },
    
    // Server Configuration
    server: {
      host: process.env.SERVER_HOST || 'localhost',
      port: process.env.SERVER_PORT || 8081,
      wsUrl: process.env.WS_SERVER_URL || 'ws://localhost:8082'
    },
    
    // Logging Configuration
    logging: {
      level: process.env.LOG_LEVEL || 'info',
      maxFiles: 5,
      maxSize: 10 * 1024 * 1024 // 10 MB
    },
    
    // UI Preferences
    ui: {
      theme: 'system', // system, light, dark
      fontSize: 'medium',
      compactMode: false
    }
  }
});

// Expose a secure API to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Configuration methods
  getConfig: (key) => {
    try {
      return store.get(key);
    } catch (error) {
      electronLog.error('Config retrieval error:', error);
      return null;
    }
  },
  
  setConfig: (key, value) => {
    try {
      store.set(key, value);
      return true;
    } catch (error) {
      electronLog.error('Config update error:', error);
      return false;
    }
  },
  
  // API Key Management
  updateApiKey: (service, key) => {
    try {
      const currentConfig = store.get('ai.models');
      currentConfig[service].apiKey = key;
      currentConfig[service].enabled = !!key;
      store.set('ai.models', currentConfig);
      return true;
    } catch (error) {
      electronLog.error('API key update error:', error);
      return false;
    }
  },
  
  // Logging methods
  log: (level, message) => {
    const validLevels = ['info', 'warn', 'error'];
    if (validLevels.includes(level)) {
      switch(level) {
        case 'info': electronLog.info(message); break;
        case 'warn': electronLog.warn(message); break;
        case 'error': electronLog.error(message); break;
      }
    }
  },
  
  // System Information
  getSystemInfo: () => ({
    platform: process.platform,
    arch: process.arch,
    version: require('./package.json').version,
    env: {
      NODE_ENV: process.env.NODE_ENV || 'production',
      ELECTRON_ENV: 'development'
    }
  }),
  
  // Secure WebSocket Creator
  createWebSocket: (url) => {
    const allowedHosts = ['localhost', 'derleiti.de'];
    const parsedUrl = new URL(url);
    
    if (!allowedHosts.includes(parsedUrl.hostname)) {
      throw new Error('Unauthorized WebSocket connection');
    }
    
    return new WebSocket(url);
  }
});

// Export for potential use in other parts of the application
module.exports = {
  store,
  electronLog
};
