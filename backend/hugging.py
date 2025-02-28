import os
from huggingface_hub import HfApi
from transformers import pipeline, AutoModelForTextGeneration, AutoTokenizer

def search_models_by_category(category):
    """Suche Modelle nach Kategorie."""
    api = HfApi()
    try:
        models = api.list_models(filter={"task": category})
        return models
    except Exception as e:
        print(f"Fehler bei der Modellabfrage: {e}")
        return []

def search_models_by_text(query):
    """Suche Modelle anhand von Schlüsselwörtern."""
    api = HfApi()
    try:
        models = api.list_models(search=query)
        return models
    except Exception as e:
        print(f"Fehler bei der Modellabfrage: {e}")
        return []

def download_and_use_model(model_name):
    """Lädt das Modell herunter und nutzt es."""
    try:
        model = pipeline("text-generation", model=model_name)
        print(f"Model {model_name} geladen. Beispieltext: ")
        print(model("Hello, this is a test."))
    except Exception as e:
        print(f"Fehler beim Laden des Modells {model_name}: {e}")

def main():
    print("Willkommen bei der Hugging Face App!")
    print("1. Suche Modelle nach Kategorie")
    print("2. Suche Modelle nach Text")
    print("3. Installiere und nutze ein Modell")
    choice = input("Wähle eine Option: ")

    if choice == "1":
        category = input("Gib die Kategorie ein (z.B. text-classification, text-generation): ")
        models = search_models_by_category(category)
        if models:
            print(f"Gefundene Modelle in der Kategorie '{category}':")
            for model in models:
                print(model.modelId)
        else:
            print("Keine Modelle gefunden.")
    
    elif choice == "2":
        query = input("Gib ein Schlüsselwort für die Modell-Suche ein: ")
        models = search_models_by_text(query)
        if models:
            print(f"Gefundene Modelle für '{query}':")
            for model in models:
                print(model.modelId)
        else:
            print("Keine Modelle gefunden.")
    
    elif choice == "3":
        model_name = input("Gib den Namen des Modells ein, das du installieren möchtest: ")
        download_and_use_model(model_name)
    else:
        print("Ungültige Auswahl. Versuch es noch einmal.")

if __name__ == "__main__":
    main()
