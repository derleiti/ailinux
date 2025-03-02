"""AILinux Backend Server for log analysis using AI models.

This module provides a Flask-based API that processes log files using 
various AI models and returns analysis results.
"""
# Import path fixer to ensure all modules can be loaded correctly
import os
import sys

# Add path fixer module path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Use path fixer to set up import paths
try:
    sys.path.insert(0, current_dir)  # Add current directory to path
    from path_fixer import fix_import_paths, import_backend_module
    fix_import_paths()
except ImportError:
    # Path fixer not available, create minimal version
    def fix_import_paths():
        """Add common AILinux directories to sys.path."""
        # Try to find the client directory
        paths_to_check = [
            os.path.join(current_dir, '..'),  # Parent directory
            os.path.join(current_dir, '..', '..'),  # Grandparent directory
            os.path.dirname(current_dir),  # Alternative parent
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                if path not in sys.path:
                    sys.path.insert(0, path)
                # Also add backend directory if it exists
                backend_dir = os.path.join(path, 'backend')
                if os.path.exists(backend_dir) and backend_dir not in sys.path:
                    sys.path.insert(0, backend_dir)
        
    def import_backend_module(name):
        """Try to import a module with different path prefixes."""
        try:
            return __import__(name)
        except ImportError:
            try:
                return __import__(f"backend.{name}", fromlist=[name])
            except ImportError:
                try:
                    return __import__(f"client.backend.{name}", fromlist=[name])
                except ImportError:
                    return None
    
    # Run the minimal path fixer
    fix_import_paths()

# Now continue with normal imports
import logging
import json
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import psutil

# Import AI model functions - use import_backend_module for flexibility
try:
    ai_model = import_backend_module('ai_model')
    if ai_model:
        analyze_log = ai_model.analyze_log
        get_available_models = ai_model.get_available_models
    else:
        raise ImportError("Failed to import ai_model module")
except ImportError:
    logging.error("Failed to import AI model module. Make sure ai_model.py is in the same directory.")
    
    # Define fallback functions
    def analyze_log(log_text, model_name="fallback", instruction=None):
        return "Error: AI model module could not be loaded. Please check the installation."
    
    def get_available_models():
        return [{"name": "fallback", "available": True, "error": "AI model module not available"}]
