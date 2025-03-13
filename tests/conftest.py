#!/usr/bin/env python3
"""
Pytest configuration file for the e-commerce search demo
"""
import os
import sys
import pytest
import json
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.query_classifier import SEARCH_METHOD_BM25, SEARCH_METHOD_VECTOR, SEARCH_METHOD_CUSTOMER_SUPPORT

@pytest.fixture
def mock_products():
    """Fixture for mock products"""
    return [
        {
            "id": "PROD-00001",
            "name": "Test Product 1",
            "description": "This is a test product 1",
            "category": "Electronics",
            "price": 100.0,
            "brand": "Brand A",
            "rating": 4.5,
            "review_count": 100,
            "stock_status": "In Stock",
            "attributes": {
                "color": "Black",
                "weight": "1.0 kg",
                "size": "Medium"
            },
            "image": {
                "url": "data/images/product_1.jpg",
                "alt_text": "Image of Test Product 1",
                "vector_embedding": [0.1] * 512
            },
            "text_embedding": [0.1] * 384
        },
        {
            "id": "PROD-00002",
            "name": "Test Product 2",
            "description": "This is a test product 2",
            "category": "Clothing",
            "price": 50.0,
            "brand": "Brand B",
            "rating": 4.0,
            "review_count": 50,
            "stock_status": "In Stock",
            "attributes": {
                "color": "Blue",
                "weight": "0.5 kg",
                "size": "Large"
            },
            "image": {
                "url": "data/images/product_2.jpg",
                "alt_text": "Image of Test Product 2",
                "vector_embedding": [0.2] * 512
            },
            "text_embedding": [0.2] * 384
        }
    ]

@pytest.fixture
def mock_personas():
    """Fixture for mock personas"""
    return [
        {
            "id": "PERS-00001",
            "name": "John Doe",
            "age": 30,
            "gender": "Male",
            "occupation": "Software Engineer",
            "interests": ["Electronics", "Gaming", "Books"],
            "search_history": [
                {
                    "query": "best laptop for programming",
                    "timestamp": "2023-01-01T12:00:00Z",
                    "results_clicked": ["PROD-00001"]
                }
            ],
            "clickstream": [
                {
                    "product_id": "PROD-00001",
                    "timestamp": "2023-01-01T12:05:00Z",
                    "time_spent": 60.0
                }
            ],
            "purchase_history": [
                {
                    "product_id": "PROD-00001",
                    "timestamp": "2023-01-01T12:10:00Z",
                    "price": 100.0,
                    "quantity": 1
                }
            ]
        }
    ]

@pytest.fixture
def mock_queries():
    """Fixture for mock queries"""
    return [
        {
            "id": "QUERY-00001",
            "text": "best laptop for programming",
            "timestamp": "2023-01-01T12:00:00Z",
            "user_id": "PERS-00001",
            "results": ["PROD-00001"],
            "clicked": ["PROD-00001"],
            "purchased": ["PROD-00001"]
        }
    ]

@pytest.fixture
def mock_elasticsearch_client():
    """Fixture for mock Elasticsearch client"""
    class MockElasticsearchClient:
        def __init__(self):
            self.indices = {}
            self.documents = {}
        
        def index(self, index, id, body):
            if index not in self.indices:
                self.indices[index] = {}
            self.indices[index][id] = body
            return {"result": "created"}
        
        def search(self, index, body):
            hits = []
            for doc_id, doc in self.indices.get(index, {}).items():
                hits.append({"_id": doc_id, "_source": doc})
            return {"hits": {"total": {"value": len(hits)}, "hits": hits}}
    
    return MockElasticsearchClient()

@pytest.fixture
def mock_ollama_client():
    """Fixture for mock Ollama client"""
    class MockOllamaClient:
        def __init__(self):
            self.embeddings = {}
        
        def generate_embedding(self, text):
            if text not in self.embeddings:
                self.embeddings[text] = [0.1] * 384
            return self.embeddings[text]
    
    return MockOllamaClient()
