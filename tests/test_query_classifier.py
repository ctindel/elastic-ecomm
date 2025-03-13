#!/usr/bin/env python3
"""
Test the query classifier with pytest
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.query_classifier import classify_query, QueryType

# Test queries for each type
TEST_QUERIES = {
    QueryType.KEYWORD: [
        "deskjet 2734e printer ink",
        "samsung galaxy s21 case",
        "nike air max size 10",
        "sony wh-1000xm4 headphones",
        "apple macbook pro 16 inch 2023"
    ],
    QueryType.SEMANTIC: [
        "comfortable shoes for standing all day",
        "best laptop for college students",
        "waterproof jacket for hiking",
        "noise cancelling headphones for travel",
        "energy efficient refrigerator for small kitchen"
    ],
    QueryType.CUSTOMER_SUPPORT: [
        "how do I return an item?",
        "where is my order?",
        "can I change my shipping address?",
        "how do I cancel my subscription?",
        "what is your refund policy?"
    ],
    QueryType.IMAGE_BASED: [
        "items in this picture",
        "find products similar to image",
        "what is this product in my photo?",
        "search using my school supply list image",
        "identify this item from my picture"
    ],
    QueryType.MIXED_INTENT: [
        "return policy for nike shoes",
        "find headphones like the ones in this image",
        "where is my order for macbook pro",
        "comfortable shoes similar to the ones in this picture",
        "how do I use the coupon code for samsung tv?"
    ]
}

@pytest.mark.parametrize("query_type,query", [
    (expected_type, query)
    for expected_type, queries in TEST_QUERIES.items()
    for query in queries
])
def test_query_classification(query_type, query):
    """Test that queries are classified correctly"""
    result = classify_query(query, mock=True)
    assert result == query_type, f"Expected {query_type.name} for '{query}', got {result.name}"

def test_overall_accuracy():
    """Test the overall accuracy of the classifier"""
    total = 0
    correct = 0
    
    for expected_type, queries in TEST_QUERIES.items():
        for query in queries:
            total += 1
            result = classify_query(query, mock=True)
            if result == expected_type:
                correct += 1
    
    accuracy = correct / total * 100 if total > 0 else 0
    assert accuracy >= 90, f"Overall accuracy is {accuracy:.2f}%, expected at least 90%"
