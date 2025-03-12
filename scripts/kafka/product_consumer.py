#!/usr/bin/env python3
"""
Kafka consumer for product data using subprocess to call kafka-console-consumer
This avoids dependency issues with the kafka-python library
"""
import os
import sys
import json
import time
import logging
import subprocess
import requests
import redis
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_INDEX_PRODUCTS,
    KAFKA_HOST,
    KAFKA_TOPIC_PRODUCTS,
    KAFKA_TOPIC_FAILED_INGESTION,
    REDIS_HOST,
    REDIS_PORT,
    TEXT_EMBEDDING_DIMS,
    IMAGE_EMBEDDING_DIMS
)
from app.utils.embedding import (
    get_text_embedding,
    get_image_embedding,
    generate_mock_embedding
)
from scripts.kafka.circuit_breaker import CircuitBreaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Redis client for circuit breaker
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

# Initialize circuit breaker
circuit_breaker = CircuitBreaker("ollama_embeddings", redis_client)

def ingest_to_elasticsearch(product):
    """
    Ingest a product to Elasticsearch.
    
    Args:
        product: Product data with embeddings
    
    Returns:
        tuple: (success, error_message)
    """
    try:
        # Extract ID from the product
        product_id = product.get('id')
        
        if not product_id:
            return False, "Product ID is missing"
        
        # Construct the URL for the Elasticsearch API
        url = f"{ELASTICSEARCH_HOST}/{ELASTICSEARCH_INDEX_PRODUCTS}/_doc/{product_id}"
        
        # Send the product to Elasticsearch
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=product
        )
        
        # Check if the request was successful
        if response.status_code in (200, 201):
            logger.info(f"Successfully ingested product {product_id} to Elasticsearch")
            return True, None
        else:
            return False, f"Elasticsearch error: {response.status_code} - {response.text}"
    
    except Exception as e:
        return False, f"Exception during ingestion: {str(e)}"

def send_to_retry_topic(product, error, retry_count=1):
    """
    Send a failed product to the retry topic.
    
    Args:
        product: Product data
        error: Error message
        retry_count: Retry count
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Add retry information to the product
        product['retry_count'] = retry_count
        product['last_error'] = error
        product['timestamp'] = time.time()
        
        # Write to a temporary file
        temp_file = f"/tmp/retry_product_{int(time.time())}.json"
        with open(temp_file, 'w') as f:
            f.write(json.dumps(product))
        
        # Send to retry topic using kafka-console-producer
        cmd = f"cat {temp_file} | docker exec -i kafka kafka-console-producer --broker-list kafka:9092 --topic {KAFKA_TOPIC_FAILED_INGESTION}"
        subprocess.run(cmd, shell=True, check=True)
        
        # Clean up
        os.remove(temp_file)
        
        return True
    except Exception as e:
        logger.error(f"Error sending to retry topic: {e}")
        return False

def process_product(product):
    """
    Process a product message from Kafka.
    
    Args:
        product: Product data
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if circuit breaker allows the request
        if not circuit_breaker.allow_request():
            logger.warning("Circuit breaker is open, skipping product processing")
            # Send to retry topic
            send_to_retry_topic(product, "Circuit breaker is open")
            return False
        
        # Generate text embedding for product description
        text_content = f"{product['name']} {product['description']}"
        
        try:
            text_embedding = get_text_embedding(text_content)
            
            # If embedding generation is successful, record success
            if text_embedding is not None:
                circuit_breaker.record_success()
            else:
                # If embedding generation fails, use mock embedding and record failure
                logger.warning(f"Using mock text embedding for product {product['id']}")
                text_embedding = generate_mock_embedding(TEXT_EMBEDDING_DIMS)
                circuit_breaker.record_failure()
        except Exception as e:
            # If embedding generation fails, use mock embedding and record failure
            logger.error(f"Error generating text embedding: {str(e)}")
            text_embedding = generate_mock_embedding(TEXT_EMBEDDING_DIMS)
            circuit_breaker.record_failure()
        
        # Update product with text embedding
        product["text_embedding"] = text_embedding
        
        # Generate image embedding if image exists
        image_path = product["image"]["url"]
        if os.path.exists(image_path):
            try:
                image_embedding = get_image_embedding(image_path)
                
                # If embedding generation is successful, record success
                if image_embedding is not None:
                    circuit_breaker.record_success()
                else:
                    # If embedding generation fails, use mock embedding and record failure
                    logger.warning(f"Using mock image embedding for product {product['id']}")
                    image_embedding = generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
                    circuit_breaker.record_failure()
            except Exception as e:
                # If embedding generation fails, use mock embedding and record failure
                logger.error(f"Error generating image embedding: {str(e)}")
                image_embedding = generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
                circuit_breaker.record_failure()
        else:
            # If image doesn't exist, use mock embedding
            logger.warning(f"Image file not found: {image_path}")
            image_embedding = generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
        
        # Update product with image embedding
        product["image"]["vector_embedding"] = image_embedding
        
        # Ingest product to Elasticsearch
        success, error = ingest_to_elasticsearch(product)
        
        if not success:
            logger.error(f"Failed to ingest product {product['id']}: {error}")
            
            # Get retry count if it exists
            retry_count = product.get('retry_count', 0) + 1
            
            # Send to retry topic if retry count is less than max retries
            if retry_count <= 3:  # Max 3 retries
                send_to_retry_topic(product, error, retry_count)
                logger.info(f"Sent product to retry topic. Retry count: {retry_count}")
            else:
                logger.warning(f"Max retries exceeded for product {product['id']}. Dropping product.")
            
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error processing product: {str(e)}")
        return False

