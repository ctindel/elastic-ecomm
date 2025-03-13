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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def generate_test_data(num_products=10):
    """Generate test data for the ingestion pipeline"""
    try:
        # Create data directory if it doesn't exist
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        
        # Generate test products
        logger.info(f"Generating {num_products} test products")
        
        # Run the generate_products.py script
        cmd = f"python scripts/generate_products.py --num-products {num_products} --output-file {os.path.join(data_dir, 'test_products.json')}"
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
    """Send data to Kafka topic"""
    try:
        # Run the direct_producer.py script
        cmd = f"python scripts/kafka/direct_producer.py --file {file_path} --topic {topic}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Error sending data to Kafka: {process.stderr}")
            return False
        
        logger.info(f"Successfully sent data to Kafka topic {topic}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending data to Kafka: {str(e)}")
        return False

def verify_elasticsearch_ingestion(num_products):
    """Verify that the data was properly ingested into Elasticsearch"""
    try:
        # Wait for the data to be ingested
        logger.info("Waiting for data to be ingested into Elasticsearch...")
        time.sleep(10)
        
        # Check if the products were ingested
        cmd = "curl -s http://localhost:9200/products/_count"
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

def main():
    parser = argparse.ArgumentParser(description='Test the Kafka ingestion pipeline')
    parser.add_argument('--num-products', type=int, default=10, help='Number of test products to generate')
    args = parser.parse_args()
    
    # Generate test data
    products_file, success = generate_test_data(args.num_products)
    
    if not success:
        logger.error("Failed to generate test data")
        return
    
    # Send data to Kafka
    if not send_to_kafka(products_file, "products"):
        logger.error("Failed to send data to Kafka")
        return
    
    # Verify Elasticsearch ingestion
    if not verify_elasticsearch_ingestion(args.num_products):
        logger.error("Failed to verify Elasticsearch ingestion")
        return
    
    # Success
    logger.info("Kafka ingestion pipeline test completed successfully")

if __name__ == "__main__":
    main()
