"""AI Model Integration for AILinux.

This module provides interfaces to various AI models for log analysis,
supporting both local models (GPT4All, Hugging Face) and cloud-based APIs 
(OpenAI, Google Gemini).
"""
import os
import logging
import json
import time
from typing import Dict, Any, Optional, Union, List, Tuple

from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("AIModel")

# Load environment variables
load_dotenv()

# Get API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HF_API_KEY = os.getenv("HF_API_KEY", "")
LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", "Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# Default models for Hugging Face
DEFAULT_HF_MODEL = os.getenv("DEFAULT_HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
HF_MODELS_CACHE_DIR = os.getenv("HF_MODELS_CACHE_DIR", os.path.join(os.path.dirname(__file__), "models"))

# Global model instances
_gpt4all_model = None
_openai = None
_gemini = None
_hf_pipeline = None

# Status flags
_gpt4all_available = None
_openai_available = None
_gemini_available = None
_hf_available = None

# Log analysis system prompt - used across all models for consistency
LOG_ANALYSIS_SYSTEM_PROMPT = """
You are an AI assistant specialized in analyzing logs and providing insights. Given a log snippet, your task is to:
1. Summarize the key information in the log
2. Identify any errors, warnings, or issues
3. Explain potential causes for the identified problems
4. Suggest troubleshooting steps or solutions
5. Highlight any security concerns if present

Be concise, technical, and precise in your analysis. Use bullet points when appropriate for clarity.
"""


def get_available_models() -> List[str]:
    """Get list of available AI models.
    
    Returns:
        List of model names that are available to use
    """
    available = []
    
    # Check GPT4All
    if is_gpt4all_available():
        available.append("gpt4all")
    
    # Check OpenAI
    if is_openai_available():
        available.append("openai")
    
    # Check Gemini
    if is_gemini_available():
        available.append("gemini")
    
    # Check Hugging Face
    if is_huggingface_available():
        available.append("huggingface")
    
    return available


def is_gpt4all_available() -> bool:
    """Check if GPT4All model is available.
    
    Returns:
        True if model is available, False otherwise
    """
    global _gpt4all_available
    
    if _gpt4all_available is not None:
        return _gpt4all_available
    
    try:
        from gpt4all import GPT4All
        # Just check if import works, don't load the model yet
        _gpt4all_available = True
        logger.info("GPT4All is available")
        return True
    except ImportError:
        logger.warning("GPT4All module is not installed")
        _gpt4all_available = False
        return False
    except Exception as e:
        logger.error(f"Error checking GPT4All availability: {str(e)}")
        _gpt4all_available = False
        return False


def is_openai_available() -> bool:
    """Check if OpenAI API is available.
    
    Returns:
        True if API is available, False otherwise
    """
    global _openai_available
    
    if _openai_available is not None:
        return _openai_available
    
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API key not found")
        _openai_available = False
        return False
    
    try:
        import openai
        # Test API key validity with a minimal request
        openai.api_key = OPENAI_API_KEY
        # Just check if import works, don't make API call yet
        _openai_available = True
        logger.info("OpenAI API is available")
        return True
    except ImportError:
        logger.warning("OpenAI module is not installed")
        _openai_available = False
        return False
    except Exception as e:
        logger.error(f"Error checking OpenAI API availability: {str(e)}")
        _openai_available = False
        return False


def is_gemini_available() -> bool:
    """Check if Google Gemini API is available.
    
    Returns:
        True if API is available, False otherwise
    """
    global _gemini_available
    
    if _gemini_available is not None:
        return _gemini_available
    
    if not GEMINI_API_KEY:
        logger.warning("Gemini API key not found")
        _gemini_available = False
        return False
    
    try:
        import google.generativeai as genai
        # Just check if import works, don't make API call yet
        _gemini_available = True
        logger.info("Google Gemini API is available")
        return True
    except ImportError:
        logger.warning("Google Generative AI module is not installed")
        _gemini_available = False
        return False
    except Exception as e:
        logger.error(f"Error checking Gemini API availability: {str(e)}")
        _gemini_available = False
        return False


def is_huggingface_available() -> bool:
    """Check if Hugging Face models are available.
    
    Returns:
        True if models are available, False otherwise
    """
    global _hf_available
    
    if _hf_available is not None:
        return _hf_available
    
    try:
        import torch
        from transformers import pipeline
        
        # Check for GPU availability for better performance indication
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            logger.info("CUDA is available for Hugging Face models")
        else:
            logger.info("CUDA is not available, Hugging Face models will use CPU only")
        
        _hf_available = True
        logger.info("Hugging Face pipeline is available")
        return True
    except ImportError:
        logger.warning("Hugging Face transformers module is not installed")
        _hf_available = False
        return False
    except Exception as e:
        logger.error(f"Error checking Hugging Face availability: {str(e)}")
        _hf_available = False
        return False


def initialize_gpt4all():
    """Initialize the GPT4All model for offline processing.
    
    Returns:
        GPT4All model instance or None if initialization fails
    """
    global _gpt4all_model
    
    # Return existing model if already loaded
    if _gpt4all_model is not None:
        return _gpt4all_model
    
    # Check if GPT4All is available
    if not is_gpt4all_available():
        return None
    
    try:
        from gpt4all import GPT4All
        
        # Check if model file exists
        if not os.path.exists(LLAMA_MODEL_PATH):
            model_dir = os.path.dirname(LLAMA_MODEL_PATH)
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)
            logger.warning(f"Model file not found at {LLAMA_MODEL_PATH}")
            logger.info(f"Please download the model file to {LLAMA_MODEL_PATH}")
            return None
        
        logger.info(f"Loading GPT4All model from: {LLAMA_MODEL_PATH}")
        start_time = time.time()
        _gpt4all_model = GPT4All(LLAMA_MODEL_PATH)
        load_time = time.time() - start_time
        logger.info(f"GPT4All model loaded successfully in {load_time:.2f}s")
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
    
    # Return existing client if already initialized
    if _openai is not None:
        return _openai
    
    # Check if OpenAI is available
    if not is_openai_available():
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
    
    # Return existing client if already initialized
    if _gemini is not None:
        return _gemini
    
    # Check if Gemini is available
    if not is_gemini_available():
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


