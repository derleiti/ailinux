#!/usr/bin/env python3
"""
AILinux Log Analysis CLI Script

This script provides command-line interface for log analysis 
using different AI models.
"""

import argparse
import sys
# Potential unused import: import json
import logging

# Add project root to Python path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AI models
from backend.ai_model # Potential unused import: import analyze_log

def main():
    """
    Main CLI entry point for log analysis
    """
    parser = argparse.ArgumentParser(description="AILinux Log Analysis Tool")
    parser.add_argument(
        '--model', 
        choices=['gpt4all', 'openai', 'gemini', 'huggingface'], 
        default='gpt4all', 
        help='AI model to use for log analysis'
    )
    parser.add_argument(
        '--log', 
        required=True, 
        help='Log text to analyze'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose logging'
    )

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)