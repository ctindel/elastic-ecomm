#!/usr/bin/env python3
"""
Script to test the AI search agent functionality.
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

from app.utils.search_agent import SearchAgent, SEARCH_METHOD_BM25, SEARCH_METHOD_VECTOR, SEARCH_METHOD_CUSTOMER_SUPPORT, SEARCH_METHOD_IMAGE
from app.config.settings import ELASTICSEARCH_HOST, OPENAI_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_search_method_determination():
    """Test the search method determination logic."""
    logger.info("Testing search method determination")
    
    # Connect to Elasticsearch
    es = Elasticsearch(ELASTICSEARCH_HOST)
    
    # Initialize the search agent
    agent = SearchAgent(es, OPENAI_API_KEY)
    
    # Test cases for different query types
    test_cases = [
        # Precision searches (BM25)
        {"query": "printer ink for deskjet 2734e", "expected_method": SEARCH_METHOD_BM25},
        {"query": "iphone 13 pro max case", "expected_method": SEARCH_METHOD_BM25},
        {"query": "samsung 65 inch qled tv", "expected_method": SEARCH_METHOD_BM25},
        
        # Semantic understanding queries (Vector)
        {"query": "comfortable chair for long hours", "expected_method": SEARCH_METHOD_VECTOR},
        {"query": "waterproof case for hiking", "expected_method": SEARCH_METHOD_VECTOR},
        {"query": "something to keep drinks cold", "expected_method": SEARCH_METHOD_VECTOR},
        
        # Customer support queries
        {"query": "how do I return an item?", "expected_method": SEARCH_METHOD_CUSTOMER_SUPPORT},
        {"query": "track my order", "expected_method": SEARCH_METHOD_CUSTOMER_SUPPORT},
        {"query": "unsubscribe from emails", "expected_method": SEARCH_METHOD_CUSTOMER_SUPPORT}
    ]
    
    # Run the tests
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases):
        query = test_case["query"]
        expected_method = test_case["expected_method"]
        
        # Determine the search method
        actual_method = agent.determine_search_method(query)
        
        # Check if the result matches the expected method
        if actual_method == expected_method:
            logger.info(f"✅ Test {i+1}: Query '{query}' correctly classified as {actual_method}")
            passed += 1
        else:
            logger.error(f"❌ Test {i+1}: Query '{query}' incorrectly classified as {actual_method} (expected {expected_method})")
            failed += 1
    
    logger.info(f"Search method determination tests: {passed} passed, {failed} failed")
    return passed, failed

def test_bm25_search():
    """Test the BM25 search functionality."""
    logger.info("Testing BM25 search")
    
    # Connect to Elasticsearch
    es = Elasticsearch(ELASTICSEARCH_HOST)
    
    # Initialize the search agent
    agent = SearchAgent(es, OPENAI_API_KEY)
    
    # Test BM25 search with a precision query
    query = "printer ink"
    
    # Perform the search
    results = agent._perform_bm25_search(query)
    
    # Check if the search was successful
    if "error" in results:
        logger.error(f"❌ BM25 search failed: {results['error']}")
        return 0, 1
    
    # Check if any results were returned
    if results["total_hits"] > 0:
        logger.info(f"✅ BM25 search returned {results['total_hits']} results")
        logger.info(f"Top result: {results['results'][0]['name']}")
        return 1, 0
    else:
        logger.warning("⚠️ BM25 search returned no results")
        return 0, 1

def test_vector_search():
    """Test the vector search functionality."""
    logger.info("Testing vector search")
    
    # Connect to Elasticsearch
    es = Elasticsearch(ELASTICSEARCH_HOST)
    
    # Initialize the search agent
    agent = SearchAgent(es, OPENAI_API_KEY)
    
    # Test vector search with a semantic query
    query = "comfortable chair for office"
    
    # Perform the search
    results = agent._perform_vector_search(query)
    
    # Check if the search was successful
    if "error" in results:
        logger.error(f"❌ Vector search failed: {results['error']}")
        return 0, 1
    
    # Check if any results were returned
    if results["total_hits"] > 0:
        logger.info(f"✅ Vector search returned {results['total_hits']} results")
        logger.info(f"Top result: {results['results'][0]['name']}")
        return 1, 0
    else:
        logger.warning("⚠️ Vector search returned no results")
        return 0, 1

def test_customer_support_query():
    """Test the customer support query handling."""
    logger.info("Testing customer support query handling")
    
    # Connect to Elasticsearch
    es = Elasticsearch(ELASTICSEARCH_HOST)
    
    # Initialize the search agent
    agent = SearchAgent(es, OPENAI_API_KEY)
    
    # Test customer support query
    query = "how do I return an item?"
    
    # Handle the query
    results = agent._handle_customer_support_query(query)
    
    # Check if the query was handled successfully
    if "error" in results:
        logger.error(f"❌ Customer support query handling failed: {results['error']}")
        return 0, 1
    
    # Check if a response was returned
    if results["total_hits"] > 0:
        logger.info(f"✅ Customer support query returned a response: {results['results'][0]['title']}")
        return 1, 0
    else:
        logger.warning("⚠️ Customer support query returned no response")
        return 0, 1

def main():
    """Main function to run all tests."""
    logger.info("Starting AI search agent tests")
    
    # Check Elasticsearch connection
    try:
        es = Elasticsearch(ELASTICSEARCH_HOST)
        if not es.ping():
            logger.error("Could not connect to Elasticsearch. Make sure it's running.")
            return 1
        logger.info("Successfully connected to Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
        return 1
    
    # Run the tests
    total_passed = 0
    total_failed = 0
    
    # Test search method determination
    passed, failed = test_search_method_determination()
    total_passed += passed
    total_failed += failed
    
    # Test BM25 search
    passed, failed = test_bm25_search()
    total_passed += passed
    total_failed += failed
    
    # Test vector search
    passed, failed = test_vector_search()
    total_passed += passed
    total_failed += failed
    
    # Test customer support query handling
    passed, failed = test_customer_support_query()
    total_passed += passed
    total_failed += failed
    
    # Print summary
    logger.info(f"All tests completed: {total_passed} passed, {total_failed} failed")
    
    if total_failed > 0:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
