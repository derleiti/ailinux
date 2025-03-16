"""Hugging Face Integration for AILinux.

This module provides comprehensive integration with Hugging Face models,
including model discovery, management, and inference capabilities.
"""
import os
import logging
import time
import json
from typing import Dict, Any, Optional, Union, List, Tuple
import threading
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("HuggingFace")

# Load environment variables
load_dotenv()

# Get API key from environment
HF_API_KEY = os.getenv("HF_API_KEY", "")

# Default settings
DEFAULT_MODEL = os.getenv("DEFAULT_HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
MODELS_CACHE_DIR = os.getenv("HF_MODELS_CACHE_DIR", os.path.join(os.path.dirname(__file__), "models"))
HF_CACHE_FILE = os.path.join(MODELS_CACHE_DIR, "huggingface_cache.json")

# Model cache
_model_cache = {}
_pipeline_cache = {}
_token_cache = {}
_model_info_cache = None

# Cache timestamp
_cache_last_updated = 0
CACHE_TTL = 3600  # 1 hour

# Thread lock for concurrent access
_cache_lock = threading.Lock()


def initialize():
    """Initialize the Hugging Face module.
    
    Creates necessary directories and loads cached model information.
    
    Returns:
        bool: True if initialization is successful, False otherwise
    """
    global _model_info_cache, _cache_last_updated

    try:
        # Create cache directory if it doesn't exist
        os.makedirs(MODELS_CACHE_DIR, exist_ok=True)

        # Load cached model information if available
        if os.path.exists(HF_CACHE_FILE):
            try:
                with open(HF_CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    _model_info_cache = cache_data.get('models', {})
                    _cache_last_updated = cache_data.get('timestamp', 0)
                    logger.info(f"Loaded {len(_model_info_cache)} models from cache")
            except json.JSONDecodeError:
                logger.warning("Invalid cache file format, will rebuild cache")
                _model_info_cache = {}
                _cache_last_updated = 0
        else:
            _model_info_cache = {}
            _cache_last_updated = 0

        # Check for required dependencies
        check_dependencies()

        return True
    except Exception as e:
        logger.error(f"Error initializing Hugging Face module: {str(e)}")
        return False


def check_dependencies():
    """Check if required dependencies are installed.
    
    Logs warnings for missing dependencies.
    """
    missing_deps = []

    try:
        import torch
    except ImportError:
        missing_deps.append("torch")

    try:
        import transformers
    except ImportError:
        missing_deps.append("transformers")

    try:
        import huggingface_hub
    except ImportError:
        missing_deps.append("huggingface_hub")

    try:
        import accelerate
    except ImportError:
        missing_deps.append("accelerate")

    try:
        import bitsandbytes
    except ImportError:
        missing_deps.append("bitsandbytes")

    if missing_deps:
        logger.warning(f"Missing dependencies: {', '.join(missing_deps)}")
        logger.warning("Install them with: pip install " + " ".join(missing_deps))
    else:
        # Check for GPU if all dependencies are installed
        try:
            import torch
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                logger.info(f"GPU available: {device_name}")
            else:
                logger.info("No GPU found, using CPU for inference (will be slower)")
        except Exception as e:
            logger.warning(f"Error checking GPU availability: {str(e)}")


def is_available() -> bool:
    """Check if Hugging Face functionality is available.
    
    Returns:
        bool: True if available, False otherwise
    """
    try:
        import torch
        import transformers
        return True
    except ImportError:
        return False


def get_model_info(model_id: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Get detailed information about a Hugging Face model.
    
    Args:
        model_id: Hugging Face model ID
        force_refresh: Force refreshing cached information
        
    Returns:
        Dictionary with model information
    """
    global _model_info_cache

    # Initialize if needed
    if _model_info_cache is None:
        initialize()

    # Return cached info if available and not forcing refresh
    if not force_refresh and model_id in _model_info_cache:
        return _model_info_cache[model_id]

    try:
        from huggingface_hub import HfApi

        api = HfApi(token=HF_API_KEY if HF_API_KEY else None)
        model_info = api.model_info(model_id)

        # Format model info for easier consumption
        info = {
            "id": model_info.id,
            "sha": model_info.sha,
            "last_modified": model_info.last_modified,
            "tags": model_info.tags,
            "pipeline_tag": model_info.pipeline_tag,
            "downloads": getattr(model_info, "downloads", None),
            "likes": getattr(model_info, "likes", None),
            "library_name": getattr(model_info, "library_name", None),
            "size_in_bytes": getattr(model_info, "_siblings_size_in_bytes", 0)
        }

        # Store in cache
        with _cache_lock:
            if _model_info_cache is None:
                _model_info_cache = {}
            _model_info_cache[model_id] = info

            # Save updated cache periodically
            _save_cache()

        return info
    except Exception as e:
        logger.error(f"Error fetching model info for {model_id}: {str(e)}")
        return {"id": model_id, "error": str(e)}


def search_models(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search for models on Hugging Face Hub.
    
    Args:
        category: Filter by model category (e.g., "text-generation")
        keyword: Search term
        limit: Maximum number of results
        
    Returns:
        List of model information dictionaries
    """
    try:
        from huggingface_hub import HfApi

        api = HfApi(token=HF_API_KEY if HF_API_KEY else None)

        # Prepare filter criteria
        filter_dict = {}
        if category:
            filter_dict["task"] = category

        # Perform search based on parameters
        if keyword:
            models = api.list_models(search=keyword, filter=filter_dict or None, limit=limit)
        else:
            models = api.list_models(filter=filter_dict or None, limit=limit)

        # Format results
        results = []
        for model in models:
            results.append({
                "id": model.id,
                "pipeline_tag": getattr(model, "pipeline_tag", None),
                "downloads": getattr(model, "downloads", None),
                "likes": getattr(model, "likes", None),
                "tags": model.tags
            })

        return results
    except Exception as e:
        logger.error(f"Error searching Hugging Face models: {str(e)}")
        return []


def get_recommended_models() -> List[Dict[str, Any]]:
    """Get a list of recommended models for log analysis.
    
    Returns:
        List of recommended model information
    """
    # Curated list of models well-suited for log analysis
    recommended_models = [
        "mistralai/Mistral-7B-Instruct-v0.2",
        "meta-llama/Llama-2-7b-chat-h",
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "microsoft/phi-2",
        "google/gemma-2b-it"
    ]

    results = []

    # Get detailed information for each recommended model
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Use threading to fetch model info in parallel
        future_to_model = {executor.submit(get_model_info, model_id): model_id for model_id in recommended_models}
        for future in future_to_model:
            model_id = future_to_model[future]
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"Error fetching info for {model_id}: {str(e)}")

    return results


def get_pipeline(
    model_id: Optional[str] = None,
    task: str = "text-generation",
    use_gpu: bool = True
):
    """Get a Hugging Face pipeline for the specified model and task.
    
    Args:
        model_id: Hugging Face model ID (defaults to DEFAULT_MODEL)
        task: Task type (e.g., "text-generation", "summarization")
        use_gpu: Whether to use GPU if available

    Returns:
        Hugging Face pipeline object or None if initialization fails
    """
    # Use default model if not specified
    model_id = model_id or DEFAULT_MODEL

    # Check if pipeline already exists in cache
    cache_key = f"{model_id}_{task}_{use_gpu}"
    if cache_key in _pipeline_cache:
        return _pipeline_cache[cache_key]

    try:
        import torch
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

        # Check GPU availability if requested
        device = -1  # CPU
        if use_gpu and torch.cuda.is_available():
            device = 0  # First GPU

        # Load tokenizer and model
        logger.info(f"Loading model: {model_id} for task: {task}")
        start_time = time.time()

        # Create pipeline
        hf_pipeline = pipeline(
            task,
            model=model_id,
            device=device,
            token=HF_API_KEY if HF_API_KEY else None,
            cache_dir=MODELS_CACHE_DIR
        )

        # Add to cache
        _pipeline_cache[cache_key] = hf_pipeline

        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f}s")

        return hf_pipeline
    except Exception as e:
        logger.error(f"Error creating pipeline for {model_id}: {str(e)}")
        return None


def get_tokenizer(model_id: Optional[str] = None):
    """Get tokenizer for the specified model.
    
    Args:
        model_id: Hugging Face model ID (defaults to DEFAULT_MODEL)

    Returns:
        Hugging Face tokenizer or None if initialization fails
    """
    # Use default model if not specified
    model_id = model_id or DEFAULT_MODEL

    # Check if tokenizer already exists in cache
    if model_id in _token_cache:
        return _token_cache[model_id]

    try:
        from transformers import AutoTokenizer

        # Load tokenizer
        logger.info(f"Loading tokenizer for: {model_id}")
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            token=HF_API_KEY if HF_API_KEY else None,
            cache_dir=MODELS_CACHE_DIR
        )

        # Add to cache
        _token_cache[model_id] = tokenizer

        return tokenizer
    except Exception as e:
        logger.error(f"Error loading tokenizer for {model_id}: {str(e)}")
        return None


