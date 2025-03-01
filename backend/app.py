"""AILinux Backend Server for log analysis using AI models.

This module provides a Flask-based API that processes log files using 
various AI models and returns analysis results.
"""
import logging
import os
import sys
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from ai_model import analyze_log

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
        logger.debug(f"Log content: {log_text[:100]}...")  # Log first 100 chars for debugging

        # Process and analyze the log
        translated_log = translate_log(log_text)
        response = analyze_log(translated_log, model_name)

        # Log the AI model response
        logger.debug(f"AI model response: {response[:100]}...")  # Log first 100 chars

        # Return analysis response
        return jsonify({"analysis": response})
    
    except Exception as e:
        logger.exception(f"Error in debug endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500


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


@app.route('/settings', methods=['POST'])
def update_settings():
    """Update application settings.
    
    Returns:
        JSON response confirming settings update
    """
    try:
        new_settings = request.json
        # Here you would save the settings to a configuration file
        # For now, just log the received settings
        logger.info(f"Received new settings: {new_settings}")
        return jsonify({"status": "success", "message": "Settings updated"})
    
    except Exception as e:
        logger.exception(f"Error updating settings: {str(e)}")
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
        "version": "1.0.0"
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
