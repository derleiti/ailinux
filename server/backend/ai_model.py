"""Optimized AI Model Integration for AILinux.

Provides robust, type-hinted interfaces for various AI models with improved error handling.
"""
import os
import logging
import tempfile
from typing import Dict, Any, Optional, Union, List, Tuple, Callable
from functools import lru_cache
from dataclasses import dataclass, field
import traceback
from pathlib import Path

# Load environment variables safely
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("dotenv package not installed, environment variables must be set manually")

# Configure logging with more structured approach
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("ai_model.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AIModel")

@dataclass
class ModelConfig:
    """Configuration for AI models with robust type handling."""
    name: str
    api_key: Optional[str] = None
    model_path: Optional[str] = None
    model_id: Optional[str] = None
    cache_dir: str = "./models"
    device: str = "cpu"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 120  # Timeout in seconds for API calls
    retry_count: int = 2  # Number of retries for failed API calls

class ModelInitializationError(Exception):
    """Custom exception for model initialization failures."""
    pass

class AIModelManager:
    """Centralized manager for AI model initialization and management."""

    def __init__(self):
        """Initialize the AI Model Manager."""
        self._models: Dict[str, Any] = {}
        self._configs = self._load_model_configs()
        # Ensure model cache directory exists
        for config in self._configs.values():
            os.makedirs(os.path.expanduser(config.cache_dir), exist_ok=True)

    def _load_model_configs(self) -> Dict[str, ModelConfig]:
        """
        Load model configurations from environment variables.
        
        Returns:
            Dictionary of model configurations
        """
        models_cache_dir = os.getenv("MODELS_CACHE_DIR", "./models")
        
        return {
            "gpt4all": ModelConfig(
                name="gpt4all",
                model_path=os.getenv("LLAMA_MODEL_PATH", "Meta-Llama-3-8B-Instruct.Q4_0.gguf"),
                model_id="local/gpt4all",
                cache_dir=models_cache_dir
            ),
            "openai": ModelConfig(
                name="openai",
                api_key=os.getenv("OPENAI_API_KEY"),
                model_id=os.getenv("OPENAI_MODEL", "gpt-4"),
                cache_dir=models_cache_dir
            ),
            "gemini": ModelConfig(
                name="gemini",
                api_key=os.getenv("GEMINI_API_KEY"),
                model_id=os.getenv("GEMINI_MODEL", "gemini-pro"),
                cache_dir=models_cache_dir
            ),
            "huggingface": ModelConfig(
                name="huggingface",
                api_key=os.getenv("HUGGINGFACE_API_KEY"),
                model_id=os.getenv("HUGGINGFACE_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2"),
                cache_dir=models_cache_dir
            )
        }

    @lru_cache(maxsize=4)
    def initialize_model(self, model_name: str) -> Any:
        """
        Initialize a specific AI model with caching and robust error handling.
        
        Args:
            model_name: Name of the model to initialize
            
        Returns:
            Initialized model instance
        
        Raises:
            ModelInitializationError: If model cannot be initialized
        """
        config = self._configs.get(model_name.lower())
        if not config:
            raise ModelInitializationError(f"Unknown model: {model_name}")

        try:
            if model_name.lower() == "gpt4all":
                return self._initialize_gpt4all(config)
            elif model_name.lower() == "openai":
                return self._initialize_openai(config)
            elif model_name.lower() == "gemini":
                return self._initialize_gemini(config)
            elif model_name.lower() == "huggingface":
                return self._initialize_huggingface(config)
            else:
                raise ModelInitializationError(f"Unsupported model type: {model_name}")
        except ImportError as e:
            logger.error(f"Required library not installed for {model_name}: {e}")
            raise ModelInitializationError(f"Missing library for {model_name} model: {e}") from e
        except Exception as e:
            logger.error(f"Model initialization failed for {model_name}: {e}")
            logger.debug(traceback.format_exc())
            raise ModelInitializationError(f"Failed to initialize {model_name} model: {e}") from e

    def _initialize_gpt4all(self, config: ModelConfig) -> Any:
        """Initialize GPT4All model with robust error handling."""
        try:
            from gpt4all import GPT4All
            
            # Handle relative and user paths
            model_path = os.path.expanduser(config.model_path)
            if not os.path.isabs(model_path):
                model_path = os.path.join(os.path.expanduser(config.cache_dir), model_path)
            
            # Ensure model directory exists
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # Check if model file exists, if not inform the user
            if not os.path.exists(model_path):
                logger.warning(f"Model file not found at {model_path}. GPT4All will attempt to download it.")
            
            # Initialize model with specified parameters
            model = GPT4All(model_path)
            logger.info(f"GPT4All model loaded successfully from {model_path}")
            return model
        except ImportError:
            logger.error("GPT4All library not installed. Install it with 'pip install gpt4all'.")
            raise
        except Exception as e:
            logger.error(f"Error initializing GPT4All model: {e}")
            logger.debug(traceback.format_exc())
            raise

    def _initialize_openai(self, config: ModelConfig) -> Any:
        """Initialize OpenAI model with API key validation."""
        if not config.api_key:
            raise ModelInitializationError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        try:
            import openai
            # Set API key
            openai.api_key = config.api_key
            
            # Test connection by making a simple request
            try:
                # Use models.list as a simple API check
                openai.models.list()
                logger.info("OpenAI API connection verified successfully")
            except Exception as api_error:
                logger.warning(f"OpenAI API connection test failed: {api_error}")
                # Continue anyway as the key might still be valid for completions
            
            return openai
        except ImportError:
            logger.error("OpenAI library not installed. Install it with 'pip install openai'.")
            raise

    def _initialize_gemini(self, config: ModelConfig) -> Any:
        """Initialize Google Gemini model with API key validation."""
        if not config.api_key:
            raise ModelInitializationError("Gemini API key is required. Set GEMINI_API_KEY environment variable.")
        
        try:
            import google.generativeai as genai
            
            # Configure with API key
            genai.configure(api_key=config.api_key)
            
            # Test connection by listing models
            try:
                genai.list_models()
                logger.info("Gemini API connection verified successfully")
            except Exception as api_error:
                logger.warning(f"Gemini API connection test failed: {api_error}")
                # Continue anyway as the key might still be valid
            
            return genai
        except ImportError:
            logger.error("Google GenerativeAI library not installed. Install it with 'pip install google-generativeai'.")
            raise

    def _initialize_huggingface(self, config: ModelConfig) -> Tuple[Any, Any, Any]:
        """Initialize Hugging Face model with comprehensive setup."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            import torch
            
            # Determine device
            if config.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = config.device
            
            # Log device information
            if device == "cuda" and torch.cuda.is_available():
                logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("Using CPU for inference")
            
            # Ensure cache directory exists
            cache_dir = os.path.expanduser(config.cache_dir)
            os.makedirs(cache_dir, exist_ok=True)
            
            # Load tokenizer
            logger.info(f"Loading tokenizer for model: {config.model_id}")
            tokenizer = AutoTokenizer.from_pretrained(
                config.model_id,
                cache_dir=cache_dir,
                token=config.api_key if config.api_key else None,
                local_files_only=False
            )
            
            # Load model with appropriate settings based on device
            logger.info(f"Loading model: {config.model_id}")
            model_loading_args = {
                "cache_dir": cache_dir,
                "token": config.api_key if config.api_key else None,
                "local_files_only": False
            }
            
            # Add device-specific optimizations
            if device == "cuda":
                model_loading_args.update({
                    "torch_dtype": torch.float16,  # Use half precision for GPU
                    "low_cpu_mem_usage": True,
                    "device_map": "auto"
                })
            
            model = AutoModelForCausalLM.from_pretrained(config.model_id, **model_loading_args)
            
            # Create text generation pipeline
            logger.info("Creating text generation pipeline")
            pipeline_model = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device=0 if device == "cuda" else -1,
                max_new_tokens=config.max_tokens,
                temperature=config.temperature
            )
            
            logger.info(f"HuggingFace model {config.model_id} initialized successfully on {device}")
            return model, tokenizer, pipeline_model
        except ImportError:
            logger.error("Transformers library not installed. Install it with 'pip install transformers'.")
            raise
        except Exception as e:
            logger.error(f"Error initializing HuggingFace model: {e}")
            logger.debug(traceback.format_exc())
            raise

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Retrieve information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model information
        """
        config = self._configs.get(model_name.lower())
        if not config:
            return {"error": f"Unknown model: {model_name}"}
        
        # Check if model is available (libraries installed)
        available = True
        try:
            if model_name.lower() == "gpt4all":
                import gpt4all
            elif model_name.lower() == "openai":
                import openai
            elif model_name.lower() == "gemini":
                import google.generativeai
            elif model_name.lower() == "huggingface":
                import transformers
                import torch
        except ImportError:
            available = False
        
        return {
            "name": config.name,
            "model_id": config.model_id,
            "is_api_model": bool(config.api_key),
            "device": config.device,
            "available": available,
            "has_api_key": bool(config.api_key) if config.api_key is required_for_model(model_name) else True,
            "cache_dir": config.cache_dir
        }

