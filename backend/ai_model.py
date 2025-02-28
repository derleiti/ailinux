import openai
from gpt4all import GPT4All

# Funktion zur Initialisierung von GPT4All (Offline-Modell)
def initialize_gpt4all():
    model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")  # Beispiel für ein GPT4All Modell
    return model

# Funktion zur Initialisierung von ChatGPT (Online-API)
def initialize_chatgpt():
    openai.api_key = "DEIN_OPENAI_API_KEY"  # API-Key für ChatGPT (oder aus Umgebungsvariablen)
    return openai.api_key is not None

# Funktion zur Auswahl des Modells
def get_model(model_name="gpt4all"):
    if model_name == "gpt4all":
        return initialize_gpt4all()
    elif model_name == "chatgpt" and initialize_chatgpt():
        return openai
    else:
        raise ValueError("Unbekanntes Modell oder Fehler bei der API-Initialisierung")

# Funktion zur Analyse des Logs mit dem gewählten Modell
def analyze_log(log_text, model_name="gpt4all"):
    model = get_model(model_name)
    if model_name == "gpt4all":
        return gpt4all_response(log_text)
    elif model_name == "chatgpt":
        return chatgpt_response(log_text)
    else:
        return "⚠ Fehler: Unbekanntes Modell angegeben!"

# GPT4All Antwort (Offline-Modell)
def gpt4all_response(text):
    model = initialize_gpt4all()
    try:
        response = model.chat(text)  # Antwort vom Modell
        return response["choices"][0]["text"].strip()
    except Exception as e:
        return f"⚠ Fehler beim Abrufen von GPT4All: {str(e)}"

# ChatGPT Antwort (Online-API)
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
