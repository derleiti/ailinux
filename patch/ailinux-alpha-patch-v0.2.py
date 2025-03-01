#!/usr/bin/env python3
"""
AILinux Complete Bugfix Script

This script addresses all remaining issues found in the optimization_fixed.log file,
focusing on the critical syntax errors and code style problems.
"""
import os
import re
# import sys
  # removed: W0611
# import shutil
  # removed: W0611
from pathlib import Path


def fix_adjust_hierarchy_with_debugger():
    """
    Fix syntax errors in adjust_hierarchy_with_debugger.py.
    The main issue is an unexpected indentation on line 15.
    """
    filepath = 'client/adjust_hierarchy_with_debugger.py'
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return False

    print(f"Fixing {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.readlines()

        # Looking for the problematic line
        for i, line in enumerate(content):
            if 'result = subprocess.run' in line and 'check=True' in line:
                # Found the problematic line, fix the syntax
                content[i] = ""
                    "    result = subprocess.run(['pylint', '--disable=all', '--enable=error'], check=True, capture_output=True, text=True)\n"
                # Remove the next line if it's a continuation of this problematic syntax
                if i+1 < len(content) and 'capture_output=True' in content[i+1]:
                    content[i+1] = ""

                print(f"  Fixed indentation error on line {i+1}")
                break

        # Write the fixed content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(content)

        print(f"✅ Successfully fixed {filepath}")
        return True

    except Exception as e:
        print(f"❌ Error fixing {filepath}: {str(e)}")
        return False


def fix_websocket_client_module():
    """
    Fix issues in the WebSocket client modules by reorganizing imports
    and addressing trailing whitespace issues.
    """
    # Fix both the original file and the renamed one created earlier
    filepaths = [
        'client/websocket-client.py',
        'client/websocket_client_module.py'
    ]

    for filepath in filepaths:
        if not os.path.exists(filepath):
            print(f"Warning: File not found: {filepath}")
            continue

        print(f"Fixing {filepath}...")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 1. Fix module docstring if missing
            if not content.strip().startswith('"""'):
                module_name = os.path.basename(filepath).replace('.py', '').replace('-', '_')
                docstring = f'"""" +
                    "WebSocket client module for AILinux project.\n\nProvides functionality for connecting to WebSocket servers and handling real-time communication.\n"""\n'
                content = docstring + content

            # 2. Remove trailing whitespace from all lines
            content = '\n'.join(line.rstrip() for line in content.split('\n'))

            # 3. Fix import ordering - move standard library imports before third-party imports
            # Extract the import section
            import_lines = []
            other_lines = []
            in_import_section = True

            for line in content.split('\n'):
                if line.strip() and not line.strip().startswith('"""" +
                    "') and not line.strip().endswith('"""'):
                    if in_import_section and (line.startswith('import ') or line.startswith('from ')):
                        import_lines.append(line)
                    else:
                        in_import_section = False
                        other_lines.append(line)
                else:
                    if in_import_section:
                        import_lines.append(line)
                    else:
                        other_lines.append(line)

            # Separate standard library imports from third-party imports
            std_lib_imports = []
            third_party_imports = []

            std_lib_modules = [
                'os', 'sys', 'time', 'json', 'logging', 'threading', 'uuid', 
                'typing', 'datetime', 'pathlib', 're', 'collections', 'functools'
            ]

            for line in import_lines:
                if line.strip() and (line.startswith('import ') or line.startswith('from ')):
                    module = line.split()[1].split('.')[0]
                    if module in std_lib_modules:
                        std_lib_imports.append(line)
                    else:
                        third_party_imports.append(line)
                else:
                    # Keep empty lines and comments in their original positions
                    if len(std_lib_imports) > 0:
                        std_lib_imports.append(line)
                    elif len(third_party_imports) > 0:
                        third_party_imports.append(line)
                    else:
                        std_lib_imports.append(line)

            # Recombine the import sections in the correct order
            new_content = '\n'.join(std_lib_imports + third_party_imports + other_lines)

            # 4. Fix string formatting in logging calls
            # Replace f-strings with % formatting in logging calls
            pattern = r'logger\.(debug|info|warning|error|critical)\(f"([^"]*)"'
            replacement = r'logger.\1("\\2"'
            new_content = re.sub(pattern, replacement, new_content)

            # 5. Fix constant naming
            new_content = new_content.replace('_instance = None', 'INSTANCE = None')
            new_content = new_content.replace('global _instance', 'global INSTANCE')
            new_content = new_content.replace('_instance is None', 'INSTANCE is None')
            new_content = new_content.replace('" +
                "_instance = WebSocketClient()', 'INSTANCE = WebSocketClient()')

            # 6. Add missing docstring to echo_handler function
            new_content = new_content.replace(
                'def echo_handler(data):',
                'def echo_handler(data):\n    """Handle echo responses from the server."""'
            )

            # 7. Remove unused import
            new_content = new_content.replace(', List', '')

            # Write the fixed content back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f"✅ Successfully fixed {filepath}")

        except Exception as e:
            print(f"❌ Error fixing {filepath}: {str(e)}")


def fix_alphaos_py():
    """
    Fix issues in alphaos.py, including class docstring and import ordering.
    """
    filepath = 'client/alphaos.py'
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return False

    print(f"Fixing {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Fix module docstring if missing
        if not content.strip().startswith('"""'):
            docstring = '"""" +
                "WebSocket client implementation using autobahn library for AILinux project.\n\nProvides a WebSocket client protocol for connecting to AILinux servers.\n"""\n'
            content = docstring + content

        # 2. Add class docstring
        class_def_pattern = r'class MyWebSocketClientProtocol\(WebSocketClientProtocol\):'
        class_docstring = 'class MyWebSocketClientProtocol(WebSocketClientProtocol):\n    """" +
            "WebSocket client protocol handler for AILinux.\n    \n    Extends the WebSocketClientProtocol to handle AILinux-specific functionality.\n    """'
        content = re.sub(class_def_pattern, class_docstring, content)

        # 3. Add docstring to main function
        if 'async def main():' in content and not re.search(r'async def main\(\):\s+"""', content):
            content = content.replace(
                'async def main():',
                'async def main():\n    """Run the main application loop."""'
            )

        # 4. Fix import ordering
        # Extract imports
        import_section = re.search(r'import.*?(?=class|\n\n)', content, re.DOTALL)
        if import_section:
            imports = import_section.group(0)

            # Separate standard lib from third-party
            std_imports = []
            third_party_imports = []

            for line in imports.split('\n'):
                if line.strip():
                    if line.startswith('import asyncio') or line.startswith('import json') or line.startswith('import ssl') or line.startswith('import logging') or 'urllib.parse' in line:
                        std_imports.append(line)
                    else:
                        third_party_imports.append(line)

            # Replace the imports section with ordered imports
            new_imports = '\n'.join(std_imports + [''] + third_party_imports)
            content = content.replace(imports, new_imports)

        # 5. Replace f-string with % formatting in logging
        pattern = r'logging\.error\(f"([^"]*)"'
        replacement = r'logging.error("\1"'
        content = re.sub(pattern, replacement, content)

        # 6. Address unused variables
        # Instead of removing them, use '_' prefix to indicate they're intentionally unused
        content = content.replace('" +
            "transport, protocol = await conn', '_transport, protocol = await conn')
        content = content.replace('" +
            "ws_client = await connect_to_server', '_ws_client = await connect_to_server')

        # Write the fixed content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Successfully fixed {filepath}")
        return True

    except Exception as e:
        print(f"❌ Error fixing {filepath}: {str(e)}")
        return False


def fix_bigfiles_py():
    """
    Fix issues in bigfiles.py, including constant naming and pointless statements.
    """
    filepath = 'client/bigfiles.py'
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return False

    print(f"Fixing {filepath}...")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.readlines()

        # Fix module docstring
        if not content[0].startswith('"""'):
            content.insert(0, '"""Module for finding large files in the AILinux project."""\n')

        # Fix constant naming
        for i, line in enumerate(content):
            if 'directory = ' in line:
                content[i] = line.replace('directory =', 'DIRECTORY =')

        # Fix pointless statements
        for i, line in enumerate(content):
            if line.strip() == 'top_20_files' or line.strip() == '"" +
                "Directory does not exist or cannot be accessed"':
                content[i] = f"    print({line.strip()})\n"

        # Write the fixed content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(content)

        print(f"✅ Successfully fixed {filepath}")
        return True

    except Exception as e:
        print(f"❌ Error fixing {filepath}: {str(e)}")
        return False


def create_unified_websocket_client():
    """
    Create a unified WebSocket client by merging the best parts of both versions
    and ensuring it meets all code quality standards.
    """
    new_filepath = 'client/websocket_client.py'

    print(f"Creating unified WebSocket client at {new_filepath}...")

    try:
        # Create a new, clean implementation
        content = '''"""
WebSocket client for AILinux system.

This module provides a standardized WebSocket client for connecting to
AILinux WebSocket servers and handling real-time communication.
"""
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
        if self.connected or (self.ws_thread and self.ws_thread.is_alive()):
            logger.info("WebSocket already connected or connecting")
            return
        
        self.shutdown_requested = False
        self.ws_thread = threading.Thread(target=self._connect_and_run, daemon=True)
        self.ws_thread.start()
        logger.info("Started WebSocket connection thread to %s", self.url)
    
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
        """Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Callback function for the message type
        """
        self.message_handlers[message_type] = handler
        logger.debug("Registered handler for message type: %s", message_type)
    
    def _connect_and_run(self):
        """Connect to the WebSocket server and run the message loop."""
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
        """Handle WebSocket connection opened event.
        
        Args:
            _: WebSocket instance (unused)
        """
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
        """Handle incoming WebSocket messages.
        
        Args:
            _: WebSocket instance (unused)
            message: Message received from the server
        """
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
        """Handle WebSocket errors.
        
        Args:
            _: WebSocket instance (unused)
            error: Error that occurred
        """
        if isinstance(error, (ConnectionRefusedError, ConnectionResetError)):
            logger.warning("Connection error: %s", str(error))
        else:
            logger.error("WebSocket error: %s", str(error))
        
        self.connected = False
    
    def _on_close(self, _, close_status_code, close_msg):
        """Handle WebSocket connection closing.
        
        Args:
            _: WebSocket instance (unused)
            close_status_code: Status code for the close event
            close_msg: Close message
        """
        self.connected = False
        
        if close_status_code:
            logger.info("WebSocket closed with code: %s, message: %s", close_status_code, close_msg)
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
                logger.error("Error sending heartbeat response: %s", str(e))


# Singleton instance for global use
INSTANCE = None

def get_client() -> WebSocketClient:
    """Get the global WebSocketClient instance.
    
    Returns:
        WebSocketClient: Global client instance
    """
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
        """Handle echo responses from the server."""
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
'''

        # Write the new implementation
        with open(new_filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Successfully created unified WebSocket client at {new_filepath}")
        return True

    except Exception as e:
        print(f"❌ Error creating unified WebSocket client: {str(e)}")
        return False


def run_pylint_check(filepath):
    """Run pylint on a specific file to check for issues."""
    try:
        import subprocess

        print(f"Running pylint check on {filepath}...")
        result = subprocess.run(['pylint', filepath], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ {filepath} passes pylint check")
            return True
        else:
            print(f"⚠️ {filepath} still has some issues:")
            for line in result.stdout.split('\n'):
                if 'E0001' in line or 'C0303' in line or 'C0103' in line:
                    print(f"  {line}")
            return False

    except Exception as e:
        print(f"❌ Error running pylint check: {str(e)}")
        return False


def main():
    """Main function to run all fixes."""
    print("\n🔧 AILinux Complete Bugfix Script 🔧")
    print("====================================")

    # Run the fixes
    fixes = [
        fix_adjust_hierarchy_with_debugger,
        fix_websocket_client_module,
        fix_alphaos_py,
        fix_bigfiles_py,
        create_unified_websocket_client
    ]

    success_count = 0
    for fix in fixes:
        if fix():
            success_count += 1

    # Run pylint checks on the fixed files
    print("\n📋 Running pylint checks on fixed files...")
    files_to_check = [
        'client/adjust_hierarchy_with_debugger.py',
        'client/alphaos.py',
        'client/bigfiles.py',
        'client/websocket_client.py'
    ]

    for file in files_to_check:
        if os.path.exists(file):
            run_pylint_check(file)

    print(f"\n✅ Applied {success_count}/{len(fixes)} fixes successfully!")
    print("\n📝 Summary of Fixes:")
    print("1. Fixed syntax error in adjust_hierarchy_with_debugger.py")
    print("2. Created a clean, compliant websocket_client.py")
    print("3. Fixed class docstrings and import ordering in alphaos.py")
    print("4. Fixed constant naming and pointless statements in bigfiles.py")
    print("5. Addressed various style issues like trailing whitespace and f-string in logging")
    print("\nThe code should now pass pylint checks and have fewer errors.")


if __name__ == "__main__":
    main()
