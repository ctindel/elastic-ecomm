#!/usr/bin/env python3
"""
Direct ingestion script for products into Elasticsearch
"""
import os
import sys
import json
import logging
import requests
import random
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_INDEX_PRODUCTS,
    TEXT_EMBEDDING_DIMS,
    IMAGE_EMBEDDING_DIMS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def generate_mock_embedding(dims):
    """Generate a mock embedding vector"""
    return [random.uniform(-1, 1) for _ in range(dims)]

def ingest_products(products_file):
    """Ingest products directly into Elasticsearch"""
    try:
        # Load products from file
        with open(products_file, "r") as f:
            products = json.load(f)
        
        logger.info(f"Loaded {len(products)} products from {products_file}")
        
        # Prepare bulk actions
        bulk_actions = []
        
        for product in products:
            # Generate text embedding
            text_embedding = generate_mock_embedding(TEXT_EMBEDDING_DIMS)
            product["text_embedding"] = text_embedding
            
            # Generate image embedding
            image_embedding = generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
            if "image" not in product:
                product["image"] = {}
            product["image"]["vector_embedding"] = image_embedding
            
            # Add to bulk actions
            bulk_actions.append({"index": {"_index": ELASTICSEARCH_INDEX_PRODUCTS, "_id": product["id"]}})
            bulk_actions.append(product)
        
        # Send bulk request
        bulk_data = "\n".join([json.dumps(action) for action in bulk_actions]) + "\n"
        
        response = requests.post(
            f"{ELASTICSEARCH_HOST}/_bulk",
            headers={"Content-Type": "application/x-ndjson"},
            data=bulk_data
        )
        
        if response.status_code != 200:
            logger.error(f"Error ingesting products: {response.text}")
            return False
        
        # Check for errors in response
        response_data = response.json()
        if response_data.get("errors", False):
            logger.error(f"Errors in bulk ingestion: {response_data}")
            return False
        
        logger.info(f"Successfully ingested {len(products)} products into Elasticsearch")
        return True
    
    except Exception as e:
        logger.error(f"Error ingesting products: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest products directly into Elasticsearch")
    parser.add_argument("--products-file", required=True, help="Path to products JSON file")
    
    args = parser.parse_args()
    
    ingest_products(args.products_file)
