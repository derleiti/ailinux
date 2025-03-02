"""WebSocket server for AILinux.

This module provides a WebSocket server for real-time communication between
the frontend and backend components of AILinux.
"""
import asyncio
import json
import logging
import os
import time
import ssl
import uuid
import traceback
from typing import Dict, Set, Any, Optional
import websockets
from datetime import datetime, timedelta

# Initialize AI model
try:
    from ai_model import analyze_log, get_available_models
except ImportError:
    logging.error("Failed to import AI model module. Make sure ai_model.py is in the same directory.")
    raise ImportError("ai_model module not found")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("dotenv package not installed, environment variables must be set manually")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("websocket_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WebSocketServer")

# Server configuration
HOST = os.getenv("WS_HOST", "0.0.0.0")
PORT = int(os.getenv("WS_PORT", 8082))
USE_SSL = os.getenv("WS_USE_SSL", "False").lower() == "true"
SSL_CERT = os.getenv("WS_SSL_CERT", "")
SSL_KEY = os.getenv("WS_SSL_KEY", "")

# API key for authentication (optional)
API_KEY = os.getenv("WEBSOCKET_API_KEY", "")

# Rate limiting configuration
RATE_LIMIT_INTERVAL = float(os.getenv("WS_RATE_LIMIT", "1.0"))  # Seconds between messages
MAX_MESSAGE_SIZE = int(os.getenv("WS_MAX_MESSAGE_SIZE", "1048576"))  # 1MB default
MAX_CONCURRENT_ANALYSES = int(os.getenv("WS_MAX_CONCURRENT_ANALYSES", "4"))  # Max concurrent analyses

# Global state
connected_clients: Dict[str, Any] = {}
active_sessions: Dict[str, Dict[str, Any]] = {}
client_rate_limits: Dict[str, float] = {}
server_start_time: float = 0

# Semaphore to limit concurrent analyses
analysis_semaphore = None  # Will be initialized in main()


async def authenticate_client(websocket, message_data):
    """Authenticate a client connection.
    
    Args:
        websocket: The WebSocket connection
        message_data: The message data containing authentication info
        
    Returns:
        bool: True if authentication successful, False otherwise
        str: Client ID if authenticated, None otherwise
    """
    client_id = str(uuid.uuid4())
    remote_address = websocket.remote_address[0] if hasattr(websocket, 'remote_address') else 'unknown'

    # If API key is set, require authentication
    if API_KEY:
        auth_key = message_data.get("auth_key", "")
        if auth_key != API_KEY:
            logger.warning(f"❌ Invalid API key from {remote_address} - Closing connection")
            await websocket.send(json.dumps({
                "type": "error",
                "error": "Unauthorized",
                "code": 401
            }))
            return False, None

    # Extract client info
    client_info = {
        "id": client_id,
        "remote_address": remote_address,
        "connected_at": time.time(),
        "last_activity": time.time(),
        "user_agent": message_data.get("user_agent", "unknown"),
        "client_type": message_data.get("client_type", "generic"),
        "version": message_data.get("version", "unknown")
    }

    # Store client info
    connected_clients[client_id] = client_info
    logger.info(f"✅ Client authenticated: {client_id} from {remote_address}")

    # Send success response
    await websocket.send(json.dumps({
        "type": "authentication",
        "status": "success",
        "client_id": client_id,
        "message": "Authentication successful"
    }))

    return True, client_id


async def handle_message(websocket, client_id, message_data):
    """Handle an incoming WebSocket message.
    
    Args:
        websocket: The WebSocket connection
        client_id: The client identifier
        message_data: The parsed message data
    """
    message_type = message_data.get("type", "unknown")

    # Update last activity timestamp
    if client_id in connected_clients:
        connected_clients[client_id]["last_activity"] = time.time()

    # Handle different message types
    if message_type == "ping":
        # Simple ping-pong for connection testing
        await websocket.send(json.dumps({
            "type": "pong",
            "timestamp": time.time()
        }))

    elif message_type == "analyze_log":
        # Process log analysis request
        log_text = message_data.get("log", "")
        model_name = message_data.get("model", "gpt4all")
        instruction = message_data.get("instruction")

        if not log_text:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "No log text provided",
                "code": 400
            }))
            return

        # Create a unique ID for this analysis request
        request_id = str(uuid.uuid4())

        # Send acknowledgment first
        await websocket.send(json.dumps({
            "type": "request_received",
            "request_id": request_id,
            "message": "Log analysis request received and being processed"
        }))

        # Process the log asynchronously with resource limiting
        asyncio.create_task(
            process_log_analysis(websocket, client_id, request_id, log_text, model_name, instruction)
        )

    elif message_type == "get_models":
        # Return information about available models
        models = get_available_models()
        await websocket.send(json.dumps({
            "type": "models_info",
            "models": models
        }))

    elif message_type == "server_status":
        # Return server status information
        status_info = {
            "uptime": time.time() - server_start_time,
            "clients_connected": len(connected_clients),
            "active_sessions": len(active_sessions),
            "server_time": time.time()
        }
        await websocket.send(json.dumps({
            "type": "server_status",
            "status": status_info
        }))

    else:
        logger.warning(f"Unknown message type: {message_type} from client {client_id}")
        await websocket.send(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "code": 400
        }))