def required_for_model(model_name: str) -> bool:
    """Check if an API key is required for a specific model."""
    return model_name.lower() in ["openai", "gemini", "huggingface"]

def get_available_models() -> List[Dict[str, Any]]:
    """
    Get information about all available models.
    
    Returns:
        List of dictionaries with model information
    """
    manager = AIModelManager()
    models = []
    
    for model_name in ["gpt4all", "openai", "gemini", "huggingface"]:
        models.append(manager.get_model_info(model_name))
    
    return models

def analyze_log(log_text: str, model_name: str = "gpt4all", instruction: Optional[str] = None) -> str:
    """
    Analyze a log using the specified AI model.
    
    Args:
        log_text: The log text to analyze
        model_name: Name of the model to use
        instruction: Optional custom instruction for the analysis
        
    Returns:
        Analysis result as string
    """
    if not log_text:
        return "Error: No log text provided for analysis."
    
    # Limit log text length if necessary to prevent excessive token usage
    max_log_length = 8000  # Characters, adjust based on model capabilities
    truncated = False
    if len(log_text) > max_log_length:
        log_text = log_text[:max_log_length] + "..."
        truncated = True
    
    # Default system prompt for log analysis
    system_prompt = """You are an AI assistant specialized in analyzing logs and providing insights.
Given a log snippet, your task is to:
1. Summarize the key information in the log
2. Identify any errors, warnings, or issues
3. Explain potential causes for the identified problems
4. Suggest troubleshooting steps or solutions

Be concise and precise in your analysis."""

    # Use custom instruction if provided
    if instruction:
        system_prompt = instruction
    
    try:
        # Initialize the model manager
        manager = AIModelManager()
        
        # Get the model based on name
        model = manager.initialize_model(model_name)
        
        # Build full prompt
        prompt = f"{system_prompt}\n\nLOG:\n{log_text}\n\nANALYSIS:"
        
        # Generate analysis based on model type
        if model_name.lower() == "gpt4all":
            return _analyze_with_gpt4all(model, prompt)
        elif model_name.lower() == "openai":
            return _analyze_with_openai(model, prompt)
        elif model_name.lower() == "gemini":
            return _analyze_with_gemini(model, prompt)
        elif model_name.lower() == "huggingface":
            return _analyze_with_huggingface(model, prompt)
        else:
            return f"Error: Unsupported model type: {model_name}"
    
    except ModelInitializationError as e:
        logger.error(f"Model initialization error: {e}")
        return f"Error initializing model: {str(e)}"
    except Exception as e:
        logger.error(f"Error analyzing log with {model_name}: {e}")
        logger.debug(traceback.format_exc())
        return f"Error analyzing log: {str(e)}"

