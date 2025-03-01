"""AI Model Integration for AILinux.

This module provides interfaces to various AI models for log analysis,
supporting both local models (GPT4All) and cloud-based APIs (OpenAI, Google Gemini).
"""
import os
import logging
import json
from dotenv import load_dotenv
from typing import Dict, Any, Optional, Union

# Configure logging
logger = logging.getLogger("AIModel")

# Load environment variables
load_dotenv()

# Get API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", "Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# Global model instances
_gpt4all_model = None
_openai = None
_gemini = None

def initialize_gpt4all():
    """Initialize the GPT4All model for offline processing.
    
    Returns:
        GPT4All model instance or None if initialization fails
    """
    global _gpt4all_model
    if _gpt4all_model is not None:
        return _gpt4all_model
    
    try:
        from gpt4all import GPT4All
        logger.info(f"Loading GPT4All model from: {LLAMA_MODEL_PATH}")
        _gpt4all_model = GPT4All(LLAMA_MODEL_PATH)
        logger.info("GPT4All model loaded successfully")
        return _gpt4all_model
    except Exception as e:
        logger.error(f"Error initializing GPT4All: {str(e)}")
        return None

def initialize_openai():
    """Initialize the OpenAI API client.
    
    Returns:
        OpenAI client object or None if initialization fails
    """
    global _openai
    if _openai is not None:
        return _openai
    
    if not OPENAI_API_KEY:
        logger.warning("No OpenAI API key found in environment")
        return None
    
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        _openai = openai
        logger.info("OpenAI API initialized successfully")
        return _openai
    except Exception as e:
        logger.error(f"Error initializing OpenAI API: {str(e)}")
        return None

def initialize_gemini():
    """Initialize the Google Gemini API client.
    
    Returns:
        Gemini client object or None if initialization fails
    """
    global _gemini
    if _gemini is not None:
        return _gemini
    
    if not GEMINI_API_KEY:
        logger.warning("No Gemini API key found in environment")
        return None
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini = genai
        logger.info("Google Gemini API initialized successfully")
        return _gemini
    except Exception as e:
        logger.error(f"Error initializing Gemini API: {str(e)}")
        return None

def get_model(model_name: str):
    """Get the requested AI model.
    
    Args:
        model_name: Name of the model to use ('gpt4all', 'openai', 'gemini')
        
    Returns:
        Model instance or None if initialization fails
        
    Raises:
        ValueError: If an unknown model name is provided
    """
    if model_name == "gpt4all":
        return initialize_gpt4all()
    elif model_name == "openai":
        return initialize_openai()
    elif model_name == "gemini":
        return initialize_gemini()
    else:
        raise ValueError(f"Unknown model: {model_name}")

def analyze_log(log_text: str, model_name: str = "gpt4all") -> str:
    """Analyze log text using the specified AI model.
    
    Args:
        log_text: The log text to analyze
        model_name: Name of the model to use for analysis
        
    Returns:
        Analysis result as a string
    """
    logger.info(f"Analyzing log with model: {model_name}")
    
    # Create prompt template based on log analysis task
    prompt = f"""Analyze the following log and provide insights:
1. Summarize what the log is showing
2. Identify any errors or warnings
3. Suggest potential solutions if problems are found

LOG:
{log_text}

ANALYSIS:
"""

    try:
        if model_name == "gpt4all":
            return gpt4all_response(prompt)
        elif model_name == "openai":
            return openai_response(prompt)
        elif model_name == "gemini":
            return gemini_response(prompt)
        else:
            return f"⚠ Error: Unknown model '{model_name}' specified"
    except Exception as e:
        logger.exception(f"Error analyzing log with {model_name}: {str(e)}")
        return f"⚠ Error analyzing log: {str(e)}"

def gpt4all_response(prompt: str) -> str:
    """Get a response from the GPT4All model.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        Model response as a string
    """
    model = initialize_gpt4all()
    if not model:
        return "⚠ Error: GPT4All model could not be initialized"
    
    try:
        logger.debug(f"Sending prompt to GPT4All (length: {len(prompt)})")
        response = ""
        
        # Use with context for proper resource handling
        with model.chat_session():
            # Stream response tokens for better performance monitoring
            for token in model.generate(prompt, max_tokens=2048, temp=0.7):
                response += token
                
        logger.debug(f"Received GPT4All response (length: {len(response)})")
        return response.strip()
    except Exception as e:
        logger.exception(f"Error with GPT4All: {str(e)}")
        return f"⚠ Error with GPT4All: {str(e)}"

def openai_response(prompt: str) -> str:
    """Get a response from the OpenAI API.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        Model response as a string
    """
    openai = initialize_openai()
    if not openai:
        return "⚠ Error: OpenAI API could not be initialized. Check your API key."
    
    try:
        logger.debug(f"Sending prompt to OpenAI (length: {len(prompt)})")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a log analysis expert. Provide clear, concise analysis of log files."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.5
        )
        
        response_text = response["choices"][0]["message"]["content"].strip()
        logger.debug(f"Received OpenAI response (length: {len(response_text)})")
        return response_text
    except Exception as e:
        logger.exception(f"Error with OpenAI: {str(e)}")
        return f"⚠ Error with OpenAI: {str(e)}"

def gemini_response(prompt: str) -> str:
    """Get a response from the Google Gemini API.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        Model response as a string
    """
    gemini = initialize_gemini()
    if not gemini:
        return "⚠ Error: Gemini API could not be initialized. Check your API key."
    
    try:
        logger.debug(f"Sending prompt to Gemini (length: {len(prompt)})")
        model = gemini.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        response_text = response.text
        logger.debug(f"Received Gemini response (length: {len(response_text)})")
        return response_text.strip()
    except Exception as e:
        logger.exception(f"Error with Gemini: {str(e)}")
        return f"⚠ Error with Gemini: {str(e)}"
