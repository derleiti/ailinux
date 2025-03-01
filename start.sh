require('dotenv').config(); // Load environment variables from .env

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Initialize log files
const startLog = path.join(__dirname, 'start.log');
const backendLog = path.join(__dirname, 'backend/backend.log');
const frontendLog = path.join(__dirname, 'frontend/frontend.log');

// Log initialization
fs.writeFileSync(startLog, 'Log file initialized: ' + new Date().toISOString() + '\n');
fs.writeFileSync(backendLog, 'Log file initialized: ' + new Date().toISOString() + '\n');
fs.writeFileSync(frontendLog, 'Log file initialized: ' + new Date().toISOString() + '\n');

// Log the API Key (for testing purposes, remove in production)
const apiKey = process.env.API_KEY;
fs.appendFileSync(startLog, `Your API key is: ${apiKey}\n`);

const backend = spawn('python3', [path.join(__dirname, 'backend', 'app.py')]);
const frontend = spawn('electron', [path.join(__dirname, 'frontend', 'main.js')]);

// Log when the backend process starts
fs.appendFileSync(startLog, 'Starting backend process\n');

// Handle backend process exit
backend.on('exit', (code) => {
  fs.appendFileSync(backendLog, `Backend process exited with code ${code}\n`);
  frontend.kill();
  process.exit(code);
});

// Log when the frontend process starts
fs.appendFileSync(startLog, 'Starting frontend process\n');
console.log("__dirname: ", __dirname);

// Handle frontend process exit
frontend.on('exit', (code) => {
  fs.appendFileSync(frontendLog, `Frontend process exited with code ${code}\n`);
  backend.kill();
  process.exit(code);
});
