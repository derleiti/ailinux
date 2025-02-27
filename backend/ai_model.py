import os
import subprocess
import openai
from llama_cpp import Llama
import google.generativeai as genai

# Load API Keys securely
openai.api_key = os.getenv("OPENAI_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
llama_model_path = os.path.expanduser("~/ailinux/backend/models/llama.bin")  # Model path

# Placeholder URL for downloading the model (replace with the actual URL)
MODEL_URL = "http://example.com/llama-model.bin"  # Replace with your actual model download URL

# Function to download the LLaMA model
def download_model():
    print("Model not found, downloading...")
    command = f"wget --progress=bar:force -O {llama_model_path} {MODEL_URL}"
    
    try:
        # Running the download command and showing the progress
        subprocess.check_call(command, shell=True)
        print("Model downloaded successfully!")
    except subprocess.CalledProcessError as e:
        print("Error downloading model:", e)
        return False

    return True

# Function to initialize LLaMA model
def initialize_llama():
    if not os.path.exists(llama_model_path):
        if not download_model():
            return None
    return Llama(model_path=llama_model_path)

# Function to initialize ChatGPT model
def initialize_chatgpt():
    return openai.api_key is not None  # Returns True if API key is set

# Function to initialize Gemini model
def initialize_gemini():
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        return True
    return False

# AI Models Dictionary
models = {
    "llama": initialize_llama(),
    "chatgpt": initialize_chatgpt(),
    "gemini": initialize_gemini(),
}

# AI Log Analysis Function
def analyze_log(log_text, model_name="chatgpt"):
    if model_name == "chatgpt":
        return chatgpt_response(log_text)
    elif model_name == "llama":
        return llama_response(log_text)
    elif model_name == "gemini":
        return gemini_response(log_text)
    else:
        return "⚠ Fehler: Unbekanntes Modell angegeben!"

# OpenAI ChatGPT API Call
def chatgpt_response(text):
    if not openai.api_key:
        return "⚠ Fehler: Kein OpenAI API-Key gefunden!"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Du bist ein KI-Assistent für Debugging."},
                      {"role": "user", "content": text}]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠ Fehler beim Abrufen von ChatGPT: {str(e)}"

# LLaMA Local Model Call
def llama_response(text):
    llama_model = models["llama"]
    if llama_model:
        try:
            response = llama_model(text)
            return response["choices"][0]["text"].strip()
        except Exception as e:
            return f"⚠ Fehler beim Abrufen von LLaMA: {str(e)}"
    return "⚠ Fehler: LLaMA Modell nicht verfügbar!"

# Gemini AI Call
def gemini_response(text):
    if not gemini_api_key:
        return "⚠ Fehler: Kein Gemini API-Key gefunden!"

    try:
        response = genai.generate_text(prompt=text)
        return response.result.strip()
    except Exception as e:
        return f"⚠ Fehler beim Abrufen von Gemini: {str(e)}"

if __name__ == "__main__":
    log = "Example error log to analyze"
    print(analyze_log(log, model_name="llama"))

