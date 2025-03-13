#!/usr/bin/env python3
"""
Test script to verify search functionality with the updated approach.
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

from app.utils.search_agent import SearchAgent
from app.config.settings import ELASTICSEARCH_HOST, OPENAI_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_search_functionality():
    """Test search functionality with the updated approach."""
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
    
    # Create search agent
    search_agent = SearchAgent(es, OPENAI_API_KEY)
    
    # Test BM25 search
    logger.info("Testing BM25 search")
    bm25_query = "samsung tv"
    bm25_results = search_agent._perform_bm25_search(bm25_query)
    
    if "error" in bm25_results:
        logger.error(f"BM25 search failed: {bm25_results['error']}")
        return False
    
    if bm25_results["total_hits"] == 0:
        logger.warning(f"BM25 search returned no results for '{bm25_query}'")
    else:
        logger.info(f"BM25 search returned {bm25_results['total_hits']} results for '{bm25_query}'")
        logger.info(f"Top result: {bm25_results['results'][0]['name']}")
    
    # Test vector search
    logger.info("Testing vector search")
    vector_query = "comfortable furniture for small apartments"
    vector_results = search_agent._perform_vector_search(vector_query)
    
    if "error" in vector_results:
        logger.error(f"Vector search failed: {vector_results['error']}")
        return False
    
    if vector_results["total_hits"] == 0:
        logger.warning(f"Vector search returned no results for '{vector_query}'")
    else:
        logger.info(f"Vector search returned {vector_results['total_hits']} results for '{vector_query}'")
        logger.info(f"Top result: {vector_results['results'][0]['name']}")
    
    # Test search method determination
    logger.info("Testing search method determination")
    
    # Test BM25 query
    bm25_method_query = "printer ink for deskjet 2734e"
    bm25_method = search_agent.determine_search_method(bm25_method_query)
    logger.info(f"Query '{bm25_method_query}' classified as {bm25_method}")
    
    # Test vector query
    vector_method_query = "comfortable chair for long hours"
    vector_method = search_agent.determine_search_method(vector_method_query)
    logger.info(f"Query '{vector_method_query}' classified as {vector_method}")
    
    # Test customer support query
    cs_method_query = "how do I return an item?"
    cs_method = search_agent.determine_search_method(cs_method_query)
    logger.info(f"Query '{cs_method_query}' classified as {cs_method}")
    
    return True

if __name__ == "__main__":
    success = test_search_functionality()
    if success:
        logger.info("Search functionality test passed")
        sys.exit(0)
    else:
        logger.error("Search functionality test failed")
        sys.exit(1)
