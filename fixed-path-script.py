#!/usr/bin/env python3
"""Script to fix file paths and folder references in AILinux project.

This script scans the AILinux project files and ensures that all paths
and folder references are consistent with the expected directory structure.
"""
import os
import re
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("path_fix.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PathFixer")

# Base directory
BASE_DIR = "/home/zombie/ailinux"

# Folders that should be standardized
STANDARD_FOLDERS = {
    "backend": os.path.join(BASE_DIR, "backend"),
    "frontend": os.path.join(BASE_DIR, "frontend"),
    "client": os.path.join(BASE_DIR, "client"),
    "logs": os.path.join(BASE_DIR, "logs")
}

# File extensions to process
FILE_EXTENSIONS = ['.py', '.js', '.html', '.json', '.sh']

# Common path patterns to fix
PATH_PATTERNS = [
    (r'\.\/backend\/', 'backend/'),
    (r'\.\/frontend\/', 'frontend/'),
    (r'\.\/client\/', 'client/'),
    (r'\.\/logs\/', 'logs/'),
    (r'/home/zombie/ailinux/backend', os.path.join(BASE_DIR, 'backend')),
    (r'/home/zombie/ailinux/frontend', os.path.join(BASE_DIR, 'frontend')),
    (r'/home/zombie/ailinux/client', os.path.join(BASE_DIR, 'client')),
    (r'/home/zombie/ailinux/logs', os.path.join(BASE_DIR, 'logs')),
    (r'/home/zombie/ailinux', BASE_DIR),
]

def fix_file_paths(file_path):
    """Fix paths in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # Apply all path patterns
        for pattern, replacement in PATH_PATTERNS:
            updated_content = re.sub(pattern, replacement, content)
            if updated_content != content:
                content = updated_content
                modified = True

        # Check for changes and write back if needed
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Fixed paths in {file_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return False

def scan_directory(directory):
    """Scan a directory recursively and fix paths in all matching files."""
    fixed_count = 0
    for root, dirs, files in os.walk(directory):
        # Skip node_modules and other large metadata directories
        if any(excluded in root for excluded in ["node_modules", "__pycache__", ".git"]):
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                if fix_file_paths(file_path):
                    fixed_count += 1
    
    return fixed_count

def create_structure_file():
    """Create a structure.txt file with the project directory structure."""
    try:
        structure_file_path = os.path.join(BASE_DIR, "structure.txt")
        
        # Create structure content
        structure_content = """AILinux Project Structure
========================

Base directory: /home/zombie/ailinux

This document provides an overview of the AILinux project structure and describes
the purpose of key files and directories.

1. Directory Structure
---------------------

/home/zombie/ailinux/
├── backend/                  # Server-side AI processing and API
│   ├── ai_model.py           # AI model integration (GPT4All, OpenAI, etc.)
│   ├── app.py                # Flask REST API server
│   ├── backend.js            # Express-based backend server
│   ├── backend.log           # Backend server logs
│   ├── gpt4all/              # GPT4All specific implementations
│   │   └── app.py            # GPT4All command line interface
│   ├── gpt4allinit.py        # GPT4All initialization script
│   ├── hugging.py            # Hugging Face model exploration utility
│   ├── huggingface.py        # Hugging Face model integration
│   ├── package-lock.json     # Node.js dependencies lock file
│   ├── requirements.txt      # Python dependencies
│   └── websocketserv.py      # WebSocket server for real-time communication
├── frontend/                 # User interface components
│   ├── aiineraction.html     # AI interaction web interface
│   ├── config.js             # Configuration management 
│   ├── config.py             # Python configuration loader
│   ├── frontend.log          # Frontend application logs
│   ├── gemini-api-setup.js   # Google Gemini API setup
│   ├── importexport.js       # Settings import/export utility
│   ├── index.html            # Main application HTML interface
│   ├── llama.html            # LLaMA model interface
│   ├── log.html              # Log viewer interface
│   ├── logmanager.js         # Log management utility
│   ├── main.js               # Electron main process
│   ├── package.json          # Frontend dependencies
│   ├── preload.js            # Electron preload script
│   ├── requirements.txt      # Frontend Python dependencies
│   ├── settings.html         # Settings management interface
│   └── twitchbot.py          # Twitch integration bot
├── client/                   # Client utilities and scripts
│   ├── adjust_hierarchy_with_debugger.py  # Directory structure fix utility
│   ├── alphaos.py            # WebSocket client implementation
│   ├── analyze.py            # Code analysis utility
│   ├── bigfiles.py           # Large file finder (Python)
│   ├── bigfiles.sh           # Large file finder (Shell)
│   ├── cleanup.py            # Code cleanup utility
│   ├── file-sync-client.py   # File synchronization with server
│   ├── package.json          # Client-side dependencies
│   ├── postcode.sh           # Code analysis and reporting script
│   ├── postlog.sh            # Log collection script
│   ├── requirements.txt      # Client Python dependencies
│   ├── start.js              # Application starter script
│   ├── start.sh              # Startup shell script
│   ├── uploadready.py        # GitHub upload preparation utility
│   └── websocket_client.py   # WebSocket client for backend communication
├── logs/                     # Directory for log files
│   ├── backend.log           # Backend process logs
│   └── frontend.log          # Frontend process logs
├── .github/                  # GitHub configurations
│   └── workflows/            # GitHub Actions workflows
│       └── pylint.yml        # Pylint automated code quality checks
├── directory_structure.json  # Project directory structure in JSON format
├── hierarchy_analysis.log    # Directory structure analysis log
├── large_files.json          # Large files tracking data
├── LICENSE                   # Project license
├── optimization.log          # Code optimization log
├── README.md                 # Project documentation
├── requirements.txt          # Project-wide Python dependencies
├── SECURITY.md               # Security guidelines and policies
└── structure.txt             # This file - Project structure overview"""

        # Write structure content to file
        with open(structure_file_path, 'w') as f:
            f.write(structure_content)
        
        logger.info(f"Created structure file at {structure_file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create structure file: {e}")
        return False

def main():
    """Main function to fix paths and create structure file."""
    logger.info("Starting path fixing process...")
    
    # Change to the base directory
    try:
        os.chdir(BASE_DIR)
    except Exception as e:
        logger.error(f"Could not change to base directory {BASE_DIR}: {e}")
        logger.info(f"Current directory: {os.getcwd()}")
        return
    
    # Fix paths in all project files
    fixed_count = scan_directory(BASE_DIR)
    logger.info(f"Fixed paths in {fixed_count} files")
    
    # Create structure.txt file
    if create_structure_file():
        logger.info("Created structure.txt file successfully")
    
    logger.info("Path fixing process completed")

if __name__ == "__main__":
    main()
