#!/usr/bin/env python3
"""
Kafka consumer for e-commerce product data

This script consumes product data from Kafka topics, generates vector embeddings
using Ollama, and ingests the data into Elasticsearch.
"""
import os
import sys
import json
import time
import base64
import random
import logging
import argparse
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ConnectionError, TransportError

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
logger = logging.getLogger("product-consumer")

# Initialize circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()
es_circuit_breaker = circuit_breaker_manager.get_circuit_breaker("elasticsearch")
ollama_circuit_breaker = circuit_breaker_manager.get_circuit_breaker("ollama")

def connect_to_elasticsearch(es_host):
    """Connect to Elasticsearch"""
    try:
        if not es_circuit_breaker.allow_request():
            logger.warning("Elasticsearch circuit breaker is open, skipping connection attempt")
            return None
        
        es = Elasticsearch(es_host)
        es.info()
        logger.info(f"Connected to Elasticsearch at {es_host}")
        es_circuit_breaker.record_success()
        return es
    except ConnectionError as e:
        logger.error(f"Could not connect to Elasticsearch: {e}")
        es_circuit_breaker.record_failure()
        return None
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {e}")
        es_circuit_breaker.record_failure()
        return None

def check_ollama_available(ollama_url):
    """Check if Ollama is available"""
    try:
        if not ollama_circuit_breaker.allow_request():
            logger.warning("Ollama circuit breaker is open, skipping availability check")
            return False
        
        response = requests.get(f"{ollama_url}/api/version", timeout=5)
        
        if response.status_code == 200:
            logger.info(f"Ollama is available at {ollama_url}")
            ollama_circuit_breaker.record_success()
            return True
        else:
            logger.error(f"Ollama returned status code {response.status_code}")
            ollama_circuit_breaker.record_failure()
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Ollama: {e}")
        ollama_circuit_breaker.record_failure()
        return False

def generate_text_embedding(text, ollama_url, ollama_model):
    """Generate vector embedding for text using Ollama"""
    try:
        if not ollama_circuit_breaker.allow_request():
            logger.warning("Ollama circuit breaker is open, skipping embedding generation")
            return None
        
        payload = {
            "model": ollama_model,
            "prompt": text
        }
        
        response = requests.post(f"{ollama_url}/api/embeddings", json=payload, timeout=30)
        
        if response.status_code == 200:
            embedding = response.json().get("embedding")
            ollama_circuit_breaker.record_success()
            return embedding
        else:
            logger.error(f"Error generating embedding: {response.status_code} - {response.text}")
            ollama_circuit_breaker.record_failure()
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error generating embedding: {e}")
        ollama_circuit_breaker.record_failure()
        return None
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        ollama_circuit_breaker.record_failure()
        return None

def generate_image_embedding(image_path, ollama_url, ollama_model):
    """Generate vector embedding for image using Ollama"""
    try:
        if not ollama_circuit_breaker.allow_request():
            logger.warning("Ollama circuit breaker is open, skipping image embedding generation")
            return None
        
        # Check if image exists
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return None
        
        # Read image file as base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Generate embedding using Ollama
        payload = {
            "model": ollama_model,
            "prompt": "",
            "image_data": f"data:image/jpeg;base64,{image_data}"
        }
        
        response = requests.post(f"{ollama_url}/api/embeddings", json=payload, timeout=60)
        
        if response.status_code == 200:
            embedding = response.json().get("embedding")
            ollama_circuit_breaker.record_success()
            return embedding
        else:
            logger.error(f"Error generating image embedding: {response.status_code} - {response.text}")
            ollama_circuit_breaker.record_failure()
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error generating image embedding: {e}")
        ollama_circuit_breaker.record_failure()
        return None
    except Exception as e:
        logger.error(f"Error generating image embedding: {e}")
        ollama_circuit_breaker.record_failure()
        return None

