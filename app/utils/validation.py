#!/usr/bin/env python3
"""
Validation utilities for the E-Commerce Search Demo.
"""
import os
import logging
import requests
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.config.settings import (
    OLLAMA_API_URL,
    OLLAMA_VISION_MODEL,
    VISION_PROVIDER
)

def check_openai_connection():
    """
    Verify that the OpenAI API key is configured and valid.
    
    Returns:
        dict: Status of OpenAI connection with keys:
            - configured: Whether an API key is set
            - api_key_valid: Whether the API key is valid
            - error: Error message if any
    """
    result = {
        "configured": False,
        "api_key_valid": False,
        "error": None
    }
    
    # Check if API key is set
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        result["error"] = "OPENAI_API_KEY environment variable is not set"
        return result
    
    result["configured"] = True
    
    # Verify API key by making a simple request
    try:
        client = openai.OpenAI(api_key=api_key)
        # Make a minimal API call to verify the key
        response = client.models.list()
        result["api_key_valid"] = True
    except Exception as e:
        result["error"] = f"API key validation failed: {str(e)}"
    
    return result

def check_ollama_vision_model():
    """
    Check if Ollama is available and the vision model is installed.
    
    Returns:
        dict: Status of Ollama vision model with keys:
            - available: Whether Ollama is available
            - model_installed: Whether the vision model is installed
            - error: Error message if any
    """
    result = {
        "available": False,
        "model_installed": False,
        "error": None
    }
    
    try:
        # Check if Ollama is running - use /api/tags endpoint which is more reliable
        response = requests.get("http://localhost:11434/api/tags")
        
        if response.status_code != 200:
            result["error"] = f"Ollama API returned status code {response.status_code}"
            return result
        
        # Ollama is available
        result["available"] = True
        
        # Check if the vision model is installed
        models = response.json().get("models", [])
        model_names = [model.get("name", "") for model in models]
        
        if OLLAMA_VISION_MODEL in model_names:
            result["model_installed"] = True
        else:
            # Try with just the model name without tag
            base_model_name = OLLAMA_VISION_MODEL.split(":")[0]
            if any(base_model_name in name for name in model_names):
                result["model_installed"] = True
            else:
                result["error"] = f"Vision model '{OLLAMA_VISION_MODEL}' is not installed"
    
    except Exception as e:
        result["error"] = f"Error connecting to Ollama: {str(e)}"
    
    return result

def check_vision_provider():
    """
    Check if the configured vision provider is available.
    
    Returns:
        dict: Status of vision provider with keys:
            - provider: The configured provider
            - available: Whether the provider is available
            - error: Error message if any
    """
    result = {
        "provider": VISION_PROVIDER,
        "available": False,
        "error": None
    }
    
    if VISION_PROVIDER == "openai":
        # Check OpenAI
        openai_status = check_openai_connection()
        result["available"] = openai_status["configured"] and openai_status["api_key_valid"]
        if not result["available"]:
            result["error"] = openai_status["error"]
    
    elif VISION_PROVIDER == "ollama":
        # Check Ollama
        ollama_status = check_ollama_vision_model()
        result["available"] = ollama_status["available"] and ollama_status["model_installed"]
        if not result["available"]:
            result["error"] = ollama_status["error"]
    
    else:
        result["error"] = f"Unknown vision provider: {VISION_PROVIDER}"
    
    return result
