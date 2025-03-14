#!/usr/bin/env python3
"""
Test script for Kafka-based ingestion pipeline

This script tests the Kafka-based ingestion pipeline for e-commerce product data,
verifying that products and product images are properly ingested into Elasticsearch
with vector embeddings.
"""
import os
import sys
import json
import time
import argparse
import logging
import subprocess
from pathlib import Path
from elasticsearch import Elasticsearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test-kafka-ingestion")

def count_elasticsearch_documents(index_name, es_host="http://localhost:9200"):
    """Count documents in Elasticsearch index"""
    try:
        es = Elasticsearch(es_host)
        result = es.count(index=index_name)
        return result["count"]
    except Exception as e:
        logger.error(f"Error counting documents: {e}")
        return 0

def check_vector_embeddings(index_name, field="text_embedding", es_host="http://localhost:9200"):
    """Check if documents have vector embeddings"""
    try:
        es = Elasticsearch(es_host)
        query = {
            "query": {
                "exists": {
                    "field": field
                }
            }
        }
        result = es.count(index=index_name, body=query)
        return result["count"]
    except Exception as e:
        logger.error(f"Error checking vector embeddings: {e}")
        return 0

def check_image_vector_embeddings(index_name, es_host="http://localhost:9200"):
    """Check if documents have image vector embeddings"""
    try:
        es = Elasticsearch(es_host)
        query = {
            "query": {
                "exists": {
                    "field": "image.vector_embedding"
                }
            }
        }
        result = es.count(index=index_name, body=query)
        return result["count"]
    except Exception as e:
        logger.error(f"Error checking image vector embeddings: {e}")
        return 0

def run_kafka_init():
    """Initialize Kafka topics"""
    try:
        logger.info("Initializing Kafka topics...")
        cmd = "bash scripts/kafka/init_kafka.sh"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error initializing Kafka topics: {result.stderr}")
            return False
        
        logger.info("Kafka topics initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing Kafka topics: {e}")
        return False

def run_producer(products_file="data/products.json", images_dir="data/images", batch_size=10, dry_run=False):
    """Run the Kafka producer to send product data"""
    try:
        logger.info("Running Kafka producer...")
        cmd = f"python scripts/kafka/product_producer.py --products-file {products_file} --images-dir {images_dir} --batch-size {batch_size}"
        
        if dry_run:
            cmd += " --dry-run"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running producer: {result.stderr}")
            return False
        
        logger.info("Producer completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error running producer: {e}")
        return False

def run_consumer(topic="all", max_messages=None):
    """Run the Kafka consumer to process product data"""
    try:
        logger.info(f"Running Kafka consumer for topic {topic}...")
        
        cmd = f"python scripts/kafka/product_consumer.py --topic {topic}"
        
        if max_messages:
            cmd += f" --max-messages {max_messages}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running consumer: {result.stderr}")
            return False
        
        logger.info("Consumer completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error running consumer: {e}")
        return False

def run_retry_processor():
    """Run the retry processor to handle failed messages"""
    try:
        logger.info("Running retry processor...")
        cmd = "python scripts/kafka/retry_processor.py"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error running retry processor: {result.stderr}")
            return False
        
        logger.info("Retry processor completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error running retry processor: {e}")
        return False

def count_products_in_file(products_file="data/products.json"):
    """Count the number of products in the products file"""
    try:
        with open(products_file, "r") as f:
            products = json.load(f)
        return len(products)
    except Exception as e:
        logger.error(f"Error counting products in file: {e}")
        return 0

def count_images_in_dir(images_dir="data/images"):
    """Count the number of images in the images directory"""
    try:
        if not os.path.exists(images_dir):
            return 0
        
        image_files = [f for f in os.listdir(images_dir) if f.endswith((".jpg", ".jpeg", ".png", ".gif"))]
        return len(image_files)
    except Exception as e:
        logger.error(f"Error counting images in directory: {e}")
        return 0

