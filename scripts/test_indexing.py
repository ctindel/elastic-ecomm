#!/usr/bin/env python3
"""
Test script to verify indexing works with the updated approach.
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

from app.config.settings import ELASTICSEARCH_HOST

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_indexing():
    """Test that indexing works with the updated approach."""
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
    
    # Check if the product has vector embeddings
    if "text_embedding" in sample_product:
        logger.warning("Product already has text_embedding field")
    else:
        logger.info("Product does not have text_embedding field as expected")
    
    if "vector_embedding" in sample_product.get("image", {}):
        logger.warning("Product image already has vector_embedding field")
    else:
        logger.info("Product image does not have vector_embedding field as expected")
    
    # Index the sample product
    try:
        # Add a test ID to avoid conflicts
        sample_product["id"] = "test_" + sample_product["id"]
        
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
        return True
    except Exception as e:
        logger.error(f"Failed to index or retrieve product: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_indexing()
    if success:
        logger.info("Indexing test passed")
        sys.exit(0)
    else:
        logger.error("Indexing test failed")
        sys.exit(1)
