"""AI Model Integration for AILinux.

This module provides interfaces to various AI models for log analysis,
supporting both local models (GPT4All, Hugging Face) and cloud-based APIs (OpenAI, Google Gemini).
"""
import os
import logging
import json
import time
from typing import Dict, Any, Optional, Union, List
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("ai_model.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AIModel")

# Load environment variables
load_dotenv()

# Get API keys and model paths from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", "Meta-Llama-3-8B-Instruct.Q4_0.gguf")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt4all")

# Hugging Face model configuration
HUGGINGFACE_MODEL_ID = os.getenv("HUGGINGFACE_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")
CACHE_DIR = os.getenv("HUGGINGFACE_CACHE_DIR", "./models/huggingface")

# Global model instances
_gpt4all_model = None
_openai = None
_gemini = None
_huggingface_pipeline = None
_huggingface_tokenizer = None
_huggingface_model = None


class ModelNotInitializedError(Exception):
    """Exception raised when a model cannot be initialized."""
    pass


def initialize_gpt4all():
    """Initialize the GPT4All model for offline processing.
    
    Returns:
        GPT4All model instance or None if initialization fails
    """
    global _gpt4all_model
    if _gpt4all_model is not None:
        return _gpt4all_model

    try:
        # pylint: disable=C0415  # Import außerhalb des Toplevel
        from gpt4all import GPT4All

        # Check if model exists
        model_path = os.path.expanduser(LLAMA_MODEL_PATH)
        if not os.path.exists(model_path):
            model_dir = os.path.dirname(model_path)
            filename = os.path.basename(model_path)
            logger.warning(f"Model file not found at: {model_path}")
            logger.info(f"Checking if model exists in directory: {model_dir}")

            # Check if the directory exists, create if not
            if not os.path.exists(model_dir):
                os.makedirs(model_dir, exist_ok=True)
                logger.info(f"Created model directory: {model_dir}")

            # List available models if directory exists
            if os.path.exists(model_dir):
                files = os.listdir(model_dir)
                gguf_files = [f for f in files if f.endswith('.gguf')]
                if gguf_files:
                    # Use the first available .gguf file
                    model_path = os.path.join(model_dir, gguf_files[0])
                    logger.info(f"Using available model: {model_path}")
                else:
                    logger.warning("No .gguf models found. Will download the default model.")

            # Model will be downloaded automatically by GPT4All if not found

        logger.info(f"Loading GPT4All model from: {model_path}")
        _gpt4all_model = GPT4All(model_path)
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


def initialize_huggingface():
    """Initialize the Hugging Face model for inference.
    
    Returns:
        A tuple of (model, tokenizer, pipeline) or None if initialization fails
    """
    global _huggingface_model, _huggingface_tokenizer, _huggingface_pipeline

    if _huggingface_pipeline is not None:
        return _huggingface_model, _huggingface_tokenizer, _huggingface_pipeline

    try:
        # pylint: disable=C0415  # Import außerhalb des Toplevel
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        import torch

        # Create cache directory if it doesn't exist
        os.makedirs(CACHE_DIR, exist_ok=True)

        # Check for CUDA availability
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device} for Hugging Face model")

        # Load tokenizer first
        logger.info(f"Loading Hugging Face tokenizer: {HUGGINGFACE_MODEL_ID}")
        _huggingface_tokenizer = AutoTokenizer.from_pretrained(
            HUGGINGFACE_MODEL_ID,
            cache_dir=CACHE_DIR,
            token=HUGGINGFACE_API_KEY if HUGGINGFACE_API_KEY else None
        )

        # Load model with appropriate configuration
        logger.info(f"Loading Hugging Face model: {HUGGINGFACE_MODEL_ID}")
        _huggingface_model = AutoModelForCausalLM.from_pretrained(
            HUGGINGFACE_MODEL_ID,
            cache_dir=CACHE_DIR,
            token=HUGGINGFACE_API_KEY if HUGGINGFACE_API_KEY else None,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            low_cpu_mem_usage=True,
            device_map="auto" if device == "cuda" else None
        )

        # Create text generation pipeline
        logger.info("Creating Hugging Face pipeline")
        _huggingface_pipeline = pipeline(
            "text-generation",
            model=_huggingface_model,
            tokenizer=_huggingface_tokenizer,
            device=0 if device == "cuda" else -1
        )

        logger.info("Hugging Face model initialized successfully")
        return _huggingface_model, _huggingface_tokenizer, _huggingface_pipeline

    except Exception as e:
        logger.error(f"Error initializing Hugging Face model: {str(e)}")
        return None, None, None


def get_model(model_name: str):
    """Get the requested AI model.
    
    Args:
        model_name: Name of the model to use ('gpt4all', 'openai', 'gemini', 'huggingface')
        
    Returns:
        Model instance or None if initialization fails
        
    Raises:
        ValueError: If an unknown model name is provided
    """
    model_name = model_name.lower()

    if model_name == "gpt4all":
        return initialize_gpt4all()
    elif model_name == "openai":
        return initialize_openai()
    elif model_name == "gemini":
        return initialize_gemini()
    elif model_name == "huggingface":
        return initialize_huggingface()
    else:
        raise ValueError(f"Unknown model: {model_name}")


def create_prompt(log_text: str, instruction: Optional[str] = None) -> str:
    """Create a standardized prompt for log analysis.
    
    Args:
        log_text: The log text to analyze
        instruction: Optional specific instruction to override default
        
    Returns:
        Formatted prompt string
    """
    default_instruction = """Analyze the following log and provide insights:
1. Summarize what the log is showing
2. Identify any errors or warnings
3. Suggest potential solutions if problems are found
"""

    instruction = instruction or default_instruction

    return f"""{instruction}

LOG:
{log_text}

ANALYSIS:
"""


