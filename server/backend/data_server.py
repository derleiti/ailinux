"""
AILinux Data Collection Server

This server application collects and stores data sent from AILinux clients.
It provides a REST API for data upload and a WebSocket server for real-time updates.
"""
import os
# Potential unused import: import sys
import json
import uuid
import time
import logging
import sqlite3
# Potential unused import: import threading
# Potential unused import: import functools
from datetime import datetime
from typing import Dict, List, Union, Optional, Any

# Web server components
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
# Potential unused import: import websockets
# Potential unused import: import asyncio

# Load environment variables if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("data_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DataServer")

# Server configuration
HOST = os.getenv("SERVER_HOST", "0.0.0.0")
HTTP_PORT = int(os.getenv("SERVER_HTTP_PORT", 8081))
WS_PORT = int(os.getenv("SERVER_WS_PORT", 8082))
DATA_DIR = os.getenv("DATA_DIR", "./collected_data")
DB_PATH = os.getenv("DB_PATH", os.path.join(DATA_DIR, "ailinux_data.db"))

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global state
connected_clients = set()
ws_server = None


class DataStorage:
    """Class to handle data storage operations."""
    
    def __init__(self, db_path: str):
        """Initialize the data storage.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """Initialize the database schema if it doesn't exist."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Create logs table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT
            )
            ''')
            
            # Create analysis results table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                log_id TEXT,
                model TEXT NOT NULL,
                analysis TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (log_id) REFERENCES logs(id)
            )
            ''')
            
            # Create general data table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS collected_data (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                data_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT
            )
            ''')
            
            # Create index for faster querying
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_timestamp ON analysis_results(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_data_timestamp ON collected_data(timestamp)')
            
            conn.commit()
            logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
        finally:
            conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection.
        
        Returns:
            SQLite connection object
        """
        return sqlite3.connect(self.db_path)
    
    def store_log(self, source: str, level: str, message: str, 
                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a log entry in the database.
        
        Args:
            source: Source of the log (client ID, component name, etc.)
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: Log message content
            metadata: Additional metadata for the log
            
        Returns:
            ID of the inserted log entry
        """
        log_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO logs (id, timestamp, source, level, message, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (log_id, timestamp, source, level, message, json.dumps(metadata) if metadata else None)
            )
            conn.commit()
            logger.debug(f"Stored log with ID {log_id}")
            return log_id
        except sqlite3.Error as e:
            logger.error(f"Error storing log: {e}")
            raise
        finally:
            conn.close()
    
    def store_analysis(self, model: str, analysis: str, log_id: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store an analysis result in the database.
        
        Args:
            model: Name of the AI model used
            analysis: Analysis content
            log_id: ID of the associated log entry (if any)
            metadata: Additional metadata for the analysis
            
        Returns:
            ID of the inserted analysis entry
        """
        analysis_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO analysis_results (id, timestamp, log_id, model, analysis, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (analysis_id, timestamp, log_id, model, analysis, json.dumps(metadata) if metadata else None)
            )
            conn.commit()
            logger.debug(f"Stored analysis with ID {analysis_id}")
            return analysis_id
        except sqlite3.Error as e:
            logger.error(f"Error storing analysis: {e}")
            raise
        finally:
            conn.close()
    
    def store_data(self, data_type: str, content: str, 
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store generic data in the database.
        
        Args:
            data_type: Type of data being stored
            content: Data content
            metadata: Additional metadata for the data
            
        Returns:
            ID of the inserted data entry
        """
        data_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO collected_data (id, timestamp, data_type, content, metadata) VALUES (?, ?, ?, ?, ?)",
                (data_id, timestamp, data_type, content, json.dumps(metadata) if metadata else None)
            )
            conn.commit()
            logger.debug(f"Stored data with ID {data_id} and type {data_type}")
            return data_id
        except sqlite3.Error as e:
            logger.error(f"Error storing data: {e}")
            raise
        finally:
            conn.close()
    
    def get_logs(self, limit: int = 100, offset: int = 0, 
                level: Optional[str] = None, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve logs from the database.
        
        Args:
            limit: Maximum number of logs to retrieve
            offset: Number of logs to skip
            level: Filter logs by level
            source: Filter logs by source
            
        Returns:
            List of log entries
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            query = "SELECT id, timestamp, source, level, message, metadata FROM logs"
            params = []
            
            # Add filters
            filters = []
                        except Exception as e:
                        except Exception as e:
                            pass  # Added by pylint fixer
                pass  # Added by pylint fixer
