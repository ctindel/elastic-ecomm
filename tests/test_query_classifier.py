#!/usr/bin/env python3
"""
Test the query classifier with pytest
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.query_classifier import classify_query, QueryType, get_search_method
from app.utils.query_classifier import SEARCH_METHOD_BM25, SEARCH_METHOD_VECTOR, SEARCH_METHOD_CUSTOMER_SUPPORT, SEARCH_METHOD_IMAGE

# Define test cases for each query type
KEYWORD_QUERIES = [
    "deskjet 2734e printer ink",
    "samsung galaxy s21 case",
    "nike air max size 10",
    "sony wh-1000xm4 headphones",
    "apple macbook pro 16 inch 2023"
]

SEMANTIC_QUERIES = [
    "comfortable shoes for standing all day",
    "best laptop for college students",
    "waterproof jacket for hiking",
    "noise cancelling headphones for travel",
    "energy efficient refrigerator for small kitchen"
]

CUSTOMER_SUPPORT_QUERIES = [
    "how do I return an item?",
    "where is my order?",
    "can I change my shipping address?",
    "how do I cancel my subscription?",
    "what is your refund policy?"
]

IMAGE_BASED_QUERIES = [
    "items in this picture",
    "find products similar to image",
    "what is this product in my photo?",
    "search using my school supply list image",
    "identify this item from my picture"
]

MIXED_INTENT_QUERIES = [
    "return policy for nike shoes",
    "find headphones like the ones in this image",
    "where is my order for macbook pro",
    "comfortable shoes similar to the ones in this picture",
    "how do I use the coupon code for samsung tv?"
]

# Generate test cases
TEST_CASES = []
for query in KEYWORD_QUERIES:
    TEST_CASES.append((query, QueryType.KEYWORD))
for query in SEMANTIC_QUERIES:
    TEST_CASES.append((query, QueryType.SEMANTIC))
for query in CUSTOMER_SUPPORT_QUERIES:
    TEST_CASES.append((query, QueryType.CUSTOMER_SUPPORT))
for query in IMAGE_BASED_QUERIES:
    TEST_CASES.append((query, QueryType.IMAGE_BASED))
for query in MIXED_INTENT_QUERIES:
    TEST_CASES.append((query, QueryType.MIXED_INTENT))

@pytest.mark.parametrize("query,expected_type", TEST_CASES)
def test_query_classification(query, expected_type):
    """Test that queries are classified correctly"""
    result = classify_query(query, mock=True)
    assert result == expected_type, f"Expected {expected_type.name} for '{query}', got {result.name}"

def test_overall_accuracy():
    """Test the overall accuracy of the classifier"""
    total = 0
    correct = 0
    
    # Test keyword queries
    for query in KEYWORD_QUERIES:
        total += 1
        result = classify_query(query, mock=True)
        if result == QueryType.KEYWORD:
            correct += 1
    
    # Test semantic queries
    for query in SEMANTIC_QUERIES:
        total += 1
        result = classify_query(query, mock=True)
        if result == QueryType.SEMANTIC:
            correct += 1
    
    # Test customer support queries
    for query in CUSTOMER_SUPPORT_QUERIES:
        total += 1
        result = classify_query(query, mock=True)
        if result == QueryType.CUSTOMER_SUPPORT:
            correct += 1
    
    # Test image-based queries
    for query in IMAGE_BASED_QUERIES:
        total += 1
        result = classify_query(query, mock=True)
        if result == QueryType.IMAGE_BASED:
            correct += 1
    
    # Test mixed intent queries
    for query in MIXED_INTENT_QUERIES:
        total += 1
        result = classify_query(query, mock=True)
        if result == QueryType.MIXED_INTENT:
            correct += 1
    
    accuracy = correct / total * 100 if total > 0 else 0
    assert accuracy >= 90, f"Overall accuracy is {accuracy:.2f}%, expected at least 90%"

def test_search_method_mapping():
    """Test that query types are mapped to the correct search methods"""
    assert get_search_method(QueryType.KEYWORD) == SEARCH_METHOD_BM25
    assert get_search_method(QueryType.SEMANTIC) == SEARCH_METHOD_VECTOR
    assert get_search_method(QueryType.CUSTOMER_SUPPORT) == SEARCH_METHOD_CUSTOMER_SUPPORT
    assert get_search_method(QueryType.IMAGE_BASED) == SEARCH_METHOD_IMAGE
    assert get_search_method(QueryType.MIXED_INTENT) == SEARCH_METHOD_VECTOR

def test_keyword_queries():
    """Test keyword queries specifically"""
    for query in KEYWORD_QUERIES:
        result = classify_query(query, mock=True)
        assert result == QueryType.KEYWORD, f"Expected KEYWORD for '{query}', got {result.name}"

def test_semantic_queries():
    """Test semantic queries specifically"""
    for query in SEMANTIC_QUERIES:
        result = classify_query(query, mock=True)
        assert result == QueryType.SEMANTIC, f"Expected SEMANTIC for '{query}', got {result.name}"

def test_customer_support_queries():
    """Test customer support queries specifically"""
    for query in CUSTOMER_SUPPORT_QUERIES:
        result = classify_query(query, mock=True)
        assert result == QueryType.CUSTOMER_SUPPORT, f"Expected CUSTOMER_SUPPORT for '{query}', got {result.name}"

def test_image_based_queries():
    """Test image-based queries specifically"""
    for query in IMAGE_BASED_QUERIES:
        result = classify_query(query, mock=True)
        assert result == QueryType.IMAGE_BASED, f"Expected IMAGE_BASED for '{query}', got {result.name}"

def test_mixed_intent_queries():
    """Test mixed intent queries specifically"""
    for query in MIXED_INTENT_QUERIES:
        result = classify_query(query, mock=True)
        assert result == QueryType.MIXED_INTENT, f"Expected MIXED_INTENT for '{query}', got {result.name}"

# Additional test cases for edge cases
def test_edge_cases():
    """Test edge cases for the query classifier"""
    # Empty query
    assert classify_query("", mock=True) == QueryType.KEYWORD
    
    # Very short query
    assert classify_query("tv", mock=True) == QueryType.KEYWORD
    
    # Query with multiple intents
    assert classify_query("return policy for headphones in this image", mock=True) == QueryType.MIXED_INTENT
    
    # Query with numbers and special characters
    assert classify_query("iphone 13 pro max $999", mock=True) == QueryType.KEYWORD
    
    # Very long query
    long_query = "I am looking for a comfortable office chair that provides good lumbar support for long hours of sitting and helps prevent back pain while working from home during the pandemic"
    assert classify_query(long_query, mock=True) == QueryType.SEMANTIC
