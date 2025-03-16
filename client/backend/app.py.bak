"""AILinux Backend Server for log analysis using AI models.

This module provides a Flask-based API that processes log files using 
various AI models and returns analysis results.
"""
import logging
import os
import sys
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import psutil

# Import AI model functions
try:
    from ai_model import analyze_log, get_available_models
except ImportError:
    logging.error("Failed to import AI model module. Make sure ai_model.py is in the same directory.")
    sys.exit(1)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("dotenv package not installed, environment variables must be set manually")

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Server configuration with fallback values
HOST = os.getenv("FLASK_HOST", "0.0.0.0")  # Default to all interfaces
PORT = int(os.getenv("FLASK_PORT", 8081))   # Default to 8081
DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
ENV = os.getenv("ENVIRONMENT", "development")

# Configure logging
log_directory = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(log_directory, exist_ok=True)
log_file_path = os.path.join(log_directory, "backend.log")

# Debug log file for storing AI model responses
DEBUG_LOG_FILE = os.path.join(log_directory, "debug_history.log")

# Configure logging with proper handlers
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Backend')

# Request logging middleware
@app.before_request
def log_request_info():
    """Log request details for debugging purposes."""
    if DEBUG:
        logger.debug(f"Request: {request.method} {request.path} - {request.remote_addr}")
        
        # Log headers and data for non-GET requests in debug mode
        if request.method != "GET":
            content_length = request.headers.get('Content-Length')
            if content_length and int(content_length) < 10000:  # Only log if not too large
                if request.is_json:
                    try:
                        logger.debug(f"Request JSON: {json.dumps(request.json, indent=2)}")
                    except Exception as e:
                        logger.debug(f"Failed to log request JSON: {str(e)}")

@app.after_request
def after_request(response):
    """Add CORS headers to allow all origins."""
    if DEBUG:
        logger.debug(f"Response: {response.status_code} - {response.content_length} bytes")
    
    return response

@app.route('/debug', methods=['POST'])
def debug():
    """Process and analyze log data with AI models.
    
    Returns:
        JSON response containing AI analysis or error information
    """
    start_time = time.time()

    try:
        # Validate input data
        if not request.is_json:
            logger.error("Request does not contain valid JSON")
            return jsonify({"error": "Request must be in JSON format"}), 400

        data = request.json
        log_text = data.get('log')
        model_name = data.get('model', 'gpt4all')  # Default to gpt4all
        instruction = data.get('instruction')

        if not log_text:
            logger.error("No log text provided")
            return jsonify({"error": "No log text provided"}), 400

        logger.info(f"Received log for analysis using model: {model_name}")
        logger.debug(f"Log content preview: {log_text[:100]}..." if len(log_text) > 100 else f"Log content: {log_text}")

        # Process and analyze the log
        translated_log = translate_log(log_text)
        response = analyze_log(translated_log, model_name, instruction)

        # Log the AI model response
        logger.debug(f"AI model response preview: {response[:100]}..." if len(response) > 100 else f"AI model response: {response}")

        # Record the debug request and response to debug history
        log_debug_history(log_text, response, model_name)

        # Calculate and log processing time
        elapsed_time = time.time() - start_time
        logger.info(f"Log analysis completed in {elapsed_time:.2f} seconds")

        # Return analysis response
        return jsonify({
            "analysis": response,
            "processing_time": elapsed_time,
            "model": model_name
        })

    except Exception as e:
        error_message = f"Error in debug endpoint: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.exception(error_message)
        logger.debug(f"Stack trace: {stack_trace}")
        return jsonify({
            "error": str(e),
            "message": "An error occurred during log analysis"
        }), 500


