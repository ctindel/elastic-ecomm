#!/usr/bin/env python3
"""
Test script for Kafka ingestion pipeline with random product IDs
"""
import json
import logging
import subprocess
import time
import uuid
import os
from elasticsearch import Elasticsearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test-kafka-random")

def count_documents():
    """Count documents in Elasticsearch"""
    es = Elasticsearch("http://localhost:9200")
    
    # Count total documents
    total = es.count(index="products")["count"]
    
    # Count documents with text embeddings
    text_query = {"query": {"exists": {"field": "text_embedding"}}}
    text_vectors = es.count(index="products", body=text_query)["count"]
    
    # Count documents with image embeddings
    image_query = {"query": {"exists": {"field": "image.vector_embedding"}}}
    image_vectors = es.count(index="products", body=image_query)["count"]
    
    return total, text_vectors, image_vectors

def create_random_products(count=2):
    """Create random test products"""
    products = []
    for i in range(count):
        product_id = str(uuid.uuid4())
        products.append({
            "id": product_id,
            "name": f"Random Test Product {i+1}",
            "description": f"This is a random test product {i+1} for Kafka ingestion testing with ID {product_id}",
            "price": 19.99 + i,
            "category": "Test",
            "brand": "TestBrand",
            "attributes": {
                "color": "Blue",
                "size": "Medium",
                "weight": "1.5 kg"
            }
        })
    
    # Write to temporary file
    temp_file = "/tmp/random_products.json"
    with open(temp_file, "w") as f:
        json.dump(products, f)
    
    return temp_file, products

def main():
    """Run a test of the Kafka ingestion pipeline with random products"""
    # Count documents before
    logger.info("Counting documents before test...")
    before_total, before_text, before_image = count_documents()
    logger.info(f"Before: {before_total} total, {before_text} with text vectors, {before_image} with image vectors")
    
    # Create random test products
    products_file, products = create_random_products(2)
    logger.info(f"Created {len(products)} random test products")
    
    # Send random products to Kafka
    logger.info("Sending random test products to Kafka...")
    subprocess.run(
        f"python scripts/kafka/product_producer.py --products-file {products_file} --skip-images",
        shell=True, check=True
    )
    
    # Process with mock consumer
    logger.info("Processing with mock consumer...")
    subprocess.run(
        "python scripts/kafka/product_consumer.py --topic products --use-mock",
        shell=True, check=True
    )
    
    # Wait for processing to complete
    logger.info("Waiting for processing to complete...")
    time.sleep(5)
    
    # Count documents after
    logger.info("Counting documents after test...")
    after_total, after_text, after_image = count_documents()
    logger.info(f"After: {after_total} total, {after_text} with text vectors, {after_image} with image vectors")
    
    # Calculate differences
    new_docs = after_total - before_total
    new_text = after_text - before_text
    new_image = after_image - before_image
    
    logger.info(f"Added {new_docs} documents, {new_text} text vectors, {new_image} image vectors")
    
    # Verify success
    if new_docs > 0 and new_text > 0:
        logger.info("Test PASSED: Successfully added documents with text vectors")
        return True
    else:
        logger.error("Test FAILED: No new documents or text vectors added")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
