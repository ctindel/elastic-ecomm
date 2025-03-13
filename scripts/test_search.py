#!/usr/bin/env python3
"""
Simple test script for search functionality.
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

def test_search():
    """Test basic search functionality."""
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
    
    # Test BM25 search
    logger.info("Testing BM25 search")
    query = "headphones"
    
    try:
        # Perform BM25 search
        response = es.search(
            index="products",
            body={
                "query": {
                    "match": {
                        "name": query
                    }
                },
                "size": 5
            }
        )
        
        # Check results
        hits = response["hits"]["hits"]
        total_hits = response["hits"]["total"]["value"]
        
        logger.info(f"BM25 search returned {total_hits} results for '{query}'")
        
        if total_hits > 0:
            for hit in hits:
                logger.info(f"Result: {hit['_source']['name']} (Score: {hit['_score']})")
        
        return True
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_search()
    if success:
        logger.info("Search test passed")
        sys.exit(0)
    else:
        logger.error("Search test failed")
        sys.exit(1)
