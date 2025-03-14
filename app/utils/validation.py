#!/usr/bin/env python3
"""
Validation utilities for the E-Commerce Search Demo.
"""
import os
import sys
import json
import logging
import requests
from elasticsearch import Elasticsearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    OLLAMA_API_URL,
    OPENAI_API_KEY,
    OPENAI_API_URL
)

def validate_api_keys():
    """
    Validate API keys and connections.
    
    Raises:
        Exception: If Elasticsearch or Ollama connection fails
    """
    # Check Elasticsearch connection
    try:
        es = Elasticsearch(ELASTICSEARCH_HOST)
        if not es.ping():
            raise Exception("Elasticsearch connection failed")
    except Exception as e:
        logger.error(f"Elasticsearch connection failed: {str(e)}")
        raise Exception(f"Elasticsearch connection failed: {str(e)}")
    
    # Check Ollama connection
    try:
        response = requests.get(OLLAMA_API_URL.replace("/generate", "/models"))
        if response.status_code != 200:
            raise Exception("Ollama connection failed")
    except Exception as e:
        logger.error(f"Ollama connection failed: {str(e)}")
        raise Exception(f"Ollama connection failed: {str(e)}")
    
    # Check OpenAI API key
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API key is missing")
    
    return True

def check_openai_connection():
    """
    Check if OpenAI API is available and the API key is valid.
    
    Returns:
        dict: Status information including connectivity and API key validity
    """
    status = {
        "configured": bool(OPENAI_API_KEY),
        "connected": False,
        "api_key_valid": False,
        "models_available": [],
        "error": None
    }
    
    # If API key is not configured, return early
    if not OPENAI_API_KEY:
        status["error"] = "API key not configured"
        return status
    
    try:
        # Test API connectivity with a simple models list request
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        response = requests.get(
            f"{OPENAI_API_URL}/models",
            headers=headers
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            status["connected"] = True
            status["api_key_valid"] = True
            
            # Get available models
            result = response.json()
            models = result.get("data", [])
            status["models_available"] = [model.get("id") for model in models]
            
        elif response.status_code == 401:
            # Unauthorized - API key is invalid
            status["connected"] = True
            status["api_key_valid"] = False
            status["error"] = "Invalid API key"
            
        else:
            # Other error
            status["connected"] = True
            status["api_key_valid"] = False
            status["error"] = f"API error: {response.status_code} - {response.text}"
    
    except requests.exceptions.ConnectionError:
        # Connection error
        status["error"] = "Connection error"
    
    except Exception as e:
        # Other exception
        status["error"] = str(e)
    
    return status