def initialize_huggingface(model_name: Optional[str] = None):
    """Initialize Hugging Face pipeline for text generation.
    
    Args:
        model_name: Name of the Hugging Face model to use. Defaults to environment variable.
    
    Returns:
        Hugging Face pipeline instance or None if initialization fails
    """
    global _hf_pipeline
    
    # Return existing pipeline if already initialized
    if _hf_pipeline is not None:
        return _hf_pipeline
    
    # Check if Hugging Face is available
    if not is_huggingface_available():
        return None
    
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        import torch
        
        # Use specified model or default from environment
        model_name = model_name or DEFAULT_HF_MODEL
        
        # Create cache directory if it doesn't exist
        os.makedirs(HF_MODELS_CACHE_DIR, exist_ok=True)
        
        logger.info(f"Loading Hugging Face model: {model_name}")
        start_time = time.time()
        
        # Configure quantization for lower memory usage
        if torch.cuda.is_available():
            # Use 4-bit quantization for GPU
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
            
            # Create pipeline with GPU acceleration
            _hf_pipeline = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=AutoTokenizer.from_pretrained(model_name),
                model_kwargs={"quantization_config": quantization_config},
                device_map="auto",
                cache_dir=HF_MODELS_CACHE_DIR,
                token=HF_API_KEY if HF_API_KEY else None
            )
        else:
            # For CPU, load the model with minimal settings
            _hf_pipeline = pipeline(
                "text-generation",
                model=model_name,
                cache_dir=HF_MODELS_CACHE_DIR,
                token=HF_API_KEY if HF_API_KEY else None
            )
        
        load_time = time.time() - start_time
        logger.info(f"Hugging Face model loaded successfully in {load_time:.2f}s")
        return _hf_pipeline
    except Exception as e:
        logger.error(f"Error initializing Hugging Face pipeline: {str(e)}")
        return None


