"""GPT4All Integration Module for AILinux.

This module provides comprehensive integration with GPT4All models,
enabling local inference without API dependencies.
"""
import os
import logging
import time
# Potential unused import: import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("gpt4all_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GPT4All")

# Model settings
DEFAULT_MODEL_PATH = os.getenv("GPT4ALL_MODEL_PATH", "Meta-Llama-3-8B-Instruct.Q4_0.ggu")
MODELS_DIR = os.getenv("GPT4ALL_MODELS_DIR", os.path.join(os.path.dirname(__file__), "models"))

# Ensure models directory exists
os.makedirs(MODELS_DIR, exist_ok=True)

# Cache for loaded models
_model_cache = {}
_model_lock = threading.RLock()

class ModelNotFoundError(Exception):
    """Exception raised when a specified model cannot be found."""
    pass

def list_available_models() -> List[Dict[str, Any]]:
    """List all available GPT4All models in the models directory.
    
    Returns:
        List of dictionaries containing model information
    """
    result = []
    
    try:
        # List .gguf and .bin files in the models directory
        model_files = list(Path(MODELS_DIR).glob("*.ggu")) + list(Path(MODELS_DIR).glob("*.bin"))
        
        for model_path in model_files:
            model_info = {
                "name": model_path.stem,
                "path": str(model_path),
                "size_mb": round(model_path.stat().st_size / (1024 * 1024), 2),
                "last_modified": time.ctime(model_path.stat().st_mtime)
            }
            result.append(model_info)
            
        return result
    
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return []

def get_model(model_name_or_path: Optional[str] = None) -> Any:
    """Get a GPT4All model instance, loading it if necessary.
    
    Args:
        model_name_or_path: Model name or path (defaults to DEFAULT_MODEL_PATH)
        
    Returns:
        GPT4All model instance
        
    Raises:
        ModelNotFoundError: If the model cannot be found
        ImportError: If gpt4all package is not installed
    """
    # Use default model if not specified
    model_path = model_name_or_path or DEFAULT_MODEL_PATH
    
    # Check if it's a name without path and construct full path
    if not os.path.isabs(model_path) and not model_path.startswith("./"):
        # Check if it's in the models directory
        full_path = os.path.join(MODELS_DIR, model_path)
        if os.path.exists(full_path):
            model_path = full_path
        else:
            # Try adding .gguf extension if it doesn't have one
            if not model_path.endswith(('.ggu', '.bin')):
                test_path = os.path.join(MODELS_DIR, f"{model_path}.ggu")
                if os.path.exists(test_path):
                    model_path = test_path
    
    # Return cached model if available
    with _model_lock:
        if model_path in _model_cache:
            logger.debug(f"Using cached model: {model_path}")
            return _model_cache[model_path]
    
    # Check if the model file exists
    if not os.path.exists(model_path):
        raise ModelNotFoundError(f"Model not found at path: {model_path}")
    
    try:
        # Import gpt4all here to avoid dependency issues
        from gpt4all import GPT4All
        
        logger.info(f"Loading GPT4All model from: {model_path}")
        start_time = time.time()
        
        # Initialize the model
        model = GPT4All(model_path)
        
        # Cache the model
        with _model_lock:
            _model_cache[model_path] = model
        
        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f}s")
        
        return model
    
    except ImportError:
        logger.error("The gpt4all package is not installed. Please install it with: pip install gpt4all")
        raise ImportError("GPT4All package not installed")
    
    except Exception as e:
        logger.error(f"Error loading model {model_path}: {str(e)}")
        raise

def analyze_log(log_text: str, model_name_or_path: Optional[str] = None) -> str:
    """Analyze a log using GPT4All.
    
    Args:
        log_text: The log text to analyze
        model_name_or_path: Model name or path (defaults to DEFAULT_MODEL_PATH)
        
    Returns:
        Analysis result as string
    """
    try:
        # Load the model
        model = get_model(model_name_or_path)
        
        # Prepare the system message
        system_message = """You are an AI assistant specialized in analyzing logs and providing insights.
Given a log snippet, your task is to:
1. Summarize the key information in the log
2. Identify any errors, warnings, or issues
3. Explain potential causes for the identified problems
4. Suggest troubleshooting steps or solutions

Be concise and precise in your analysis."""

        # Prepare the conversation
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Please analyze this log:\n\n{log_text}"}
        ]
        
        # Generate the response
        logger.info(f"Analyzing log with model: {model_name_or_path or DEFAULT_MODEL_PATH}")
        start_time = time.time()
        
        response = model.chat_completion(messages)
        
        process_time = time.time() - start_time
        logger.info(f"Analysis completed in {process_time:.2f}s")
        
        return response['choices'][0]['message']['content']
    
    except ModelNotFoundError as e:
        logger.error(f"Model not found: {str(e)}")
        return f"Error: {str(e)}"
    
    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        return f"Error: {str(e)}. Please install the gpt4all package."
    
    except Exception as e:
        logger.error(f"Error during log analysis: {str(e)}")
        return f"Error analyzing log: {str(e)}"

def check_installation() -> bool:
    """Verify that the GPT4All installation is working correctly.
    
    Returns:
        True if installation is OK, False otherwise
    """
    try:
        # Try to import gpt4all
        from gpt4all import GPT4All
        
        # Check if we have at least one model
        models = list_available_models()
        if not models:
            logger.warning("No GPT4All models found in the models directory")
            return False
        
        return True
    
    except ImportError:
        logger.error("GPT4All package is not installed")
        return False
    
    except Exception as e:
        logger.error(f"Error checking GPT4All installation: {str(e)}")
        return False

def interactive_chat(model_name_or_path: Optional[str] = None):
    """Run an interactive chat session with the model.
    
    Args:
        model_name_or_path: Model name or path (defaults to DEFAULT_MODEL_PATH)
    """
    try:
        # Load the model
        model = get_model(model_name_or_path)
        model_name = model_name_or_path or DEFAULT_MODEL_PATH
        
        print(f"Interactive chat with {model_name}")
        print("Type 'exit' or 'quit' to end the conversation.")
        print("=" * 50)
        
        # Initialize conversation with system message
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]
        
        while True:
            # Get user input
            user_input = input("\nYou: ")
            
            # Check for exit command
            if user_input.lower() in ['exit', 'quit']:
                print("Ending conversation.")
                break
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Generate response
            print("\nAI: ", end="", flush=True)
            
            response = model.chat_completion(messages)
            assistant_message = response['choices'][0]['message']['content']
            
            print(assistant_message)
            
            # Add assistant message to conversation history
            messages.append({"role": "assistant", "content": assistant_message})
    
    except Exception as e:
        print(f"Error in interactive chat: {str(e)}")

if __name__ == "__main__":
    # Test the module functionality
    if check_installation():
        print("GPT4All is properly installed.")
        models = list_available_models()
        print(f"Found {len(models)} model(s):")
        for model in models:
            print(f"- {model['name']} ({model['size_mb']} MB)")
        
        # Ask if user wants to start interactive chat
        choice = input("\nStart interactive chat? (y/n): ")
        if choice.lower() == 'y':
            interactive_chat()
    else:
        print("GPT4All installation check failed.")