def analyze_log(log_text: str,

model_name: str = DEFAULT_MODEL,
instruction: Optional[str] = None) -> str:
    """Analyze log text using the specified AI model.
    
    Args:
        log_text: The log text to analyze
        model_name: Name of the model to use for analysis
        instruction: Optional specific instruction for the model
        
    Returns:
        Analysis result as a string
    """
    start_time = time.time()
    logger.info(f"Analyzing log with model: {model_name}")

    # Create the prompt
    prompt = create_prompt(log_text, instruction)

    try:
        if model_name == "gpt4all":
            response = gpt4all_response(prompt)
        elif model_name == "openai":
            response = openai_response(prompt)
        elif model_name == "gemini":
            response = gemini_response(prompt)
        elif model_name == "huggingface":
            response = huggingface_response(prompt)
        else:
            return f"⚠ Error: Unknown model '{model_name}' specified"
    except Exception as e:
        logger.exception(f"Error analyzing log with {model_name}: {str(e)}")
        return f"⚠ Error analyzing log: {str(e)}"

    elapsed_time = time.time() - start_time
    logger.info(f"Log analysis completed in {elapsed_time:.2f} seconds")

    return response


def gpt4all_response(prompt: str) -> str:
    """Get a response from the GPT4All model.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        Model response as a string
    """
    model = initialize_gpt4all()
    if not model:
        raise ModelNotInitializedError("GPT4All model could not be initialized")

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
        raise


def openai_response(prompt: str) -> str:
    """Get a response from the OpenAI API.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        Model response as a string
    """
    openai = initialize_openai()
    if not openai:
        raise ModelNotInitializedError("OpenAI API could not be initialized. Check your API key.")

    try:
        logger.debug(f"Sending prompt to OpenAI (length: {len(prompt)})")

        # Use the ChatCompletion API
        response = openai.ChatCompletion.create(
            model="gpt-4",

            messages=[
                {"role": "system", "content": "" +
                    "You are a log analysis expert. Provide clear, concise analysis of log files."},
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
        raise


def gemini_response(prompt: str) -> str:
    """Get a response from the Google Gemini API.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        Model response as a string
    """
    gemini = initialize_gemini()
    if not gemini:
        raise ModelNotInitializedError("Gemini API could not be initialized. Check your API key.")

    try:
        logger.debug(f"Sending prompt to Gemini (length: {len(prompt)})")
        model = gemini.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)

        response_text = response.text
        logger.debug(f"Received Gemini response (length: {len(response_text)})")
        return response_text.strip()
    except Exception as e:
        logger.exception(f"Error with Gemini: {str(e)}")
        raise


def huggingface_response(prompt: str) -> str:
    """Get a response from the Hugging Face model.
    
    Args:
        prompt: The prompt to send to the model
        
    Returns:
        Model response as a string
    """
    model, tokenizer, pipe = initialize_huggingface()
    if not pipe:
        raise ModelNotInitializedError("Hugging Face model could not be initialized.")

    try:
        logger.debug(f"Sending prompt to Hugging Face (length: {len(prompt)})")

        # Generate text with appropriate parameters
        outputs = pipe(
            prompt,
            max_new_tokens=1024,
            temperature=0.7,
            top_p=0.95,
            repetition_penalty=1.15,
            do_sample=True
        )

        # Extract the generated text
        generated_text = outputs[0]['generated_text']

        # Remove the prompt from the response
        response_text = generated_text[len(prompt):].strip()

        logger.debug(f"Received Hugging Face response (length: {len(response_text)})")
        return response_text
    except Exception as e:
        logger.exception(f"Error with Hugging Face: {str(e)}")
        raise


def get_available_models() -> List[Dict[str, Any]]:
    """Get information about available models.
    
    Returns:
        List of dictionaries with model information
    """
    models = []

    # Check GPT4All
    try:
        gpt4all = initialize_gpt4all()
        models.append({
            "name": "gpt4all",
            "available": gpt4all is not None,
            "type": "local",
            "file": LLAMA_MODEL_PATH
        })
    except Exception:
        models.append({
            "name": "gpt4all",
            "available": False,
            "type": "local",
            "error": "Failed to initialize"
        })

    # Check OpenAI
    models.append({
        "name": "openai",
        "available": OPENAI_API_KEY != "",
        "type": "api",
        "model": "gpt-4"
    })

    # Check Gemini
    models.append({
        "name": "gemini",
        "available": GEMINI_API_KEY != "",
        "type": "api",
        "model": "gemini-pro"
    })

    # Check Hugging Face
    try:
        _, _, pipe = initialize_huggingface()
        models.append({
            "name": "huggingface",
            "available": pipe is not None,
            "type": "local" if not HUGGINGFACE_API_KEY else "api",
            "model": HUGGINGFACE_MODEL_ID
        })
    except Exception:
        models.append({
            "name": "huggingface",
            "available": False,
            "type": "local",
            "error": "Failed to initialize"
        })

    return models


if __name__ == "__main__":
    # Simple test for the module
    models = get_available_models()
    print(json.dumps(models, indent=2))

    # Test a model if available
    for model_info in models:
        if model_info["available"]:
            model_name = model_info["name"]
            print(f"\nTesting {model_name} model...")

            test_log = "2023-05-01 12:34:56 ERROR Failed to connect to database: Connection refused"
            result = analyze_log(test_log, model_name)

            print(f"\nAnalysis result from {model_name}:")
            print(result)
            break
