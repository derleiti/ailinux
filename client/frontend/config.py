"""Configuration module for AILinux frontend.

Provides settings management for the application.
"""
import os

CONFIG = {
    "logging_enabled": True,
    "use_gpu_only": False,
    "synchronous_mode": False,
    "chatgpt_enabled": bool(os.getenv("OPENAI_API_KEY"))
}

def get(key):
    """Get a configuration value by key.
    
    Args:
        key: Configuration key to retrieve
        
    Returns:
        Value associated with the key or None if not found
    """
    return CONFIG.get(key)

def set_config(key, value):
    """Set a configuration value.
    
    Args:
        key: Configuration key to set
        value: Value to associate with the key
    """
    CONFIG[key] = value
