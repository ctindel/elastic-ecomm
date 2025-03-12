#!/usr/bin/env python3
"""
Setup Elasticsearch indices and mappings for the e-commerce search demo
"""
import os
import sys
import json
import logging
import requests
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_INDEX_PRODUCTS,
    ELASTICSEARCH_INDEX_PERSONAS,
    ELASTICSEARCH_INDEX_QUERIES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def create_index(index_name, mapping_file=None):
    """
    Create an Elasticsearch index with the specified mapping
    
    Args:
        index_name: Name of the index to create
        mapping_file: Path to the mapping file (optional)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if index already exists
        response = requests.head(f"{ELASTICSEARCH_HOST}/{index_name}")
        
        if response.status_code == 200:
            logger.info(f"Index {index_name} already exists")
            return True
        
        # Create index with mapping if provided
        if mapping_file and os.path.exists(mapping_file):
            with open(mapping_file, "r") as f:
                mapping = json.load(f)
            
            response = requests.put(
                f"{ELASTICSEARCH_HOST}/{index_name}",
                json=mapping,
                headers={"Content-Type": "application/json"}
            )
        else:
            # Create index without mapping
            response = requests.put(f"{ELASTICSEARCH_HOST}/{index_name}")
        
        if response.status_code in (200, 201):
            logger.info(f"Created index {index_name}")
            return True
        else:
            logger.error(f"Failed to create index {index_name}: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error creating index {index_name}: {str(e)}")
        return False

def create_vectorization_pipeline():
    """
    Create the vectorization pipeline for products
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create the product vectorization pipeline
        product_pipeline = {
            "description": "Pipeline to mark products for vectorization",
            "processors": [
                {
                    "set": {
                        "field": "text_for_vectorization",
                        "value": "{{#name}}{{name}}{{/name}} - {{#description}}{{description}}{{/description}} {{#category}}Category: {{category}}{{/category}} {{#brand}}Brand: {{brand}}{{/brand}}"
                    }
                },
                {
                    "set": {
                        "field": "vectorize",
                        "value": True
                    }
                }
            ]
        }
        
        response = requests.put(
            f"{ELASTICSEARCH_HOST}/_ingest/pipeline/product-vectorization",
            json=product_pipeline,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in (200, 201):
            logger.info("Created product vectorization pipeline")
        else:
            logger.error(f"Failed to create product vectorization pipeline: {response.text}")
            return False
        
        # Create the product image vectorization pipeline
        image_pipeline = {
            "description": "Pipeline to mark product images for vectorization",
            "processors": [
                {
                    "set": {
                        "field": "vectorize",
                        "value": True
                    }
                }
            ]
        }
        
        response = requests.put(
            f"{ELASTICSEARCH_HOST}/_ingest/pipeline/product-image-vectorization",
            json=image_pipeline,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in (200, 201):
            logger.info("Created product image vectorization pipeline")
            return True
        else:
            logger.error(f"Failed to create product image vectorization pipeline: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error creating vectorization pipeline: {str(e)}")
        return False

def main():
    """Main entry point"""
    # Create indices
    mappings_dir = os.path.join(project_root, "docker", "elasticsearch", "mappings")
    
    create_index(
        ELASTICSEARCH_INDEX_PRODUCTS,
        os.path.join(mappings_dir, "products.json")
    )
    
    create_index(
        ELASTICSEARCH_INDEX_PERSONAS,
        os.path.join(mappings_dir, "personas.json")
    )
    
    create_index(ELASTICSEARCH_INDEX_QUERIES)
    
    # Create vectorization pipeline
    create_vectorization_pipeline()
    
    logger.info("Elasticsearch setup complete")

if __name__ == "__main__":
    main()
