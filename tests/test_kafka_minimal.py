#!/usr/bin/env python3
"""
Minimal test script for Kafka ingestion pipeline
"""
import json
import logging
import subprocess
import time
from elasticsearch import Elasticsearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test-kafka-minimal")

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

def main():
    """Run a minimal test of the Kafka ingestion pipeline"""
    # Count documents before
    logger.info("Counting documents before test...")
    before_total, before_text, before_image = count_documents()
    logger.info(f"Before: {before_total} total, {before_text} with text vectors, {before_image} with image vectors")
    
    # Send 2 test products to Kafka
    logger.info("Sending test products to Kafka...")
    subprocess.run(
        "python scripts/kafka/product_producer.py --products-file data/products.json --max-products 2 --skip-images",
        shell=True, check=True
    )
    
    # Process with mock consumer
    logger.info("Processing with mock consumer...")
    subprocess.run(
        "python scripts/kafka/product_consumer.py --topic products --use-mock --max-messages 2",
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
    else:
        logger.error("Test FAILED: No new documents or text vectors added")

if __name__ == "__main__":
    main()
