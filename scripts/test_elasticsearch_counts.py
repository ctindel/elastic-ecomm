#!/usr/bin/env python3
"""
Test script to count documents and vector embeddings in Elasticsearch
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
    ELASTICSEARCH_INDEX_PRODUCTS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def count_documents():
    """Count the total number of documents in the products index"""
    try:
        response = requests.get(f"{ELASTICSEARCH_HOST}/{ELASTICSEARCH_INDEX_PRODUCTS}/_count")
        
        if response.status_code != 200:
            logger.error(f"Error counting documents: {response.text}")
            return 0
        
        count = response.json().get("count", 0)
        logger.info(f"Found {count} products in Elasticsearch")
        return count
    
    except Exception as e:
        logger.error(f"Error counting documents: {str(e)}")
        return 0

def count_documents_with_vectors():
    """Count the number of documents with vector embeddings"""
    try:
        # Query for documents with text embeddings
        query = {
            "query": {
                "exists": {
                    "field": "text_embedding"
                }
            }
        }
        
        response = requests.post(
            f"{ELASTICSEARCH_HOST}/{ELASTICSEARCH_INDEX_PRODUCTS}/_count",
            json=query,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.error(f"Error counting documents with vectors: {response.text}")
            return 0
        
        count = response.json().get("count", 0)
        logger.info(f"Found {count} products with text embeddings")
        return count
    
    except Exception as e:
        logger.error(f"Error counting documents with vectors: {str(e)}")
        return 0

def main():
    """Main entry point"""
    # Count documents
    total_docs = count_documents()
    
    # Count documents with vectors
    vector_docs = count_documents_with_vectors()
    
    # Calculate percentage
    percentage = (vector_docs / total_docs * 100) if total_docs > 0 else 0
    
    # Print results
    print("\nElasticsearch Document Counts:")
    print(f"Total documents: {total_docs}")
    print(f"Documents with vector embeddings: {vector_docs}")
    print(f"Percentage with vector embeddings: {percentage:.2f}%")

if __name__ == "__main__":
    main()
