#!/usr/bin/env python3
"""
Kafka producer for product data using subprocess to call kafka-console-producer
This avoids dependency issues with the kafka-python library
"""
import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
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

def send_to_kafka(data, topic):
    """
    Send data to Kafka topic using subprocess.
    
    Args:
        data: Data to send (will be converted to JSON)
        topic: Kafka topic to send to
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create a temporary file for the data
        temp_file = f"/tmp/kafka_data_{int(time.time())}.json"
        with open(temp_file, 'w') as f:
            if isinstance(data, list):
                # Write each item on a separate line
                for item in data:
                    f.write(json.dumps(item) + '\n')
            else:
                # Write a single item
                f.write(json.dumps(data))
        
        # Send to Kafka using kafka-console-producer
        cmd = f"cat {temp_file} | docker exec -i kafka kafka-console-producer --broker-list kafka:9092 --topic {topic}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Clean up
        os.remove(temp_file)
        
        if process.returncode != 0:
            logger.error(f"Failed to send data to Kafka: {process.stderr}")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error sending data to Kafka: {str(e)}")
        return False

def process_products_file(file_path, batch_size=100):
    """
    Process products file and send to Kafka.
    
    Args:
        file_path: Path to products JSON file
        batch_size: Number of products to send in each batch
    """
    logger.info(f"Processing products file: {file_path}")
    
    try:
        # Load products from file
        with open(file_path, 'r') as f:
            products = json.load(f)
        
        if not products:
            logger.warning("No products found in file")
            return
        
        logger.info(f"Found {len(products)} products")
        
        # Process products in batches
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            logger.info(f"Sending batch {i//batch_size + 1}/{(len(products) + batch_size - 1)//batch_size}")
            
            # Prepare products for Kafka (remove embeddings)
            for product in batch:
                # Remove any existing embeddings
                if "text_embedding" in product:
                    del product["text_embedding"]
                
                if "image" in product and "vector_embedding" in product["image"]:
                    del product["image"]["vector_embedding"]
            
            # Send batch to Kafka
            success = send_to_kafka(batch, KAFKA_TOPIC_PRODUCTS)
            
            if not success:
                logger.error(f"Failed to send batch {i//batch_size + 1}")
                return
            
            # Sleep briefly to avoid overwhelming Kafka
            time.sleep(0.1)
        
        logger.info("Successfully sent all products to Kafka")
    
    except Exception as e:
        logger.error(f"Error processing products file: {str(e)}")

def main():
    """Main function to process products and send to Kafka."""
    logger.info("Starting product producer")
    
    # Check if products file exists
    products_file = Path("data/products.json")
    if not products_file.exists():
        logger.error("Products file not found. Run generate_data.py first.")
        return
    
    # Process products file
    process_products_file(products_file)
    
    logger.info("Product producer completed")

if __name__ == "__main__":
    main()
