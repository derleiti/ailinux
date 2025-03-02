"""Gpt4Allinit module for AILinux.

This module provides functionality for the AILinux system.
"""
from gpt4all import GPT4All

# Lade das GPT4All Modell
model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

# Starte eine Chat-Sitzung mit GPT4All
with model.chat_session():
    # Generiere eine Antwort und streame sie
    for token in model.generate("Erzähle mir eine Geschichte über einen Drachen.", streaming=True):
        print(token, end='', flush=True)