def _analyze_with_gpt4all(model, prompt: str) -> str:
    """Generate analysis using GPT4All model."""
    try:
        # Use chat completion API
        response = model.chat_completion([
            {"role": "system", "content": "You are a helpful AI assistant specializing in log analysis."},
            {"role": "user", "content": prompt}
        ])
        
        return response['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Error in GPT4All analysis: {e}")
        logger.debug(traceback.format_exc())
        raise

def _analyze_with_openai(openai_client, prompt: str) -> str:
    """Generate analysis using OpenAI API."""
    try:
        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant specializing in log analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in OpenAI analysis: {e}")
        logger.debug(traceback.format_exc())
        raise

def _analyze_with_gemini(genai, prompt: str) -> str:
    """Generate analysis using Google Gemini API."""
    try:
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-pro"))
        response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        logger.error(f"Error in Gemini analysis: {e}")
        logger.debug(traceback.format_exc())
        raise

def _analyze_with_huggingface(model_tuple, prompt: str) -> str:
    """Generate analysis using HuggingFace model."""
    try:
        # Unpack the model tuple
        model, tokenizer, pipeline_model = model_tuple
        
        # Generate text
        response = pipeline_model(
            prompt,
            do_sample=True,
            top_p=0.95,
            temperature=0.7,
            return_full_text=False
        )
        
        return response[0]['generated_text']
    except Exception as e:
        logger.error(f"Error in HuggingFace analysis: {e}")
        logger.debug(traceback.format_exc())
        raise

if __name__ == "__main__":
    # Simple CLI for testing the module
    import argparse
    
    parser = argparse.ArgumentParser(description="AILinux Model Manager CLI")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--analyze", type=str, help="Analyze log file")
    parser.add_argument("--model", type=str, default="gpt4all", help="Model to use for analysis")
    
    args = parser.parse_args()
    
    if args.list_models:
        models = get_available_models()
        print("\nAvailable AI Models:")
        print("===================")
        for model in models:
            status = "✓ Available" if model["available"] else "✗ Not available"
            api_status = ""
            if model["is_api_model"]:
                api_status = "✓ API Key Set" if model["has_api_key"] else "✗ API Key Missing"
            
            print(f"{model['name']} ({model['model_id']}): {status} {api_status}")
        print()
    
    if args.analyze:
        try:
            with open(args.analyze, 'r') as f:
                log_text = f.read()
            
            print(f"\nAnalyzing log with {args.model}...\n")
            result = analyze_log(log_text, args.model)
            print(result)
            print()
        except FileNotFoundError:
            print(f"Error: File not found: {args.analyze}")
        except Exception as e:
            print(f"Error: {e}")
