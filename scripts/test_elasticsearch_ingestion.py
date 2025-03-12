#!/usr/bin/env python3
"""
Test script to verify the Elasticsearch ingestion pipeline with Ollama embeddings.
"""
import os
import sys
import json
import logging
from pathlib import Path
from elasticsearch import Elasticsearch

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import ELASTICSEARCH_HOST, TEXT_EMBEDDING_DIMS, IMAGE_EMBEDDING_DIMS
from app.utils.embedding import get_text_embedding, get_image_embedding, generate_mock_embedding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_elasticsearch_ingestion():
    """Test the Elasticsearch ingestion pipeline with Ollama embeddings."""
    # Connect to Elasticsearch
    try:
        es = Elasticsearch(ELASTICSEARCH_HOST)
        
        # Check connection
        if not es.ping():
            logger.error("Could not connect to Elasticsearch. Make sure it's running.")
            return False
        
        logger.info("Successfully connected to Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
        return False
    
    # Load a sample product
    with open("data/products.json", "r") as f:
        products = json.load(f)
    
    if not products:
        logger.error("No products found in data/products.json")
        return False
    
    # Get a sample product
    sample_product = products[0]
    logger.info(f"Testing with product: {sample_product['name']}")
    
    # Check if the product has vector embeddings
    if "text_embedding" in sample_product:
        logger.warning("Product already has text_embedding field")
    else:
        logger.info("Product does not have text_embedding field as expected")
    
    if "vector_embedding" in sample_product.get("image", {}):
        logger.warning("Product image already has vector_embedding field")
    else:
        logger.info("Product image does not have vector_embedding field as expected")
    
    # Generate embeddings for the product
    logger.info("Generating embeddings for the product")
    
    # Generate text embedding
    text_content = f"{sample_product['name']} {sample_product['description']}"
    text_embedding = get_text_embedding(text_content)
    
    # If Ollama fails, use mock embedding
    if text_embedding is None:
        logger.warning("Using mock text embedding")
        text_embedding = generate_mock_embedding(TEXT_EMBEDDING_DIMS)
    
    # Add text embedding to the product
    sample_product["text_embedding"] = text_embedding
    
    # Generate image embedding
    image_path = sample_product["image"]["url"]
    if os.path.exists(image_path):
        image_embedding = get_image_embedding(image_path)
        
        # If Ollama fails, use mock embedding
        if image_embedding is None:
            logger.warning("Using mock image embedding")
            image_embedding = generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
    else:
        logger.warning(f"Image not found at {image_path}, using mock embedding")
        image_embedding = generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
    
    # Add image embedding to the product
    sample_product["image"]["vector_embedding"] = image_embedding
    
    # Index the sample product
    try:
        # Add a test ID to avoid conflicts
        sample_product["id"] = "test_ingestion_" + sample_product["id"]
        
        # Index the product
        es.index(index="products", id=sample_product["id"], document=sample_product)
        logger.info(f"Successfully indexed product {sample_product['id']}")
        
        # Retrieve the product
        indexed_product = es.get(index="products", id=sample_product["id"])
        logger.info(f"Successfully retrieved product {sample_product['id']}")
        
        # Check if the product has the expected fields
        source = indexed_product["_source"]
        if "text_embedding" not in source:
            logger.error("Indexed product does not have text_embedding field")
            return False
        
        if "vector_embedding" not in source.get("image", {}):
            logger.error("Indexed product does not have image.vector_embedding field")
            return False
        
        logger.info("Indexed product has all expected fields")
        
        # Check if the embeddings are the expected length
        text_embedding_length = len(source["text_embedding"])
        if text_embedding_length != TEXT_EMBEDDING_DIMS:
            logger.error(f"Text embedding has incorrect dimensions: {text_embedding_length} (expected {TEXT_EMBEDDING_DIMS})")
            return False
        
        image_embedding_length = len(source["image"]["vector_embedding"])
        if image_embedding_length != IMAGE_EMBEDDING_DIMS:
            logger.error(f"Image embedding has incorrect dimensions: {image_embedding_length} (expected {IMAGE_EMBEDDING_DIMS})")
            return False
        
        logger.info(f"Text embedding dimensions: {text_embedding_length}")
        logger.info(f"Image embedding dimensions: {image_embedding_length}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to index or retrieve product: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_elasticsearch_ingestion()
    if success:
        logger.info("Elasticsearch ingestion test passed")
        sys.exit(0)
    else:
        logger.error("Elasticsearch ingestion test failed")
        sys.exit(1)
