"""
WebSocket Client for AILinux

This module provides a robust WebSocket client with improved connection handling,
error recovery, and compatibility with both local and remote WebSocket servers.
"""
import websocket
import threading
import logging
import json
import time
import os
import uuid
import ssl
import traceback
from typing import Dict, Any, Optional, Callable, List, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("websocket_client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WebSocketClient")

# Load environment variables with safe defaults
WS_SERVER_URL = os.getenv("WS_SERVER_URL", "ws://localhost:8082")
WS_API_KEY = os.getenv("WS_API_KEY", "")
WS_RECONNECT_DELAY = int(os.getenv("WS_RECONNECT_DELAY", "5"))
WS_MAX_RECONNECT = int(os.getenv("WS_MAX_RECONNECT", "10"))
WS_HEARTBEAT_INTERVAL = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
WS_DEBUG = os.getenv("WS_DEBUG", "False").lower() == "true"

# Check if websocket-client is available
try:
    import websocket
except ImportError:
    logger.error("websocket-client package not installed. Installing...")
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websocket-client"])
        import websocket
        logger.info("websocket-client installed successfully")
    except Exception as e:
        logger.error(f"Failed to install websocket-client: {e}")

class WebSocketClient:
    """WebSocket client implementation with reconnection and error handling."""

    def __init__(self, url: Optional[str] = None, auto_connect: bool = False):
        """Initialize the WebSocket client.

        Args:
            url: WebSocket server URL (defaults to environment variable)
            auto_connect: Whether to connect automatically on initialization
        """
        self.url = url or WS_SERVER_URL
        self.ws = None
        self.connected = False
        self.reconnect_count = 0
        self.client_id = f"ailinux-{str(uuid.uuid4())[:8]}"
        self.shutdown_requested = False
        self.ws_thread = None
        self.message_handlers = {}
        self.last_activity = time.time()
        self.last_heartbeat = time.time()
        self.connection_lock = threading.Lock()

        # Start connection if requested
        if auto_connect:
            self.connect()

    def connect(self):
        """Connect to the WebSocket server."""
        with self.connection_lock:
            if self.connected or (self.ws_thread and self.ws_thread.is_alive()):
                logger.info("WebSocket already connected or connecting")
                return

            self.shutdown_requested = False
            self.ws_thread = threading.Thread(target=self._connect_and_run, daemon=True)
            self.ws_thread.start()
            logger.info(f"Connecting to WebSocket server at {self.url}")

    def disconnect(self):
        """Disconnect from the WebSocket server."""
        with self.connection_lock:
            self.shutdown_requested = True
            if self.ws:
                try:
                    self.ws.close()
                except Exception as e:
                    logger.error(f"Error closing WebSocket connection: {str(e)}")

            # Wait for thread to terminate
            if self.ws_thread and self.ws_thread.is_alive():
                try:
                    self.ws_thread.join(timeout=2.0)
                except Exception as e:
                    logger.error(f"Error joining WebSocket thread: {str(e)}")

            self.connected = False
            logger.info("WebSocket disconnected")

    def is_connected(self) -> bool:
        """Check if the WebSocket is connected.

        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected

    def send_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        """Send a message to the WebSocket server.

        Args:
            message_type: Type of the message
            data: Message data

        Returns:
            bool: True if message was sent, False otherwise
        """
        if not self.connected or not self.ws:
            logger.warning(f"Cannot send message of type '{message_type}': Not connected to server")
            return False

        try:
            message = {
                "type": message_type,
                "client_id": self.client_id,
                "timestamp": time.time(),
                "data": data
            }

            self.ws.send(json.dumps(message))
            self.last_activity = time.time()
            logger.debug(f"Sent message of type '{message_type}' to server")
            return True
        except Exception as e:
            logger.error(f"Error sending message of type '{message_type}': {str(e)}")
            # Reconnect on send failure
            self._schedule_reconnect()
            return False

    def register_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Register a handler for a specific message type.

        Args:
            message_type: Type of message to handle
            handler: Callback function for the message type
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type '{message_type}'")

    def _schedule_reconnect(self):
        """Schedule a reconnection attempt."""
        if self.shutdown_requested:
            return

        # Run reconnect in a separate thread to avoid blocking
        reconnect_thread = threading.Thread(target=self.reconnect, daemon=True)
        reconnect_thread.start()

    def reconnect(self):
        """Force reconnection to the WebSocket server."""
        with self.connection_lock:
            if self.ws:
                try:
                    self.ws.close()
                except Exception:
                    pass

            self.connected = False

            # Only start a new thread if the old one is done
            if not self.ws_thread or not self.ws_thread.is_alive():
                self.reconnect_count = 0
                self.shutdown_requested = False
                self.ws_thread = threading.Thread(target=self._connect_and_run, daemon=True)
                self.ws_thread.start()
                logger.info(f"Reconnecting to WebSocket server at {self.url}")

    def _connect_and_run(self):
        """Connect to the WebSocket server and run the message loop."""
        while not self.shutdown_requested:
            try:
                # Connect to the server
                logger.info(f"Attempting to connect to {self.url} (attempt {self.reconnect_count + 1}/{WS_MAX_RECONNECT})")

                # Set up SSL context if using secure WebSocket
                ssl_opt = None
                if self.url.startswith("wss://"):
                    ssl_opt = {"cert_reqs": ssl.CERT_REQUIRED}
                    # Uncomment to disable certificate verification (not recommended for production)
                    # ssl_opt = {"cert_reqs": ssl.CERT_NONE}

                # Backoff strategy to avoid excessive reconnection attempts
                # Try a simpler connection test first
                test_ws = None
                try:
                    # Try a quick connection to see if server is reachable
                    test_ws = websocket.create_connection(
                        self.url,
                        timeout=5,
                        sslopt=ssl_opt
                    )
                    test_ws.close()
                    logger.info("Server connection test successful")
                except Exception as e:
                    logger.warning(f"Server connection test failed: {str(e)}")
                    # If we can't connect at all, wait before retrying
                    self.reconnect_count += 1
                    if self.reconnect_count > WS_MAX_RECONNECT:
                        logger.error(f"Maximum reconnection attempts ({WS_MAX_RECONNECT}) reached, giving up")
                        break

                    # Exponential backoff
                    delay = min(WS_RECONNECT_DELAY * (2 ** (self.reconnect_count - 1)), 60)
                    logger.info(f"Waiting {delay} seconds before next connection attempt...")
                    time.sleep(delay)
                    continue

                # Create WebSocket connection
                websocket.enableTrace(WS_DEBUG)
                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                    on_ping=self._on_ping,
                    on_pong=self._on_pong
                )

                # Start the WebSocket loop with appropriate settings
                self.ws.run_forever(
                    ping_interval=WS_HEARTBEAT_INTERVAL,
                    ping_timeout=10,
                    sslopt=ssl_opt
                )

                # Check if shutdown was requested
                if self.shutdown_requested:
                    logger.info("Shutdown requested, stopping reconnection attempts")
                    break

                # Reconnect after delay if not shutdown
                self.reconnect_count += 1
                if self.reconnect_count > WS_MAX_RECONNECT:
                    logger.error(f"Maximum reconnection attempts ({WS_MAX_RECONNECT}) reached, giving up")
                    break

                # Exponential backoff for reconnection
                delay = min(WS_RECONNECT_DELAY * (2 ** (self.reconnect_count - 1)), 60)
                logger.info(f"Reconnecting in {delay} seconds...")
                time.sleep(delay)

            except Exception as e:
                logger.error(f"Error in WebSocket connection: {str(e)}")
                logger.debug(traceback.format_exc())

                if self.shutdown_requested:
                    break

                time.sleep(WS_RECONNECT_DELAY)

        # Clean up
        self.connected = False
        logger.info("WebSocket thread terminated")

    def _on_open(self, ws):
        """Handle WebSocket connection opened event.

        Args:
            ws: WebSocket instance
        """
        self.connected = True
        self.reconnect_count = 0
        self.last_activity = time.time()
        logger.info("WebSocket connection opened successfully")

        # Send authentication message if API key is set
        if WS_API_KEY:
            auth_message = {
                "type": "auth",
                "client_id": self.client_id,
                "auth_key": WS_API_KEY
            }
            ws.send(json.dumps(auth_message))
            logger.debug("Sent authentication message")

        # Send initial handshake
        handshake = {
            "type": "handshake",
            "client_id": self.client_id,
            "timestamp": time.time(),
            "version": "1.0.0",
            "platform": "AILinux Backend"
        }
        ws.send(json.dumps(handshake))
        logger.debug("Sent handshake message")

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages.

        Args:
            ws: WebSocket instance
            message: Message received from the server
        """
        self.last_activity = time.time()

        try:
            # Parse message JSON
            data = json.loads(message)
            message_type = data.get("type", "unknown")

            logger.debug(f"Received message of type '{message_type}' from server")

            # Handle heartbeat messages
            if message_type == "heartbeat":
                self._send_heartbeat_response()
                return

            # Handle authentication response
            if message_type == "auth_response":
                status = data.get("status", "unknown")
                logger.info(f"Authentication {status}")
                return

            # Dispatch to registered handlers
            if message_type in self.message_handlers:
                try:
                    self.message_handlers[message_type](data)
                except Exception as e:
                    logger.error(f"Error in message handler for type '{message_type}': {str(e)}")
                    logger.debug(traceback.format_exc())
            else:
                logger.debug(f"No handler registered for message type '{message_type}'")

        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON message: {message[:100]}...")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.debug(traceback.format_exc())

    def _on_error(self, ws, error):
        """Handle WebSocket errors.

        Args:
            ws: WebSocket instance
            error: Error that occurred
        """
        if isinstance(error, (ConnectionRefusedError, ConnectionResetError)):
            logger.warning(f"Connection error: {str(error)}")
        else:
            logger.error(f"WebSocket error: {str(error)}")
            logger.debug(traceback.format_exc())

        self.connected = False

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closing.

        Args:
            ws: WebSocket instance
            close_status_code: Status code for the close event
            close_msg: Close message
        """
        self.connected = False

        if close_status_code:
            logger.info(f"WebSocket closed with status code {close_status_code}: {close_msg or 'No message'}")
        else:
            logger.info("WebSocket closed")

    def _on_ping(self, ws, message):
        """Handle ping messages from the server.

        Args:
            ws: WebSocket instance
            message: Ping message
        """
        logger.debug("Received ping from server")
        # WebSocketApp automatically sends pong response

    def _on_pong(self, ws, message):
        """Handle pong messages from the server.

        Args:
            ws: WebSocket instance
            message: Pong message
        """
        logger.debug("Received pong from server")
        self.last_heartbeat = time.time()

    def _send_heartbeat_response(self):
        """Send heartbeat response to server."""
        if self.connected and self.ws:
            try:
                heartbeat_response = {
                    "type": "heartbeat_response",
                    "client_id": self.client_id,
                    "timestamp": time.time()
                }
                self.ws.send(json.dumps(heartbeat_response))
                self.last_heartbeat = time.time()
                logger.debug("Sent heartbeat response")
            except Exception as e:
                logger.error(f"Error sending heartbeat response: {str(e)}")


# Singleton instance for global use
_instance = None

def get_client() -> WebSocketClient:
    """Get the global WebSocketClient instance.

    Returns:
        WebSocketClient: Global client instance
    """
    global _instance
    if _instance is None:
        _instance = WebSocketClient()
    return _instance


if __name__ == "__main__":
    # Set up logging when run directly
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Test client with echo handler
    def echo_handler(data):
        """Handle echo responses from the server."""
        print(f"Echo: {data}")

    # Create client and register handler
    client = WebSocketClient()
    client.register_handler("echo", echo_handler)

    # Connect to server
    client.connect()

    try:
        # Simple test loop
        for i in range(10):
            if client.is_connected():
                client.send_message("echo", {"text": f"Hello from AILinux! Message {i+1}"})
            time.sleep(5)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        client.disconnect()
        print("Client disconnected")
