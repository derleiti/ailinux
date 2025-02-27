import logging
from flask import Flask, jsonify, request
from ai_model import analyze_log  # Placeholder function to analyze logs with AI

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename="backend/backend.log", filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger('Backend')

# Debugging route
@app.route('/debug', methods=['POST'])
def debug():
    try:
        log_text = request.json.get('log')
        model_name = request.json.get('model', 'chatgpt')
        
        if not log_text:
            logger.error("No log text provided")
            return jsonify({"error": "No log received"}), 400
        
        logger.info(f"Received log for analysis: {log_text}")
        
        # Log translation if necessary
        translated_log = translate_log(log_text)
        response = analyze_log(translated_log, model_name)
        
        # Log the AI's response
        logger.debug(f"AI Model Response: {response}")
        
        # Return the response
        return jsonify({"analysis": response})
    except Exception as e:
        logger.exception("Error in the debug endpoint")
        return jsonify({"error": str(e)}), 500

def translate_log(log_text):
    # Your translation or simplification logic
    return log_text  # Simple return for debugging

if __name__ == "__main__":
    logger.info("Starting the backend server...")
    app.run(host='0.0.0.0', port=8081, debug=True)
