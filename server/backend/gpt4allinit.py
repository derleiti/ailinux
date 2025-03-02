#!/usr/bin/env python3
"""
GPT4All Initialisierungsmodul
Stellt sicher, dass GPT4All korrekt initialisiert wird.
"""
import os
import sys
import logging

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("gpt4all_init.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("gpt4all_init")

# Überprüfen, ob das gpt4all-Paket verfügbar ist
try:
    # Versuche verschiedene Möglichkeiten für den Import
    try:
        # Standardimport
        from gpt4all import GPT4All
        logger.info("gpt4all erfolgreich über Standardimport importiert")
    except ImportError:
        try:
            # Alternativer Import
            from gpt4all.gpt4all import GPT4All
            logger.info("gpt4all erfolgreich über alternativen Import importiert")
        except ImportError:
            logger.error("gpt4all-Paket nicht gefunden. Installiere es mit: pip install gpt4all")
            print("gpt4all-Paket nicht gefunden. Installiere es mit: pip install gpt4all")
            sys.exit(1)
except Exception as e:
    logger.error(f"Unerwarteter Fehler beim Import von gpt4all: {e}")
    print(f"Unerwarteter Fehler beim Import von gpt4all: {e}")
    sys.exit(1)

def initialize_model(model_path=None):
    """
    Initialisiere ein GPT4All-Modell mit Fehlerbehandlung.

    Args:
        model_path: Pfad zur Modelldatei. Wenn None, wird der Standardpfad verwendet.

    Returns:
        Initialisiertes GPT4All-Modell oder None bei Fehler
    """
    try:
        # Standardpfad für das Modell
        if model_path is None:
            model_path = os.getenv("LLAMA_MODEL_PATH", "Meta-Llama-3-8B-Instruct.Q4_0.gguf")
            
        # Stelle sicher, dass der Pfad absolut ist
        if not os.path.isabs(model_path):
            models_dir = os.getenv("MODELS_CACHE_DIR", "./models")
            model_path = os.path.join(os.path.abspath(models_dir), model_path)
            
        # Stelle sicher, dass das Modellverzeichnis existiert
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
        logger.info(f"Initialisiere GPT4All mit Modell: {model_path}")
        
        # Überprüfe, ob die Modelldatei existiert
        if not os.path.exists(model_path):
            logger.warning(f"Modelldatei nicht gefunden: {model_path}")
            logger.info("Das Modell wird automatisch heruntergeladen, wenn es nicht existiert.")
            
        # Initialisiere das Modell
        model = GPT4All(model_path)
        logger.info("GPT4All-Modell erfolgreich initialisiert")
        
        return model
    except Exception as e:
        logger.error(f"Fehler bei der Initialisierung des GPT4All-Modells: {e}")
        return None

def test_model(model):
    """
    Teste das initialisierte Modell mit einer einfachen Anfrage.

    Args:
        model: Das zu testende GPT4All-Modell

    Returns:
        True bei erfolgreicher Ausführung, False bei Fehler
    """
    if model is None:
        logger.error("Kein Modell zum Testen bereitgestellt")
        return False
        
    try:
        logger.info("Teste GPT4All-Modell mit einer einfachen Anfrage...")
        
        # Einfache Testanfrage
        response = model.chat_completion([
            {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
            {"role": "user", "content": "Hallo! Was ist heute für ein Tag?"}
        ])
        
        if response and 'choices' in response and len(response['choices']) > 0:
            logger.info("Modelltest erfolgreich!")
            return True
        else:
            logger.error("Modelltest fehlgeschlagen: Unerwartete Antwortstruktur")
            return False
            
    except Exception as e:
        logger.error(f"Fehler beim Testen des Modells: {e}")
        return False

if __name__ == "__main__":
    # Wenn dieses Skript direkt ausgeführt wird, initialisiere und teste das Modell
    custom_model_path = None
    if len(sys.argv) > 1:
        custom_model_path = sys.argv[1]
        
    model = initialize_model(custom_model_path)
    
    if model:
        success = test_model(model)
        sys.exit(0 if success else 1)
    else:
        sys.exit(1)
