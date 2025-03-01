"""WebSocket client for AILinux using Autobahn.

Provides connection to WebSocket server on derleiti.de.
"""
import asyncio
import json
import ssl
import logging
from urllib.parse import urlparse
import traceback

from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("WebSocketClient")

class MyWebSocketClientProtocol(WebSocketClientProtocol):
    """WebSocket client protocol handler for AILinux.
    
    Extends the WebSocketClientProtocol to handle AILinux-specific functionality.
    """
    def onConnect(self, response):
        """Handle successful connection to the server."""
        logger.info(f"Connected to server: {response.peer}")

    def onOpen(self):
        """Handle WebSocket connection open event."""
        logger.info("WebSocket connection opened")
        try:
            message = json.dumps({"message": "Hello, AI Model!"})
            self.sendMessage(message.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error sending initial message: {str(e)}")

    def onMessage(self, payload, isBinary):
        """Handle incoming WebSocket messages."""
        try:
            if not isBinary:
                message = payload.decode('utf-8')
                logger.info(f"Received message: {message}")
                
                # Parse JSON if possible to handle structured messages
                try:
                    data = json.loads(message)
                    if "type" in data:
                        self.handleTypedMessage(data)
                except json.JSONDecodeError:
                    # Not JSON, treat as plain text
                    pass
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
    
    def handleTypedMessage(self, data):
        """Handle typed messages based on their 'type' field."""
        message_type = data.get("type", "")
        
        if message_type == "ping":
            # Respond to ping messages
            try:
                response = json.dumps({"type": "pong", "timestamp": data.get("timestamp")})
                self.sendMessage(response.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error sending pong response: {str(e)}")
        
        # Add other message type handlers as needed

    def onClose(self, wasClean, code, reason):
        """Handle WebSocket connection closed event."""
        logger.error(f"WebSocket connection closed: {reason or 'Unknown reason'}")

async def connect_to_server(url):
    """
    Connect to the WebSocket server using Autobahn.
    
    Args:
        url: WebSocket URL to connect to
        
    Returns:
        WebSocket protocol handler
    """
    try:
        uri = urlparse(url)
        ssl_context = None
        
        # Set up SSL if using secure WebSocket
        if uri.scheme == "wss":
            ssl_context = ssl.create_default_context()
            # Verify hostname and certificates by default
            # Uncomment to disable verification (not recommended for production)
            # ssl_context.check_hostname = False
            # ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create factory and set protocol
        factory = WebSocketClientFactory(url)
        factory.protocol = MyWebSocketClientProtocol
        
        # Get event loop and create connection
        loop = asyncio.get_event_loop()
        try:
            conn = loop.create_connection(factory, uri.hostname, uri.port or (443 if uri.scheme == "wss" else 80), ssl=ssl_context)
            transport, protocol = await conn
            logger.info(f"Successfully connected to {url}")
            return protocol
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            raise
    except Exception as e:
        logger.error(f"Error setting up connection: {str(e)}")
        logger.debug(traceback.format_exc())
        raise

async def main():
    """Run the main application loop."""
    ws_client = None
    try:
        ws_url = "wss://derleiti.de:8082"
        logger.info(f"Connecting to WebSocket server at {ws_url}")
        
        # Connect to server
        ws_client = await connect_to_server(ws_url)
        
        # Keep connection open for demonstration
        await asyncio.sleep(10)
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
    finally:
        logger.info("Closing WebSocket connection")
        if ws_client and hasattr(ws_client, 'sendClose'):
            try:
                # Attempt a clean shutdown
                await ws_client.sendClose(1000, "Normal shutdown")
            except Exception as shutdown_error:
                logger.warning(f"Error during clean shutdown: {str(shutdown_error)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.debug(traceback.format_exc())