@app.route('/logs', methods=['GET'])
def get_logs():
    """Retrieve log files.
    
    Returns:
        JSON response containing available logs
    """
    try:
        # Optional limit parameter
        limit = request.args.get('limit', default=100, type=int)
        search = request.args.get('search', default=None, type=str)

        # Read the log file if it exists
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                logs = f.readlines()

            # Apply search filter if provided
            if search:
                logs = [log for log in logs if search.lower() in log.lower()]
            
            # Return only the last 'limit' lines
            logs = logs[-limit:]
            return jsonify({"logs": logs})

        return jsonify({"logs": []})

    except Exception as e:
        logger.exception(f"Error retrieving logs: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/models', methods=['GET'])
def get_models():
    """Get list of available AI models.
    
    Returns:
        JSON response containing available models
    """
    try:
        models = get_available_models()
        return jsonify({"models": models})
    except Exception as e:
        logger.exception(f"Error retrieving models: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/system', methods=['GET'])
def system_status():
    """Get system status information.
    
    Returns:
        JSON response with system metrics
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
        logger.exception(f"Error retrieving system status: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    """Update or retrieve application settings.
    
    Returns:
        JSON response with settings data or confirmation
    """
    settings_file = os.path.join(os.path.dirname(__file__), "settings.json")

    if request.method == 'POST':
        try:
            new_settings = request.json

            # Validate settings
            if not isinstance(new_settings, dict):
                return jsonify({"error": "Invalid settings format"}), 400

            # Ensure settings directory exists
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            
            # Save settings to file
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(new_settings, f, indent=2)

            logger.info(f"Updated settings: {new_settings}")
            return jsonify({"status": "success", "message": "Settings updated"})
        except Exception as e:
            logger.exception(f"Error updating settings: {str(e)}")
            return jsonify({"error": str(e)}), 500
    else:
        try:
            # Load settings from file if it exists
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return jsonify({"settings": settings})
            else:
                # Return default settings if file doesn't exist
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
            logger.exception(f"Error retrieving settings: {str(e)}")
            return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Check the health of the backend server.
    
    Returns:
        JSON response with server status
    """
    return jsonify({
        "status": "online",
        "environment": ENV,
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/analysis_history', methods=['GET'])
def get_analysis_history():
    """Get the history of log analyses.
    
    Returns:
        JSON response with analysis history
    """
    try:
        history_file = os.path.join(log_directory, "analysis_history.json")
        
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # Apply limit if provided
            limit = request.args.get('limit', default=50, type=int)
            history = history[:limit]
            
            return jsonify({"history": history})
        else:
            return jsonify({"history": []})
    except Exception as e:
        logger.exception(f"Error retrieving analysis history: {str(e)}")
        return jsonify({"error": str(e)}), 500


def translate_log(log_text):
    """Preprocess log text before AI analysis.
    
    This function can be expanded to implement more sophisticated 
    log translation or normalization.
    
    Args:
        log_text: The original log text
        
    Returns:
        Processed log text
    """
    # In a real implementation, you might want to:
    # - Remove sensitive information (IPs, usernames, etc.)
    # - Normalize timestamps
    # - Format and structure log entries
    # - Highlight errors and warnings
    
    # For now, just return the original text
    return log_text


def log_debug_history(log_text: str, response: str, model_name: str):
    """Record debug requests and responses to a history file.
    
    Args:
        log_text: The original log text
        response: The AI response
        model_name: The AI model used
    """
    try:
        timestamp = datetime.now().isoformat()
        
        # Create history directory if it doesn't exist
        os.makedirs(os.path.dirname(DEBUG_LOG_FILE), exist_ok=True)
        
        # Append to debug history log
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(f"--- {timestamp} ---\n")
            log_file.write(f"Model: {model_name}\n")
            log_file.write(f"Log: {log_text[:500]}...\n" if len(log_text) > 500 else f"Log: {log_text}\n")
            log_file.write(f"Response: {response[:500]}...\n\n" if len(response) > 500 else f"Response: {response}\n\n")
        
        # Also update JSON history file for structured access
        history_file = os.path.join(log_directory, "analysis_history.json")
        
        history_entry = {
            "timestamp": timestamp,
            "model": model_name,
            "log_text": log_text[:500] + "..." if len(log_text) > 500 else log_text,
            "response": response[:500] + "..." if len(response) > 500 else response
        }
        
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                # File exists but is not valid JSON, start with empty history
                history = []
        
        # Add new entry at the beginning (newest first)
        history.insert(0, history_entry)
        
        # Limit history size to 100 entries
        history = history[:100]
        
        # Write updated history
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
        
    except Exception as e:
        logger.error(f"Error writing to debug history: {str(e)}")


def handle_shutdown():
    """Perform cleanup tasks before server shutdown."""
    logger.info("Performing shutdown tasks...")
    # Add any cleanup tasks here
    logger.info("Server shutting down")


if __name__ == "__main__":
    # Print banner
    print("""
    █████╗ ██╗██╗     ██╗███╗   ██╗██╗   ██╗██╗  ██╗
   ██╔══██╗██║██║     ██║████╗  ██║██║   ██║╚██╗██╔╝
   ███████║██║██║     ██║██╔██╗ ██║██║   ██║ ╚███╔╝ 
   ██╔══██║██║██║     ██║██║╚██╗██║██║   ██║ ██╔██╗ 
   ██║  ██║██║███████╗██║██║ ╚████║╚██████╔╝██╔╝ ██╗
   ╚═╝  ╚═╝╚═╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝

   AI-Powered Log Analysis Server
   """)

    # Allow command line arguments to override environment variables
    if len(sys.argv) > 1:
        if sys.argv[1] == "local":
            HOST = "localhost"
            logger.info("Using localhost configuration")
        elif sys.argv[1] == "remote":
            HOST = "0.0.0.0"  # Listen on all interfaces for remote access
            logger.info("Using remote configuration (listening on all interfaces)")

    logger.info(f"Starting backend server on {HOST}:{PORT} (Debug: {DEBUG})")
    logger.info(f"Environment: {ENV}")

    # Check if models are available
    models = get_available_models()
    available_models = [model["name"] for model in models if model.get("available", False)]
    logger.info(f"Available models: {', '.join(available_models)}")

    # Register shutdown handler
    import atexit
    atexit.register(handle_shutdown)

    try:
        # Start the Flask server
        app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)
    except KeyboardInterrupt:
        logger.info("Server terminated by user")
    except Exception as e:
        logger.critical(f"Server failed to start: {str(e)}")
        logger.debug(traceback.format_exc())
