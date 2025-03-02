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

// Configure logging with clear levels and formatting
electronLog.transports.file.level = 'info';
electronLog.transports.console.level = 'debug';

/**
 * Create a secure configuration store with enhanced defaults
 * @type {Store<object>}
 */
const store = new Store({
  name: 'ailinux-user-preferences',
  encryptionKey: process.env.STORE_ENCRYPTION_KEY, // Optional encryption
  clearInvalidConfig: true, // Clear any corrupted config
  defaults: {
    // AI Model Configuration
    ai: {
      defaultModel: process.env.DEFAULT_MODEL || 'gpt4all',
      models: {
        gpt4all: { 
          enabled: true, 
          path: process.env.GPTALL_MODEL_PATH || './models/default-model.gguf' 
        },
        openai: { 
          enabled: Boolean(process.env.OPENAI_API_KEY), 
          apiKey: process.env.OPENAI_API_KEY || '' 
        },
        gemini: { 
          enabled: Boolean(process.env.GEMINI_API_KEY), 
          apiKey: process.env.GEMINI_API_KEY || '' 
        },
        huggingface: { 
          enabled: Boolean(process.env.HUGGINGFACE_API_KEY), 
          apiKey: process.env.HUGGINGFACE_API_KEY || '' 
        }
      }
    },
    
    // Server Configuration
    server: {
      host: process.env.SERVER_HOST || 'localhost',
      port: Number(process.env.SERVER_PORT) || 8081,
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

/**
 * Validates the URL is allowed for WebSocket connection
 * @param {string} url - The URL to validate
 * @returns {boolean} True if URL is allowed, false otherwise
 */
function isAllowedWebSocketUrl(url) {
  try {
    const allowedHosts = ['localhost', '127.0.0.1', 'derleiti.de'];
    const parsedUrl = new URL(url);
    return allowedHosts.includes(parsedUrl.hostname);
  } catch (error) {
    electronLog.error('URL validation error:', error);
    return false;
  }
}

// Expose a secure API to the renderer process with proper error handling
contextBridge.exposeInMainWorld('electronAPI', {
  // Configuration methods
  getConfig: (key) => {
    try {
      return store.get(key);
    } catch (error) {
      electronLog.error(`Config retrieval error for key "${key}":`, error);
      return null;
    }
  },
  
  setConfig: (key, value) => {
    try {
      // Validate input - prevent undefined or null keys
      if (!key || typeof key !== 'string') {
        throw new Error('Invalid configuration key');
      }
      
      store.set(key, value);
      return true;
    } catch (error) {
      electronLog.error(`Config update error for key "${key}":`, error);
      return false;
    }
  },
  
  // API Key Management with improved security
  updateApiKey: (service, key) => {
    try {
      // Validate service name
      if (!['openai', 'gemini', 'huggingface'].includes(service)) {
        throw new Error(`Invalid service: ${service}`);
      }
      
      const currentConfig = store.get('ai.models');
      if (!currentConfig) {
        throw new Error('Configuration not properly initialized');
      }
      
      // Update API key and enabled status
      currentConfig[service] = {
        ...(currentConfig[service] || {}),
        apiKey: key,
        enabled: Boolean(key)
      };
      
      store.set('ai.models', currentConfig);
      return true;
    } catch (error) {
      electronLog.error(`API key update error for ${service}:`, error);
      return false;
    }
  },
  
  // Logging methods with validation
  log: (level, message) => {
    const validLevels = ['info', 'warn', 'error', 'debug'];
    if (!validLevels.includes(level)) {
      electronLog.warn(`Invalid log level '${level}', defaulting to 'info'`);
      level = 'info';
    }
    
    if (typeof message !== 'string') {
      message = String(message);
    }
    
    switch(level) {
      case 'info': electronLog.info(message); break;
      case 'warn': electronLog.warn(message); break;
      case 'error': electronLog.error(message); break;
      case 'debug': electronLog.debug(message); break;
    }
  },
  
  // System Information (safe, read-only)
  getSystemInfo: () => ({
    platform: process.platform,
    arch: process.arch,
    version: require('../package.json').version || '1.0.0',
    nodeVersion: process.version,
    electronVersion: process.versions.electron,
    env: {
      NODE_ENV: process.env.NODE_ENV || 'production'
    }
  }),
  
  // Secure WebSocket Creator with URL validation
  createWebSocket: (url) => {
    if (!isAllowedWebSocketUrl(url)) {
      throw new Error('Unauthorized WebSocket connection');
    }
    
    try {
      return new WebSocket(url);
    } catch (error) {
      electronLog.error('WebSocket creation error:', error);
      throw new Error(`Failed to create WebSocket: ${error.message}`);
    }
  }
});

// Export for potential use in other parts of the application
module.exports = {
  store,
  electronLog
};