async def process_log_analysis(websocket, client_id, request_id, log_text, model_name, instruction):
    """Process a log analysis request asynchronously.
    
    Args:
        websocket: The WebSocket connection
        client_id: The client identifier
        request_id: The unique request identifier
        log_text: The log text to analyze
        model_name: The model to use for analysis
        instruction: Optional instruction for the analysis
    """
    # Use semaphore to limit concurrent analyses
    async with analysis_semaphore:
        try:
            # Track the session
            active_sessions[request_id] = {
                "client_id": client_id,
                "start_time": time.time(),
                "model": model_name,
                "status": "processing"
            }

            # Send processing status update
            await websocket.send(json.dumps({
                "type": "analysis_status",
                "request_id": request_id,
                "status": "processing",
                "message": f"Processing log with {model_name} model"
            }))

            # Analyze the log in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            analysis_result = await loop.run_in_executor(
                None, lambda: analyze_log(log_text, model_name, instruction)
            )

            # Calculate processing time
            processing_time = time.time() - active_sessions[request_id]["start_time"]

            # Update session info
            active_sessions[request_id]["status"] = "completed"
            active_sessions[request_id]["processing_time"] = processing_time
            active_sessions[request_id]["completed_at"] = time.time()

            # Send result back to client
            await websocket.send(json.dumps({
                "type": "analysis_result",
                "request_id": request_id,
                "analysis": analysis_result,
                "processing_time": processing_time,
                "model": model_name
            }))

            logger.info(f"Log analysis completed for request {request_id} in {processing_time:.2f} seconds")

        except Exception as e:
            logger.exception(f"Error processing log analysis request {request_id}: {str(e)}")
            logger.debug(traceback.format_exc())

            # Send error message to client
            try:
                await websocket.send(json.dumps({
                    "type": "error",
                    "request_id": request_id,
                    "message": f"Error analyzing log: {str(e)}",
                    "code": 500
                }))
            except Exception as send_error:
                logger.error(f"Error sending error response to client: {str(send_error)}")

            # Update session info
            if request_id in active_sessions:
                active_sessions[request_id]["status"] = "error"
                active_sessions[request_id]["error"] = str(e)
                active_sessions[request_id]["completed_at"] = time.time()

        finally:
            # Clean up the session after a delay (keep it for a while for reference)
            await asyncio.sleep(300)  # 5 minutes
            if request_id in active_sessions:
                del active_sessions[request_id]


async def connection_handler(websocket, path):
    """Handle WebSocket connections.
    
    Args:
        websocket: The WebSocket connection
        path: The connection path
    """
    client_id = None
    authenticated = False
    remote_address = websocket.remote_address[0] if hasattr(websocket, 'remote_address') else 'unknown'

    try:
        logger.info(f"New connection from {remote_address}")

        # Wait for the authentication message
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            message_data = json.loads(message)

            # Authenticate the client
            authenticated, client_id = await authenticate_client(websocket, message_data)
            if not authenticated:
                return

        except asyncio.TimeoutError:
            logger.warning(f"Authentication timeout for {remote_address}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Authentication timeout",
                "code": 408
            }))
            return
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in authentication message from {remote_address}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON",
                "code": 400
            }))
            return

        # Main message handling loop
        async for message in websocket:
            now = time.time()

            # Check rate limit
            if client_id in client_rate_limits:
                last_message_time = client_rate_limits[client_id]
                if now - last_message_time < RATE_LIMIT_INTERVAL:
                    logger.warning(f"⏳ Rate limit reached for client {client_id}, message ignored")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Rate limit reached, please slow down",
                        "code": 429
                    }))
                    continue

            # Update rate limit timestamp
            client_rate_limits[client_id] = now

            try:
                # Check message size
                if len(message) > MAX_MESSAGE_SIZE:
                    logger.warning(f"Message too large from client {client_id}: {len(message)} bytes")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Message too large",
                        "code": 413
                    }))
                    continue

                # Parse and handle the message
                message_data = json.loads(message)
                await handle_message(websocket, client_id, message_data)

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client {client_id}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON",
                    "code": 400
                }))
            except Exception as e:
                logger.exception(f"Error handling message from client {client_id}: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Server error processing message",
                    "code": 500
                }))

    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Connection closed with client {client_id or remote_address}: {e.code} {e.reason}")
    except Exception as e:
        logger.exception(f"Error in connection handler for {client_id or remote_address}: {str(e)}")
    finally:
        # Clean up client data
        if client_id:
            if client_id in connected_clients:
                del connected_clients[client_id]
            if client_id in client_rate_limits:
                del client_rate_limits[client_id]
            logger.info(f"Client disconnected: {client_id}")


