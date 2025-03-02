#!/usr/bin/env python3
"""
WebSocket Server für AILinux
Bietet Echtzeit-Kommunikation zwischen Client und Server.
"""
import os
import sys
import asyncio
import logging
import json
import time
import traceback
from typing import Dict, Any, List, Set, Optional, Union
from datetime import datetime, timedelta

# Importiere Websockets mit Fehlerbehandlung
try:
    import websockets
except ImportError:
    print("websockets nicht installiert. Installiere mit: pip install websockets")
    sys.exit(1)

# Importiere AI-Modell mit Fehlerbehandlung
try:
    from ai_model import analyze_log
except ImportError:
    try:
        # Versuche, den relativen Import für das Modul
        from .ai_model import analyze_log
    except ImportError:
        print("ai_model Modul nicht gefunden. Stelle sicher, dass es im richtigen Pfad liegt.")
        sys.exit(1)

# Lade Umgebungsvariablen
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv nicht installiert. Standardeinstellungen werden verwendet.")

# Konfiguration
HOST = os.getenv("WS_HOST", "0.0.0.0")
PORT = int(os.getenv("WS_PORT", "8082"))  # Richtige Umwandlung als String
DEBUG = os.getenv("WS_DEBUG", "False").lower() == "true"
ENV = os.getenv("ENVIRONMENT", "development")

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("websocket_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("websocket_server")

# Globale Websocket-Verbindungen und letzte Aktivitäten
CONNECTIONS = set()
LAST_ACTIVITY = {}
analysis_semaphore = asyncio.Semaphore(5)  # Begrenze parallele Analysen

async def register_connection(websocket):
    """Registriere eine neue Websocket-Verbindung."""
    CONNECTIONS.add(websocket)
    LAST_ACTIVITY[websocket] = time.time()
    logger.info(f"Neue Verbindung registriert. Aktive Verbindungen: {len(CONNECTIONS)}")

async def unregister_connection(websocket):
    """Entferne eine Websocket-Verbindung."""
    CONNECTIONS.remove(websocket)
    LAST_ACTIVITY.pop(websocket, None)
    logger.info(f"Verbindung geschlossen. Verbleibende Verbindungen: {len(CONNECTIONS)}")

async def send_message(websocket, message_type, data=None):
    """Sende eine Nachricht an einen Client."""
    if data is None:
        data = {}
    
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        await websocket.send(json.dumps(message))
        LAST_ACTIVITY[websocket] = time.time()
    except websockets.exceptions.ConnectionClosed:
        await unregister_connection(websocket)
    except Exception as e:
        logger.error(f"Fehler beim Senden der Nachricht: {e}")

async def broadcast_message(message_type, data=None, exclude=None):
    """Sende eine Nachricht an alle verbundenen Clients."""
    if exclude is None:
        exclude = set()
    
    if data is None:
        data = {}
    
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    json_message = json.dumps(message)
    
    # Speichere die zu entfernenden Verbindungen
    to_remove = set()
    
    for conn in CONNECTIONS:
        if conn in exclude:
            continue
        
        try:
            await conn.send(json_message)
            LAST_ACTIVITY[conn] = time.time()
        except websockets.exceptions.ConnectionClosed:
            to_remove.add(conn)
        except Exception as e:
            logger.error(f"Fehler beim Broadcast: {e}")
            to_remove.add(conn)
    
    # Entferne fehlerhafte Verbindungen
    for conn in to_remove:
        await unregister_connection(conn)

async def analyze_log_task(websocket, log_text, model="gpt4all", instruction=None):
    """Führe Log-Analyse durch und sende Ergebnisse an den Client."""
    try:
        logger.info(f"Starte Log-Analyse mit Modell {model}")
        
        # Sende Bestätigung, dass die Analyse gestartet wurde
        await send_message(websocket, "analysis_started", {
            "model": model,
            "timestamp": datetime.now().isoformat()
        })
        
        # Führe die Analyse mit einem Semaphor durch, um gleichzeitige Anfragen zu begrenzen
        async with analysis_semaphore:
            # Verwende asyncio.to_thread in neueren Python-Versionen oder das Executor-Pattern
            # für ältere Versionen, um blockierende Aufrufe zu behandeln
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: analyze_log(log_text, model, instruction)
                )
                
                # Sende Analyseergebnis zurück
                await send_message(websocket, "analysis_result", {
                    "result": result,
                    "model": model
                })
                logger.info("Log-Analyse erfolgreich abgeschlossen")
                
            except Exception as e:
                logger.error(f"Fehler während der Analyse: {e}")
                await send_message(websocket, "analysis_error", {
                    "error": str(e),
                    "model": model
                })
                
    except Exception as e:
        logger.error(f"Fehler im Analyse-Task: {e}")
        try:
            await send_message(websocket, "analysis_error", {"error": str(e)})
        except:
            pass

