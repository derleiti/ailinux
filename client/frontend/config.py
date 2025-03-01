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

def set(key, value):
    CONFIG[key] = value
