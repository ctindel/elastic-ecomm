"""
Validation utilities for the E-Commerce Search Demo.
"""
import os
import logging
import requests
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)

def validate_api_keys():
    """
    Validate that all required API keys are present and connections to services are working.
    
    Returns:
        dict: A dictionary with validation results
            {
                "valid": bool,
                "message": str,
                "services": {
                    "openai": bool,
                    "elasticsearch": bool,
                    "ollama": bool
                }
            }
    """
    result = {
        "valid": True,
        "message": "All validations passed",
        "services": {
            "openai": False,
            "elasticsearch": False,
            "ollama": False
        }
    }
    
    # Validate OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        result["valid"] = False
        result["message"] = "OpenAI API key not found. Image-based queries will not work."
        logger.warning(result["message"])
    else:
        result["services"]["openai"] = True
    
    # Validate Elasticsearch connection
    es_host = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
    try:
        es = Elasticsearch(es_host)
        if not es.ping():
            result["valid"] = False
            result["message"] = "Could not connect to Elasticsearch"
            logger.warning(result["message"])
        else:
            result["services"]["elasticsearch"] = True
            logger.info("Successfully connected to Elasticsearch")
    except Exception as e:
        result["valid"] = False
        result["message"] = f"Elasticsearch connection failed: {str(e)}"
        logger.warning(result["message"])
    
    # Validate Ollama connection
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    try:
        response = requests.get(f"{ollama_host}/api/tags")
        if response.status_code != 200:
            result["valid"] = False
            result["message"] = "Could not connect to Ollama"
            logger.warning(result["message"])
        else:
            result["services"]["ollama"] = True
            logger.info("Successfully connected to Ollama")
    except Exception as e:
        result["valid"] = False
        result["message"] = f"Ollama connection failed: {str(e)}"
        logger.warning(result["message"])
    
    return result
