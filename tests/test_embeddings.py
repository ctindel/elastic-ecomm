#!/usr/bin/env python3
"""
Test cases for embedding functionality.
"""
import os
import sys
import pytest
import json
from pathlib import Path
from elasticsearch import Elasticsearch

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.embedding import get_text_embedding, get_image_embedding
from app.utils.validation import check_ollama_connection
from app.config.settings import settings

# Skip all tests if Ollama is not available
@pytest.fixture(scope="module")
def check_ollama():
    """Check if Ollama is available."""
    if not check_ollama_connection():
        pytest.skip("Ollama is not available")

@pytest.fixture
def test_image():
    """Fixture for test image."""
    # Create a test image if it doesn't exist
    test_image_path = "data/images/test_school_supply_list.png"
    if not os.path.exists(test_image_path):
        from scripts.generate_test_image import generate_test_image
        test_image_path = generate_test_image()
    return test_image_path

def test_text_embedding_dimensions(check_ollama):
    """Test text embedding dimensions."""
    # Get embedding for a test text
    text = "This is a test text for embedding generation"
    embedding = get_text_embedding(text)
    
    # Check if embedding has the correct dimensions
    assert len(embedding) == settings.TEXT_EMBEDDING_DIMS

def test_image_embedding_dimensions(check_ollama, test_image):
    """Test image embedding dimensions."""
    # Get embedding for the test image
    embedding = get_image_embedding(test_image)
    
    # Check if embedding has the correct dimensions
    assert len(embedding) == settings.IMAGE_EMBEDDING_DIMS

def test_text_embedding_consistency(check_ollama):
    """Test text embedding consistency."""
    # Get embeddings for the same text multiple times
    text = "This is a test text for embedding consistency"
    embedding1 = get_text_embedding(text)
    embedding2 = get_text_embedding(text)
    
    # Check if embeddings are consistent
    assert len(embedding1) == len(embedding2)
    assert all(abs(a - b) < 1e-6 for a, b in zip(embedding1, embedding2))

def test_image_embedding_consistency(check_ollama, test_image):
    """Test image embedding consistency."""
    # Get embeddings for the same image multiple times
    embedding1 = get_image_embedding(test_image)
    embedding2 = get_image_embedding(test_image)
    
    # Check if embeddings are consistent
    assert len(embedding1) == len(embedding2)
    assert all(abs(a - b) < 1e-6 for a, b in zip(embedding1, embedding2))

def test_text_embedding_invalid_input(check_ollama):
    """Test text embedding with invalid input."""
    # Try to get embedding for empty text
    with pytest.raises(Exception):
        get_text_embedding("")

def test_image_embedding_invalid_input(check_ollama):
    """Test image embedding with invalid input."""
    # Try to get embedding for non-existent image
    with pytest.raises(Exception):
        get_image_embedding("nonexistent_image.png")
