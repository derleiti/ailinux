import os
import sys
import logging
from flask import Flask, jsonify, request
from ai_model import analyze_log  # The function to interact with your AI models

app = Flask(__name__)

# Logging Configuration
LOG_FILE = "system.log"
DEBUG_LOG_FILE = "debug_history.log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

# Human-readable log translation (simplification)
def translate_log(log_text):
    # Here, you can implement any log translation logic, for example:
    log_text = log_text.replace("ERROR", "Problem")
    log_text = log_text.replace("WARN", "Warning")
    log_text = log_text[:200]  # Limit log size for readability
    return log_text

# Log and AI Debugging Endpoint
@app.route('/debug', methods=['POST'])
def debug():
    log_text = request.json.get("log")
    model_name = request.json.get("model", "chatgpt")

    if not log_text:
        return jsonify({"error": "No log received"}), 400

    # Translate or simplify the log for better AI recognition
    translated_log = translate_log(log_text)
    response = analyze_log(translated_log, model_name).strip()

    # Save the log and its AI response for debugging history
    with open(DEBUG_LOG_FILE, "a") as log_file:
        log_file.write(f"Log: {log_text}\nAI Response ({model_name}): {response}\n\n")

    return jsonify({"analysis": response})

# System Log Retrieval
@app.route('/logs', methods=['GET'])
def get_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as log_file:
            logs = log_file.read()
        return jsonify({"logs": logs})
    return jsonify({"error": "Logfile not found"}), 404

# Start Flask Server
if __name__ == "__main__":
    print("📢 Flask-Backend starting on port 8081...")
    try:
        app.run(host='0.0.0.0', port=8081, debug=False)
    except KeyboardInterrupt:
        print("Flask server stopped.")
    except Exception as e:
        print(f"Error while starting: {e}")