async def heartbeat_sender():
    """Send periodic heartbeat messages to clients."""
    while True:
        try:
            # Send heartbeat to all connected clients
            if connected_clients:
                heartbeat_time = time.time()
                count = 0
                
                # Create a copy to avoid modification during iteration
                clients = list(connected_clients.items())
                
                for client_id, client_info in clients:
                    # Only send heartbeat if client hasn't been active recently
                    if heartbeat_time - client_info.get("last_activity", 0) > 30:
                        try:
                            # Get client's WebSocket connection
                            if "websocket" in client_info and client_info["websocket"]:
                                websocket = client_info["websocket"]
                                
                                # Send heartbeat
                                await websocket.send(json.dumps({
                                    "type": "heartbeat",
                                    "timestamp": heartbeat_time,
                                    "server_time": heartbeat_time
                                }))
                                count += 1
                        except Exception as e:
                            logger.debug(f"Error sending heartbeat to client {client_id}: {str(e)}")
                
                if count > 0:
                    logger.debug(f"Sent heartbeat to {count} clients")
        except Exception as e:
            logger.error(f"Error in heartbeat sender: {str(e)}")
        
        # Send heartbeat every 30 seconds
        await asyncio.sleep(30)


async def periodic_cleanup():
    """Periodically clean up inactive sessions and clients."""
    while True:
        try:
            now = time.time()

            # Clean up inactive clients (no activity for 1 hour)
            inactive_clients = []
            for client_id, client_info in connected_clients.items():
                if "last_activity" in client_info and now - client_info["last_activity"] > 3600:
                    inactive_clients.append(client_id)

            for client_id in inactive_clients:
                logger.info(f"Removing inactive client: {client_id}")
                if client_id in connected_clients:
                    del connected_clients[client_id]
                if client_id in client_rate_limits:
                    del client_rate_limits[client_id]

            # Clean up old sessions (completed or error for more than 1 hour)
            old_sessions = []
            for request_id, session_info in active_sessions.items():
                if session_info["status"] in ["completed", "error"] and now - session_info["start_time"] > 3600:
                    old_sessions.append(request_id)

            for request_id in old_sessions:
                if request_id in active_sessions:
                    del active_sessions[request_id]

            # Log server status periodically
            if logger.isEnabledFor(logging.INFO):
                logger.info(f"Server status: {len(connected_clients)} connected clients, {len(active_sessions)} active sessions")

        except Exception as e:
            logger.exception(f"Error in periodic cleanup: {str(e)}")

        # Run every 15 minutes
        await asyncio.sleep(900)


async def main():
    """Main function to start the WebSocket server."""
    global server_start_time, analysis_semaphore
    
    # Record server start time
    server_start_time = time.time()
    
    # Initialize semaphore to limit concurrent analyses
    analysis_semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSES)

    # Set up SSL if enabled
    ssl_context = None
    if USE_SSL and SSL_CERT and SSL_KEY:
        if os.path.exists(SSL_CERT) and os.path.exists(SSL_KEY):
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(SSL_CERT, SSL_KEY)
            logger.info(f"SSL enabled with cert: {SSL_CERT}")
        else:
            logger.error(f"SSL certificate or key not found: {SSL_CERT}, {SSL_KEY}")
            logger.info("Running without SSL")

    # Start the server
    async with websockets.serve(
        connection_handler,
        HOST,
        PORT,
        ssl=ssl_context,
        max_size=MAX_MESSAGE_SIZE,
        ping_interval=30,
        ping_timeout=10,
        close_timeout=10
    ):
        logger.info(f"🚀 WebSocket server running on {HOST}:{PORT} (SSL: {'enabled' if ssl_context else 'disabled'})")

        # Start the periodic tasks
        cleanup_task = asyncio.create_task(periodic_cleanup())
        heartbeat_task = asyncio.create_task(heartbeat_sender())

        # Keep the server running indefinitely
        await asyncio.Future()


if __name__ == "__main__":
    try:
        # Print banner
        print("""
        █████╗ ██╗██╗     ██╗███╗   ██╗██╗   ██╗██╗  ██╗
       ██╔══██╗██║██║     ██║████╗  ██║██║   ██║╚██╗██╔╝
       ███████║██║██║     ██║██╔██╗ ██║██║   ██║ ╚███╔╝
       ██╔══██║██║██║     ██║██║╚██╗██║██║   ██║ ██╔██╗
       ██║  ██║██║███████╗██║██║ ╚████║╚██████╔╝██╔╝ ██╗
       ╚═╝  ╚═╝╚═╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝
                                                         
       WebSocket Server
       """)

        # Add graceful shutdown handler
        def handle_shutdown():
            logger.info("Server shutting down...")
            # Add any cleanup tasks here

        import atexit
        atexit.register(handle_shutdown)

        # Start the server
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Error starting server: {str(e)}")
        logger.debug(traceback.format_exc())
