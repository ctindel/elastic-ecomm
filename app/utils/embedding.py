#!/usr/bin/env python3
"""
Embedding utilities for the E-Commerce Search Demo.
"""
import os
import sys
import json
import logging
import requests
import base64
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from app.config.settings import (
    OLLAMA_MODEL,
    OLLAMA_API_URL,
    TEXT_EMBEDDING_DIMS,
    IMAGE_EMBEDDING_DIMS
)

def check_ollama_connection():
    """
    Check if Ollama is available.
    
    Returns:
        bool: True if Ollama is available, False otherwise
    """
    try:
        response = requests.get(OLLAMA_API_URL.replace("/generate", "/models"))
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error connecting to Ollama: {str(e)}")
        return False

def get_text_embedding(text):
    """
    Get text embedding from Ollama.
    
    Args:
        text: Text to embed
    
    Returns:
        list: Text embedding
    """
    try:
        # Call Ollama API
        response = requests.post(
            OLLAMA_API_URL.replace("/generate", "/embeddings"),
            json={
                "model": OLLAMA_MODEL,
                "prompt": text
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error calling Ollama API: {response.text}")
            return generate_mock_embedding(TEXT_EMBEDDING_DIMS)
        
        # Parse response
        result = response.json()
        embedding = result.get("embedding", [])
        
        return embedding
    
    except Exception as e:
        logger.error(f"Error getting text embedding: {str(e)}")
        return generate_mock_embedding(TEXT_EMBEDDING_DIMS)

def get_image_embedding(image_path):
    """
    Get image embedding from Ollama.
    
    Args:
        image_path: Path to image file
    
    Returns:
        list: Image embedding
    """
    try:
        # Read image file
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Encode image data as base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        # Call Ollama API
        response = requests.post(
            OLLAMA_API_URL.replace("/generate", "/embeddings"),
            json={
                "model": OLLAMA_MODEL,
                "prompt": f"<img src=\"data:image/jpeg;base64,{image_base64}\">"
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error calling Ollama API: {response.text}")
            return generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
        
        # Parse response
        result = response.json()
        embedding = result.get("embedding", [])
        
        return embedding
    
    except Exception as e:
        logger.error(f"Error getting image embedding: {str(e)}")
        return generate_mock_embedding(IMAGE_EMBEDDING_DIMS)

def generate_mock_embedding(dims):
    """
    Generate a mock embedding for testing.
    
    Args:
        dims: Embedding dimensions
    
    Returns:
        list: Mock embedding
    """
    import numpy as np
    
    # Generate random embedding
    embedding = np.random.normal(0, 1, dims).tolist()
    
    # Normalize embedding
    norm = np.linalg.norm(embedding)
    embedding = [x / norm for x in embedding]
    
    return embedding
