#!/usr/bin/env python3
"""
Test script to verify Elasticsearch setup for the ingestion process.
"""
import json
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test-es-setup")

# Define variables
es_host = "http://localhost:9200"
index_name = "products"
mapping_file = "config/elasticsearch/mappings/products.json"

def test_elasticsearch_connection():
    """Test connection to Elasticsearch."""
    try:
        cmd = f"curl -s {es_host}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error connecting to Elasticsearch: {result.stderr}")
            return False
        
        logger.info("Successfully connected to Elasticsearch")
        return True
    
    except Exception as e:
        logger.error(f"Error testing Elasticsearch connection: {str(e)}")
        return False

def test_elasticsearch_index_setup():
    """Test setting up Elasticsearch index with mapping."""
    try:
        # Load mapping from file
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        
        logger.info(f"Loaded mapping from {mapping_file}")
        
        # Check if index exists
        check_cmd = f"curl -s -X HEAD {es_host}/{index_name}"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Index {index_name} already exists, deleting it")
            delete_cmd = f"curl -s -X DELETE {es_host}/{index_name}"
            subprocess.run(delete_cmd, shell=True, check=True)
        
        # Create index with mapping
        create_cmd = f"curl -s -X PUT {es_host}/{index_name} -H 'Content-Type: application/json' -d '{json.dumps(mapping)}'"
        result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error creating index: {result.stderr}")
            return False
        
        response = json.loads(result.stdout)
        if response.get("acknowledged", False):
            logger.info(f"Successfully created index {index_name}")
            return True
        else:
            logger.error(f"Failed to create index: {response}")
            return False
    
    except Exception as e:
        logger.error(f"Error setting up Elasticsearch index: {str(e)}")
        return False

def test_index_document():
    """Test indexing a single document."""
    try:
        # Create a test document
        test_doc = {
            "id": "test-product-1",
            "name": "Test Product",
            "description": "This is a test product for Elasticsearch indexing",
            "category": "Test",
            "subcategory": "Test Products",
            "price": 9.99,
            "brand": "Test Brand",
            "attributes": {
                "color": "blue",
                "size": "medium"
            }
        }
        
        # Index the document
        index_cmd = f"curl -s -X POST {es_host}/{index_name}/_doc/test-product-1 -H 'Content-Type: application/json' -d '{json.dumps(test_doc)}'"
        result = subprocess.run(index_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error indexing document: {result.stderr}")
            return False
        
        response = json.loads(result.stdout)
        if response.get("result") in ["created", "updated"]:
            logger.info(f"Successfully indexed test document with ID {test_doc['id']}")
            return True
        else:
            logger.error(f"Failed to index document: {response}")
            return False
    
    except Exception as e:
        logger.error(f"Error indexing document: {str(e)}")
        return False

def verify_document():
    """Verify that the document was indexed."""
    try:
        # Get the document
        get_cmd = f"curl -s -X GET {es_host}/{index_name}/_doc/test-product-1"
        result = subprocess.run(get_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error getting document: {result.stderr}")
            return False
        
        response = json.loads(result.stdout)
        if response.get("found", False):
            logger.info(f"Successfully retrieved test document")
            return True
        else:
            logger.error(f"Failed to retrieve document: {response}")
            return False
    
    except Exception as e:
        logger.error(f"Error verifying document: {str(e)}")
        return False

def main():
    """Main function to run tests."""
    logger.info("Starting Elasticsearch setup tests")
    
    # Test connection
    if not test_elasticsearch_connection():
        logger.error("Failed to connect to Elasticsearch, exiting")
        return
    
    # Test index setup
    if not test_elasticsearch_index_setup():
        logger.error("Failed to set up Elasticsearch index, exiting")
        return
    
    # Test indexing document
    if not test_index_document():
        logger.error("Failed to index document, exiting")
        return
    
    # Verify document
    if not verify_document():
        logger.error("Failed to verify document, exiting")
        return
    
    logger.info("All tests passed successfully!")

if __name__ == "__main__":
    main()
