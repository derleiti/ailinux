#!/usr/bin/env python3
"""
AI Model Manager für AILinux
Zentrales Modul für die Verwaltung und Nutzung von KI-Modellen.
"""
import os
import sys
import logging
import traceback
import tempfile
from functools import lru_cache
from typing import Dict, Any, List, Union, Callable, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("ai_model.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AIModel")

# Lade Umgebungsvariablen
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("dotenv Paket nicht installiert, Umgebungsvariablen müssen manuell gesetzt werden")

@dataclass
class ModelConfig:
    """Konfiguration für AI-Modelle mit robuster Typbehandlung."""
    name: str
    api_key: Optional[str] = None
    model_path: Optional[str] = None
    model_id: Optional[str] = None
    cache_dir: str = "./models"
    device: str = "cpu"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 120  # Timeout in Sekunden für API-Aufrufe
    retry_count: int = 2  # Anzahl der Wiederholungsversuche bei fehlgeschlagenen API-Aufrufen

class ModelInitializationError(Exception):
    """Benutzerdefinierte Ausnahme für Fehler bei der Modellinitialisierung."""
    pass

class AIModelManager:
    """Zentralisierter Manager für AI-Modellinitialisierung und -verwaltung."""

    def __init__(self):
        """Initialisiere den AI Model Manager."""
        self._models = {}
        self._configs = self._load_model_configs()
        # Stelle sicher, dass das Modell-Cache-Verzeichnis existiert
        for config in self._configs.values():
            os.makedirs(os.path.expanduser(config.cache_dir), exist_ok=True)

    def _load_model_configs(self) -> Dict[str, ModelConfig]:
        """
        Lade Modellkonfigurationen aus Umgebungsvariablen.

        Returns:
            Dictionary mit Modellkonfigurationen
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
        Initialisiere ein spezifisches AI-Modell mit Caching und robuster Fehlerbehandlung.

        Args:
            model_name: Name des zu initialisierenden Modells

        Returns:
            Initialisierte Modellinstanz

        Raises:
            ModelInitializationError: Wenn das Modell nicht initialisiert werden kann
        """
        config = self._configs.get(model_name.lower())
        if not config:
            raise ModelInitializationError(f"Unbekanntes Modell: {model_name}")

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
                raise ModelInitializationError(f"Nicht unterstützter Modelltyp: {model_name}")
        except ImportError as e:
            logger.error(f"Erforderliche Bibliothek nicht installiert für {model_name}: {e}")
            raise ModelInitializationError(f"Fehlende Bibliothek für {model_name} Modell: {e}") from e
        except Exception as e:
            logger.error(f"Modellinitialisierung fehlgeschlagen für {model_name}: {e}")
            logger.debug(traceback.format_exc())
            raise ModelInitializationError(f"Konnte {model_name} Modell nicht initialisieren: {e}") from e

    def _initialize_gpt4all(self, config: ModelConfig) -> Any:
        """Initialisiere GPT4All-Modell mit robuster Fehlerbehandlung."""
        try:
            # Korrigiere Import für GPT4All
            try:
                from gpt4all import GPT4All
            except ImportError:
                logger.warning("Standard gpt4all Modul nicht gefunden, versuche alternativen Import")
                # Alternativ, falls die Struktur des gpt4all Pakets anders ist
                try:
                    from gpt4all.gpt4all import GPT4All
                except ImportError:
                    raise ImportError("GPT4All Bibliothek nicht installiert oder nicht korrekt konfiguriert. Installiere mit 'pip install gpt4all'")

            # Behandle relative und Benutzerpfade
            model_path = os.path.expanduser(config.model_path)
            if not os.path.isabs(model_path):
                model_path = os.path.join(os.path.expanduser(config.cache_dir), model_path)

            # Stelle sicher, dass das Modellverzeichnis existiert
            os.makedirs(os.path.dirname(model_path), exist_ok=True)

            # Prüfe, ob die Modelldatei existiert, falls nicht, informiere den Benutzer
            if not os.path.exists(model_path):
                logger.warning(f"Modelldatei nicht gefunden unter {model_path}. GPT4All wird versuchen, sie herunterzuladen.")

            # Initialisiere Modell mit angegebenen Parametern
            model = GPT4All(model_path)
            logger.info(f"GPT4All-Modell erfolgreich geladen von {model_path}")
            return model
        except ImportError:
            logger.error("GPT4All-Bibliothek nicht installiert. Installiere sie mit 'pip install gpt4all'.")
            raise
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung des GPT4All-Modells: {e}")
            logger.debug(traceback.format_exc())
            raise

    def _initialize_openai(self, config: ModelConfig) -> Any:
        """Initialisiere OpenAI-Modell mit API-Schlüsselvalidierung."""
        if not config.api_key:
            raise ModelInitializationError("OpenAI API-Schlüssel ist erforderlich. Setze die OPENAI_API_KEY Umgebungsvariable.")

        try:
            import openai
            # Setze API-Schlüssel
            openai.api_key = config.api_key

            # Teste Verbindung mit einer einfachen Anfrage
            try:
                # Verwende models.list als einfachen API-Check
                openai.models.list()
                logger.info("OpenAI API-Verbindung erfolgreich verifiziert")
            except Exception as api_error:
                logger.warning(f"OpenAI API-Verbindungstest fehlgeschlagen: {api_error}")
                # Trotzdem fortfahren, da der Schlüssel möglicherweise noch für Vervollständigungen gültig ist

            return openai
        except ImportError:
            logger.error("OpenAI-Bibliothek nicht installiert. Installiere sie mit 'pip install openai'.")
            raise

    def _initialize_gemini(self, config: ModelConfig) -> Any:
        """Initialisiere Google Gemini-Modell mit API-Schlüsselvalidierung."""
        if not config.api_key:
            raise ModelInitializationError("Gemini API-Schlüssel ist erforderlich. Setze die GEMINI_API_KEY Umgebungsvariable.")

        try:
            import google.generativeai as genai

            # Konfiguriere mit API-Schlüssel
            genai.configure(api_key=config.api_key)

            # Teste Verbindung durch Auflisten von Modellen
            try:
                genai.list_models()
                logger.info("Gemini API-Verbindung erfolgreich verifiziert")
            except Exception as api_error:
                logger.warning(f"Gemini API-Verbindungstest fehlgeschlagen: {api_error}")
                # Trotzdem fortfahren, da der Schlüssel möglicherweise noch gültig ist

            return genai
        except ImportError:
            logger.error("Google GenerativeAI-Bibliothek nicht installiert. Installiere sie mit 'pip install google-generativeai'.")
            raise

    def _initialize_huggingface(self, config: ModelConfig) -> Any:
        """Initialisiere Hugging Face-Modell mit umfassendem Setup."""
        try:
            # Lazy-Import, um Abhängigkeiten zu reduzieren, wenn das Modell nicht verwendet wird
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            import torch

            # Bestimme Gerät
            if config.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = config.device

            # Protokolliere Geräteinformationen
            if device == "cuda" and torch.cuda.is_available():
                logger.info(f"Verwende CUDA-Gerät: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("Verwende CPU für Inferenz")

            # Stelle sicher, dass das Cache-Verzeichnis existiert
            cache_dir = os.path.expanduser(config.cache_dir)
            os.makedirs(cache_dir, exist_ok=True)

            # Lade Tokenizer
            logger.info(f"Lade Tokenizer für Modell: {config.model_id}")
            tokenizer = AutoTokenizer.from_pretrained(
                config.model_id,
                cache_dir=cache_dir,
                token=config.api_key if config.api_key else None,
                local_files_only=False
            )

            # Lade Modell mit geeigneten Einstellungen basierend auf dem Gerät
            logger.info(f"Lade Modell: {config.model_id}")
            model_loading_args = {
                "cache_dir": cache_dir,
                "token": config.api_key if config.api_key else None,
                "local_files_only": False
            }

            # Füge gerätespezifische Optimierungen hinzu
            if device == "cuda":
                model_loading_args.update({
                    "torch_dtype": torch.float16,  # Verwende halbe Präzision für GPU
                    "low_cpu_mem_usage": True,
                    "device_map": "auto"
                })

            model = AutoModelForCausalLM.from_pretrained(config.model_id, **model_loading_args)

            # Erstelle Textgenerierungs-Pipeline
            logger.info("Erstelle Textgenerierungs-Pipeline")
            pipeline_model = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device=0 if device == "cuda" else -1,
                max_new_tokens=config.max_tokens,
                temperature=config.temperature
            )

            logger.info(f"HuggingFace-Modell {config.model_id} erfolgreich auf {device} initialisiert")
            return model, tokenizer, pipeline_model
        except ImportError:
            logger.error("Transformers-Bibliothek nicht installiert. Installiere sie mit 'pip install transformers'.")
            raise
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung des HuggingFace-Modells: {e}")
            logger.debug(traceback.format_exc())
            raise

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Rufe Informationen über ein bestimmtes Modell ab.

        Args:
            model_name: Name des Modells

        Returns:
            Dictionary mit Modellinformationen
        """
        config = self._configs.get(model_name.lower())
        if not config:
            return {"error": f"Unbekanntes Modell: {model_name}"}

        # Prüfe, ob das Modell verfügbar ist (Bibliotheken installiert)
        available = True
        try:
            if model_name.lower() == "gpt4all":
                # Verwende eine einfachere Methode, um die gpt4all-Verfügbarkeit zu prüfen
                # ohne sie vollständig zu importieren oder zu initialisieren
                import importlib.util
                spec = importlib.util.find_spec("gpt4all")
                available = spec is not None
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
            "has_api_key": bool(config.api_key) if required_for_model(model_name) else True,
            "cache_dir": config.cache_dir
        }

def required_for_model(model_name: str) -> bool:
    """Prüfe, ob ein API-Schlüssel für ein bestimmtes Modell erforderlich ist."""
    return model_name.lower() in ["openai", "gemini", "huggingface"]

def get_available_models() -> List[Dict[str, Any]]:
    """
    Hole Informationen über alle verfügbaren Modelle.

    Returns:
        Liste von Dictionaries mit Modellinformationen
    """
    manager = AIModelManager()
    models = []

    for model_name in ["gpt4all", "openai", "gemini", "huggingface"]:
        models.append(manager.get_model_info(model_name))

    return models

def analyze_log(log_text: str, model_name: str = "gpt4all", instruction: Optional[str] = None) -> str:
    """
    Analysiere ein Log mit dem angegebenen AI-Modell.

    Args:
        log_text: Der zu analysierende Log-Text
        model_name: Name des zu verwendenden Modells
        instruction: Optionale benutzerdefinierte Anweisung für die Analyse

    Returns:
        Analyseergebnis als String
    """
    if not log_text:
        return "Fehler: Kein Log-Text für die Analyse bereitgestellt."

    # Begrenze die Log-Textlänge, falls nötig, um übermäßigen Token-Verbrauch zu vermeiden
    max_log_length = 8000  # Zeichen, anpassen basierend auf Modellkapazitäten
    truncated = False
    if len(log_text) > max_log_length:
        log_text = log_text[:max_log_length] + "..."
        truncated = True

    # Standard-Systemprompt für Log-Analyse
    system_prompt = """Du bist ein KI-Assistent, der sich auf die Analyse von Logs und die Bereitstellung von Erkenntnissen spezialisiert hat.
