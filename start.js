require('dotenv').config();  // Lade Umgebungsvariablen aus .env-Datei
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Definiere Log-Dateipfade
const backendLogPath = path.join(__dirname, 'backend', 'backend.log');
const frontendLogPath = path.join(__dirname, 'frontend', 'frontend.log');
const startLogPath = path.join(__dirname, 'start.log');

// Funktion zum Initialisieren und Überschreiben von Log-Dateien
function initializeLog(filePath) {
  try {
    fs.writeFileSync(filePath, '');  // Lösche die Log-Datei zum Überschreiben
    console.log(`Log-Datei initialisiert: ${filePath}`);
  } catch (error) {
    console.error(`Fehler beim Initialisieren der Log-Datei: ${filePath}`, error);
  }
}

// Initialisiere Log-Dateien
initializeLog(startLogPath);
initializeLog(backendLogPath);
initializeLog(frontendLogPath);

// Funktion zum Loggen von Nachrichten in Log-Dateien
function logMessage(message, logPath) {
  try {
    const timestamp = new Date().toISOString();
    const logEntry = `${timestamp} - ${message}\n`;
    fs.appendFileSync(logPath, logEntry);
  } catch (error) {
    console.error('Fehler beim Schreiben in Log-Datei:', error);
  }
}

// Logge Initialisierungsnachricht
logMessage('Initialisierung gestartet', startLogPath);

// Hole den API-Schlüssel aus den Umgebungsvariablen
const apiKey = process.env.API_KEY;
logMessage(`Ihr API-Schlüssel: ${apiKey}`, startLogPath);

// Starte den Backend-Prozess (Flask backend)
const backendProcess = spawn('python3', [path.join(__dirname, 'backend', 'app.py')]);

// Logge Backend-Startnachricht
logMessage('Backend-Prozess gestartet', startLogPath);

// Starte den Frontend-Prozess (Electron frontend)
const frontendProcess = spawn('npm', ['start'], { cwd: path.join(__dirname, 'frontend') });

// Logge Frontend-Startnachricht
logMessage('Frontend-Prozess gestartet', startLogPath);

// Wenn der Backend-Prozess Fehler ausgibt
backendProcess.stderr.on('data', (data) => {
  logMessage(`Backend-Fehler: ${data}`, backendLogPath);
});

// Wenn der Frontend-Prozess Fehler ausgibt
frontendProcess.stderr.on('data', (data) => {
  logMessage(`Frontend-Fehler: ${data}`, frontendLogPath);
});

// Wenn der Backend-Prozess standardmäßig eine Ausgabe macht
backendProcess.stdout.on('data', (data) => {
  logMessage(`Backend-Ausgabe: ${data}`, backendLogPath);
});

// Wenn der Frontend-Prozess standardmäßig eine Ausgabe macht
frontendProcess.stdout.on('data', (data) => {
  logMessage(`Frontend-Ausgabe: ${data}`, frontendLogPath);
});

// Wenn der Backend-Prozess beendet wird
backendProcess.on('close', (code) => {
  logMessage(`Backend-Prozess beendet mit Code: ${code}`, backendLogPath);
});

// Wenn der Frontend-Prozess beendet wird
frontendProcess.on('close', (code) => {
  logMessage(`Frontend-Prozess beendet mit Code: ${code}`, frontendLogPath);
});
