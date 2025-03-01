"""WebSocket client for AILinux system.

This module provides a WebSocket client that can connect to either a local
or remote WebSocket server for real-time communication.
"""
import websocket
import logging
import json
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("websocket_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WebSocketClient")

# Server configuration with environment variables and fallbacks
SERVER_MODE = os.getenv("SERVER_MODE", "local")  # 'local' or 'remote'
LOCAL_WS_URL = "ws://localhost:8082"
REMOTE_WS_URL = "wss://derleiti.de:8082"
WS_SERVER_URL = REMOTE_WS_URL if SERVER_MODE == "remote" else LOCAL_WS_URL

# Maximum reconnection attempts
MAX_RECONNECT_ATTEMPTS = 5
reconnect_count = 0
reconnect_delay = 2  # Initial delay in seconds

def on_message(ws, message):
    """Handle incoming WebSocket messages.
    
    Args:
        ws: WebSocket instance
        message: Message received from the server
    """
    try:
        data = json.loads(message)
        logger.info(f"Received message: {json.dumps(data, indent=2)}")
        
        # Process different message types (customize based on your protocol)
        if "type" in data:
            if data["type"] == "status":
                logger.info(f"Server status: {data.get('status', 'unknown')}")
            elif data["type"] == "ai_response":
                logger.info(f"AI response received for query: {data.get('query_id', 'unknown')}")
            elif data["type"] == "error":
                logger.error(f"Server error: {data.get('message', 'Unknown error')}")
    except json.JSONDecodeError:
        logger.warning(f"Received non-JSON message: {message}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def on_error(ws, error):
    """Handle WebSocket errors.
    
    Args:
        ws: WebSocket instance
        error: Error that occurred
    """
    logger.error(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    """Handle WebSocket connection closing.
    
    Args:
        ws: WebSocket instance
        close_status_code: Status code for the close event
        close_msg: Close message
    """
    global reconnect_count
    
    if close_status_code:
        logger.info(f"WebSocket closed with code: {close_status_code}, message: {close_msg}")
    else:
        logger.info("WebSocket closed")
    
    # Attempt to reconnect if not closed cleanly and within max attempts
    if close_status_code not in [1000, 1001]:  # Normal closure codes
        if reconnect_count < MAX_RECONNECT_ATTEMPTS:
            reconnect_count += 1
            reconnect_delay_with_backoff = reconnect_delay * reconnect_count
            logger.info(f"Attempting to reconnect in {reconnect_delay_with_backoff} seconds (attempt {reconnect_count}/{MAX_RECONNECT_ATTEMPTS})...")
            time.sleep(reconnect_delay_with_backoff)
            connect_to_server(WS_SERVER_URL)
        else:
            logger.error(f"Failed to reconnect after {MAX_RECONNECT_ATTEMPTS} attempts")
    else:
        reconnect_count = 0  # Reset count on clean close

def on_open(ws):
    """Handle successful WebSocket connection.
    
    Args:
        ws: WebSocket instance
    """
    global reconnect_count
    reconnect_count = 0  # Reset reconnect counter on successful connection
    
    logger.info(f"WebSocket connection opened to {WS_SERVER_URL}")
    
    # Send initial authentication/handshake message
    message = {
        "type": "handshake",
        "client_id": "ailinux_client",
        "version": "1.2.0"
    }
    ws.send(json.dumps(message))
    logger.info("Sent handshake message")

def connect_to_server(url):
    """Connect to WebSocket server with the given URL.
    
    Args:
        url: WebSocket server URL to connect to
    """
    logger.info(f"Connecting to WebSocket server at {url}")
    
    # Enable trace for detailed connection debugging if needed
    websocket.enableTrace(os.getenv("WS_DEBUG", "False").lower() == "true")
    
    # Create WebSocket connection with appropriate handlers
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Run the WebSocket connection in a blocking manner
    # For non-blocking, consider using threading or asyncio
    ws.run_forever(
        ping_interval=30,  # Send a ping every 30 seconds
        ping_timeout=10,   # Wait 10 seconds for a pong response
        reconnect=5        # Auto-reconnect after 5 seconds on network errors
    )

def send_message(ws, message_type, data):
    """Send a structured message to the WebSocket server.
    
    Args:
        ws: WebSocket instance
        message_type: Type of message being sent (e.g., 'query', 'log', 'status')
        data: Dictionary containing the message data
    """
    message = {
        "type": message_type,
        "timestamp": time.time(),
        "data": data
    }
    ws.send(json.dumps(message))
    logger.debug(f"Sent {message_type} message")

if __name__ == "__main__":
    # Override environment variables with command line args if provided
    if len(sys.argv) > 1 and sys.argv[1] in ["local", "remote"]:
        SERVER_MODE = sys.argv[1]
        WS_SERVER_URL = REMOTE_WS_URL if SERVER_MODE == "remote" else LOCAL_WS_URL
    
    logger.info(f"Starting WebSocket client in {SERVER_MODE} mode")
    logger.info(f"Target server: {WS_SERVER_URL}")
    
    try:
        connect_to_server(WS_SERVER_URL)
    except KeyboardInterrupt:
        logger.info("WebSocket client stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("WebSocket client shutdown complete")
