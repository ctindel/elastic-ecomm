#!/usr/bin/env python3
"""
Test script to check Elasticsearch document and vector counts
"""
import os
import sys
import json
import requests
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_INDEX_PRODUCTS,
    TEXT_EMBEDDING_DIMS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def check_elasticsearch_document_count():
    """Check the number of documents in Elasticsearch"""
    try:
        response = requests.get(f"{ELASTICSEARCH_HOST}/{ELASTICSEARCH_INDEX_PRODUCTS}/_count")
        
        if response.status_code != 200:
            logger.error(f"Error checking Elasticsearch: {response.text}")
            return 0
        
        data = response.json()
        count = data.get("count", 0)
        
        logger.info(f"Found {count} products in Elasticsearch")
        return count
    
    except Exception as e:
        logger.error(f"Error checking Elasticsearch document count: {str(e)}")
        return 0

def check_elasticsearch_vector_count():
    """Check the number of documents with vector embeddings in Elasticsearch"""
    try:
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
            logger.error(f"Error checking vector embeddings: {response.text}")
            return 0
        
        data = response.json()
        count = data.get("count", 0)
        
        logger.info(f"Found {count} products with text embeddings")
        return count
    
    except Exception as e:
        logger.error(f"Error checking vector embeddings count: {str(e)}")
        return 0

def main():
    """Main entry point"""
    # Check document count
    doc_count = check_elasticsearch_document_count()
    
    # Check vector count
    vector_count = check_elasticsearch_vector_count()
    
    # Calculate percentage
    percentage = (vector_count / doc_count * 100) if doc_count > 0 else 0
    
    # Print results
    print(f"\nElasticsearch Document Counts:")
    print(f"Total documents: {doc_count}")
    print(f"Documents with vector embeddings: {vector_count}")
    print(f"Percentage with vector embeddings: {percentage:.2f}%")

if __name__ == "__main__":
    main()
