#!/usr/bin/env python3
"""
Test cases for Ollama embedding functionality.
"""
import os
import sys
import pytest
import json
import requests
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import settings

def test_ollama_connection():
    """Test connection to Ollama server."""
    try:
        response = requests.get(f"{settings.OLLAMA_API_URL}/api/tags")
        if response.status_code == 200:
            # Check if our model is available
            models = [tag["name"] for tag in response.json()["models"]]
            return settings.OLLAMA_MODEL in models
    except requests.exceptions.RequestException:
        return False
    return False

def test_model_availability():
    """Test if the specified Ollama model is available."""
    assert test_ollama_connection(), f"Ollama model {settings.OLLAMA_MODEL} is not available"

def test_api_url_configuration():
    """Test if Ollama API URL is properly configured."""
    assert settings.OLLAMA_API_URL, "Ollama API URL is not configured"
    assert settings.OLLAMA_API_URL.startswith(("http://", "https://")), "Invalid Ollama API URL format"

def test_model_configuration():
    """Test if Ollama model is properly configured."""
    assert settings.OLLAMA_MODEL, "Ollama model is not configured"
    assert isinstance(settings.OLLAMA_MODEL, str), "Ollama model must be a string"

def test_text_embedding_generation():
    """Test text embedding generation."""
    # Test with a simple text
    text = "This is a test product description for embedding generation"
    embedding = get_text_embedding(text)
    
    # Check if embedding was generated
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    
    # Check if embedding has the expected properties
    assert all(isinstance(x, float) for x in embedding)
    
    # Check if embeddings are normalized (optional)
    embedding_np = np.array(embedding)
    norm = np.linalg.norm(embedding_np)
    assert abs(norm - 1.0) < 0.01  # Should be close to 1.0 if normalized

def test_image_embedding_generation():
    """Test image embedding generation."""
    # Find a test image
    test_image_path = "data/images/test_school_supply_list.png"
    
    # Skip if test image doesn't exist
    if not os.path.exists(test_image_path):
        pytest.skip(f"Test image not found: {test_image_path}")
    
    # Generate embedding
    embedding = get_image_embedding(test_image_path)
    
    # Check if embedding was generated
    assert embedding is not None
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    
    # Check if embedding has the expected properties
    assert all(isinstance(x, float) for x in embedding)

def test_embedding_consistency():
    """Test that the same input produces consistent embeddings."""
    # Test with a simple text
    text = "This is a test product description for embedding generation"
    
    # Generate embeddings twice
    embedding1 = get_text_embedding(text)
    embedding2 = get_text_embedding(text)
    
    # Check if both embeddings were generated
    assert embedding1 is not None
    assert embedding2 is not None
    
    # Check if embeddings are identical
    assert embedding1 == embedding2

def test_different_texts_different_embeddings():
    """Test that different inputs produce different embeddings."""
    # Test with two different texts
    text1 = "This is a test product description for embedding generation"
    text2 = "This is a completely different product description"
    
    # Generate embeddings
    embedding1 = get_text_embedding(text1)
    embedding2 = get_text_embedding(text2)
    
    # Check if both embeddings were generated
    assert embedding1 is not None
    assert embedding2 is not None
    
    # Check if embeddings are different
    assert embedding1 != embedding2

def test_embedding_similarity():
    """Test that similar texts have similar embeddings."""
    # Test with similar texts
    text1 = "Blue cotton t-shirt with short sleeves"
    text2 = "Blue t-shirt made of cotton with short sleeves"
    text3 = "Red leather jacket with zipper"
    
    # Generate embeddings
    embedding1 = get_text_embedding(text1)
    embedding2 = get_text_embedding(text2)
    embedding3 = get_text_embedding(text3)
    
    # Convert to numpy arrays for similarity calculation
    embedding1_np = np.array(embedding1)
    embedding2_np = np.array(embedding2)
    embedding3_np = np.array(embedding3)
    
    # Calculate cosine similarities
    similarity_1_2 = np.dot(embedding1_np, embedding2_np)
    similarity_1_3 = np.dot(embedding1_np, embedding3_np)
    
    # Similar texts should have higher similarity
    assert similarity_1_2 > similarity_1_3

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
