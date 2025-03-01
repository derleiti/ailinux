# /home/zombie/ailinux/websocket_client.py

import websocket
import logging
import json

# Setze das Logging-Level für die Debugging-Zwecke
logging.basicConfig(level=logging.INFO)

def on_message(ws, message):
    """ Funktion, die auf eingehende Nachrichten reagiert """
    logging.info(f"Received message: {message}")

def on_error(ws, error):
    """ Funktion, die auf Fehler reagiert """
    logging.error(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    """ Funktion, die beim Schließen des WebSockets aufgerufen wird """
    logging.info(f"Closed with code: {close_status_code}, message: {close_msg}")

def on_open(ws):
    """ Funktion, die beim Öffnen des WebSocket-Verbindung aufgerufen wird """
    logging.info("WebSocket connection opened")
    message = {"message": "Hello, AI Model!"}
    ws.send(json.dumps(message))  # Sende eine Nachricht

def connect_to_server(url):
    """ Funktion, um eine WebSocket-Verbindung aufzubauen """
    websocket.enableTrace(True)  # Aktiviert die Trace-Ausgabe für Debugging
    ws = websocket.WebSocketApp(url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    ws.run_forever()  # Startet die Verbindung und wartet auf Nachrichten

if __name__ == "__main__":
    try:
        connect_to_server("wss://derleiti.de:8082")  # Beispiel WebSocket URL
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        logging.info("Closing WebSocket connection")
