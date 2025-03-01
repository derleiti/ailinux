"""AILinux Backend Server for log analysis using AI models.

This module provides a Flask-based API that processes log files using 
various AI models and returns analysis results.
"""
import logging
import os
import sys
import traceback
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import psutil
from ai_model import analyze_log, get_available_models

# Load environment variables
load_dotenv()

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

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    filename=log_file_path,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger('Backend')

# Create console handler for logging to console as well
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Debug log file for storing AI model responses
DEBUG_LOG_FILE = os.path.join(log_directory, "debug_history.log")


@app.route('/debug', methods=['POST'])
def debug():
    """Process and analyze log data with AI models.
    
    Returns:
        JSON response containing AI analysis or error information
    """
    try:
        # Validate input data
        if not request.is_json:
            logger.error("Request does not contain valid JSON")
            return jsonify({"error": "Request must be in JSON format"}), 400

        data = request.json
        log_text = data.get('log')
        model_name = data.get('model', 'gpt4all')  # Default to gpt4all

        if not log_text:
            logger.error("No log text provided")
            return jsonify({"error": "No log text provided"}), 400

        logger.info(f"Received log for analysis using model: {model_name}")
        logger.debug(f"" +
            "Log content preview: {log_text[:100]}...")  # Log first 100 chars for debugging

        # Process and analyze the log
        translated_log = translate_log(log_text)
        response = analyze_log(translated_log, model_name)

        # Log the AI model response
        logger.debug(f"AI model response preview: {response[:100]}...")  # Log first 100 chars

        # Record the debug request and response to debug history
        log_debug_history(log_text, response, model_name)

        # Return analysis response
        return jsonify({"analysis": response})

    except Exception as e:
        error_message = f"Error in debug endpoint: {str(e)}"
        stack_trace = traceback.format_exc()
        logger.exception(error_message)
        logger.debug(f"Stack trace: {stack_trace}")
        return jsonify({"error": error_message}), 500


@app.route('/logs', methods=['GET'])
def get_logs():
    """Retrieve log files.
    
    Returns:
        JSON response containing available logs
    """
    try:
        # Read the log file if it exists
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                logs = f.readlines()
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

            import json
            with open(settings_file, 'w') as f:
                json.dump(new_settings, f, indent=2)

            logger.info(f"Updated settings: {new_settings}")
            return jsonify({"status": "success", "message": "Settings updated"})
        except Exception as e:
            logger.exception(f"Error updating settings: {str(e)}")
            return jsonify({"error": str(e)}), 500
    else:
        try:
            import json
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
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


def translate_log(log_text):
    """Preprocess log text before AI analysis.
    
    This function can be expanded to implement more sophisticated 
    log translation or normalization.
    
    Args:
        log_text: The original log text
        
    Returns:
        Processed log text
    """
    # In the future, add log normalization or preprocessing here
    return log_text


def log_debug_history(log_text, response, model_name):
    """Record debug requests and responses to a history file.
    
    Args:
        log_text: The original log text
        response: The AI response
        model_name: The AI model used
    """
    try:
        timestamp = datetime.now().isoformat()
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(f"--- {timestamp} ---\n")
            log_file.write(f"Model: {model_name}\n")
            log_file.write(f"Log: {log_text}\n")
            log_file.write(f"Response: {response}\n\n")
    except Exception as e:
        logger.error(f"Error writing to debug history: {str(e)}")


if __name__ == "__main__":
    # Allow command line arguments to override environment variables
    if len(sys.argv) > 1:
        if sys.argv[1] == "local":
            HOST = "localhost"
            logger.info("Using localhost configuration")
        elif sys.argv[1] == "remote":
            HOST = "derleiti.de"
            logger.info("Using remote (derleiti.de) configuration")

    logger.info(f"Starting backend server on {HOST}:{PORT} (Debug: {DEBUG})...")
    logger.info(f"Environment: {ENV}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
