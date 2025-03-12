#!/usr/bin/env python3
"""
Test script for the Kafka ingestion pipeline
This script tests the end-to-end ingestion pipeline for products and product images
"""
import os
import sys
import json
import time
import logging
import argparse
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_INDEX_PRODUCTS,
    KAFKA_HOST,
    KAFKA_TOPIC_PRODUCTS,
    KAFKA_TOPIC_PRODUCT_IMAGES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def generate_test_data(num_products=10):
    """
    Generate test data for the ingestion pipeline
    
    Args:
        num_products: Number of test products to generate
    
    Returns:
        tuple: (products_file, success)
    """
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Create images directory if it doesn't exist
        images_dir = os.path.join(data_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Generate test products
        logger.info(f"Generating {num_products} test products")
        
        # Run the generate_products.py script
        cmd = f"python {os.path.join(project_root, 'scripts', 'generate_products.py')} --num-products {num_products} --output-file {os.path.join(data_dir, 'test_products.json')}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Error generating test products: {process.stderr}")
            return None, False
        
        logger.info(f"Successfully generated {num_products} test products")
        return os.path.join(data_dir, "test_products.json"), True
    
    except Exception as e:
        logger.error(f"Error generating test data: {str(e)}")
        return None, False

def send_to_kafka(file_path, topic):
    """
    Send data to Kafka topic
    
    Args:
        file_path: Path to the JSON file
        topic: Kafka topic to send to
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Run the simple_producer.py script
        cmd = f"python {os.path.join(project_root, 'scripts', 'kafka', 'simple_producer.py')} --file {file_path} --topic {topic}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Error sending data to Kafka: {process.stderr}")
            return False
        
        logger.info(f"Successfully sent data to Kafka topic {topic}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending data to Kafka: {str(e)}")
        return False

def start_consumer(topic):
    """
    Start a Kafka consumer for the specified topic
    
    Args:
        topic: Kafka topic to consume from
    
    Returns:
        subprocess.Popen: Consumer process
    """
    try:
        # Run the product_consumer.py script
        cmd = f"python {os.path.join(project_root, 'scripts', 'kafka', 'product_consumer.py')}"
        process = subprocess.Popen(cmd, shell=True)
        
        logger.info(f"Started consumer for topic {topic}")
        return process
    
    except Exception as e:
        logger.error(f"Error starting consumer: {str(e)}")
        return None

def verify_elasticsearch_ingestion(num_products):
    """
    Verify that the data was properly ingested into Elasticsearch
    
    Args:
        num_products: Number of products to verify
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Wait for the data to be ingested
        logger.info("Waiting for data to be ingested into Elasticsearch...")
        time.sleep(10)
        
        # Check if the products were ingested
        cmd = f"curl -s {ELASTICSEARCH_HOST}/{ELASTICSEARCH_INDEX_PRODUCTS}/_count"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Error checking Elasticsearch: {process.stderr}")
            return False
        
        # Parse the response
        response = json.loads(process.stdout)
        count = response.get("count", 0)
        
        logger.info(f"Found {count} products in Elasticsearch")
        
        # Check if all products were ingested
        if count >= num_products:
            logger.info("All products were successfully ingested")
            return True
        else:
            logger.warning(f"Only {count}/{num_products} products were ingested")
            return False
    
    except Exception as e:
        logger.error(f"Error verifying Elasticsearch ingestion: {str(e)}")
        return False

def verify_vector_embeddings():
    """
    Verify that vector embeddings were properly generated
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if the products have vector embeddings
        cmd = f"curl -s {ELASTICSEARCH_HOST}/{ELASTICSEARCH_INDEX_PRODUCTS}/_search?q=_exists_:text_embedding"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Error checking vector embeddings: {process.stderr}")
            return False
        
        # Parse the response
        response = json.loads(process.stdout)
        hits = response.get("hits", {}).get("total", {}).get("value", 0)
        
        logger.info(f"Found {hits} products with text embeddings")
        
        # Check if any products have vector embeddings
        if hits > 0:
            logger.info("Vector embeddings were successfully generated")
            return True
        else:
            logger.warning("No products have vector embeddings")
            return False
    
    except Exception as e:
        logger.error(f"Error verifying vector embeddings: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test the Kafka ingestion pipeline')
    parser.add_argument('--num-products', type=int, default=10, help='Number of test products to generate')
    args = parser.parse_args()
    
    # Generate test data
    products_file, success = generate_test_data(args.num_products)
    
    if not success:
        logger.error("Failed to generate test data")
        return
    
    # Start the consumer
    consumer_process = start_consumer(KAFKA_TOPIC_PRODUCTS)
    
    if not consumer_process:
        logger.error("Failed to start consumer")
        return
    
    # Send data to Kafka
    if not send_to_kafka(products_file, KAFKA_TOPIC_PRODUCTS):
        logger.error("Failed to send data to Kafka")
        consumer_process.terminate()
        return
    
    # Verify Elasticsearch ingestion
    if not verify_elasticsearch_ingestion(args.num_products):
        logger.error("Failed to verify Elasticsearch ingestion")
        consumer_process.terminate()
        return
    
    # Verify vector embeddings
    if not verify_vector_embeddings():
        logger.error("Failed to verify vector embeddings")
        consumer_process.terminate()
        return
    
    # Success
    logger.info("Kafka ingestion pipeline test completed successfully")
    
    # Terminate the consumer process
    consumer_process.terminate()

if __name__ == "__main__":
    main()
