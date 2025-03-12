#!/usr/bin/env python3
"""
Script to test the complete e-commerce search system.
This script verifies that all components work together correctly.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from elasticsearch import Elasticsearch

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.validation import validate_api_keys
from app.utils.embedding import check_ollama_connection
from app.utils.search_agent import SearchAgent, SEARCH_METHOD_BM25, SEARCH_METHOD_VECTOR, SEARCH_METHOD_CUSTOMER_SUPPORT, SEARCH_METHOD_IMAGE
from app.utils.image_processor import extract_text_from_image, analyze_school_supply_list
from app.config.settings import ELASTICSEARCH_HOST, OPENAI_API_KEY, OLLAMA_HOST, OLLAMA_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_api_key_validation():
    """Test API key validation."""
    logger.info("Testing API key validation...")
    
    try:
        # Validate API keys
        validation_result = validate_api_keys()
        
        if validation_result["valid"]:
            logger.info("✅ API key validation passed")
        else:
            logger.warning(f"⚠️ API key validation failed: {validation_result['message']}")
            logger.warning("Some functionality may be limited")
        
        # Log individual service statuses
        for service, status in validation_result["services"].items():
            if status:
                logger.info(f"✅ {service.capitalize()} validation passed")
            else:
                logger.warning(f"⚠️ {service.capitalize()} validation failed")
        
        return validation_result["valid"]
    except Exception as e:
        logger.error(f"❌ API key validation error: {str(e)}")
        return False

def test_elasticsearch_connection():
    """Test Elasticsearch connection."""
    logger.info("Testing Elasticsearch connection...")
    
    try:
        # Connect to Elasticsearch
        es = Elasticsearch(ELASTICSEARCH_HOST)
        
        # Check if Elasticsearch is running
        if es.ping():
            logger.info("✅ Successfully connected to Elasticsearch")
            
            # Check if indices exist
            indices = es.indices.get_alias(index="*")
            if "products" in indices:
                logger.info("✅ Products index exists")
                
                # Check if there are any products
                count = es.count(index="products")
                logger.info(f"✅ Products index contains {count['count']} documents")
            else:
                logger.warning("⚠️ Products index does not exist")
            
            return True
        else:
            logger.error("❌ Failed to connect to Elasticsearch")
            return False
    
    except Exception as e:
        logger.error(f"❌ Elasticsearch connection error: {str(e)}")
        return False

def test_ollama_connection():
    """Test Ollama connection."""
    logger.info("Testing Ollama connection...")
    
    if check_ollama_connection():
        logger.info("✅ Successfully connected to Ollama")
        return True
    else:
        logger.warning("⚠️ Failed to connect to Ollama")
        logger.warning("Vector search functionality may be limited")
        return False

def test_search_agent():
    """Test the search agent."""
    logger.info("Testing search agent...")
    
    try:
        # Connect to Elasticsearch
        es = Elasticsearch(ELASTICSEARCH_HOST)
        
        # Initialize the search agent
        agent = SearchAgent(es, OPENAI_API_KEY)
        
        # Test cases for different query types
        test_cases = [
            {"query": "printer ink for deskjet 2734e", "expected_method": SEARCH_METHOD_BM25},
            {"query": "comfortable chair for long hours", "expected_method": SEARCH_METHOD_VECTOR},
            {"query": "how do I return an item?", "expected_method": SEARCH_METHOD_CUSTOMER_SUPPORT}
        ]
        
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
        
        logger.info(f"Search agent tests: {passed} passed, {failed} failed")
        return passed > 0 and failed == 0
    
    except Exception as e:
        logger.error(f"❌ Search agent error: {str(e)}")
        return False

def test_image_processing():
    """Test image processing."""
    logger.info("Testing image processing...")
    
    # Skip if OpenAI API key is not available
    if not OPENAI_API_KEY:
        logger.warning("⚠️ OpenAI API key is not available")
        logger.warning("Image processing tests skipped")
        return False
    
    # Check if test image exists
    test_image_path = "data/images/test_school_supply_list.png"
    if not os.path.exists(test_image_path):
        logger.warning(f"⚠️ Test image not found: {test_image_path}")
        logger.warning("Generating test image...")
        
        # Try to generate a test image
        try:
            from scripts.generate_test_image import generate_test_image
            test_image_path = generate_test_image()
            
            if not test_image_path:
                logger.error("❌ Failed to generate test image")
                return False
        except Exception as e:
            logger.error(f"❌ Error generating test image: {str(e)}")
            return False
    
    # Test text extraction
    extracted_text = extract_text_from_image(test_image_path)
    
    if extracted_text:
        logger.info("✅ Successfully extracted text from image")
        logger.info(f"Extracted text: {extracted_text[:100]}...")
    else:
        logger.error("❌ Failed to extract text from image")
        return False
    
    # Test school supply list analysis
    analysis = analyze_school_supply_list(test_image_path)
    
    if analysis and "items" in analysis and analysis["items"]:
        logger.info(f"✅ Successfully analyzed school supply list with {len(analysis['items'])} items")
        
        # Print the first few items
        for i, item in enumerate(analysis["items"][:3]):
            logger.info(f"Item {i+1}: {item['name']}")
            if "alternatives" in item and item["alternatives"]:
                for alt in item["alternatives"][:2]:
                    logger.info(f"  - {alt['price_tier']}: {alt['product']}")
    else:
        logger.error("❌ Failed to analyze school supply list")
        return False
    
    return True

def main():
    """Main function to run all tests."""
    parser = argparse.ArgumentParser(description="Test the complete e-commerce search system")
    parser.add_argument("--skip-elasticsearch", action="store_true", help="Skip Elasticsearch tests")
    parser.add_argument("--skip-ollama", action="store_true", help="Skip Ollama tests")
    parser.add_argument("--skip-image", action="store_true", help="Skip image processing tests")
    args = parser.parse_args()
    
    logger.info("Starting complete system tests")
    
    # Test API key validation
    api_keys_valid = test_api_key_validation()
    
    # Test Elasticsearch connection
    es_connected = True
    if not args.skip_elasticsearch:
        es_connected = test_elasticsearch_connection()
    else:
        logger.info("Skipping Elasticsearch tests")
    
    # Test Ollama connection
    ollama_connected = True
    if not args.skip_ollama:
        ollama_connected = test_ollama_connection()
    else:
        logger.info("Skipping Ollama tests")
    
    # Test search agent
    search_agent_working = True
    if es_connected and not args.skip_elasticsearch:
        search_agent_working = test_search_agent()
    else:
        logger.info("Skipping search agent tests (requires Elasticsearch)")
    
    # Test image processing
    image_processing_working = True
    if not args.skip_image:
        image_processing_working = test_image_processing()
    else:
        logger.info("Skipping image processing tests")
    
    # Print summary
    logger.info("\n=== System Test Summary ===")
    logger.info(f"API Keys: {'✅ Valid' if api_keys_valid else '⚠️ Some keys missing or invalid'}")
    logger.info(f"Elasticsearch: {'✅ Connected' if es_connected else '❌ Not connected'}")
    logger.info(f"Ollama: {'✅ Connected' if ollama_connected else '⚠️ Not connected'}")
    logger.info(f"Search Agent: {'✅ Working' if search_agent_working else '❌ Not working'}")
    logger.info(f"Image Processing: {'✅ Working' if image_processing_working else '❌ Not working'}")
    
    # Overall status
    if api_keys_valid and es_connected and ollama_connected and search_agent_working and image_processing_working:
        logger.info("\n✅ All systems operational!")
        return 0
    elif es_connected and search_agent_working:
        logger.info("\n⚠️ Core search functionality operational, but some features may be limited")
        return 0
    else:
        logger.error("\n❌ Critical system components not operational")
        return 1

if __name__ == "__main__":
    sys.exit(main())
