#!/usr/bin/env python3
"""
Test cases for Elasticsearch indexing functionality.
"""
import os
import sys
import pytest
import json
from pathlib import Path
from elasticsearch import Elasticsearch

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import ELASTICSEARCH_HOST

# Skip all tests if Elasticsearch is not available
@pytest.fixture(scope="module")
def elasticsearch_client():
    """Fixture for Elasticsearch client."""
    try:
        es = Elasticsearch(ELASTICSEARCH_HOST)
        if not es.ping():
            pytest.skip("Elasticsearch is not available")
        return es
    except Exception:
        pytest.skip("Elasticsearch is not available")

def test_elasticsearch_connection(elasticsearch_client):
    """Test connection to Elasticsearch."""
    assert elasticsearch_client.ping() is True

def test_indices_exist(elasticsearch_client):
    """Test that required indices exist."""
    # Check if indices exist
    indices = elasticsearch_client.indices.get_alias(index="*")
    
    # Check for products index
    assert "products" in indices, "Products index does not exist"
    
    # Check for personas index (optional)
    if "personas" not in indices:
        pytest.skip("Personas index does not exist")

def test_products_index_mapping(elasticsearch_client):
    """Test that products index has the correct mapping."""
    # Get the mapping for the products index
    mapping = elasticsearch_client.indices.get_mapping(index="products")
    
    # Check if the mapping exists
    assert "products" in mapping, "Products index mapping not found"
    
    # Check if the mapping has the required fields
    properties = mapping["products"]["mappings"]["properties"]
    
    # Check for text fields with BM25 indexing
    assert "name" in properties, "Name field not found in products mapping"
    assert "description" in properties, "Description field not found in products mapping"
    
    # Check for vector fields
    assert "text_embedding" in properties, "Text embedding field not found in products mapping"
    assert properties["text_embedding"]["type"] == "dense_vector", "Text embedding field is not a dense_vector"

def test_products_index_content(elasticsearch_client):
    """Test that products index has content."""
    # Count documents in the products index
    count = elasticsearch_client.count(index="products")
    
    # Check if there are any products
    assert count["count"] > 0, "Products index is empty"
    
    # Get a sample product
    sample = elasticsearch_client.search(
        index="products",
        body={"query": {"match_all": {}}, "size": 1}
    )
    
    # Check if a product was returned
    assert sample["hits"]["total"]["value"] > 0, "No products found"
    
    # Get the first product
    product = sample["hits"]["hits"][0]["_source"]
    
    # Check if the product has the required fields
    assert "name" in product, "Product name not found"
    assert "description" in product, "Product description not found"
    assert "price" in product, "Product price not found"
    assert "category" in product, "Product category not found"
    assert "brand" in product, "Product brand not found"
    
    # Check if the product has vector embeddings
    assert "text_embedding" in product, "Product text embedding not found"
    assert isinstance(product["text_embedding"], list), "Product text embedding is not a list"
    assert len(product["text_embedding"]) > 0, "Product text embedding is empty"

def test_bm25_search(elasticsearch_client):
    """Test BM25 search functionality."""
    # Perform a simple BM25 search
    query = "laptop"
    
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["name^2", "description", "brand", "category"]
            }
        },
        "size": 5
    }
    
    results = elasticsearch_client.search(index="products", body=search_body)
    
    # Check if any results were returned
    assert results["hits"]["total"]["value"] > 0, f"BM25 search returned no results for '{query}'"
    
    # Check if the results contain the query term
    found_term = False
    for hit in results["hits"]["hits"]:
        product = hit["_source"]
        if (
            query.lower() in product.get("name", "").lower() or
            query.lower() in product.get("description", "").lower() or
            query.lower() in product.get("category", "").lower() or
            query.lower() in product.get("brand", "").lower()
        ):
            found_term = True
            break
    
    assert found_term, f"BM25 search results do not contain the query term '{query}'"

def test_vector_search(elasticsearch_client):
    """Test vector search functionality."""
    # Skip if no products have text embeddings
    sample = elasticsearch_client.search(
        index="products",
        body={
            "query": {
                "exists": {
                    "field": "text_embedding"
                }
            },
            "size": 1
        }
    )
    
    if sample["hits"]["total"]["value"] == 0:
        pytest.skip("No products with text embeddings found")
    
    # Get a sample embedding
    embedding = sample["hits"]["hits"][0]["_source"]["text_embedding"]
    
    # Perform a vector search using the sample embedding
    search_body = {
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'text_embedding') + 1.0",
                    "params": {"query_vector": embedding}
                }
            }
        },
        "size": 5
    }
    
    results = elasticsearch_client.search(index="products", body=search_body)
    
    # Check if any results were returned
    assert results["hits"]["total"]["value"] > 0, "Vector search returned no results"
    
    # The first result should be the product we used for the embedding
    first_hit_id = results["hits"]["hits"][0]["_id"]
    sample_id = sample["hits"]["hits"][0]["_id"]
    
    assert first_hit_id == sample_id, "Vector search did not return the expected product as the top result"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
