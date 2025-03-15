#!/usr/bin/env python3
"""
Script to ingest products into Elasticsearch via Kafka.

This script:
1. Loads Elasticsearch index mappings
2. Creates the index definition in Elasticsearch
3. Pushes product data into the Kafka topic
4. Sets up consumers to pull data from Kafka, generate embeddings, and index in Elasticsearch
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
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_INDEX_PRODUCTS,
    KAFKA_TOPIC_PRODUCTS,
    KAFKA_TOPIC_PRODUCT_IMAGES
)
from scripts.kafka.circuit_breaker_manager import CircuitBreakerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ingest-products")

def setup_elasticsearch_index(es_host, mapping_file):
    """
    Set up Elasticsearch index with the specified mapping.
    
    Args:
        es_host: Elasticsearch host URL
        mapping_file: Path to the mapping file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load mapping from file
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)
        
        # Check if index exists
        check_cmd = f"curl -s -X HEAD {es_host}/{ELASTICSEARCH_INDEX_PRODUCTS}"
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Index {ELASTICSEARCH_INDEX_PRODUCTS} already exists, deleting it")
            delete_cmd = f"curl -s -X DELETE {es_host}/{ELASTICSEARCH_INDEX_PRODUCTS}"
            subprocess.run(delete_cmd, shell=True, check=True)
        
        # Create index with mapping
        create_cmd = f"curl -s -X PUT {es_host}/{ELASTICSEARCH_INDEX_PRODUCTS} -H 'Content-Type: application/json' -d '{json.dumps(mapping)}'"
        result = subprocess.run(create_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error creating index: {result.stderr}")
            return False
        
        logger.info(f"Successfully created index {ELASTICSEARCH_INDEX_PRODUCTS}")
        return True
    
    except Exception as e:
        logger.error(f"Error setting up Elasticsearch index: {str(e)}")
        return False

def push_products_to_kafka(products_file, batch_size=100, max_products=None):
    """
    Push products from JSON file to Kafka topic.
    
    Args:
        products_file: Path to products JSON file
        batch_size: Number of products to process in each batch
        max_products: Maximum number of products to process
    
    Returns:
        tuple: (success_count, failure_count)
    """
    try:
        # Use the existing product_producer.py script
        cmd = [
            "python", f"{project_root}/scripts/kafka/product_producer.py",
            "--products-file", products_file,
            "--batch-size", str(batch_size)
        ]
        
        if max_products:
            cmd.extend(["--max-products", str(max_products)])
        
        logger.info(f"Pushing products to Kafka topic {KAFKA_TOPIC_PRODUCTS}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error pushing products to Kafka: {result.stderr}")
            return 0, 0
        
        # Parse output to get success/failure counts
        output = result.stdout
        success_count = 0
        failure_count = 0
        
        for line in output.splitlines():
            if "successfully sent to Kafka" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "Products:":
                        counts = parts[i+1].split('/')
                        success_count = int(counts[0])
                        total = int(counts[1])
                        failure_count = total - success_count
                        break
        
        logger.info(f"Pushed {success_count} products to Kafka (failed: {failure_count})")
        return success_count, failure_count
    
    except Exception as e:
        logger.error(f"Error pushing products to Kafka: {str(e)}")
        return 0, 0

def consume_from_kafka(topic, max_messages=None, es_host="http://localhost:9200", 
                      ollama_host="http://localhost:11434", ollama_model="llama3"):
    """
    Consume messages from Kafka topic, generate embeddings, and index in Elasticsearch.
    
    Args:
        topic: Kafka topic to consume from
        max_messages: Maximum number of messages to consume
        es_host: Elasticsearch host URL
        ollama_host: Ollama host URL
        ollama_model: Ollama model to use for embeddings
    
    Returns:
        tuple: (message_count, success_count, failure_count)
    """
    try:
        # Use the existing product_consumer.py script
        cmd = [
            "python", f"{project_root}/scripts/kafka/product_consumer.py",
            "--topic", topic,
            "--es-host", es_host,
            "--ollama-host", ollama_host,
            "--ollama-model", ollama_model
        ]
        
        if max_messages:
            cmd.extend(["--max-messages", str(max_messages)])
        
        logger.info(f"Consuming from Kafka topic {topic}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error consuming from Kafka: {result.stderr}")
            return 0, 0, 0
        
        # Parse output to get counts
        output = result.stdout
        message_count = 0
        success_count = 0
        failure_count = 0
        
        for line in output.splitlines():
            if "Overall stats:" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "processed,":
                        message_count = int(parts[i-1])
                        success_count = int(parts[i+1])
                        failure_count = int(parts[i+3])
                        break
        
        logger.info(f"Consumed {message_count} messages from {topic} (success: {success_count}, failed: {failure_count})")
        return message_count, success_count, failure_count
    
    except Exception as e:
        logger.error(f"Error consuming from Kafka: {str(e)}")
        return 0, 0, 0

def verify_elasticsearch_index(es_host):
    """
    Verify that the Elasticsearch index has been populated.
    
    Args:
        es_host: Elasticsearch host URL
    
    Returns:
        int: Number of documents in the index
    """
    try:
        cmd = f"curl -s -X GET {es_host}/{ELASTICSEARCH_INDEX_PRODUCTS}/_count"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error getting document count: {result.stderr}")
            return 0
        
        count_data = json.loads(result.stdout)
        count = count_data.get("count", 0)
        
        logger.info(f"Found {count} documents in index {ELASTICSEARCH_INDEX_PRODUCTS}")
        return count
    
    except Exception as e:
        logger.error(f"Error verifying Elasticsearch index: {str(e)}")
        return 0

def main():
    """Main function to orchestrate the ingestion process."""
    parser = argparse.ArgumentParser(description="Ingest products into Elasticsearch via Kafka")
    parser.add_argument("--products-file", default="data/products.json", help="Path to products JSON file")
    parser.add_argument("--mapping-file", default="config/elasticsearch/mappings/products.json", help="Path to Elasticsearch mapping file")
    parser.add_argument("--es-host", default="http://localhost:9200", help="Elasticsearch host URL")
    parser.add_argument("--ollama-host", default="http://localhost:11434", help="Ollama host URL")
    parser.add_argument("--ollama-model", default="llama3", help="Ollama model to use for embeddings")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--max-products", type=int, help="Maximum number of products to process")
    parser.add_argument("--skip-setup", action="store_true", help="Skip Elasticsearch index setup")
    parser.add_argument("--skip-producer", action="store_true", help="Skip pushing products to Kafka")
    parser.add_argument("--skip-consumer", action="store_true", help="Skip consuming from Kafka")
    args = parser.parse_args()
    
    # Set up Elasticsearch index
    if not args.skip_setup:
        logger.info("Setting up Elasticsearch index")
        success = setup_elasticsearch_index(args.es_host, args.mapping_file)
        if not success:
            logger.error("Failed to set up Elasticsearch index, exiting")
            return
    else:
        logger.info("Skipping Elasticsearch index setup")
    
    # Push products to Kafka
    if not args.skip_producer:
        logger.info("Pushing products to Kafka")
        success_count, failure_count = push_products_to_kafka(
            args.products_file, args.batch_size, args.max_products
        )
        
        if success_count == 0:
            logger.error("Failed to push any products to Kafka, exiting")
            return
    else:
        logger.info("Skipping pushing products to Kafka")
    
    # Consume from Kafka
    if not args.skip_consumer:
        logger.info("Consuming from Kafka")
        
        # First consume from products topic
        message_count, success_count, failure_count = consume_from_kafka(
            KAFKA_TOPIC_PRODUCTS, args.max_products, args.es_host, args.ollama_host, args.ollama_model
        )
        
        if message_count == 0:
            logger.warning("No messages consumed from products topic")
        
        # Then consume from product-images topic
        image_count, image_success, image_failure = consume_from_kafka(
            KAFKA_TOPIC_PRODUCT_IMAGES, args.max_products, args.es_host, args.ollama_host, args.ollama_model
        )
        
        if image_count == 0:
            logger.warning("No messages consumed from product-images topic")
    else:
        logger.info("Skipping consuming from Kafka")
    
    # Verify Elasticsearch index
    doc_count = verify_elasticsearch_index(args.es_host)
    
    if doc_count > 0:
        logger.info(f"Successfully ingested {doc_count} products into Elasticsearch")
    else:
        logger.warning("No products found in Elasticsearch index")
    
    logger.info("Ingestion process completed")

if __name__ == "__main__":
    main()