def analyze_log(
    log_text: str,
    model_id: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7
) -> str:
    """Analyze log text using a Hugging Face model.
    
    Args:
        log_text: The log text to analyze
        model_id: Hugging Face model ID (defaults to DEFAULT_MODEL)
        max_tokens: Maximum number of tokens in the response
        temperature: Temperature parameter for generation
        
    Returns:
        Analysis result as a string
    """
    # Use default model if not specified
    model_id = model_id or DEFAULT_MODEL

    try:
        # Create analysis prompt
        system_prompt = """You are an AI assistant specialized in analyzing logs and providing insights.
Given a log snippet, your task is to:
1. Summarize the key information in the log
2. Identify any errors, warnings, or issues
3. Explain potential causes for the identified problems
4. Suggest troubleshooting steps or solutions

Be concise and precise in your analysis."""

        prompt = f"{system_prompt}\n\nLOG:\n{log_text}\n\nANALYSIS:"

        # Get pipeline for text generation
        text_pipeline = get_pipeline(model_id, "text-generation")
        if not text_pipeline:
            return "⚠ Error: Could not initialize text generation pipeline"

        # Generate response
        logger.info(f"Analyzing log with model: {model_id}")
        start_time = time.time()

        result = text_pipeline(
            prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.1,
            return_full_text=False
        )

        processing_time = time.time() - start_time
        logger.info(f"Log analyzed in {processing_time:.2f}s with {model_id}")

        # Extract and clean response
        response = result[0]['generated_text']

        return response.strip()
    except Exception as e:
        logger.exception(f"Error analyzing log with {model_id}: {str(e)}")
        return f"⚠ Error analyzing log: {str(e)}"


def _save_cache():
    """Save model information cache to disk."""
    global _model_info_cache, _cache_last_updated

    try:
        # Skip if cache is empty or was recently saved
        current_time = time.time()
        if not _model_info_cache or current_time - _cache_last_updated < 300:  # 5 minutes
            return

        # Prepare cache data
        cache_data = {
            "timestamp": current_time,
            "models": _model_info_cache
        }

        # Save to file
        with open(HF_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)

        _cache_last_updated = current_time
        logger.debug(f"Saved model cache with {len(_model_info_cache)} entries")
    except Exception as e:
        logger.error(f"Error saving model cache: {str(e)}")


# Initialize module when imported
initialize()
