#!/usr/bin/env python3
"""
Script to index generated data into Elasticsearch.
"""
import os
import sys
import json
import logging
from pathlib import Path
from elasticsearch import Elasticsearch, helpers

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_INDEX_PRODUCTS,
    ELASTICSEARCH_INDEX_PERSONAS,
    TEXT_EMBEDDING_DIMS,
    IMAGE_EMBEDDING_DIMS
)
from app.utils.embedding import (
    check_ollama_connection,
    get_text_embedding,
    get_image_embedding,
    generate_mock_embedding
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def create_indices(es: Elasticsearch):
    """
    Create Elasticsearch indices with appropriate mappings.
    
    Args:
        es: Elasticsearch client
    """
    logger.info("Creating Elasticsearch indices")
    
    # Products index mapping
    products_mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "analyzer": "english",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "description": {
                    "type": "text",
                    "analyzer": "english"
                },
                "category": {"type": "keyword"},
                "subcategory": {"type": "keyword"},
                "price": {"type": "float"},
                "brand": {"type": "keyword"},
                "attributes": {"type": "object", "dynamic": True},
                "image": {
                    "properties": {
                        "url": {"type": "keyword"},
                        "vector_embedding": {
                            "type": "dense_vector", 
                            "dims": IMAGE_EMBEDDING_DIMS,
                            "index": True,
                            "similarity": "cosine"
                        }
                    }
                },
                "text_embedding": {
                    "type": "dense_vector", 
                    "dims": TEXT_EMBEDDING_DIMS,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "index": {
                "refresh_interval": "1s"
            }
        }
    }
    
    # Buyer personas index mapping
    personas_mapping = {
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "preferences": {"type": "object", "dynamic": True},
                "search_history": {"type": "text"},
                "clickstream": {"type": "keyword"},
                "purchase_history": {"type": "keyword"}
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "index": {
                "refresh_interval": "1s"
            }
        }
    }
    
    # Create indices if they don't exist
    if not es.indices.exists(index=ELASTICSEARCH_INDEX_PRODUCTS):
        es.indices.create(index=ELASTICSEARCH_INDEX_PRODUCTS, body=products_mapping)
        logger.info(f"Created index: {ELASTICSEARCH_INDEX_PRODUCTS}")
    
    if not es.indices.exists(index=ELASTICSEARCH_INDEX_PERSONAS):
        es.indices.create(index=ELASTICSEARCH_INDEX_PERSONAS, body=personas_mapping)
        logger.info(f"Created index: {ELASTICSEARCH_INDEX_PERSONAS}")

def index_products(es: Elasticsearch, use_ollama: bool = True):
    """
    Index products into Elasticsearch.
    
    Args:
        es: Elasticsearch client
        use_ollama: Whether to use Ollama for embeddings or generate mock embeddings
    """
    data_file = Path("data/products.json")
    
    if not data_file.exists():
        logger.error("Products data file not found. Run generate_data.py first.")
        return
    
    with open(data_file, "r") as f:
        products = json.load(f)
    
    if not products:
        logger.warning("No products to index")
        return
    
    logger.info(f"Processing {len(products)} products for indexing")
    
    # Process products to add embeddings
    for i, product in enumerate(products):
        if i % 50 == 0:
            logger.info(f"Processing product {i+1}/{len(products)}")
        
        # Generate text embedding for product description
        if use_ollama:
            # Combine name and description for better text embedding
            text_content = f"{product['name']} {product['description']}"
            text_embedding = get_text_embedding(text_content)
            
            # If Ollama fails, use mock embedding
            if text_embedding is None:
                logger.warning(f"Using mock text embedding for product {product['id']}")
                text_embedding = generate_mock_embedding(TEXT_EMBEDDING_DIMS)
        else:
            text_embedding = generate_mock_embedding(TEXT_EMBEDDING_DIMS)
        
        # Update product with text embedding
        product["text_embedding"] = text_embedding
        
        # Generate image embedding if image exists
        image_path = product["image"]["url"]
        if os.path.exists(image_path) and use_ollama:
            image_embedding = get_image_embedding(image_path)
            
            # If Ollama fails, use mock embedding
            if image_embedding is None:
                logger.warning(f"Using mock image embedding for product {product['id']}")
                image_embedding = generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
        else:
            image_embedding = generate_mock_embedding(IMAGE_EMBEDDING_DIMS)
        
        # Update product with image embedding
        if "vector_embedding" not in product["image"]:
            product["image"]["vector_embedding"] = {}
        product["image"]["vector_embedding"] = image_embedding
    
    # Prepare bulk indexing actions
    actions = [
        {
            "_index": ELASTICSEARCH_INDEX_PRODUCTS,
            "_id": product["id"],
            "_source": product
        }
        for product in products
    ]
    
    # Perform bulk indexing
    logger.info("Bulk indexing products to Elasticsearch")
    success, failed = helpers.bulk(es, actions, stats_only=True)
    logger.info(f"Indexed {success} products, {failed} failed")

def index_personas(es: Elasticsearch):
    """
    Index buyer personas into Elasticsearch.
    
    Args:
        es: Elasticsearch client
    """
    data_file = Path("data/personas.json")
    
    if not data_file.exists():
        logger.error("Personas data file not found. Run generate_data.py first.")
        return
    
    with open(data_file, "r") as f:
        personas = json.load(f)
    
    if not personas:
        logger.warning("No personas to index")
        return
    
    # Prepare bulk indexing actions
    actions = [
        {
            "_index": ELASTICSEARCH_INDEX_PERSONAS,
            "_id": persona["id"],
            "_source": persona
        }
        for persona in personas
    ]
    
    # Perform bulk indexing
    success, failed = helpers.bulk(es, actions, stats_only=True)
    logger.info(f"Indexed {success} personas, {failed} failed")

def main():
    """Main function to index all data into Elasticsearch."""
    logger.info("Starting data indexing")
    
    # Connect to Elasticsearch
    try:
        es = Elasticsearch(ELASTICSEARCH_HOST)
        
        # Check connection
        if not es.ping():
            logger.error("Could not connect to Elasticsearch. Make sure it's running.")
            return
        
        logger.info("Successfully connected to Elasticsearch")
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
        return
    
    # Check Ollama connection
    use_ollama = check_ollama_connection()
    if use_ollama:
        logger.info("Successfully connected to Ollama")
    else:
        logger.warning("Could not connect to Ollama. Will use mock embeddings.")
    
    # Create indices
    create_indices(es)
    
    # Index data
    index_products(es, use_ollama=use_ollama)
    index_personas(es)
    
    logger.info("Data indexing complete")

if __name__ == "__main__":
    main()
