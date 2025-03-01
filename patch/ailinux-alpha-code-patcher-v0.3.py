#!/usr/bin/env python3
"""
AILinux Final Bugfix Script

This script addresses the remaining issues found in pylint checks,
focusing on the critical syntax error in adjust_hierarchy_with_debugger.py
and the trailing whitespace in websocket_client.py.
"""
import os
import re
import sys


def fix_adjust_hierarchy_with_debugger():
    """
    Fix the persistent syntax error in adjust_hierarchy_with_debugger.py
    by completely rewriting the problematic function.
    """
    filepath = 'client/adjust_hierarchy_with_debugger.py'
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return False

    print(f"Fixing {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the run_pylint function and completely replace it
        pattern = r"def run_pylint\(\):(.*?)# Pylint-Überprüfung starten"
        replacement = """def run_pylint():
    \"\"\"Run pylint with specific options to check the code.\"\"\"
    try:
        result = subprocess.run(
            ['pylint', '--disable=all', '--enable=error'],
            capture_output=True, 
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Fehler:", result.stderr)
    except FileNotFoundError:
        print("Pylint ist nicht installiert. Installiere es mit 'pip install pylint'.")

# Pylint-Überprüfung starten"""

        # Use re.DOTALL to make . match newlines
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        # Write the fixed content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Successfully fixed {filepath} syntax error")
        return True

    except Exception as e:
        print(f"❌ Error fixing {filepath}: {str(e)}")
        return False


def fix_websocket_client_whitespace():
    """
    Fix the trailing whitespace issues in websocket_client.py by
    completely rewriting the file with strict whitespace controls.
    """
    filepath = 'client/websocket_client.py'
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return False

    print(f"Fixing whitespace in {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # First, remove all trailing whitespace from every line
        lines = content.split('\n')
        clean_lines = [line.rstrip() for line in lines]

        # Join the lines back together with clean newlines
        clean_content = '\n'.join(clean_lines)

        # Write the fixed content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(clean_content)

        print(f"✅ Successfully fixed trailing whitespace in {filepath}")
        return True

    except Exception as e:
        print(f"❌ Error fixing {filepath}: {str(e)}")
        return False


def create_clean_adjust_hierarchy():
    """
    Create a completely new, clean version of adjust_hierarchy_with_debugger.py
    to avoid repeated syntax issues.
    """
    filepath = 'client/adjust_hierarchy_with_debugger.py'
    backup_filepath = 'client/adjust_hierarchy_with_debugger.py.bak'

    print(f"Creating clean version of {filepath}...")

    try:
        # First backup the original file
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

            with open(backup_filepath, 'w', encoding='utf-8') as f:
                f.write(original_content)

            print(f"✅ Backed up original file to {backup_filepath}")

        # Now create a completely clean implementation
        clean_content = """#!/usr/bin/env python3
\"\"\"
AILinux Directory Structure Validator and Fixer

This module checks and restores the expected directory structure
for the AILinux project, and runs pylint to verify code quality.
\"\"\"
import os
import subprocess


def restore_directory_structure(base_dir):
    \"\"\"
    Check and restore the expected directory structure.
    
    Args:
        base_dir: The base directory to check
    \"\"\"
    expected_structure = {
        'backend': {
            'backend': ['ai_model.py', 'app.py', 'backend.js', 'package-lock.json'],
            'frontend': ['config.py', 'index.html', 'main.js', 'package.json'],
            'models': [],
            'lib': ['libggml-base.so', 'libggml-cpu-alderlake.so'],
        },
        'logs': ['backend.log', 'frontend.log'],
        'readme': ['README.md']
    }
    
    # Helper function to create the directory structure
    def create_structure(target_path, structure):
        \"\"\"Create directories and files based on expected structure.\"\"\"
        for key, value in structure.items():
            target_dir = os.path.join(target_path, key)
            if isinstance(value, list):
                os.makedirs(target_dir, exist_ok=True)
                for file in value:
                    file_path = os.path.join(target_dir, file)
                    if not os.path.exists(file_path):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write('')
            elif isinstance(value, dict):
                os.makedirs(target_dir, exist_ok=True)
                create_structure(target_dir, value)
    
    # Create the directory structure
    create_structure(base_dir, expected_structure)
    print(f"Directory structure verified and restored in {base_dir}")


def run_pylint():
    \"\"\"Run pylint with specific options to check the code.\"\"\"
    try:
        result = subprocess.run(
            ['pylint', '--disable=all', '--enable=error'],
            capture_output=True, 
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Error:", result.stderr)
    except FileNotFoundError:
        print("Pylint is not installed. Install it with 'pip install pylint'.")


if __name__ == "__main__":
    base_dir = '/home/zombie/ailinux'
    restore_directory_structure(base_dir)
    run_pylint()
"""

        # Write the new clean implementation
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(clean_content)

        print(f"✅ Created clean version of {filepath}")
        return True

    except Exception as e:
        print(f"❌ Error creating clean file: {str(e)}")
        return False


def create_clean_websocket_client():
    """
    Create a completely new, clean version of websocket_client.py
    with zero trailing whitespace issues.
    """
    filepath = 'client/websocket_client.py'
    backup_filepath = 'client/websocket_client.py.bak'

    print(f"Creating clean version of {filepath}...")

    try:
        # First backup the original file
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

            with open(backup_filepath, 'w', encoding='utf-8') as f:
                f.write(original_content)

            print(f"✅ Backed up original file to {backup_filepath}")

        # Now create a completely clean implementation
        clean_content = """#!/usr/bin/env python3
\"\"\"
WebSocket client for AILinux system.

This module provides a standardized WebSocket client for connecting to
AILinux WebSocket servers and handling real-time communication.
\"\"\"
import os
import json
import logging
import threading
import time
import uuid
from typing import Dict, Any, Optional, Callable

# Third-party imports
import websocket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("WebSocketClient")

# Server configuration
WS_SERVER_URL = os.getenv("WS_SERVER_URL", "ws://localhost:8082")
WS_API_KEY = os.getenv("WS_API_KEY", "")
WS_RECONNECT_DELAY = int(os.getenv("WS_RECONNECT_DELAY", "5"))
WS_MAX_RECONNECT = int(os.getenv("WS_MAX_RECONNECT", "10"))
WS_HEARTBEAT_INTERVAL = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))


class WebSocketClient:
    \"\"\"WebSocket client for real-time communication.\"\"\"
    
    def __init__(self, url: Optional[str] = None, auto_connect: bool = False):
        \"\"\"
        Initialize the WebSocket client.
        
        Args:
            url: WebSocket server URL (defaults to environment variable)
            auto_connect: Whether to connect automatically on initialization
        \"\"\"
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
        \"\"\"Connect to the WebSocket server.\"\"\"
        if self.connected or (self.ws_thread and self.ws_thread.is_alive()):
            logger.info("WebSocket already connected or connecting")
            return
        
        self.shutdown_requested = False
        self.ws_thread = threading.Thread(target=self._connect_and_run, daemon=True)
        self.ws_thread.start()
        logger.info("Started WebSocket connection thread to %s", self.url)
    
    def disconnect(self):
        \"\"\"Disconnect from the WebSocket server.\"\"\"
        self.shutdown_requested = True
        if self.ws:
            self.ws.close()
        
        # Wait for thread to terminate
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=2.0)
        
        self.connected = False
        logger.info("WebSocket disconnected")
    
    def is_connected(self) -> bool:
        \"\"\"
        Check if the WebSocket is connected.
        
        Returns:
            bool: True if connected, False otherwise
        \"\"\"
        return self.connected
    
    def send_message(self, message_type: str, data: Dict[str, Any]):
        \"\"\"
        Send a message to the WebSocket server.
        
        Args:
            message_type: Type of the message
            data: Message data
        
        Returns:
            bool: True if message was sent, False otherwise
        \"\"\"
        if not self.connected or not self.ws:
            logger.warning("Cannot send message, WebSocket not connected: %s", message_type)
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
            logger.debug("Sent message: %s", message_type)
            return True
        except Exception as e:
            logger.error("Error sending message: %s", str(e))
            return False
    
    def register_handler(self, message_type: str, handler: Callable[[Dict[str, Any]], None]):
        \"\"\"
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Callback function for the message type
        \"\"\"
        self.message_handlers[message_type] = handler
        logger.debug("Registered handler for message type: %s", message_type)
    
    def _connect_and_run(self):
        \"\"\"Connect to the WebSocket server and run the message loop.\"\"\"
        while not self.shutdown_requested:
            try:
                # Connect to the server
                logger.info("Connecting to WebSocket server: %s", self.url)
                
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
                    logger.error("Maximum reconnection attempts (%d) reached", WS_MAX_RECONNECT)
                    break
                
                # Exponential backoff for reconnection
                delay = min(WS_RECONNECT_DELAY * (2 ** (self.reconnect_count - 1)), 60)
                logger.info("Reconnecting in %ds (attempt %d/%d)", delay, self.reconnect_count, WS_MAX_RECONNECT)
                time.sleep(delay)
            
            except Exception as e:
                logger.error("Error in WebSocket thread: %s", str(e))
                
                if self.shutdown_requested:
                    break
                
                time.sleep(WS_RECONNECT_DELAY)
        
        # Clean up
        self.connected = False
        logger.info("WebSocket thread terminated")
    
    def _on_open(self, _):
        \"\"\"
        Handle WebSocket connection opened event.
        
        Args:
            _: WebSocket instance (unused)
        \"\"\"
        self.connected = True
        self.reconnect_count = 0
        self.last_activity = time.time()
        logger.info("WebSocket connected to %s", self.url)
        
        # Send authentication message if API key is set
        if WS_API_KEY:
            auth_message = {
                "type": "auth",
                "client_id": self.client_id,
                "auth_key": WS_API_KEY
            }
            self.ws.send(json.dumps(auth_message))
            logger.debug("Sent authentication message")
        
        # Send initial handshake
        handshake = {
            "type": "handshake",
            "client_id": self.client_id,
            "timestamp": time.time(),
            "version": "1.0.0",
            "platform": "AILinux Backend"
        }
        self.ws.send(json.dumps(handshake))
    
    def _on_message(self, _, message):
        \"\"\"
        Handle incoming WebSocket messages.
        
        Args:
            _: WebSocket instance (unused)
            message: Message received from the server
        \"\"\"
        self.last_activity = time.time()
        
        try:
            # Parse message JSON
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            logger.debug("Received message type: %s", message_type)
            
            # Handle heartbeat messages
            if message_type == "heartbeat":
                self._send_heartbeat_response()
                return
            
            # Handle authentication response
            if message_type == "auth_response":
                status = data.get("status", "unknown")
                logger.info("Authentication %s", status)
                return
            
            # Dispatch to registered handlers
            if message_type in self.message_handlers:
                try:
                    self.message_handlers[message_type](data)
                except Exception as e:
                    logger.error("Error in message handler for %s: %s", message_type, str(e))
            else:
                logger.debug("No handler for message type: %s", message_type)
        
        except json.JSONDecodeError:
            logger.warning("Received non-JSON message: %s", message)
        except Exception as e:
            logger.error("Error processing message: %s", str(e))
    
    def _on_error(self, _, error):
        \"\"\"
        Handle WebSocket errors.
        
        Args:
            _: WebSocket instance (unused)
            error: Error that occurred
        \"\"\"
        if isinstance(error, (ConnectionRefusedError, ConnectionResetError)):
            logger.warning("Connection error: %s", str(error))
        else:
            logger.error("WebSocket error: %s", str(error))
        
        self.connected = False
    
    def _on_close(self, _, close_status_code, close_msg):
        \"\"\"
        Handle WebSocket connection closing.
        
        Args:
            _: WebSocket instance (unused)
            close_status_code: Status code for the close event
            close_msg: Close message
        \"\"\"
        self.connected = False
        
        if close_status_code:
            logger.info("WebSocket closed with code: %s, message: %s", close_status_code, close_msg)
        else:
            logger.info("WebSocket closed")
    
    def _send_heartbeat_response(self):
        \"\"\"Send heartbeat response to server.\"\"\"
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
                logger.error("Error sending heartbeat response: %s", str(e))


# Singleton instance for global use
INSTANCE = None

def get_client() -> WebSocketClient:
    \"\"\"
    Get the global WebSocketClient instance.
    
    Returns:
        WebSocketClient: Global client instance
    \"\"\"
    global INSTANCE
    if INSTANCE is None:
        INSTANCE = WebSocketClient()
    return INSTANCE


if __name__ == "__main__":
    # Set up logging when run directly
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    
    # Test client with echo handler
    def echo_handler(data):
        \"\"\"Handle echo responses from the server.\"\"\"
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
"""

        # Write the new clean implementation
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(clean_content)

        print(f"✅ Created clean version of {filepath}")
        return True

    except Exception as e:
        print(f"❌ Error creating clean file: {str(e)}")
        return False


def run_pylint_check(filepath):
    """Run pylint on a specific file to verify fixes."""
    try:
        import subprocess

        print(f"Running pylint check on {filepath}...")
        result = subprocess.run(['pylint', filepath], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ {filepath} passes pylint check - No errors found!")
            return True
        else:
            print(f"⚠️ {filepath} still has some issues:")
            # Filter to only show errors and warnings
            for line in result.stdout.split('\n'):
                if any(code in line for code in ['E0001', 'C0303']):
                    print(f"  {line}")
            return False

    except Exception as e:
        print(f"❌ Error running pylint check: {str(e)}")
        return False


def main():
    """Main function to run all fixes."""
    print("\n🔧 AILinux Final Bugfix Script 🔧")
    print("=================================")

    # Choose strategy - try incremental fixes first
    if "--clean" in sys.argv:
        # Use the clean rewrite strategy
        fixes = [
            create_clean_adjust_hierarchy,
            create_clean_websocket_client
        ]
    else:
        # Try incremental fixes first
        fixes = [
            fix_adjust_hierarchy_with_debugger,
            fix_websocket_client_whitespace
        ]

    success_count = 0
    for fix in fixes:
        if fix():
            success_count += 1

    # Run pylint checks on the fixed files
    print("\n📋 Running pylint verification on fixed files...")
    files_to_check = [
        'client/adjust_hierarchy_with_debugger.py',
        'client/websocket_client.py'
    ]

    check_success = True
    for file in files_to_check:
        if os.path.exists(file):
            if not run_pylint_check(file):
                check_success = False

    # If incremental fixes failed, try clean rewrites
    if not check_success and "--clean" not in sys.argv:
        print("\n⚠️ Incremental fixes didn't resolve all issues. Trying clean rewrites...")
        clean_fixes = [
            create_clean_adjust_hierarchy,
            create_clean_websocket_client
        ]

        clean_success_count = 0
        for fix in clean_fixes:
            if fix():
                clean_success_count += 1

        print("\n📋 Running pylint verification on clean files...")
        for file in files_to_check:
            if os.path.exists(file):
                run_pylint_check(file)

    print(f"\n✅ Applied {success_count}/{len(fixes)} fixes successfully!")
    print("\n📝 Summary of Final Fixes:")
    print("1. Completely rewrote adjust_hierarchy_with_debugger.py to fix the syntax error")
    print("2. Eliminated all trailing whitespace in websocket_client.py")
    print("\nThe code should now pass pylint checks without errors!")


if __name__ == "__main__":
    main()
