import logging
from flask import Flask, jsonify, request
from ai_model import analyze_log  # Importiere die Funktion zur Log-Analyse

app = Flask(__name__)

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG, filename="backend/backend.log", filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger('Backend')

# Debugging-Route
@app.route('/debug', methods=['POST'])
def debug():
    try:
        log_text = request.json.get('log')
        model_name = request.json.get('model', 'gpt4all')  # Standardmäßig gpt4all verwenden

        if not log_text:
            logger.error("Kein Logtext bereitgestellt")
            return jsonify({"error": "Kein Log erhalten"}), 400

        logger.info(f"Erhaltenes Log zur Analyse: {log_text}")

        # Log-Übersetzung, falls erforderlich
        translated_log = translate_log(log_text)
        response = analyze_log(translated_log, model_name)

        # Logge die Antwort des KI-Modells
        logger.debug(f"Antwort vom KI-Modell: {response}")

        # Antwort zurückgeben
        return jsonify({"analysis": response})
    except Exception as e:
        logger.exception("Fehler im Debug-Endpunkt")
        return jsonify({"error": str(e)}), 500

def translate_log(log_text):
    # Hier könnte Log-Übersetzungs- oder Vereinfachungslogik eingefügt werden
    return log_text  # Einfaches Zurückgeben des Logtexts für Debugging

if __name__ == "__main__":
    logger.info("Starte den Backend-Server...")
    app.run(host='0.0.0.0', port=8081, debug=True)
