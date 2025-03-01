"""AILinux Backend Server for AI-powered log analysis.

This module provides a Flask-based API that processes log files using 
various AI models and returns analysis results. It supports multiple AI platforms
including GPT4All, OpenAI, Google Gemini, and Hugging Face.
"""
import os
import sys
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Import AI model functionality
from ai_model import (
    analyze_log,
    get_model_status,
    list_available_huggingface_models,
    search_huggingface_models
)

# Load environment variables
load_dotenv()

# Initialize Flask app with CORS support
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Server configuration with fallback values
HOST = os.getenv("FLASK_HOST", "0.0.0.0")  # Default to all interfaces
PORT = int(os.getenv("FLASK_PORT", 8081))   # Default to 8081
DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"
ENV = os.getenv("ENVIRONMENT", "development")

# Directory paths for logs and storage
ROOT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = ROOT_DIR / "logs"
DATA_DIR = ROOT_DIR / "data"

# Make sure directories exist
LOGS_DIR.mkdir(exist_ok=True, parents=True)
DATA_DIR.mkdir(exist_ok=True, parents=True)

# Log file paths
LOG_FILE = LOGS_DIR / "backend.log"
DEBUG_LOG_FILE = LOGS_DIR / "debug_history.log"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Backend')

# Request logging middleware
@app.before_request
def log_request_info():
    """Log information about each incoming request."""
    logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
    
    # Log request data for debugging if needed
    if DEBUG and request.is_json and request.content_length < 10000:  # Only log small JSON payloads
        logger.debug(f"Request data: {request.json}")

