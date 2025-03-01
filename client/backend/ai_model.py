"""Optimized AI Model Integration for AILinux.

Provides robust, type-hinted interfaces for various AI models with improved error handling.
"""
import os
import logging
from typing import Dict, Any, Optional, Union, List, Tuple
from functools import lru_cache
from dataclasses import dataclass, field
from dotenv import load_dotenv

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

# Load environment variables safely
load_dotenv()

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

class ModelInitializationError(Exception):
    """Custom exception for model initialization failures."""
    pass

class AIModelManager:
    """Centralized manager for AI model initialization and management."""

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._configs = self._load_model_configs()

    def _load_model_configs(self) -> Dict[str, ModelConfig]:
        """
        Load model configurations from environment variables.
        
        Returns:
            Dictionary of model configurations
        """
        return {
            "gpt4all": ModelConfig(
                name="gpt4all",
                model_path=os.getenv("LLAMA_MODEL_PATH", "Meta-Llama-3-8B-Instruct.Q4_0.gguf"),
                model_id="local/gpt4all"
            ),
            "openai": ModelConfig(
                name="openai",
                api_key=os.getenv("OPENAI_API_KEY"),
                model_id="gpt-4"
            ),
            "gemini": ModelConfig(
                name="gemini",
                api_key=os.getenv("GEMINI_API_KEY"),
                model_id="gemini-pro"
            ),
            "huggingface": ModelConfig(
                name="huggingface",
                api_key=os.getenv("HUGGINGFACE_API_KEY"),
                model_id=os.getenv("HUGGINGFACE_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")
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
            if model_name == "gpt4all":
                return self._initialize_gpt4all(config)
            elif model_name == "openai":
                return self._initialize_openai(config)
            elif model_name == "gemini":
                return self._initialize_gemini(config)
            elif model_name == "huggingface":
                return self._initialize_huggingface(config)
        except Exception as e:
            logger.error(f"Model initialization failed for {model_name}: {e}")
            raise ModelInitializationError(f"Failed to initialize {model_name} model") from e

    def _initialize_gpt4all(self, config: ModelConfig) -> Any:
        """Initialize GPT4All model with robust error handling."""
        try:
            from gpt4all import GPT4All
            model_path = os.path.expanduser(config.model_path)
            
            # Ensure model directory exists
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            model = GPT4All(model_path)
            logger.info(f"GPT4All model loaded successfully from {model_path}")
            return model
        except ImportError:
            logger.error("GPT4All library not installed")
            raise

    def _initialize_openai(self, config: ModelConfig) -> Any:
        """Initialize OpenAI model with API key validation."""
        if not config.api_key:
            raise ModelInitializationError("OpenAI API key is required")
        
        import openai
        openai.api_key = config.api_key
        return openai

    def _initialize_gemini(self, config: ModelConfig) -> Any:
        """Initialize Google Gemini model with API key validation."""
        if not config.api_key:
            raise ModelInitializationError("Gemini API key is required")
        
        import google.generativeai as genai
        genai.configure(api_key=config.api_key)
        return genai

    def _initialize_huggingface(self, config: ModelConfig) -> Tuple[Any, Any, Any]:
        """Initialize Hugging Face model with comprehensive setup."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            tokenizer = AutoTokenizer.from_pretrained(
                config.model_id,
                cache_dir=config.cache_dir,
                token=config.api_key
            )
            
            model = AutoModelForCausalLM.from_pretrained(
                config.model_id,
                cache_dir=config.cache_dir,
                token=config.api_key,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                low_cpu_mem_usage=True,
                device_map="auto" if device == "cuda" else None
            )
            
            pipeline_model = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device=0 if device == "cuda" else -1
            )
            
            return model, tokenizer, pipeline_model
        except ImportError:
            logger.error("Transformers library not installed")
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
        
        return {
            "name": config.name,
            "model_id": config.model_id,
            "is_api_model": bool(config.api_key),
            "device": config.device
        }