async def handle_client_message(websocket, message, path):
    """Verarbeite eine Nachricht von einem Client."""
    try:
        msg_type = message.get("type", "")
        msg_data = message.get("data", {})
        
        # Aktualisiere die letzte Aktivitätszeit
        LAST_ACTIVITY[websocket] = time.time()
        
        if msg_type == "ping":
            # Einfache Ping-Pong für Verbindungstests
            await send_message(websocket, "pong", {"received_at": datetime.now().isoformat()})
            
        elif msg_type == "analyze_log":
            # Starte Log-Analyse
            if "log" not in msg_data:
                await send_message(websocket, "error", {"message": "Log-Text fehlt in der Anfrage"})
                return
                
            log_text = msg_data.get("log", "")
            model = msg_data.get("model", "gpt4all")  # Standardmäßig GPT4All verwenden
            instruction = msg_data.get("instruction")
            
            # Starte die Analyse als separate Task
            asyncio.create_task(analyze_log_task(websocket, log_text, model, instruction))
            
        elif msg_type == "get_models":
            # Hole verfügbare Modelle (wird vom ai_model-Modul importiert)
            try:
                from ai_model import get_available_models
                models = get_available_models()
                await send_message(websocket, "available_models", {"models": models})
            except ImportError:
                logger.error("Konnte get_available_models nicht importieren")
                await send_message(websocket, "error", {"message": "Modellinformationen nicht verfügbar"})
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Modelle: {e}")
                await send_message(websocket, "error", {"message": f"Fehler: {str(e)}"})
                
        elif msg_type == "system_status":
            # Systemstatusdaten senden (wenn psutil verfügbar ist)
            try:
                import psutil
                system_info = {
                    "cpu": psutil.cpu_percent(interval=0.5),
                    "ram": psutil.virtual_memory().percent,
                    "disk": psutil.disk_usage("/").percent,
                }
                await send_message(websocket, "system_status", system_info)
            except ImportError:
                await send_message(websocket, "error", {"message": "psutil nicht installiert"})
                
        else:
            logger.warning(f"Unbekannter Nachrichtentyp erhalten: {msg_type}")
            await send_message(websocket, "error", {"message": f"Unbekannter Nachrichtentyp: {msg_type}"})
            
    except Exception as e:
        logger.error(f"Fehler bei der Nachrichtenverarbeitung: {e}")
        try:
            await send_message(websocket, "error", {"message": f"Interner Serverfehler: {str(e)}"})
        except:
            pass

async def handle_connection(websocket, path):
    """Haupthandler für WebSocket-Verbindungen."""
    try:
        # Registriere neue Verbindung
        await register_connection(websocket)
        
        # Sende Begrüßungsnachricht
        await send_message(websocket, "welcome", {
            "message": "Willkommen beim AILinux WebSocket-Server",
            "server_time": datetime.now().isoformat(),
            "version": "1.0.0"
        })
        
        # Verarbeite eingehende Nachrichten
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_client_message(websocket, data, path)
            except json.JSONDecodeError:
                logger.error("Ungültige JSON-Nachricht erhalten")
                await send_message(websocket, "error", {"message": "Ungültiges JSON-Format"})
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung der Nachricht: {e}")
                await send_message(websocket, "error", {"message": f"Fehler: {str(e)}"})
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Verbindung geschlossen: {e}")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}")
    finally:
        await unregister_connection(websocket)

async def cleanup_inactive_connections():
    """Bereinige inaktive Verbindungen."""
    while True:
        try:
            now = time.time()
            inactive_time = 300  # 5 Minuten Inaktivität
            
            # Finde inaktive Verbindungen
            to_close = set()
            for ws, last_time in LAST_ACTIVITY.items():
                if now - last_time > inactive_time:
                    to_close.add(ws)
            
            # Schließe inaktive Verbindungen
            for ws in to_close:
                try:
                    logger.info(f"Schließe inaktive Verbindung")
                    await ws.close(1000, "Inaktive Verbindung")
                    await unregister_connection(ws)
                except Exception as e:
                    logger.error(f"Fehler beim Schließen der inaktiven Verbindung: {e}")
            
            # Warte für die nächste Überprüfung
            await asyncio.sleep(60)  # Überprüfe jede Minute
            
        except Exception as e:
            logger.error(f"Fehler bei der Bereinigung inaktiver Verbindungen: {e}")
            await asyncio.sleep(60)  # Auch bei Fehler warten wir

async def heartbeat():
    """Sende regelmäßig Heartbeat-Nachrichten an alle Clients."""
    while True:
        try:
            if CONNECTIONS:  # Nur wenn Verbindungen vorhanden sind
                await broadcast_message("heartbeat", {
                    "server_time": datetime.now().isoformat(),
                    "active_connections": len(CONNECTIONS)
                })
            await asyncio.sleep(30)  # Alle 30 Sekunden
            
        except Exception as e:
            logger.error(f"Fehler beim Heartbeat: {e}")
            await asyncio.sleep(30)  # Auch bei Fehler warten wir

async def main():
    """Hauptfunktion zum Starten des WebSocket-Servers."""
    global PORT
    
    # Starte Hintergrundtasks
    cleanup_task = asyncio.create_task(cleanup_inactive_connections())
    heartbeat_task = asyncio.create_task(heartbeat())
    
    # Starte den WebSocket-Server
    logger.info(f"Starte WebSocket-Server auf {HOST}:{PORT}")
    async with websockets.serve(handle_connection, HOST, PORT):
        logger.info(f"WebSocket-Server läuft auf {HOST}:{PORT}")
        try:
            # Server unbegrenzt laufen lassen
            await asyncio.Future()
        except asyncio.CancelledError:
            # Server sauber beenden
            logger.info("Server wird beendet...")
            cleanup_task.cancel()
            heartbeat_task.cancel()

def run_server():
    """Startet den WebSocket-Server."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server durch Benutzer gestoppt")
    except Exception as e:
        logger.error(f"Fehler beim Starten des Servers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()
