"""AILinux Backend Server for log analysis using AI models.

This module provides a Flask-based API that processes log files using 
various AI models and returns analysis results.
"""
import logging
import os
import sys
import json
import time
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
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
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Backend')


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
        logger.debug(f"" +
            "Log content (truncated): {log_text[:100]}..." if len(log_text) > 100 else f"Log content: {log_text}")

        # Process and analyze the log
        response = analyze_log(log_text, model_name, instruction)

        # Save the analysis to a history file for reference
        save_analysis_history(log_text, response, model_name)

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
        logger.exception(f"Error in debug endpoint: {str(e)}")
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

        # Read the log file if it exists
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                logs = f.readlines()

            # Return only the last 'limit' lines
            logs = logs[-limit:]
            return jsonify({"logs": logs})

        return jsonify({"logs": []})

    except Exception as e:
        logger.exception(f"Error retrieving logs: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/models', methods=['GET'])
def get_models():
    """Get information about available AI models.
    
    Returns:
        JSON response with model information
    """
    try:
        models = get_available_models()
        return jsonify({"models": models})
    except Exception as e:
        logger.exception(f"Error getting model information: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/settings', methods=['GET', 'POST'])
def handle_settings():
    """Get or update application settings.
    
    Returns:
        JSON response with settings or confirmation
    """
    settings_file = os.path.join(os.path.dirname(__file__), 'settings.json')

    if request.method == 'GET':
        try:
            # Load settings from file if it exists
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return jsonify(settings)
            else:
                # Return default settings
                default_settings = {
                    "default_model": "gpt4all",
                    "max_log_size": 10000,
                    "theme": "light",
                    
                    "huggingface_model_id": os.getenv("HUGGINGFACE_MODEL_ID", "" +
                        "mistralai/Mistral-7B-Instruct-v0.2")
                }
                return jsonify(default_settings)
        except Exception as e:
            logger.exception(f"Error getting settings: {str(e)}")
            return jsonify({"error": str(e)}), 500
    else:  # POST
        try:
            new_settings = request.json

            # Save settings to file
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(new_settings, f, indent=2)

            # Update environment variables if needed
            if "huggingface_model_id" in new_settings:
                os.environ["HUGGINGFACE_MODEL_ID"] = new_settings["huggingface_model_id"]

            logger.info(f"Settings updated: {new_settings}")
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
        "version": "1.0.0",
        "server_time": time.time()
    })


@app.route('/analysis_history', methods=['GET'])
def get_analysis_history():
    """Get the history of past analyses.
    
    Returns:
        JSON response with analysis history
    """
    try:
        history_file = os.path.join(log_directory, "analysis_history.json")

        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return jsonify({"history": history})
        else:
            return jsonify({"history": []})
    except Exception as e:
        logger.exception(f"Error retrieving analysis history: {str(e)}")
        return jsonify({"error": str(e)}), 500


def save_analysis_history(log_text, analysis, model_name):
    """Save the log analysis to a history file.
    
    Args:
        log_text: The original log text
        analysis: The AI analysis result
        model_name: The model used for analysis
    """
    try:
        history_file = os.path.join(log_directory, "analysis_history.json")

        # Create a new history entry
        entry = {
            "timestamp": time.time(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": model_name,
            "log_text": log_text[:100] + "..." if len(log_text) > 100 else log_text,
            "analysis": analysis[:500] + "..." if len(analysis) > 500 else analysis
        }

        # Load existing history or initialize new one
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []
        else:
            history = []

        # Add new entry and limit size to 100 entries
        history.insert(0, entry)
        history = history[:100]

        # Save back to file
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)

    except Exception as e:
        logger.error(f"Error saving analysis history: {str(e)}")


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
            logger.info("Using remote configuration")

    logger.info(f"Starting backend server on {HOST}:{PORT} (Debug: {DEBUG})")
    logger.info(f"Environment: {ENV}")

    # Check if models are available
    models = get_available_models()
    available_models = [model["name"] for model in models if model["available"]]
    logger.info(f"Available models: {', '.join(available_models)}")

    # Start the Flask server
    app.run(host=HOST, port=PORT, debug=DEBUG)
