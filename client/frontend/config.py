"""Configuration module for AILinux frontend.

Provides settings management for the application.
"""
# config.py
import os

CONFIG = {
    "logging_enabled": True,
    "use_gpu_only": False,
    "synchronous_mode": False,
    "chatgpt_enabled": bool(os.getenv("OPENAI_API_KEY"))
}

def get(key):
    return CONFIG.get(key)

def set_config(key, value):
    CONFIG[key] = value