def check_ollama_available():
    """Check if Ollama is available"""
    try:
        response = subprocess.run(
            "curl -s http://localhost:11434/api/version",
            shell=True,
            capture_output=True,
            text=True
        )
        is_available = response.returncode == 0 and response.stdout.strip() != ""
        if is_available:
            logger.info("Ollama is available")
        else:
            logger.warning("Ollama is not available, but consumer will retry indefinitely")
        return is_available
    except Exception as e:
        logger.error(f"Error checking Ollama availability: {e}")
        logger.warning("Ollama is not available, but consumer will retry indefinitely")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test Kafka ingestion pipeline")
    parser.add_argument("--es-host", default="http://localhost:9200", help="Elasticsearch host")
    parser.add_argument("--products-file", default="data/products.json", help="Path to products JSON file")
    parser.add_argument("--images-dir", default="data/images", help="Path to images directory")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    parser.add_argument("--max-messages", type=int, help="Maximum number of messages to consume")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually send to Kafka, just log what would be sent")
    parser.add_argument("--skip-init", action="store_true", help="Skip Kafka topic initialization")
    parser.add_argument("--skip-producer", action="store_true", help="Skip running the producer")
    parser.add_argument("--skip-consumer", action="store_true", help="Skip running the consumer")
    parser.add_argument("--skip-retry", action="store_true", help="Skip running the retry processor")
    parser.add_argument("--topic", choices=["products", "product-images", "all"], default="all", help="Kafka topic to consume from")
    args = parser.parse_args()
    
    # Check if Ollama is available
    ollama_available = check_ollama_available()
    if not ollama_available:
        logger.warning("Ollama is not available, but consumer will retry indefinitely until it becomes available")
    
    # Count products and images before ingestion
    product_count = count_products_in_file(args.products_file)
    image_count = count_images_in_dir(args.images_dir)
    
    logger.info(f"Found {product_count} products in {args.products_file}")
    logger.info(f"Found {image_count} images in {args.images_dir}")
    
    # Count documents before ingestion
    logger.info("Counting documents before ingestion...")
    products_before = count_elasticsearch_documents("products", args.es_host)
    text_vectors_before = check_vector_embeddings("products", "text_embedding", args.es_host)
    image_vectors_before = check_image_vector_embeddings("products", args.es_host)
    
    logger.info(f"Products before: {products_before}")
    logger.info(f"Text vectors before: {text_vectors_before}")
    logger.info(f"Image vectors before: {image_vectors_before}")
    
    # Initialize Kafka topics
    if not args.skip_init:
        if not run_kafka_init():
            logger.error("Failed to initialize Kafka topics")
            return 1
    
    # Run producer
    if not args.skip_producer:
        if not run_producer(args.products_file, args.images_dir, args.batch_size, args.dry_run):
            logger.error("Failed to run producer")
            return 1
    
    # Run consumer
    if not args.skip_consumer:
        if not run_consumer(args.topic, args.max_messages):
            logger.error("Failed to run consumer")
            return 1
    
    # Run retry processor
    if not args.skip_retry:
        if not run_retry_processor():
            logger.error("Failed to run retry processor")
            return 1
    
    # Wait for processing to complete
    logger.info("Waiting for processing to complete...")
    time.sleep(10)
    
    # Count documents after ingestion
    logger.info("Counting documents after ingestion...")
    products_after = count_elasticsearch_documents("products", args.es_host)
    text_vectors_after = check_vector_embeddings("products", "text_embedding", args.es_host)
    image_vectors_after = check_image_vector_embeddings("products", args.es_host)
    
    logger.info(f"Products after: {products_after}")
    logger.info(f"Text vectors after: {text_vectors_after}")
    logger.info(f"Image vectors after: {image_vectors_after}")
    
    # Check if ingestion was successful
    products_ingested = products_after - products_before
    text_vectors_ingested = text_vectors_after - text_vectors_before
    image_vectors_ingested = image_vectors_after - image_vectors_before
    
    if products_ingested > 0:
        logger.info(f"Successfully ingested {products_ingested} products")
    else:
        logger.warning("No new products were ingested")
    
    if text_vectors_ingested > 0:
        logger.info(f"Successfully generated {text_vectors_ingested} text vector embeddings")
    else:
        logger.warning("No new text vector embeddings were generated")
    
    if image_vectors_ingested > 0:
        logger.info(f"Successfully generated {image_vectors_ingested} image vector embeddings")
    else:
        logger.warning("No new image vector embeddings were generated")
    
    # Calculate success rates
    if products_ingested > 0:
        text_vector_success_rate = text_vectors_ingested / products_ingested * 100
        image_vector_success_rate = image_vectors_ingested / products_ingested * 100
        
        logger.info(f"Text vector success rate: {text_vector_success_rate:.2f}%")
        logger.info(f"Image vector success rate: {image_vector_success_rate:.2f}%")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