def analyze_log(
    log_text: str, 
    model_name: str = "gpt4all",
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> str:
    """Analyze log text using the specified AI model.
    
    Args:
        log_text: The log text to analyze
        model_name: Name of the model to use for analysis
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature parameter for generation (0.0 to 1.0)
        
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
        # Route to appropriate model handler
        if model_name == "gpt4all":
            return gpt4all_response(prompt, max_tokens, temperature)
        elif model_name == "openai":
            return openai_response(prompt, max_tokens, temperature)
        elif model_name == "gemini":
            return gemini_response(prompt, max_tokens, temperature)
        elif model_name == "huggingface":
            return huggingface_response(prompt, max_tokens, temperature)
        else:
            return f"⚠ Error: Unknown model '{model_name}' specified"
    except Exception as e:
        logger.exception(f"Error analyzing log with {model_name}: {str(e)}")
        return f"⚠ Error analyzing log: {str(e)}"


def gpt4all_response(
    prompt: str, 
    max_tokens: int = 1024, 
    temperature: float = 0.7
) -> str:
    """Get a response from the GPT4All model.
    
    Args:
        prompt: The prompt to send to the model
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature parameter for generation (0.0 to 1.0)
        
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
            for token in model.generate(
                prompt, 
                max_tokens=max_tokens, 
                temp=temperature,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1
            ):
                response += token
                
        logger.debug(f"Received GPT4All response (length: {len(response)})")
        return response.strip()
    except Exception as e:
        logger.exception(f"Error with GPT4All: {str(e)}")
        return f"⚠ Error with GPT4All: {str(e)}"


def openai_response(
    prompt: str, 
    max_tokens: int = 1024, 
    temperature: float = 0.7
) -> str:
    """Get a response from the OpenAI API.
    
    Args:
        prompt: The prompt to send to the model
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature parameter for generation (0.0 to 1.0)
        
    Returns:
        Model response as a string
    """
    openai = initialize_openai()
    if not openai:
        return "⚠ Error: OpenAI API could not be initialized. Check your API key."
    
    try:
        logger.debug(f"Sending prompt to OpenAI (length: {len(prompt)})")
        
        # Create a client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Send request to ChatCompletion
        response = client.chat.completions.create(
            model="gpt-4",  # Can be changed to other models
            messages=[
                {"role": "system", "content": LOG_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        response_text = response.choices[0].message.content.strip()
        logger.debug(f"Received OpenAI response (length: {len(response_text)})")
        return response_text
    except Exception as e:
        logger.exception(f"Error with OpenAI: {str(e)}")
        return f"⚠ Error with OpenAI: {str(e)}"


def gemini_response(
    prompt: str, 
    max_tokens: int = 1024, 
    temperature: float = 0.7
) -> str:
    """Get a response from the Google Gemini API.
    
    Args:
        prompt: The prompt to send to the model
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature parameter for generation (0.0 to 1.0)
        
    Returns:
        Model response as a string
    """
    gemini = initialize_gemini()
    if not gemini:
        return "⚠ Error: Gemini API could not be initialized. Check your API key."
    
    try:
        logger.debug(f"Sending prompt to Gemini (length: {len(prompt)})")
        
        # Initialize with system prompt for better results
        full_prompt = f"{LOG_ANALYSIS_SYSTEM_PROMPT}\n\n{prompt}"
        
        # Create a model instance
        model = gemini.GenerativeModel('gemini-pro')
        
        # Generate content
        response = model.generate_content(
            full_prompt,
            generation_config=gemini.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
        )
        
        response_text = response.text
        logger.debug(f"Received Gemini response (length: {len(response_text)})")
        return response_text.strip()
    except Exception as e:
        logger.exception(f"Error with Gemini: {str(e)}")
        return f"⚠ Error with Gemini: {str(e)}"


def huggingface_response(
    prompt: str, 
    max_tokens: int = 1024, 
    temperature: float = 0.7
) -> str:
    """Get a response from a Hugging Face model.
    
    Args:
        prompt: The prompt to send to the model
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature parameter for generation (0.0 to 1.0)
        
    Returns:
        Model response as a string
    """
    hf_pipeline = initialize_huggingface()
    if not hf_pipeline:
        return "⚠ Error: Hugging Face model could not be initialized"
    
    try:
        logger.debug(f"Sending prompt to Hugging Face model (length: {len(prompt)})")
        
        # Initialize with system prompt for better results
        full_prompt = f"{LOG_ANALYSIS_SYSTEM_PROMPT}\n\n{prompt}"
        
        # Generate response
        response = hf_pipeline(
            full_prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.1,
            return_full_text=False  # Only return the generated response, not the input
        )
        
        # Extract text from response object
        response_text = response[0]['generated_text']
        logger.debug(f"Received Hugging Face response (length: {len(response_text)})")
        return response_text.strip()
    except Exception as e:
        logger.exception(f"Error with Hugging Face model: {str(e)}")
        return f"⚠ Error with Hugging Face model: {str(e)}"


def list_huggingface_models(category: str = None, keyword: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """List available models from Hugging Face Hub.
    
    Args:
        category: Filter by model category (e.g., "text-generation")
        keyword: Filter by keyword search
        limit: Maximum number of models to return
        
    Returns:
        List of model information dictionaries
    """
    if not HF_API_KEY:
        logger.warning("No Hugging Face API key provided for model listing")
    
    try:
        from huggingface_hub import HfApi
        
        api = HfApi(token=HF_API_KEY if HF_API_KEY else None)
        
        # Define filter criteria
        filter_dict = {}
        if category:
            filter_dict["task"] = category
        
        # Perform model search
        if keyword:
            models = api.list_models(search=keyword, filter=filter_dict if filter_dict else None, limit=limit)
        else:
            models = api.list_models(filter=filter_dict if filter_dict else None, limit=limit)
        
        # Format results for easier consumption
        results = []
        for model in models:
            results.append({
                "id": model.id,
                "downloads": getattr(model, "downloads", None),
                "likes": getattr(model, "likes", None),
                "tags": getattr(model, "tags", []),
                "pipeline_tag": getattr(model, "pipeline_tag", None)
            })
        
        return results
    except Exception as e:
        logger.error(f"Error listing Hugging Face models: {str(e)}")
        return []
