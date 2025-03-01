"""WebSocket client for AILinux system.

This module provides a WebSocket client that can connect to either a local
or remote WebSocket server for real-time communication between backend and frontend.
"""
import websocket
import threading
import logging
import json
import time
import os
import uuid
from typing import Dict, Any, Optional, Callable, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("WebSocketClient")

# Server configuration
WS_SERVER_URL = os.getenv("WS_SERVER_URL", "ws://localhost:8082")
WS_API_KEY = os.getenv("WS_API_KEY", "")
WS_RECONNECT_DELAY = int(os.getenv("WS_RECONNECT_DELAY", "5"))
WS_MAX_RECONNECT = int(os.getenv("WS_MAX_RECONNECT", "10"))
WS_HEARTBEAT_INTERVAL = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))

class WebSocketClient:
    """WebSocket client for real-time communication."""
    
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
        
        # Start connection if requested
        if auto_connect:
            self.connect()
    
    def connect(self):
        """Connect to the WebSocket server."""
        if self.connected or self.ws_thread and self.ws_thread.is_alive():
            logger.info("WebSocket already connected or connecting")
            return
        
        self.shutdown_requested = False
        self.ws_thread = threading.Thread(target=self._connect_and_run, daemon=True)
        self.ws_thread.start()
        logger.info(f"Started WebSocket connection thread to {self.url}")
    
    def disconnect(self):
        """Disconnect from the WebSocket server."""
        self.shutdown_requested = True
        if self.ws:
            self.ws.close()
        
        # Wait for thread to terminate
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=2.0)
        
        self.connected = False
        logger.info("WebSocket disconnected")
    
    def is_connected(self) -> bool:
        """Check if the WebSocket is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected
    
    def send_message(self, message_type: str, data: Dict[str, Any]):
        """Send a message to the WebSocket server.
        
        Args:
            message_type: Type of the message
            data: Message data
        
        Returns:
            bool: True if message was sent, False otherwise
        """
        if not self.connected or not self.ws:
            logger.warning(f"Cannot send message, WebSocket not connected: {message_type}")
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
            logger.debug(f"Sent message: {message_type}")
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False
    
    def register_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Callback function for the message type
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")
    
    def _connect_and_run(self):
        """Connect to the WebSocket server and run the message loop."""
        while not self.shutdown_requested:
            try:
                # Connect to the server
                logger.info(f"Connecting to WebSocket server: {self.url}")
                
                # Create WebSocket connection
                websocket.enableTrace(os.getenv("WS_DEBUG", "False").lower() == "true")
                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                
                # Start the WebSocket loop
                self.ws.run_forever(
                    ping_interval=WS_HEARTBEAT_INTERVAL,
                    ping_timeout=5
                )
                
                # Check if shutdown was requested
                if self.shutdown_requested:
                    logger.info("Shutdown requested, stopping reconnection attempts")
                    break
                
                # Reconnect after delay if not shutdown
                self.reconnect_count += 1
                if self.reconnect_count > WS_MAX_RECONNECT:
                    logger.error(f"Maximum reconnection attempts ({WS_MAX_RECONNECT}) reached")
                    break
                
                # Exponential backoff for reconnection
                delay = min(WS_RECONNECT_DELAY * (2 ** (self.reconnect_count - 1)), 60)
                logger.info(f"Reconnecting in {delay}s (attempt {self.reconnect_count}/{WS_MAX_RECONNECT})")
                time.sleep(delay)
            
            except Exception as e:
                logger.error(f"Error in WebSocket thread: {str(e)}")
                
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
        logger.info(f"WebSocket connected to {self.url}")
        
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
            
            logger.debug(f"Received message type: {message_type}")
            
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
                    logger.error(f"Error in message handler for {message_type}: {str(e)}")
            else:
                logger.debug(f"No handler for message type: {message_type}")
        
        except json.JSONDecodeError:
            logger.warning(f"Received non-JSON message: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
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
            logger.info(f"WebSocket closed with code: {close_status_code}, message: {close_msg}")
        else:
            logger.info("WebSocket closed")
    
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
        print(f"Echo: {data}")
    
    # Create client and register handler
    client = WebSocketClient()
    client.register_handler("echo", echo_handler)
    
    # Connect to server
    client.connect()
    
    try:
        # Keep running until interrupted
        while True:
            if client.is_connected():
                client.send_message("echo", {"text": "Hello from AILinux!"})
            time.sleep(5)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        client.disconnect()
