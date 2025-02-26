const fs = require('fs');
const path = require('path');

// Example settings object representing your app's state
const appSettings = {
  apiKey: '',
  preferences: {
    darkMode: false,
    notifications: true,
  },
};

/**
 * Exports the current settings to a JSON file
 * @param {string} exportPath - The file path where settings should be saved
 */
function exportSettings(exportPath = './settings-export.json') {
  try {
    // Convert the current settings to a JSON string
    const jsonData = JSON.stringify(appSettings, null, 2);

    // Write the JSON data to the specified file
    fs.writeFileSync(exportPath, jsonData, 'utf-8');

    console.log(`Settings exported successfully to ${exportPath}`);
  } catch (err) {
    console.error('Failed to export settings:', err);
  }
}

/**
 * Imports settings from a JSON file and applies them to the current app state
 * @param {string} importPath - The file path from which to read settings
 */
function importSettings(importPath = './settings-export.json') {
  try {
    // Check if the file exists
    if (!fs.existsSync(importPath)) {
      console.error(`The file "${importPath}" does not exist.`);
      return;
    }

    // Read and parse the JSON data from the file
    const rawData = fs.readFileSync(importPath, 'utf-8');
    const importedSettings = JSON.parse(rawData);

    // Validate the structure of the imported data
    if (importedSettings.apiKey && importedSettings.preferences) {
      // Update the app's settings
      appSettings.apiKey = importedSettings.apiKey;
      appSettings.preferences = { ...importedSettings.preferences };

      console.log('Settings imported successfully:', appSettings);
    } else {
      console.error('Invalid settings structure in the imported file.');
    }
  } catch (err) {
    console.error('Failed to import settings:', err);
  }
}

// Example usage
// Uncomment one line at a time to test exporting and importing:

// Export the current settings
// exportSettings('./path/to/export.json');

// Import settings from a file
// importSettings('./path/to/export.json');

// Export functions for use in other modules
module.exports = { exportSettings, importSettings };
