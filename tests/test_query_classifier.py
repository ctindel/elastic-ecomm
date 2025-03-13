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

# Load test data
TEST_DATA_PATH = os.path.join(project_root, "tests", "test_data", "query_classifier_test_cases.json")
with open(TEST_DATA_PATH, "r") as f:
    TEST_DATA = json.load(f)

# Map string query types to enum values
QUERY_TYPE_MAP = {
    "keyword": QueryType.KEYWORD,
    "semantic": QueryType.SEMANTIC,
    "customer_support": QueryType.CUSTOMER_SUPPORT,
    "image_based": QueryType.IMAGE_BASED,
    "mixed_intent": QueryType.MIXED_INTENT
}

# Generate test cases from test data
TEST_CASES = []
for query_type, queries in TEST_DATA.items():
    for query_data in queries:
        TEST_CASES.append((query_data["query"], QUERY_TYPE_MAP[query_data["expected"]]))

@pytest.mark.parametrize("query,expected_type", TEST_CASES)
def test_query_classification(query, expected_type):
    """Test that queries are classified correctly"""
    result = classify_query(query, mock=True)
    assert result == expected_type, f"Expected {expected_type.name} for '{query}', got {result.name}"

def test_overall_accuracy():
    """Test the overall accuracy of the classifier"""
    total = 0
    correct = 0
    
    for query_type, queries in TEST_DATA.items():
        expected_type = QUERY_TYPE_MAP[query_type]
        for query_data in queries:
            total += 1
            result = classify_query(query_data["query"], mock=True)
            if result == expected_type:
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
    for query_data in TEST_DATA["keyword_search"]:
        result = classify_query(query_data["query"], mock=True)
        assert result == QueryType.KEYWORD, f"Expected KEYWORD for '{query_data['query']}', got {result.name}"

def test_semantic_queries():
    """Test semantic queries specifically"""
    for query_data in TEST_DATA["semantic_search"]:
        result = classify_query(query_data["query"], mock=True)
        assert result == QueryType.SEMANTIC, f"Expected SEMANTIC for '{query_data['query']}', got {result.name}"

def test_customer_support_queries():
    """Test customer support queries specifically"""
    for query_data in TEST_DATA["customer_support"]:
        result = classify_query(query_data["query"], mock=True)
        assert result == QueryType.CUSTOMER_SUPPORT, f"Expected CUSTOMER_SUPPORT for '{query_data['query']}', got {result.name}"

def test_image_based_queries():
    """Test image-based queries specifically"""
    for query_data in TEST_DATA["image_based"]:
        result = classify_query(query_data["query"], mock=True)
        assert result == QueryType.IMAGE_BASED, f"Expected IMAGE_BASED for '{query_data['query']}', got {result.name}"

def test_mixed_intent_queries():
    """Test mixed intent queries specifically"""
    for query_data in TEST_DATA["mixed_intent"]:
        result = classify_query(query_data["query"], mock=True)
        assert result == QueryType.MIXED_INTENT, f"Expected MIXED_INTENT for '{query_data['query']}', got {result.name}"
