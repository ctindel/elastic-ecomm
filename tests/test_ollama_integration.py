#!/usr/bin/env python3
"""
Script to test Ollama integration for embeddings.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.embedding import (
    check_ollama_connection,
    get_text_embedding,
    get_image_embedding
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Test Ollama integration for embeddings."""
    logger.info("Testing Ollama integration for embeddings")
    
    # Check Ollama connection
    logger.info("Checking Ollama connection...")
    if check_ollama_connection():
        logger.info("✅ Successfully connected to Ollama")
    else:
        logger.error("❌ Failed to connect to Ollama")
        return 1
    
    # Test text embedding
    logger.info("Testing text embedding...")
    sample_text = "This is a test product description for embedding generation"
    text_embedding = get_text_embedding(sample_text)
    
    if text_embedding:
        logger.info(f"✅ Successfully generated text embedding with {len(text_embedding)} dimensions")
        logger.info(f"Sample values: {text_embedding[:5]}...")
    else:
        logger.error("❌ Failed to generate text embedding")
        return 1
    
    # Test image embedding
    logger.info("Testing image embedding...")
    # Find a sample image
    image_dir = Path("data/images")
    if not image_dir.exists() or not any(image_dir.iterdir()):
        logger.error("❌ No images found in data/images directory")
        return 1
    
    image_path = next(image_dir.glob("*.png"))
    logger.info(f"Using image: {image_path}")
    
    image_embedding = get_image_embedding(str(image_path))
    
    if image_embedding:
        logger.info(f"✅ Successfully generated image embedding with {len(image_embedding)} dimensions")
        logger.info(f"Sample values: {image_embedding[:5]}...")
    else:
        logger.error("❌ Failed to generate image embedding")
        return 1
    
    logger.info("All tests passed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