Deine Aufgabe ist es, auf Basis eines Log-Ausschnitts:
1. Die wichtigsten Informationen im Log zusammenzufassen
2. Fehler, Warnungen oder Probleme zu identifizieren
3. Mögliche Ursachen für die identifizierten Probleme zu erklären
4. Schritte zur Fehlerbehebung oder Lösungen vorzuschlagen

Sei präzise und knapp in deiner Analyse."""

    # Verwende benutzerdefinierte Anweisung, falls vorhanden
    if instruction:
        system_prompt = instruction

    try:
        # Initialisiere den Modellmanager
        manager = AIModelManager()

        # Hole das Modell basierend auf dem Namen
        model = manager.initialize_model(model_name)

        # Baue vollständigen Prompt
        prompt = f"{system_prompt}\n\nLOG:\n{log_text}\n\nANALYSE:"

        # Generiere Analyse basierend auf dem Modelltyp
        if model_name.lower() == "gpt4all":
            return _analyze_with_gpt4all(model, prompt)
        elif model_name.lower() == "openai":
            return _analyze_with_openai(model, prompt)
        elif model_name.lower() == "gemini":
            return _analyze_with_gemini(model, prompt)
        elif model_name.lower() == "huggingface":
            return _analyze_with_huggingface(model, prompt)
        else:
            return f"Fehler: Nicht unterstützter Modelltyp: {model_name}"

    except ModelInitializationError as e:
        logger.error(f"Modellinitialisierungsfehler: {e}")
        return f"Fehler bei der Initialisierung des Modells: {str(e)}"
    except Exception as e:
        logger.error(f"Fehler bei der Analyse des Logs mit {model_name}: {e}")
        logger.debug(traceback.format_exc())
        return f"Fehler bei der Analyse des Logs: {str(e)}"

def _analyze_with_gpt4all(model, prompt: str) -> str:
    """Generiere Analyse mit GPT4All-Modell."""
    try:
        # Verwende die Chat-Completion-API
        response = model.chat_completion([
            {"role": "system", "content": "Du bist ein hilfreicher KI-Assistent, der sich auf Log-Analyse spezialisiert."},
            {"role": "user", "content": prompt}
        ])

        return response['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"Fehler bei der GPT4All-Analyse: {e}")
        logger.debug(traceback.format_exc())
        raise

def _analyze_with_openai(openai_client, prompt: str) -> str:
    """Generiere Analyse mit OpenAI API."""
    try:
        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher KI-Assistent, der sich auf Log-Analyse spezialisiert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Fehler bei der OpenAI-Analyse: {e}")
        logger.debug(traceback.format_exc())
        raise

def _analyze_with_gemini(genai, prompt: str) -> str:
    """Generiere Analyse mit Google Gemini API."""
    try:
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-pro"))
        response = model.generate_content(prompt)

        return response.text
    except Exception as e:
        logger.error(f"Fehler bei der Gemini-Analyse: {e}")
        logger.debug(traceback.format_exc())
        raise

def _analyze_with_huggingface(model_tuple, prompt: str) -> str:
    """Generiere Analyse mit HuggingFace-Modell."""
    try:
        # Entpacke das Modelltupel
        model, tokenizer, pipeline_model = model_tuple

        # Generiere Text
        response = pipeline_model(
            prompt,
            do_sample=True,
            top_p=0.95,
            temperature=0.7,
            return_full_text=False
        )

        return response[0]['generated_text']
    except Exception as e:
        logger.error(f"Fehler bei der HuggingFace-Analyse: {e}")
        logger.debug(traceback.format_exc())
        raise

if __name__ == "__main__":
    # Einfaches CLI zum Testen des Moduls
    import argparse

    parser = argparse.ArgumentParser(description="AILinux-Modellmanager-CLI")
    parser.add_argument("--list-models", action="store_true", help="Verfügbare Modelle auflisten")
    parser.add_argument("--analyze", type=str, help="Log-Datei analysieren")
    parser.add_argument("--model", type=str, default="gpt4all", help="Zu verwendendes Modell für die Analyse")

    args = parser.parse_args()

    if args.list_models:
        models = get_available_models()
        print("\nVerfügbare AI-Modelle:")
        print("=====================")
        for model in models:
            status = "✓ Verfügbar" if model["available"] else "✗ Nicht verfügbar"
            api_status = ""
            if model["is_api_model"]:
                api_status = "✓ API-Schlüssel gesetzt" if model["has_api_key"] else "✗ API-Schlüssel fehlt"

            print(f"{model['name']} ({model['model_id']}): {status} {api_status}")
        print()

    if args.analyze:
        try:
            with open(args.analyze, 'r') as f:
                log_text = f.read()

            print(f"\nAnalysiere Log mit {args.model}...\n")
            result = analyze_log(log_text, args.model)
            print(result)
            print()
        except FileNotFoundError:
            print(f"Fehler: Datei nicht gefunden: {args.analyze}")
        except Exception as e:
            print(f"Fehler: {e}")
