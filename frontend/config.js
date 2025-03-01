/**
 * Unified configuration system for AILinux
 * 
 * This module provides a centralized configuration system that works
 * across both frontend and backend components of the application.
 */
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');
const electronLog = require('electron-log');

// Load environment variables from .env file
dotenv.config();

/**
 * Default configuration values
 */
const DEFAULT_CONFIG = {
  // AI Model Settings
  ai: {
    defaultModel: 'gpt4all',
    openaiApiKey: process.env.OPENAI_API_KEY || '',
    googleApiKey: process.env.GOOGLE_API_KEY || '',
    geminiApiKey: process.env.GEMINI_API_KEY || '',
    llamaModelPath: process.env.LLAMA_MODEL_PATH || 'Meta-Llama-3-8B-Instruct.Q4_0.gguf',
  },
  
  // Server Settings
  server: {
    host: '0.0.0.0',
    port: parseInt(process.env.PORT) || 8081,
    corsEnabled: true,
    debug: process.env.DEBUG === 'true' || false
  },
  
  // Frontend Settings
  frontend: {
    windowWidth: 1200,
    windowHeight: 800,
    devTools: process.env.NODE_ENV === 'development',
    theme: 'light'
  },
  
  // Logging Settings
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    logToConsole: true,
    logToFile: true,
    maxLogFiles: 5,
    maxLogSize: 10 * 1024 * 1024 // 10 MB
  },
  
  // Feature Flags
  features: {
    twitchIntegration: false,
    youtubeIntegration: false,
    localAiOnly: false
  }
};

/**
 * User configuration path
 */
const USER_CONFIG_PATH = path.join(
  process.env.APPDATA || 
  (process.platform === 'darwin' ? 
    path.join(process.env.HOME, 'Library', 'Preferences') : 
    path.join(process.env.HOME, '.config')),
  'ailinux',
  'config.json'
);

/**
 * Configuration class to manage application settings
 */
class Config {
  constructor() {
    this.config = { ...DEFAULT_CONFIG };
    this.load();
  }
  
  /**
   * Load configuration from file
   */
  load() {
    try {
      // Check if user config directory exists and create it if not
      const configDir = path.dirname(USER_CONFIG_PATH);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      
      // Check if user config file exists
      if (fs.existsSync(USER_CONFIG_PATH)) {
        const userConfig = JSON.parse(fs.readFileSync(USER_CONFIG_PATH, 'utf8'));
        
        // Deep merge with default config
        this.config = this._deepMerge(this.config, userConfig);
        
        electronLog.info('Loaded user configuration');
      } else {
        // Create default config file if it doesn't exist
        this.save();
        electronLog.info('Created default configuration file');
      }
    } catch (error) {
      electronLog.error(`Error loading config: ${error.message}`);
      // Continue with default config if loading fails
    }
  }
  
  /**
   * Save configuration to file
   */
  save() {
    try {
      fs.writeFileSync(USER_CONFIG_PATH, JSON.stringify(this.config, null, 2), 'utf8');
      electronLog.info('Saved configuration to file');
      return true;
    } catch (error) {
      electronLog.error(`Error saving config: ${error.message}`);
      return false;
    }
  }
  
  /**
   * Get a configuration value by key path
   * @param {string} keyPath - Path to the desired config value (e.g., 'ai.defaultModel')
   * @param {any} defaultValue - Default value to return if the key doesn't exist
   * @returns {any} The configuration value
   */
  get(keyPath, defaultValue = undefined) {
    try {
      const keys = keyPath.split('.');
      let value = this.config;
      
      for (const key of keys) {
        if (value === undefined || value === null) {
          return defaultValue;
        }
        value = value[key];
      }
      
      return value !== undefined ? value : defaultValue;
    } catch (error) {
      electronLog.error(`Error getting config value for ${keyPath}: ${error.message}`);
      return defaultValue;
    }
  }
  
  /**
   * Set a configuration value by key path
   * @param {string} keyPath - Path to the config value to set (e.g., 'ai.defaultModel')
   * @param {any} value - Value to set
   * @returns {boolean} True if successful, false otherwise
   */
  set(keyPath, value) {
    try {
      const keys = keyPath.split('.');
      const lastKey = keys.pop();
      
      let obj = this.config;
      
      for (const key of keys) {
        if (obj[key] === undefined) {
          obj[key] = {};
        }
        obj = obj[key];
      }
      
      obj[lastKey] = value;
      return true;
    } catch (error) {
      electronLog.error(`Error setting config value for ${keyPath}: ${error.message}`);
      return false;
    }
  }
  
  /**
   * Update multiple configuration values at once
   * @param {Object} updates - Object containing key-value pairs to update
   * @returns {boolean} True if successful, false otherwise
   */
  update(updates) {
    try {
      // Apply all updates
      Object.entries(updates).forEach(([keyPath, value]) => {
        this.set(keyPath, value);
      });
      
      // Save the configuration
      return this.save();
    } catch (error) {
      electronLog.error(`Error updating config: ${error.message}`);
      return false;
    }
  }
  
  /**
   * Reset configuration to defaults
   * @returns {boolean} True if successful, false otherwise
   */
  reset() {
    try {
      this.config = { ...DEFAULT_CONFIG };
      return this.save();
    } catch (error) {
      electronLog.error(`Error resetting config: ${error.message}`);
      return false;
    }
  }
  
  /**
   * Get all configuration
   * @returns {Object} Complete configuration object
   */
  getAll() {
    return { ...this.config };
  }
  
  /**
   * Deep merge two objects
   * @private
   * @param {Object} target - Target object
   * @param {Object} source - Source object
   * @returns {Object} Merged object
   */
  _deepMerge(target, source) {
    const output = { ...target };
    
    if (this._isObject(target) && this._isObject(source)) {
      Object.keys(source).forEach(key => {
        if (this._isObject(source[key])) {
          if (!(key in target)) {
            output[key] = source[key];
          } else {
            output[key] = this._deepMerge(target[key], source[key]);
          }
        } else {
          output[key] = source[key];
        }
      });
    }
    
    return output;
  }
  
  /**
   * Check if a value is an object
   * @private
   * @param {any} item - Item to check
   * @returns {boolean} True if the item is an object
   */
  _isObject(item) {
    return (item && typeof item === 'object' && !Array.isArray(item));
  }
}

// Export a singleton instance
const config = new Config();
module.exports = config;
