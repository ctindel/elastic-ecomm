#!/usr/bin/env python3
"""
Embedding utilities for the E-Commerce Search Demo.
"""
import os
import sys
import json
import time
import random
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
    Get text embedding from Ollama with TRUE infinite retry.
    
    Args:
        text: Text to embed
    
    Returns:
        list: Text embedding
    """
    retry_delay = 5
    max_delay = 60
    retries = 0
    
    while True:  # True infinite retry - will never give up
        try:
            # Call Ollama API
            response = requests.post(
                OLLAMA_API_URL.replace("/generate", "/embeddings"),
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": text
                }
            )
            
            if response.status_code == 200:
                # Parse response
                result = response.json()
                embedding = result.get("embedding", [])
                if retries > 0:
                    logger.info(f"Successfully generated text embedding after {retries} retries")
                return embedding
            else:
                retries += 1
                logger.error(f"Error calling Ollama API: {response.text}")
                # Calculate delay with exponential backoff and jitter, capped at max_delay
                import random
                delay = min(retry_delay * (2 ** (retries - 1)) * (0.5 + random.random()), max_delay)
                logger.error(f"Ollama is not available. Retrying text embedding generation (attempt {retries}, waiting {delay:.2f}s)")
                time.sleep(delay)
        
        except Exception as e:
            retries += 1
            logger.error(f"Error getting text embedding: {str(e)}")
            # Calculate delay with exponential backoff and jitter, capped at max_delay
            import random
            delay = min(retry_delay * (2 ** (retries - 1)) * (0.5 + random.random()), max_delay)
            logger.error(f"Ollama is not available. Retrying text embedding generation (attempt {retries}, waiting {delay:.2f}s)")
            time.sleep(delay)

def get_image_embedding(image_path):
    """
    Get image embedding from Ollama with TRUE infinite retry.
    
    Args:
        image_path: Path to image file
    
    Returns:
        list: Image embedding
    """
    retry_delay = 5
    max_delay = 60
    retries = 0
    
    # Read image file
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Encode image data as base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
    except Exception as e:
        logger.error(f"Error reading image file {image_path}: {str(e)}")
        raise  # Re-raise the exception as we can't proceed without the image data
    
    while True:  # True infinite retry - will never give up
        try:
            # Call Ollama API
            response = requests.post(
                OLLAMA_API_URL.replace("/generate", "/embeddings"),
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": f"<img src=\"data:image/jpeg;base64,{image_base64}\">"
                }
            )
            
            if response.status_code == 200:
                # Parse response
                result = response.json()
                embedding = result.get("embedding", [])
                if retries > 0:
                    logger.info(f"Successfully generated image embedding after {retries} retries")
                return embedding
            else:
                retries += 1
                logger.error(f"Error calling Ollama API: {response.text}")
                # Calculate delay with exponential backoff and jitter, capped at max_delay
                delay = min(retry_delay * (2 ** (retries - 1)) * (0.5 + random.random()), max_delay)
                logger.error(f"Ollama is not available. Retrying image embedding generation (attempt {retries}, waiting {delay:.2f}s)")
                time.sleep(delay)
        
        except Exception as e:
            retries += 1
            logger.error(f"Error getting image embedding: {str(e)}")
            # Calculate delay with exponential backoff and jitter, capped at max_delay
            delay = min(retry_delay * (2 ** (retries - 1)) * (0.5 + random.random()), max_delay)
            logger.error(f"Ollama is not available. Retrying image embedding generation (attempt {retries}, waiting {delay:.2f}s)")
            time.sleep(delay)

# Mock embedding generation has been removed to ensure we always use real embeddings from Ollama
# with true infinite retry until Ollama becomes available