def generate_mock_embedding(size=384):
    """Generate a mock vector embedding for testing"""
    return [random.uniform(-1, 1) for _ in range(size)]

def index_product(es, product, ollama_url, ollama_model, use_mock=False):
    """Index a product in Elasticsearch"""
    try:
        if not es_circuit_breaker.allow_request():
            logger.warning("Elasticsearch circuit breaker is open, skipping indexing")
            return False
        
        # Generate text embedding if not already present
        if "text_embedding" not in product:
            # Combine name and description for better embedding
            text = f"{product.get('name', '')} {product.get('description', '')}"
            
            if use_mock:
                product["text_embedding"] = generate_mock_embedding()
                logger.info(f"Generated mock text embedding for product {product['id']}")
            else:
                product["text_embedding"] = generate_text_embedding(text, ollama_url, ollama_model)
                if not product["text_embedding"]:
                    logger.error(f"Failed to generate text embedding for product {product['id']}")
                    return False
        
        # Index the product
        result = es.index(index="products", document=product, id=product["id"])
        
        if result["result"] in ["created", "updated"]:
            logger.info(f"Successfully indexed product {product['id']}")
            es_circuit_breaker.record_success()
            return True
        else:
            logger.error(f"Error indexing product {product['id']}: {result}")
            es_circuit_breaker.record_failure()
            return False
    except TransportError as e:
        logger.error(f"Transport error indexing product {product['id']}: {e}")
        es_circuit_breaker.record_failure()
        return False
    except Exception as e:
        logger.error(f"Error indexing product {product['id']}: {e}")
        es_circuit_breaker.record_failure()
        return False

def update_product_image_embedding(es, product_id, image_embedding):
    """Update a product with image embedding in Elasticsearch"""
    try:
        if not es_circuit_breaker.allow_request():
            logger.warning("Elasticsearch circuit breaker is open, skipping update")
            return False
        
        # Update the product with image embedding
        update_doc = {
            "doc": {
                "image": {
                    "vector_embedding": image_embedding
                }
            }
        }
        
        result = es.update(index="products", id=product_id, body=update_doc)
        
        if result["result"] == "updated":
            logger.info(f"Successfully updated product {product_id} with image embedding")
            es_circuit_breaker.record_success()
            return True
        else:
            logger.error(f"Error updating product {product_id} with image embedding: {result}")
            es_circuit_breaker.record_failure()
            return False
    except TransportError as e:
        logger.error(f"Transport error updating product {product_id} with image embedding: {e}")
        es_circuit_breaker.record_failure()
        return False
    except Exception as e:
        logger.error(f"Error updating product {product_id} with image embedding: {e}")
        es_circuit_breaker.record_failure()
        return False