@app.after_request
def log_response_info(response):
    """Log information about each outgoing response."""
    logger.info(f"Response: {response.status} to {request.remote_addr}")
    return response

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    return jsonify({"error": "Resource not found", "path": request.path}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors."""
    return jsonify({"error": "Method not allowed", "method": request.method, "path": request.path}), 405

@app.errorhandler(500)
def server_error(error):
    """Handle 500 Internal Server Error errors."""
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Check the health of the backend server.
    
    Returns:
        JSON response with server status
    """
    return jsonify({
        "status": "online",
        "environment": ENV,
        "version": "1.2.0",
        "timestamp": datetime.now().isoformat()
    })

# Model status endpoint
@app.route('/models/status', methods=['GET'])
def model_status():
    """Get the status of all AI models.
    
    Returns:
        JSON response with model status information
    """
    status = get_model_status()
    return jsonify({"status": status})

# Hugging Face models list endpoint
@app.route('/models/huggingface', methods=['GET'])
def huggingface_models():
    """List available Hugging Face models.
    
    Query parameters:
        category: Model category (default: text-generation)
        limit: Maximum number of models to return (default: 10)
    
    Returns:
        JSON response with list of models
    """
    category = request.args.get('category', 'text-generation')
    limit = int(request.args.get('limit', 10))
    
    models = list_available_huggingface_models(category, limit)
    return jsonify({"models": models})

# Hugging Face model search endpoint
@app.route('/models/huggingface/search', methods=['GET'])
def search_models():
    """Search for Hugging Face models.
    
    Query parameters:
        q: Search query
        limit: Maximum number of models to return (default: 10)
    
    Returns:
        JSON response with search results
    """
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({"error": "Search query is required"}), 400
    
    models = search_huggingface_models(query, limit)
    return jsonify({"results": models})

# Log analysis endpoint
@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze log data with AI models.
    
    Request JSON:
        log: The log text to analyze
        model: The AI model to use (default: gpt4all)
        options: Additional options for the model
    
    Returns:
        JSON response containing AI analysis
    """
    try:
        # Validate input data
        if not request.is_json:
            return jsonify({"error": "Request must be in JSON format"}), 400
            
        data = request.json
        log_text = data.get('log')
        model_name = data.get('model', 'gpt4all')
        model_options = data.get('options', {})

        if not log_text:
            return jsonify({"error": "No log text provided"}), 400

        logger.info(f"Analyzing log with model: {model_name}")
        
        # Process and analyze the log
        results = analyze_log(log_text, model_name, model_options)
        
        # Save analysis to debug history log
        with open(DEBUG_LOG_FILE, "a") as log_file:
            timestamp = datetime.now().isoformat()
            log_file.write(f"[{timestamp}] Model: {model_name}\n")
            log_file.write(f"Log: {log_text[:500]}{'...' if len(log_text) > 500 else ''}\n")
            log_file.write(f"Analysis: {results['analysis']}\n\n")

        # Return analysis response
        return jsonify(results)
    
    except ValueError as e:
        logger.error(f"Value error in analyze endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        logger.exception(f"Error in analyze endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Legacy endpoint for backward compatibility
@app.route('/debug', methods=['POST'])
def debug():
    """Legacy endpoint for log analysis (redirects to /analyze).
    
    Returns:
        JSON response containing AI analysis
    """
    try:
        # Validate input data
        if not request.is_json:
            return jsonify({"error": "Request must be in JSON format"}), 400
            
        data = request.json
        log_text = data.get('log')
        model_name = data.get('model', 'gpt4all')

        if not log_text:
            return jsonify({"error": "No log text provided"}), 400

        logger.info(f"Legacy debug endpoint called with model: {model_name}")
        
        # Process and analyze the log
        results = analyze_log(log_text, model_name)
        
        # Format response for legacy clients
        return jsonify({"analysis": results["analysis"]})
    
    except Exception as e:
        logger.exception(f"Error in debug endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Logs retrieval endpoint
@app.route('/logs', methods=['GET'])
def get_logs():
    """Retrieve log files.
    
    Query parameters:
        type: Log type (default: backend, options: backend, debug)
        lines: Number of lines to return (default: 100)
    
    Returns:
        JSON response containing logs
    """
    try:
        log_type = request.args.get('type', 'backend')
        lines = int(request.args.get('lines', 100))
        
        # Determine which log file to read
        if log_type == 'debug':
            log_path = DEBUG_LOG_FILE
        else:  # Default to backend logs
            log_path = LOG_FILE
        
        # Read the log file if it exists
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                logs = f.readlines()
            
            # Return the last N lines
            return jsonify({"logs": logs[-lines:] if lines > 0 else logs})
        
        return jsonify({"logs": [], "warning": f"Log file {log_path} does not exist"})
    
    except Exception as e:
        logger.exception(f"Error retrieving logs: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Settings endpoint
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Get or update application settings.
    
    GET: Retrieve current settings
    POST: Update settings
    
    Returns:
        JSON response with settings or confirmation
    """
    settings_file = DATA_DIR / "settings.json"
    
    if request.method == 'GET':
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings_data = json.load(f)
                return jsonify(settings_data)
            else:
                # Return default settings if no file exists
                default_settings = {
                    "ai": {
                        "defaultModel": "gpt4all",
                        "modelsEnabled": {
                            "gpt4all": True,
                            "openai": bool(os.getenv("OPENAI_API_KEY")),
                            "gemini": bool(os.getenv("GEMINI_API_KEY")),
                            "huggingface": True
                        }
                    },
                    "ui": {
                        "theme": "light",
                        "logHistoryLimit": 100
                    },
                    "system": {
                        "logLevel": "info"
                    }
                }
                return jsonify(default_settings)
        except Exception as e:
            logger.exception(f"Error retrieving settings: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        try:
            new_settings = request.json
            
            # Validate settings format
            if not isinstance(new_settings, dict):
                return jsonify({"error": "Invalid settings format"}), 400
            
            # Save settings to file
            with open(settings_file, 'w') as f:
                json.dump(new_settings, f, indent=2)
            
            logger.info(f"Settings updated: {list(new_settings.keys())}")
            return jsonify({"status": "success", "message": "Settings updated"})
        except Exception as e:
            logger.exception(f"Error updating settings: {str(e)}")
            return jsonify({"error": str(e)}), 500

# Static file serving (for frontend)
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from the frontend directory.
    
    Args:
        path: Relative path to the file
    
    Returns:
        Static file response
    """
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')
    return send_from_directory(static_dir, path)

def translate_log(log_text):
    """Preprocess log text before AI analysis.
    
    This function normalizes log text by removing certain sensitive information
    and standardizing format.
    
    Args:
        log_text: The original log text
        
    Returns:
        Processed log text
    """
    # Remove potential sensitive information like API keys
    import re
    
    # Pattern to match potential API keys
    api_key_pattern = r'(api[_-]?key|token)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]{20,})["\']?'
    
    # Replace API keys with placeholder
    processed_text = re.sub(api_key_pattern, r'\1: [API_KEY_REDACTED]', log_text, flags=re.IGNORECASE)
    
    return processed_text

def main():
    """Main function to run the Flask server."""
    # Allow command line arguments to override environment variables
    if len(sys.argv) > 1:
        global HOST
        
        if sys.argv[1] == "local":
            HOST = "localhost"
            logger.info("Using localhost configuration")
        elif sys.argv[1] == "remote":
            HOST = "0.0.0.0"  # Listen on all interfaces
            logger.info("Using remote configuration")
    
    # Additional configuration logging
    logger.info(f"Starting backend server on {HOST}:{PORT} (Debug: {DEBUG})")
    logger.info(f"Environment: {ENV}")
    logger.info(f"Log file: {LOG_FILE}")
    
    # Start the Flask server
    app.run(host=HOST, port=PORT, debug=DEBUG)

if __name__ == "__main__":
    main()
