"""
GPT4All System Log Analyzer

This module provides functionality to collect system logs and analyze them
using the local GPT4All model. It helps identify issues and provides solutions.
"""
import os
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import re
import glob
import traceback

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("gpt4all_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GPT4AllAnalyzer")

# Try to import GPT4All
try:
    from gpt4all import GPT4All
    HAS_GPT4ALL = True
except ImportError:
    logger.warning("GPT4All not installed. Install with: pip install gpt4all")
    HAS_GPT4ALL = False

# Constants
DEFAULT_MODEL_PATH = "Meta-Llama-3-8B-Instruct.Q4_0.ggu"  # Default model
LOG_DIRECTORIES = [
    "./logs",
    "./client/logs",
    "./backend/logs"
]
MAX_LOG_SIZE = 8000  # Maximum log size to analyze (in characters)


class GPT4AllLogAnalyzer:
    """Class to analyze system logs using GPT4All."""

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the log analyzer.
        
        Args:
            model_path: Path to the GPT4All model
        """
        self.model_path = model_path or os.getenv("LLAMA_MODEL_PATH", DEFAULT_MODEL_PATH)
        self.model = None
        self.initialized = False
        
        # Try to initialize model
        self._initialize_model()

    def _initialize_model(self) -> bool:
        """
        Initialize the GPT4All model.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not HAS_GPT4ALL:
            logger.error("GPT4All not installed. Cannot initialize model.")
            return False
            
        try:
            logger.info(f"Initializing GPT4All model: {self.model_path}")
            start_time = time.time()
            
            # Initialize model
            self.model = GPT4All(self.model_path)
            
            # Log initialization time
            elapsed_time = time.time() - start_time
            logger.info(f"Model initialized in {elapsed_time:.2f} seconds")
            
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize GPT4All model: {str(e)}")
            logger.debug(traceback.format_exc())
            return False

    def collect_logs(self, max_age_hours: int = 24) -> Dict[str, str]:
        """
        Collect logs from various sources.
        
        Args:
            max_age_hours: Maximum age of logs to collect (in hours)
            
        Returns:
            Dict[str, str]: Dictionary mapping log sources to log content
        """
        logs = {}
        current_time = datetime.now()
        
        try:
            # Collect log files
            for log_dir in LOG_DIRECTORIES:
                if os.path.exists(log_dir):
                    for log_file in glob.glob(os.path.join(log_dir, "*.log")):
                        try:
                            # Check file modification time
                            file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                            age_hours = (current_time - file_mtime).total_seconds() / 3600
                            
                            if age_hours <= max_age_hours:
                                with open(log_file, 'r', encoding='utf-8') as f:
                                    log_content = f.read()
                                    
                                    # Add log file content
                                    logs[os.path.basename(log_file)] = log_content
                                    logger.info(f"Collected log from {log_file} ({len(log_content)} bytes)")
                        except Exception as e:
                            logger.warning(f"Error reading log file {log_file}: {str(e)}")
            
            # If no logs found, check some standard system log locations
            if not logs:
                system_logs = [
                    "/var/log/syslog",
                    "/var/log/messages",
                    "/var/log/kern.log"
                ]
                
                for sys_log in system_logs:
                    if os.path.exists(sys_log):
                        try:
                            # Get last 100 lines
                            with open(sys_log, 'r', encoding='utf-8', errors='replace') as f:
                                lines = f.readlines()[-100:]
                                logs[os.path.basename(sys_log)] = ''.join(lines)
                                logger.info(f"Collected system log from {sys_log} (last 100 lines)")
                        except Exception as e:
                            logger.warning(f"Error reading system log {sys_log}: {str(e)}")
            
            return logs
        except Exception as e:
            logger.error(f"Error collecting logs: {str(e)}")
            logger.debug(traceback.format_exc())
            return {}

    def analyze_log(self, log_text: str, custom_prompt: Optional[str] = None) -> str:
        """
        Analyze log text using GPT4All.
        
        Args:
            log_text: Log text to analyze
            custom_prompt: Custom prompt instructions
            
        Returns:
            str: Analysis results
        """
        if not self.initialized:
            if not self._initialize_model():
                return "Error: GPT4All model not initialized"
        
        # Truncate log if too large
        if len(log_text) > MAX_LOG_SIZE:
            log_text = log_text[:MAX_LOG_SIZE] + "\n[... truncated due to length]"
        
        # Create the analysis prompt
        system_prompt = custom_prompt or """
You are an AI assistant specialized in analyzing system logs. Your task is to analyze the provided log and:
1. Provide a summary of the main events and status
2. Identify any errors, warnings, or issues
3. Explain potential causes for identified problems
4. Suggest troubleshooting steps or solutions
5. Prioritize the issues by severity (Critical, High, Medium, Low)

Respond in a clear, concise manner with separate sections for each part of your analysis.
"""

        prompt = f"{system_prompt}\n\nLOG:\n{log_text}\n\nANALYSIS:"
        
        try:
            # Use model for analysis
            logger.info("Analyzing log with GPT4All...")
            start_time = time.time()
            
            # Use chat completion API
            response = self.model.chat_completion([
                {"role": "system", "content": "You are a helpful AI assistant specializing in system log analysis."},
                {"role": "user", "content": prompt}
            ])
            
            # Log analysis time
            elapsed_time = time.time() - start_time
            logger.info(f"Log analyzed in {elapsed_time:.2f} seconds")
            
            # Return analysis
            analysis = response['choices'][0]['message']['content']
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing log with GPT4All: {str(e)}")
            logger.debug(traceback.format_exc())
            return f"Error analyzing log: {str(e)}"

    def analyze_system_logs(self, max_age_hours: int = 24) -> Dict[str, str]:
        """
        Analyze all system logs.
        
        Args:
            max_age_hours: Maximum age of logs to analyze (in hours)
            
        Returns:
            Dict[str, str]: Dictionary mapping log sources to analysis results
        """
        results = {}
        
        # Collect logs
        logs = self.collect_logs(max_age_hours)
        
        if not logs:
            return {"error": "No logs found or could not collect logs"}
        
        # Analyze each log
        for log_source, log_content in logs.items():
            logger.info(f"Analyzing log: {log_source}")
            
            # Skip empty logs
            if not log_content.strip():
                results[log_source] = "Log file is empty"
                continue
                
            # Analyze log
            analysis = self.analyze_log(log_content)
            results[log_source] = analysis
        
        return results

    def save_analysis(self, analysis_results: Dict[str, str], output_file: str = "log_analysis.json") -> bool:
        """
        Save analysis results to file.
        
        Args:
            analysis_results: Analysis results to save
            output_file: Output file path
            
        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            # Create output with metadata
            output = {
                "timestamp": datetime.now().isoformat(),
                "model": self.model_path,
                "analysis": analysis_results
            }
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2)
                
            logger.info(f"Analysis results saved to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving analysis results: {str(e)}")
            return False


def main():
    """Main function for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GPT4All System Log Analyzer")
    parser.add_argument("--model", type=str, help="Path to GPT4All model")
    parser.add_argument("--log", type=str, help="Log file to analyze")
    parser.add_argument("--output", type=str, default="log_analysis.json", 
                       help="Output file for analysis results")
    parser.add_argument("--hours", type=int, default=24, 
                       help="Maximum age of logs to analyze (in hours)")
    parser.add_argument("--all", action="store_true", 
                       help="Analyze all system logs")
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = GPT4AllLogAnalyzer(model_path=args.model)
    
    if args.log:
        # Analyze specific log file
        try:
            with open(args.log, 'r', encoding='utf-8') as f:
                log_content = f.read()
                
            analysis = analyzer.analyze_log(log_content)
            print(analysis)
            
            # Save analysis
            analyzer.save_analysis({os.path.basename(args.log): analysis}, args.output)
        except Exception as e:
            logger.error(f"Error analyzing log file {args.log}: {str(e)}")
    elif args.all:
        # Analyze all system logs
        results = analyzer.analyze_system_logs(max_age_hours=args.hours)
        
        # Print summary
        print(f"Analyzed {len(results)} log files")
        for log_source in results.keys():
            print(f"- {log_source}")
            
        # Save analysis
        analyzer.save_analysis(results, args.output)
        print(f"Analysis saved to {args.output}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
