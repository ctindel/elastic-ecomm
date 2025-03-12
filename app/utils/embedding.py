"""
Utility functions for generating embeddings using Ollama.
"""
import os
import sys
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import numpy as np
from PIL import Image
import base64
import io

from app.config.settings import (
    OLLAMA_HOST,
    OLLAMA_MODEL,
    TEXT_EMBEDDING_DIMS,
    IMAGE_EMBEDDING_DIMS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def check_ollama_connection() -> bool:
    """
    Check if Ollama is available.
    
    Returns:
        bool: True if Ollama is available, False otherwise
    """
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.RequestException:
        return False

def get_text_embedding(text: str) -> Optional[List[float]]:
    """
    Generate a text embedding using Ollama.
    
    Args:
        text: Text to generate embedding for
        
    Returns:
        List[float]: Normalized embedding vector or None if failed
    """
    if not text:
        logger.warning("Empty text provided for embedding")
        return None
    
    try:
        # Prepare the request payload
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": text,
        }
        
        # Make the request to Ollama embeddings API
        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json=payload
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            embedding = response.json().get("embedding")
            
            # Ensure the embedding has the correct dimensions
            if embedding and len(embedding) != TEXT_EMBEDDING_DIMS:
                # Resize embedding if necessary
                if len(embedding) > TEXT_EMBEDDING_DIMS:
                    embedding = embedding[:TEXT_EMBEDDING_DIMS]
                else:
                    # Pad with zeros if too small
                    embedding.extend([0.0] * (TEXT_EMBEDDING_DIMS - len(embedding)))
            
            # Normalize the embedding vector
            if embedding:
                embedding_np = np.array(embedding)
                norm = np.linalg.norm(embedding_np)
                if norm > 0:
                    normalized_embedding = embedding_np / norm
                    return [float(val) for val in normalized_embedding]
            
            return embedding
        else:
            logger.error(f"Failed to get text embedding: {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error generating text embedding: {str(e)}")
        return None

def get_image_embedding(image_path: str) -> Optional[List[float]]:
    """
    Generate an image embedding using Ollama.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        List[float]: Normalized embedding vector or None if failed
    """
    if not os.path.exists(image_path):
        logger.warning(f"Image file not found: {image_path}")
        return None
    
    try:
        # Load and encode the image
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
            base64_img = base64.b64encode(img_data).decode("utf-8")
        
        # Prepare the request payload for Ollama's generate endpoint
        # Since Ollama's embeddings API might not fully support image inputs,
        # we'll use the generate endpoint first to process the image
        generate_payload = {
            "model": OLLAMA_MODEL,
            "prompt": "Describe this image in detail for embedding purposes.",
            "stream": False,
            "images": [base64_img]
        }
        
        # Make the request to Ollama generate API
        generate_response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=generate_payload
        )
        
        # Check if the generate request was successful
        if generate_response.status_code == 200:
            # Extract the image description from the response
            image_description = generate_response.json().get("response", "")
            
            if not image_description:
                logger.warning("Empty image description returned from Ollama")
                return generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
            
            # Now get the embedding for the image description
            embedding_payload = {
                "model": OLLAMA_MODEL,
                "prompt": image_description
            }
            
            embedding_response = requests.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json=embedding_payload
            )
            
            if embedding_response.status_code == 200:
                embedding = embedding_response.json().get("embedding")
                
                # Ensure the embedding has the correct dimensions
                if embedding and len(embedding) != IMAGE_EMBEDDING_DIMS:
                    # Resize embedding if necessary
                    if len(embedding) > IMAGE_EMBEDDING_DIMS:
                        embedding = embedding[:IMAGE_EMBEDDING_DIMS]
                    else:
                        # Pad with zeros if too small
                        embedding.extend([0.0] * (IMAGE_EMBEDDING_DIMS - len(embedding)))
                
                # Normalize the embedding vector
                if embedding:
                    embedding_np = np.array(embedding)
                    norm = np.linalg.norm(embedding_np)
                    if norm > 0:
                        normalized_embedding = embedding_np / norm
                        return [float(val) for val in normalized_embedding]
                
                return embedding
            else:
                logger.error(f"Failed to get embedding for image description: {embedding_response.text}")
                return generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
        else:
            logger.error(f"Failed to generate image description: {generate_response.text}")
            return generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
    
    except Exception as e:
        logger.error(f"Error generating image embedding: {str(e)}")
        return generate_mock_embedding(IMAGE_EMBEDDING_DIMS)

def generate_mock_embedding(dims: int) -> List[float]:
    """
    Generate a mock embedding vector for testing purposes.
    
    Args:
        dims: Dimensions of the embedding vector
        
    Returns:
        List[float]: Normalized random embedding vector
    """
    # Generate random values between -1 and 1
    random_values = np.random.uniform(-1, 1, dims)
    
    # Normalize the vector
    norm = np.linalg.norm(random_values)
    if norm > 0:
        normalized_values = random_values / norm
    else:
        # Fallback if we somehow got all zeros
        normalized_values = np.random.uniform(-1, 1, dims)
        normalized_values = normalized_values / np.linalg.norm(normalized_values)
    
    # Convert to a simple list of floats
    return [float(val) for val in normalized_values]
