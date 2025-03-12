#!/usr/bin/env python3
"""
Script to test Ollama embeddings functionality.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.embedding import (
    check_ollama_connection,
    get_text_embedding,
    get_image_embedding,
    generate_mock_embedding
)
from app.config.settings import TEXT_EMBEDDING_DIMS, IMAGE_EMBEDDING_DIMS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_ollama_connection():
    """Test connection to Ollama server."""
    logger.info("Testing Ollama connection...")
    if check_ollama_connection():
        logger.info("✅ Successfully connected to Ollama")
        return True
    else:
        logger.error("❌ Failed to connect to Ollama")
        return False

def test_text_embedding():
    """Test text embedding generation."""
    logger.info("Testing text embedding generation...")
    
    # Test with a sample text
    sample_text = "This is a test text for embedding generation using Ollama"
    embedding = get_text_embedding(sample_text)
    
    if embedding is None:
        logger.error("❌ Failed to generate text embedding")
        return False
    
    # Check embedding dimensions
    if len(embedding) != TEXT_EMBEDDING_DIMS:
        logger.error(f"❌ Text embedding has incorrect dimensions: {len(embedding)} (expected {TEXT_EMBEDDING_DIMS})")
        return False
    
    logger.info(f"✅ Successfully generated text embedding with {len(embedding)} dimensions")
    logger.info(f"Sample values: {embedding[:5]}...")
    return True

def test_image_embedding():
    """Test image embedding generation."""
    logger.info("Testing image embedding generation...")
    
    # Find a sample image from the data directory
    data_dir = Path("data/images")
    if not data_dir.exists() or not any(data_dir.iterdir()):
        logger.error("❌ No images found in data/images directory")
        return False
    
    # Get the first image file
    image_file = next(data_dir.glob("*.png"))
    logger.info(f"Using image file: {image_file}")
    
    # Generate embedding
    embedding = get_image_embedding(str(image_file))
    
    if embedding is None:
        logger.error("❌ Failed to generate image embedding")
        return False
    
    # Check embedding dimensions
    if len(embedding) != IMAGE_EMBEDDING_DIMS:
        logger.error(f"❌ Image embedding has incorrect dimensions: {len(embedding)} (expected {IMAGE_EMBEDDING_DIMS})")
        return False
    
    logger.info(f"✅ Successfully generated image embedding with {len(embedding)} dimensions")
    logger.info(f"Sample values: {embedding[:5]}...")
    return True

def main():
    """Main function to test Ollama embeddings."""
    logger.info("Starting Ollama embeddings test")
    
    # Test Ollama connection
    if not test_ollama_connection():
        logger.error("Ollama connection test failed. Exiting.")
        return 1
    
    # Test text embedding
    if not test_text_embedding():
        logger.error("Text embedding test failed.")
        return 1
    
    # Test image embedding
    if not test_image_embedding():
        logger.error("Image embedding test failed.")
        return 1
    
    logger.info("All tests passed successfully!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