def consume_from_kafka(topic, max_messages=None, max_workers=4):
    """
    Consume messages from Kafka topic using subprocess.
    
    Args:
        topic: Kafka topic to consume from
        max_messages: Maximum number of messages to consume (None for unlimited)
        max_workers: Maximum number of worker threads
    """
    try:
        # Create a temporary file for the consumer output
        temp_file = f"/tmp/kafka_consumer_{int(time.time())}.out"
        
        # Start Kafka consumer
        cmd = f"docker exec -i kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic {topic} --from-beginning"
        
        if max_messages:
            cmd += f" --max-messages {max_messages}"
        
        # Redirect output to temporary file
        cmd += f" > {temp_file}"
        
        # Run the consumer in the background
        process = subprocess.Popen(cmd, shell=True)
        
        logger.info(f"Started Kafka consumer for topic {topic}")
        
        # Wait for some data to be available
        time.sleep(2)
        
        # Process messages as they arrive
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            message_count = 0
            
            while True:
                # Check if process is still running
                if process.poll() is not None:
                    logger.info(f"Kafka consumer process exited with code {process.returncode}")
                    break
                
                # Read new messages from the file
                with open(temp_file, 'r') as f:
                    lines = f.readlines()
                
                # Process new messages
                for line in lines[message_count:]:
                    message_count += 1
                    
                    # Skip empty lines
                    if not line.strip():
                        continue
                    
                    try:
                        # Parse the message
                        product = json.loads(line.strip())
                        
                        # Submit the product for processing
                        executor.submit(process_product, product)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse message: {line.strip()}")
                
                # Sleep briefly before checking for new messages
                time.sleep(1)
        
        # Clean up
        os.remove(temp_file)
        
        logger.info(f"Processed {message_count} messages from topic {topic}")
    
    except Exception as e:
        logger.error(f"Error consuming from Kafka: {str(e)}")

def main():
    """Main function to consume products from Kafka and process them."""
    logger.info("Starting product consumer")
    
    # Consume from products topic
    consume_from_kafka(KAFKA_TOPIC_PRODUCTS)
    
    logger.info("Product consumer completed")

if __name__ == "__main__":
    main()