def send_to_retry_topic(record, error, topic):
    """Send a failed record to the retry topic"""
    try:
        # Add retry information to the record
        retry_info = record.get("_retry", {})
        retry_count = retry_info.get("count", 0) + 1
        
        record["_retry"] = {
            "count": retry_count,
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
            "original_topic": topic.replace("-retry", "")
        }
        
        # Create a temporary file for the record
        temp_file = f"/tmp/retry_record_{int(time.time())}.json"
        with open(temp_file, "w") as f:
            f.write(json.dumps(record) + "\n")
        
        # Send to Kafka using kafka-console-producer
        retry_topic = f"{topic}-retry"
        cmd = f"cat {temp_file} | docker exec -i kafka kafka-console-producer --broker-list localhost:9092 --topic {retry_topic}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error sending to retry topic {retry_topic}: {result.stderr}")
            return False
        else:
            logger.info(f"Successfully sent record to retry topic {retry_topic}")
            return True
    except Exception as e:
        logger.error(f"Error sending to retry topic: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)

def send_to_dead_letter_queue(record, error, topic):
    """Send a record to the dead letter queue after max retries"""
    try:
        # Add dead letter information to the record
        record["_dead_letter"] = {
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
            "original_topic": topic
        }
        
        # Create a temporary file for the record
        temp_file = f"/tmp/dlq_record_{int(time.time())}.json"
        with open(temp_file, "w") as f:
            f.write(json.dumps(record) + "\n")
        
        # Send to Kafka using kafka-console-producer
        cmd = f"cat {temp_file} | docker exec -i kafka kafka-console-producer --broker-list localhost:9092 --topic dead-letter-queue"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error sending to dead letter queue: {result.stderr}")
            return False
        else:
            logger.info(f"Successfully sent record to dead letter queue")
            return True
    except Exception as e:
        logger.error(f"Error sending to dead letter queue: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)

def process_product(record, es, ollama_url, ollama_model, use_mock=False):
    """Process a product record from Kafka"""
    try:
        # Check if this is a retry
        retry_info = record.get("_retry", {})
        retry_count = retry_info.get("count", 0)
        
        if retry_count >= 5:
            logger.warning(f"Max retries exceeded for product {record.get('id')}, sending to dead letter queue")
            send_to_dead_letter_queue(record, "Max retries exceeded", "products")
            return True
        
        # Index the product
        success = index_product(es, record, ollama_url, ollama_model, use_mock)
        
        if not success and retry_count < 5:
            logger.warning(f"Failed to index product {record.get('id')}, sending to retry topic")
            send_to_retry_topic(record, "Failed to index product", "products")
        
        return success
    except Exception as e:
        logger.error(f"Error processing product: {e}")
        if retry_count < 5:
            send_to_retry_topic(record, str(e), "products")
        else:
            send_to_dead_letter_queue(record, str(e), "products")
        return False

def process_product_image(record, es, ollama_url, ollama_model, use_mock=False):
    """Process a product image record from Kafka"""
    try:
        # Check if this is a retry
        retry_info = record.get("_retry", {})
        retry_count = retry_info.get("count", 0)
        
        if retry_count >= 5:
            logger.warning(f"Max retries exceeded for product image {record.get('product_id')}, sending to dead letter queue")
            send_to_dead_letter_queue(record, "Max retries exceeded", "product-images")
            return True
        
        # Get product ID and image path
        product_id = record.get("product_id")
        image_path = record.get("image_path")
        
        if not product_id or not image_path:
            logger.error(f"Missing product_id or image_path in record: {record}")
            send_to_dead_letter_queue(record, "Missing product_id or image_path", "product-images")
            return False
        
        # Generate image embedding
        if use_mock:
            image_embedding = generate_mock_embedding()
            logger.info(f"Generated mock image embedding for product {product_id}")
        else:
            image_embedding = generate_image_embedding(image_path, ollama_url, ollama_model)
        
        if not image_embedding:
            logger.error(f"Failed to generate image embedding for product {product_id}")
            if retry_count < 5:
                send_to_retry_topic(record, "Failed to generate image embedding", "product-images")
            else:
                send_to_dead_letter_queue(record, "Failed to generate image embedding", "product-images")
            return False
        
        # Update product with image embedding
        success = update_product_image_embedding(es, product_id, image_embedding)
        
        if not success and retry_count < 5:
            logger.warning(f"Failed to update product {product_id} with image embedding, sending to retry topic")
            send_to_retry_topic(record, "Failed to update product with image embedding", "product-images")
        
        return success
    except Exception as e:
        logger.error(f"Error processing product image: {e}")
        if retry_count < 5:
            send_to_retry_topic(record, str(e), "product-images")
        else:
            send_to_dead_letter_queue(record, str(e), "product-images")
        return False

def consume_from_topic(topic, max_messages=None, es_host="http://localhost:9200", 
                      ollama_host="http://localhost:11434", ollama_model="llama3", use_mock=False):
    """Consume messages from a Kafka topic"""
    logger.info(f"Starting consumer for topic {topic}")
    
    # Connect to Elasticsearch
    es = connect_to_elasticsearch(es_host)
    if not es:
        logger.error("Could not connect to Elasticsearch, exiting")
        return 0, 0, 0
    
    # Check if Ollama is available (if not using mock)
    if not use_mock:
        ollama_available = check_ollama_available(ollama_host)
        if not ollama_available:
            logger.warning("Ollama is not available, using mock embeddings instead")
            use_mock = True
    
    # Use kafka-console-consumer to get messages
    cmd = f"docker exec -i kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic {topic} --from-beginning"
    
    if max_messages:
        cmd += f" --max-messages {max_messages}"
    
    try:
        # Start the consumer process
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Process messages
        message_count = 0
        success_count = 0
        failure_count = 0
        
        while True:
            line = process.stdout.readline()
            
            if not line and process.poll() is not None:
                break
            
            if line:
                line = line.strip()
                if line:
                    message_count += 1
                    
                    try:
                        # Parse the message
                        record = json.loads(line)
                        
                        # Process based on topic
                        if topic == "products":
                            success = process_product(record, es, ollama_host, ollama_model, use_mock)
                        elif topic == "product-images":
                            success = process_product_image(record, es, ollama_host, ollama_model, use_mock)
                        else:
                            logger.warning(f"Unknown topic: {topic}")
                            success = False
                        
                        if success:
                            success_count += 1
                        else:
                            failure_count += 1
                        
                        # Log progress
                        if message_count % 10 == 0:
                            logger.info(f"Processed {message_count} messages from topic {topic} ({success_count} successful, {failure_count} failed)")
                        
                        # Check if we've reached max_messages
                        if max_messages and message_count >= max_messages:
                            logger.info(f"Reached max messages limit ({max_messages})")
                            break
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing message: {e}")
                        failure_count += 1
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        failure_count += 1
        
        # Log final stats
        logger.info(f"Completed processing {message_count} messages from topic {topic}")
        logger.info(f"Success: {success_count}, Failures: {failure_count}")
        
        return message_count, success_count, failure_count
    
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
        return message_count, success_count, failure_count
    except Exception as e:
        logger.error(f"Error consuming from topic {topic}: {e}")
        return 0, 0, 0

def main():
    parser = argparse.ArgumentParser(description="Consume e-commerce product data from Kafka")
    parser.add_argument("--topic", choices=["products", "product-images", "all"], default="all", help="Kafka topic to consume from")
    parser.add_argument("--max-messages", type=int, help="Maximum number of messages to consume")
    parser.add_argument("--es-host", default="http://localhost:9200", help="Elasticsearch host")
    parser.add_argument("--ollama-host", default="http://localhost:11434", help="Ollama host")
    parser.add_argument("--ollama-model", default="llama3", help="Ollama model to use for embeddings")
    parser.add_argument("--use-mock", action="store_true", help="Use mock embeddings instead of Ollama")
    args = parser.parse_args()
    
    # Consume from topics
    if args.topic == "all":
        # Consume from products topic first
        products_count, products_success, products_failure = consume_from_topic(
            "products", args.max_messages, args.es_host, args.ollama_host, args.ollama_model, args.use_mock
        )
        
        # Then consume from product-images topic
        images_count, images_success, images_failure = consume_from_topic(
            "product-images", args.max_messages, args.es_host, args.ollama_host, args.ollama_model, args.use_mock
        )
        
        # Log overall stats
        total_count = products_count + images_count
        total_success = products_success + images_success
        total_failure = products_failure + images_failure
        
        logger.info(f"Overall stats: {total_count} messages processed, {total_success} successful, {total_failure} failed")
    else:
        # Consume from specified topic
        count, success, failure = consume_from_topic(
            args.topic, args.max_messages, args.es_host, args.ollama_host, args.ollama_model, args.use_mock
        )
        
        logger.info(f"Overall stats: {count} messages processed, {success} successful, {failure} failed")
    
    logger.info("Consumer completed successfully!")

if __name__ == "__main__":
    main()
