#!/usr/bin/env python3
"""
Script to update existing products in Elasticsearch with vector embeddings.

This script:
1. Retrieves products from Elasticsearch that don't have embeddings
2. Generates embeddings using Ollama or falls back to mock embeddings if Ollama is not available
3. Updates the products in Elasticsearch with the generated embeddings
"""
import os
import sys
import json
import time
import random
import logging
import argparse
import requests
import numpy as np
from pathlib import Path
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import TransportError

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_INDEX_PRODUCTS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("update-embeddings")

def connect_to_elasticsearch(es_host):
    """Connect to Elasticsearch."""
    try:
        es = Elasticsearch(es_host)
        info = es.info()
        logger.info(f"Connected to Elasticsearch: {info['version']['number']}")
        return es
    except Exception as e:
        logger.error(f"Error connecting to Elasticsearch: {str(e)}")
        return None

def check_ollama_availability(ollama_url):
    """Check if Ollama is available."""
    try:
        response = requests.get(f"{ollama_url}/api/version", timeout=5)
        if response.status_code == 200:
            logger.info(f"Ollama is available: {response.json()}")
            return True
        else:
            logger.warning(f"Ollama returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.warning(f"Ollama is not available: {str(e)}")
        return False

def generate_text_embedding_with_ollama(text, ollama_url, ollama_model, max_retries=5, retry_delay=5):
    """Generate vector embedding for text using Ollama with retries."""
    retries = 0
    while retries < max_retries:
        try:
            payload = {
                "model": ollama_model,
                "prompt": text
            }
            
            response = requests.post(f"{ollama_url}/api/embeddings", json=payload, timeout=30)
            
            if response.status_code == 200:
                embedding = response.json().get("embedding")
                return embedding
            else:
                logger.error(f"Error generating embedding: {response.status_code} - {response.text}")
                retries += 1
                logger.warning(f"Retrying embedding generation (attempt {retries}/{max_retries})")
                time.sleep(retry_delay * (2 ** (retries - 1)))  # Exponential backoff
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error generating embedding: {e}")
            retries += 1
            logger.warning(f"Retrying embedding generation after request error (attempt {retries}/{max_retries})")
            time.sleep(retry_delay * (2 ** (retries - 1)))  # Exponential backoff
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            retries += 1
            logger.warning(f"Retrying embedding generation after error (attempt {retries}/{max_retries})")
            time.sleep(retry_delay * (2 ** (retries - 1)))  # Exponential backoff
    
    logger.error(f"Failed to generate embedding after {max_retries} attempts")
    return None

def generate_mock_text_embedding(text, dims=384):
    """Generate a mock text embedding for testing purposes."""
    # Use a deterministic seed based on the text to ensure consistency
    seed = sum(ord(c) for c in text)
    random.seed(seed)
    np.random.seed(seed)
    
    # Generate a random vector and normalize it
    vector = np.random.normal(0, 1, dims)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    
    return vector.tolist()

def generate_mock_image_embedding(image_path, dims=512):
    """Generate a mock image embedding for testing purposes."""
    # Use a deterministic seed based on the image path to ensure consistency
    seed = sum(ord(c) for c in image_path)
    random.seed(seed)
    np.random.seed(seed)
    
    # Generate a random vector and normalize it
    vector = np.random.normal(0, 1, dims)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    
    return vector.tolist()

def get_products_without_embeddings(es, batch_size=100, max_products=None):
    """Get products from Elasticsearch that don't have text embeddings."""
    query = {
        "bool": {
            "must_not": {
                "exists": {
                    "field": "text_embedding"
                }
            }
        }
    }
    
    # Set up the search parameters
    search_params = {
        "index": ELASTICSEARCH_INDEX_PRODUCTS,
        "query": query,
        "size": batch_size
    }
    
    # If max_products is specified, limit the number of products
    total_products = 0
    products = []
    
    # Use the scroll API to get all products
    scroll_time = "1m"
    result = es.search(
        **search_params,
        scroll=scroll_time
    )
    
    # Process the first batch of results
    scroll_id = result["_scroll_id"]
    hits = result["hits"]["hits"]
    
    while hits and (max_products is None or total_products < max_products):
        # Add the current batch of products
        for hit in hits:
            products.append(hit["_source"])
            total_products += 1
            
            # If we've reached the maximum number of products, break
            if max_products is not None and total_products >= max_products:
                break
        
        # If we've reached the maximum number of products, break
        if max_products is not None and total_products >= max_products:
            break
        
        # Get the next batch of results
        result = es.scroll(
            scroll_id=scroll_id,
            scroll=scroll_time
        )
        
        scroll_id = result["_scroll_id"]
        hits = result["hits"]["hits"]
    
    # Clear the scroll
    es.clear_scroll(scroll_id=scroll_id)
    
    logger.info(f"Found {total_products} products without text embeddings")
    return products

def update_product_with_embedding(es, product, text_embedding):
    """Update a product in Elasticsearch with text embedding."""
    try:
        # Update the product with text embedding
        product["text_embedding"] = text_embedding
        
        # Update the product in Elasticsearch
        result = es.index(
            index=ELASTICSEARCH_INDEX_PRODUCTS,
            id=product["id"],
            document=product
        )
        
        if result["result"] in ["created", "updated"]:
            logger.info(f"Successfully updated product {product['id']} with text embedding")
            return True
        else:
            logger.error(f"Error updating product {product['id']} with text embedding: {result}")
            return False
    except TransportError as e:
        logger.error(f"Transport error updating product {product['id']} with text embedding: {e}")
        return False
    except Exception as e:
        logger.error(f"Error updating product {product['id']} with text embedding: {e}")
        return False

def update_products_with_embeddings(es, products, ollama_available, ollama_url, ollama_model):
    """Update products with embeddings."""
    success_count = 0
    failure_count = 0
    
    for i, product in enumerate(products):
        # Generate text embedding
        text = f"{product.get('name', '')} {product.get('description', '')}"
        
        if ollama_available:
            # Generate embedding with Ollama
            text_embedding = generate_text_embedding_with_ollama(text, ollama_url, ollama_model)
            if not text_embedding:
                logger.warning(f"Failed to generate text embedding with Ollama for product {product['id']}, falling back to mock embedding")
                text_embedding = generate_mock_text_embedding(text)
        else:
            # Generate mock embedding
            logger.info(f"Ollama not available, generating mock text embedding for product {product['id']}")
            text_embedding = generate_mock_text_embedding(text)
        
        # Update product with embedding
        success = update_product_with_embedding(es, product, text_embedding)
        
        if success:
            success_count += 1
        else:
            failure_count += 1
        
        # Log progress
        if (i + 1) % 100 == 0 or i == len(products) - 1:
            logger.info(f"Processed {i + 1}/{len(products)} products (success: {success_count}, failure: {failure_count})")
    
    return success_count, failure_count

def main():
    """Main function to update products with embeddings."""
    parser = argparse.ArgumentParser(description="Update products in Elasticsearch with vector embeddings")
    parser.add_argument("--es-host", default="http://localhost:9200", help="Elasticsearch host URL")
    parser.add_argument("--ollama-host", default="http://localhost:11434", help="Ollama host URL")
    parser.add_argument("--ollama-model", default="llama3", help="Ollama model to use for embeddings")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--max-products", type=int, help="Maximum number of products to process")
    parser.add_argument("--force-mock", action="store_true", help="Force using mock embeddings even if Ollama is available")
    args = parser.parse_args()
    
    # Connect to Elasticsearch
    es = connect_to_elasticsearch(args.es_host)
    if not es:
        logger.error("Failed to connect to Elasticsearch, exiting")
        return
    
    # Check if Ollama is available
    ollama_available = check_ollama_availability(args.ollama_host)
    if args.force_mock:
        logger.info("Forcing use of mock embeddings")
        ollama_available = False
    
    # Get products without embeddings
    products = get_products_without_embeddings(es, args.batch_size, args.max_products)
    
    if not products:
        logger.info("No products found without embeddings, exiting")
        return
    
    # Update products with embeddings
    success_count, failure_count = update_products_with_embeddings(
        es, products, ollama_available, args.ollama_host, args.ollama_model
    )
    
    logger.info(f"Updated {success_count} products with embeddings (failed: {failure_count})")
    
    # Verify the updates
    remaining_products = get_products_without_embeddings(es, 1)
    remaining_count = len(remaining_products)
    
    if remaining_count > 0:
        logger.info(f"There are still {remaining_count} products without embeddings")
        if args.max_products:
            logger.info("Run the script again without --max-products to update all remaining products")
    else:
        logger.info("All products have been updated with embeddings")

if __name__ == "__main__":
    main()
