#!/usr/bin/env python3
"""
Kafka producer for e-commerce product data

This script reads product data from a JSON file and sends it to Kafka topics.
"""
import os
import sys
import json
import time
import logging
import argparse
import subprocess
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.kafka.circuit_breaker_manager import CircuitBreakerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("product-producer")

# Initialize circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()
kafka_circuit_breaker = circuit_breaker_manager.get_circuit_breaker("kafka")

def send_to_kafka(topic, record, dry_run=False):
    """Send a record to a Kafka topic"""
    try:
        if not kafka_circuit_breaker.allow_request():
            logger.warning("Kafka circuit breaker is open, skipping send")
            return False
        
        if dry_run:
            logger.info(f"DRY RUN: Would send record to topic {topic}")
            return True
        
        # Create a temporary file for the record
        temp_file = f"/tmp/kafka_record_{int(time.time())}.json"
        with open(temp_file, "w") as f:
            f.write(json.dumps(record) + "\n")
        
        # Send to Kafka using kafka-console-producer
        cmd = f"cat {temp_file} | docker exec -i kafka kafka-console-producer --broker-list localhost:9092 --topic {topic}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error sending to topic {topic}: {result.stderr}")
            kafka_circuit_breaker.record_failure()
            return False
        else:
            kafka_circuit_breaker.record_success()
            return True
    except Exception as e:
        logger.error(f"Error sending to topic {topic}: {e}")
        kafka_circuit_breaker.record_failure()
        return False
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)

def process_products(products_file, batch_size=100, dry_run=False, max_products=None):
    """Process products from a JSON file and send to Kafka"""
    try:
        # Load products from file
        with open(products_file, "r") as f:
            products = json.load(f)
        
        # Limit number of products if specified
        if max_products is not None:
            products = products[:max_products]
            
        logger.info(f"Read {len(products)} products from {products_file}")
        
        # Send products to Kafka
        success_count = 0
        failure_count = 0
        
        logger.info(f"Sending {len(products)} products to Kafka topic 'products'")
        
        if dry_run:
            # Just show a sample of what would be sent
            logger.info(f"DRY RUN: Would send {len(products)} records to topic products")
            for i, product in enumerate(products[:2]):
                logger.info(f"DRY RUN: Sample record: {json.dumps(product)[:100]}...")
            success_count = len(products)
        else:
            # Actually send to Kafka
            for i, product in enumerate(products):
                success = send_to_kafka("products", product, dry_run)
                
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                
                # Log progress
                if (i + 1) % batch_size == 0 or i == len(products) - 1:
                    logger.info(f"Processed {i + 1}/{len(products)} products ({success_count} successful, {failure_count} failed)")
                
                # Sleep briefly to avoid overwhelming Kafka
                time.sleep(0.01)
        
        logger.info(f"Products: {success_count}/{len(products)} successfully sent to Kafka")
        
        return success_count, failure_count
    except Exception as e:
        logger.error(f"Error processing products: {e}")
        return 0, 0

def process_product_images(products_file, images_dir, batch_size=100, dry_run=False, max_products=None):
    """Process product images and send to Kafka"""
    try:
        # Load products from file
        with open(products_file, "r") as f:
            products = json.load(f)
        
        # Limit number of products if specified
        if max_products is not None:
            products = products[:max_products]
            
        # Check if images directory exists
        if not os.path.exists(images_dir):
            logger.warning(f"Images directory not found: {images_dir}")
            return 0, 0
        
        # Find image files
        image_files = [f for f in os.listdir(images_dir) if f.endswith((".jpg", ".jpeg", ".png", ".gif"))]
        logger.info(f"Found {len(image_files)} product images in {images_dir}")
        
        # Send product images to Kafka
        success_count = 0
        failure_count = 0
        
        if dry_run:
            # Just show a sample of what would be sent
            logger.info(f"DRY RUN: Would send {len(products)} image records to topic product-images")
            success_count = len(products)
        else:
            # Actually send to Kafka
            for i, product in enumerate(products):
                product_id = product["id"]
                image_path = os.path.join(images_dir, f"{product_id}.jpg")
                
                # Check if image exists
                if not os.path.exists(image_path):
                    logger.warning(f"Image not found for product {product_id}: {image_path}")
                    failure_count += 1
                    continue
                
                # Create record for Kafka
                record = {
                    "product_id": product_id,
                    "image_path": image_path
                }
                
                success = send_to_kafka("product-images", record, dry_run)
                
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                
                # Log progress
                if (i + 1) % batch_size == 0 or i == len(products) - 1:
                    logger.info(f"Processed {i + 1}/{len(products)} product images ({success_count} successful, {failure_count} failed)")
                
                # Sleep briefly to avoid overwhelming Kafka
                time.sleep(0.01)
        
        logger.info(f"Product images: {success_count}/{len(products)} successfully sent to Kafka")
        
        return success_count, failure_count
    except Exception as e:
        logger.error(f"Error processing product images: {e}")
        return 0, 0

def main():
    parser = argparse.ArgumentParser(description="Send e-commerce product data to Kafka")
    parser.add_argument("--products-file", default="data/products.json", help="Path to products JSON file")
    parser.add_argument("--images-dir", default="data/images", help="Path to images directory")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually send to Kafka, just log what would be sent")
    parser.add_argument("--skip-products", action="store_true", help="Skip processing products")
    parser.add_argument("--skip-images", action="store_true", help="Skip processing product images")
    parser.add_argument("--max-products", type=int, help="Maximum number of products to process")
    args = parser.parse_args()
    
    # Process products
    if not args.skip_products:
        product_success, product_failure = process_products(
            args.products_file, args.batch_size, args.dry_run, args.max_products
        )
    else:
        logger.info("Skipping products processing")
        product_success, product_failure = 0, 0
    
    # Process product images
    if not args.skip_images:
        image_success, image_failure = process_product_images(
            args.products_file, args.images_dir, args.batch_size, args.dry_run, args.max_products
        )
    else:
        logger.info("Skipping product images processing")
        image_success, image_failure = 0, 0
    
    # Log overall stats
    logger.info(f"Products: {product_success}/{product_success + product_failure} successfully sent to Kafka")
    logger.info(f"Product images: {image_success}/{image_success + image_failure} successfully sent to Kafka")
    
    if product_success + image_success > 0:
        logger.info("All records successfully sent to Kafka")
    else:
        logger.error("No records were successfully sent to Kafka")

if __name__ == "__main__":
    main()
