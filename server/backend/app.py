#!/usr/bin/env python3
"""
Backend Server Application
Provides REST API endpoints for the AILinux system.
"""
import os
import sys
import logging
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Stelle sicher, dass die Abhängigkeiten verfügbar sind
try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
except ImportError:
    print("Flask oder Flask-CORS nicht installiert. Installiere mit: pip install flask flask-cors")
    sys.exit(1)

# Import für Umgebungsvariablen
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv nicht installiert. Installiere mit: pip install python-dotenv")
    # Keine System-Exit hier, da wir auch ohne dotenv fortfahren können

# Eigene Module für AI-Modell-Integrationen
try:
    from ai_model import analyze_log, get_available_models
    import psutil
except ImportError as e:
    print(f"Modul nicht gefunden: {e}")
    print("Stelle sicher, dass die notwendigen Module installiert sind.")
    sys.exit(1)

# Initialisiere Flask-App
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Server-Konfiguration mit korrekten Standard-Werten
HOST = os.getenv("FLASK_HOST", "0.0.0.0")  # Default to all interfaces
PORT = int(os.getenv("FLASK_PORT", "8081"))  # Richtige Umwandlung als String
DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
ENV = os.getenv("ENVIRONMENT", "development")

# Konfiguriere Logging
log_directory = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_directory, exist_ok=True)
log_file_path = os.path.join(log_directory, "backend.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backend.app")

@app.route('/analyze', methods=['POST'])
def analyze_logs_endpoint():
    """
    Endpoint für Log-Analyse
    
    Erwartet JSON mit 'log'-Text und optionalem 'model'-Parameter.
    """
    try:
        # Validiere Eingabedaten
        if not request.is_json:
            logger.error("Anfrage enthält kein gültiges JSON")
            return jsonify({"error": "Anfrage muss im JSON-Format sein"}), 400

        data = request.json
        log_text = data.get('log')
        model_name = data.get('model', 'gpt4all')  # Default zu gpt4all
        
        # Eigene Anweisung, falls vorhanden
        instruction = data.get('instruction')

        if not log_text:
            logger.error("Keine Log-Daten in der Anfrage")
            return jsonify({"error": "Keine Log-Daten bereitgestellt"}), 400

        # Analysiere Log mit dem angegebenen Modell
        logger.info(f"Analysiere Log mit Modell: {model_name}")
        result = analyze_log(log_text, model_name, instruction)
        
        # Protokolliere Analyse-Anfrage
        with open(os.path.join(log_directory, "analysis_requests.log"), "a") as log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"{timestamp} - Model: {model_name}\n")

        return jsonify({"analysis": result})

    except Exception as e:
        error_message = f"Fehler in analyse-Endpunkt: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.exception(error_message)
        logger.debug(f"Stack-Trace: {stack_trace}")
        return jsonify({"error": error_message}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Endpunkt zum Abrufen von Logs
    
    Optionale Parameter: count (Anzahl der Logs), type (Log-Typ)
    """
    try:
        count = request.args.get('count', default=100, type=int)
        log_type = request.args.get('type', default='backend')
        
        log_file = f"{log_type}.log"
        logs_path = os.path.join(log_directory, log_file)
        
        if os.path.exists(logs_path):
            with open(logs_path, 'r') as f:
                logs = f.readlines()[-count:]  # Letzte 'count' Zeilen
            return jsonify({"logs": logs})

        return jsonify({"logs": []})

    except Exception as e:
        logger.exception(f"Fehler beim Abrufen von Logs: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/models', methods=['GET'])
def get_models():
    """
    Endpunkt zum Abrufen verfügbarer AI-Modelle
    
    Gibt eine Liste der verfügbaren Modelle zurück
    """
    try:
        models = get_available_models()
        return jsonify({"models": models})
    except Exception as e:
        logger.exception(f"Fehler beim Abrufen der Modelle: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/system', methods=['GET'])
def system_status():
    """
    Endpunkt zum Abrufen des Systemstatus
    
    Gibt Systemmetriken zurück
    """
    try:
        system_info = {
            "cpu": psutil.cpu_percent(interval=1),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
            "network": psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv,
            "running_processes": len(psutil.pids()),
            "timestamp": datetime.now().isoformat()
        }
        return jsonify(system_info)
    except Exception as e:
        logger.exception(f"Fehler beim Abrufen des Systemstatus: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    """
    Endpunkt zum Aktualisieren oder Abrufen von Anwendungseinstellungen
    
    PUT: Aktualisiert Einstellungen basierend auf übergebenem JSON
    GET: Gibt aktuelle Einstellungen zurück
    """
    settings_file = os.path.join(os.path.dirname(__file__), "settings.json")

    if request.method == 'POST':
        try:
            new_settings = request.json

            # Einstellungen validieren
            if not isinstance(new_settings, dict):
                return jsonify({"error": "Ungültiges Einstellungsformat"}), 400

            # Stelle sicher, dass das Einstellungsverzeichnis existiert
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)

            # Schreibe die neuen Einstellungen
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(new_settings, f, indent=2)

            logger.info(f"Einstellungen aktualisiert: {new_settings}")
            return jsonify({"status": "success", "message": "Einstellungen aktualisiert"})
        except Exception as e:
            logger.exception(f"Fehler beim Aktualisieren der Einstellungen: {str(e)}")
            return jsonify({"error": str(e)}), 500
    else:
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return jsonify({"settings": settings})
            else:
                # Gib Standardeinstellungen zurück, wenn die Datei nicht existiert
                default_settings = {
                    "ai": {
                        "defaultModel": "gpt4all",
                        "gpt4all_enabled": True,
                        "openai_enabled": bool(os.getenv("OPENAI_API_KEY")),
                        "gemini_enabled": bool(os.getenv("GEMINI_API_KEY")),
                        "huggingface_enabled": bool(os.getenv("HUGGINGFACE_API_KEY"))
                    },
                    "logging": {
                        "level": "info",
                        "log_to_file": True,
                        "max_log_files": 5
                    }
                }
                return jsonify({"settings": default_settings})
        except Exception as e:
            logger.exception(f"Fehler beim Abrufen der Einstellungen: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Endpunkt zum Überprüfen der Gesundheit des Backend-Servers
    
    Gibt Serverstatus zurück
    """
    return jsonify({
        "status": "online",
        "environment": ENV,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

def translate_log(log_text):
    """Vorverarbeitung von Log-Text vor der KI-Analyse.

    Diese Funktion kann erweitert werden, um eine anspruchsvollere
    Log-Übersetzung oder -Normalisierung zu implementieren.

    Args:
        log_text: Der ursprüngliche Log-Text

    Returns:
        Verarbeiteter Log-Text
    """
    # In Zukunft hier Log-Normalisierung oder -Vorverarbeitung hinzufügen
    return log_text

if __name__ == "__main__":
    logger.info(f"Starting backend server on {HOST}:{PORT}, debug={DEBUG}")
    logger.info(f"Server environment: {ENV}")
    
    # Server starten
    try:
        app.run(host=HOST, port=PORT, debug=DEBUG)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)
