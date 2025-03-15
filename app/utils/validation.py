#!/usr/bin/env python3
import os
import logging
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
