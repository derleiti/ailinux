const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const axios = require('axios');

let mainWindow;

// Funktion zum Schreiben von Log-Nachrichten in die Log-Datei
function writeLog(message) {
    const logFilePath = path.join(__dirname, 'frontend.log');
    const logEntry = `${new Date().toISOString()} - ${message}\n`;
    try {
        fs.appendFileSync(logFilePath, logEntry);
    } catch (error) {
        console.error(`Fehler beim Schreiben in Log-Datei: ${logFilePath}`, error);
    }
}

// Erstelle das Hauptanwendungsfenster
function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')  // Preload-Skript für zusätzliche API-Interaktionen
        }
    });

    // Lade die Haupt-HTML-Datei
    mainWindow.loadFile('index.html');
    writeLog("Main Window geladen");

    // Handle das Schließen des Hauptfensters
    mainWindow.on('closed', () => {
        mainWindow = null;
        writeLog("Main Window geschlossen");
    });
}

// Wenn die App bereit ist, erstelle das Fenster
app.whenReady().then(() => {
    writeLog("App bereit zur Ausführung");
    createMainWindow();
});

// Handle das Event, wenn das Frontend eine Chat-Nachricht an das Backend sendet
ipcMain.handle('chat-message', async (event, message, modelType) => {
    try {
        // Sende eine POST-Anfrage an das Backend (Flask-API)
        const response = await axios.post("http://127.0.0.1:8081/debug", {
            log: message,
            model: modelType
        });

        // Logge die Antwort der KI
        const botResponse = response.data.analysis;
        writeLog(`Erhaltene Antwort von der KI: ${botResponse}`);

        // Gebe die Antwort der KI an das Frontend zurück
        return botResponse;
    } catch (error) {
        writeLog(`Fehler bei der Kommunikation mit dem Backend: ${error.message}`);
        return "⚠ Der KI-Server antwortet nicht!";
    }
});
