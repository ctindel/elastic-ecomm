#!/usr/bin/env python3
"""
Script to set up Elasticsearch indices with proper mappings.
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from elasticsearch import Elasticsearch, exceptions

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_INDEX_PRODUCTS,
    ELASTICSEARCH_INDEX_PERSONAS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def wait_for_elasticsearch(es: Elasticsearch, max_retries=10, delay=5):
    """
    Wait for Elasticsearch to become available.
    
    Args:
        es: Elasticsearch client
        max_retries: Maximum number of connection attempts
        delay: Delay between attempts in seconds
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    for i in range(max_retries):
        try:
            if es.ping():
                logger.info("Successfully connected to Elasticsearch")
                return True
            else:
                logger.warning(f"Elasticsearch ping failed (attempt {i+1}/{max_retries})")
        except exceptions.ConnectionError:
            logger.warning(f"Elasticsearch connection error (attempt {i+1}/{max_retries})")
        
        time.sleep(delay)
    
    logger.error("Failed to connect to Elasticsearch after multiple attempts")
    return False

def create_index(es: Elasticsearch, index_name: str, mapping_file: str):
    """
    Create an Elasticsearch index with the specified mapping.
    
    Args:
        es: Elasticsearch client
        index_name: Name of the index to create
        mapping_file: Path to the mapping file
    """
    try:
        # Check if index already exists
        if es.indices.exists(index=index_name):
            logger.info(f"Index {index_name} already exists, deleting it")
            es.indices.delete(index=index_name)
        
        # Load mapping from file
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        
        # Create index with mapping
        es.indices.create(index=index_name, body=mapping)
        logger.info(f"Successfully created index {index_name}")
    
    except Exception as e:
        logger.error(f"Error creating index {index_name}: {str(e)}")
        raise

def main():
    """Main function to set up Elasticsearch indices."""
    logger.info("Starting Elasticsearch setup")
    
    # Connect to Elasticsearch
    es = Elasticsearch(ELASTICSEARCH_HOST)
    
    # Wait for Elasticsearch to become available
    if not wait_for_elasticsearch(es):
        logger.error("Elasticsearch is not available. Exiting.")
        return
    
    # Get mapping file paths
    docker_dir = Path(__file__).parent.parent / "docker" / "elasticsearch" / "mappings"
    products_mapping = str(docker_dir / "products.json")
    personas_mapping = str(docker_dir / "personas.json")
    
    # Create indices
    create_index(es, ELASTICSEARCH_INDEX_PRODUCTS, products_mapping)
    create_index(es, ELASTICSEARCH_INDEX_PERSONAS, personas_mapping)
    
    logger.info("Elasticsearch setup complete")

if __name__ == "__main__":
    main()
