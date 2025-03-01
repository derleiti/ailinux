"""Hugging module for AILinux.

This module provides functionality for searching and using Hugging Face models.
"""
import os
from huggingface_hub import HfApi
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

# Get HuggingFace API key from environment variable
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')

# Initialize API with token if available
api = HfApi(token=HUGGINGFACE_API_KEY if HUGGINGFACE_API_KEY else None)

def search_models_by_category(category):
    """Search models by category.
    
    Args:
        category: The model category to search for
        
    Returns:
        List of models in the specified category
    """
    # Use global api instance with API key already set
    try:
        models = api.list_models(filter={"task": category})
        return models
    except Exception as e:
        print(f"Error querying models: {e}")
        return []

def search_models_by_text(query):
    """Search models using keywords.
    
    Args:
        query: The search query text
        
    Returns:
        List of models matching the query
    """
    # Use global api instance with API key already set
    try:
        models = api.list_models(search=query)
        return models
    except Exception as e:
        print(f"Error querying models: {e}")
        return []

def download_and_use_model(model_name):
    """Download and use a model.
    
    Args:
        model_name: The name of the model to download
    """
    try:
        # Use API token when loading model
        model = pipeline("text-generation", 
                        model=model_name, 
                        token=HUGGINGFACE_API_KEY)
        
        print(f"Model {model_name} loaded. Example text: ")
        print(model("Hello, this is a test."))
        
        # Provide status about API key
        if HUGGINGFACE_API_KEY:
            print("Using Hugging Face API key for authentication")
        else:
            print("Warning: No Hugging Face API key provided. Some models may not be accessible.")
            
    except Exception as e:
        print(f"Error loading model {model_name}: {e}")

def main():
    """Main function to run the Hugging Face app."""
    print("Welcome to the Hugging Face App!")
    print("1. Search models by category")
    print("2. Search models by text")
    print("3. Install and use a model")
    choice = input("Choose an option: ")

    if choice == "1":
        category = input("Enter category (e.g. text-classification, text-generation): ")
        models = search_models_by_category(category)
        if models:
            print(f"Models found in category '{category}':")
            for model in models:
                print(model.modelId)
        else:
            print("No models found.")

    elif choice == "2":
        query = input("Enter a keyword for the model search: ")
        models = search_models_by_text(query)
        if models:
            print(f"Models found for '{query}':")
            for model in models:
                print(model.modelId)
        else:
            print("No models found.")

    elif choice == "3":
        model_name = input("Enter the name of the model to install: ")
        download_and_use_model(model_name)
    else:
        print("Invalid selection. Try again.")

if __name__ == "__main__":
    main()
