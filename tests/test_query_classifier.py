#!/usr/bin/env python3
"""
Test script for the query classifier
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

from app.utils.query_classifier import classify_query

# Load test cases
TEST_DATA_PATH = os.path.join(Path(__file__).parent, "test_data", "query_classifier_test_cases.json")

def load_test_cases():
    """Load test cases from JSON file"""
    if not os.path.exists(TEST_DATA_PATH):
        pytest.skip(f"Test data file not found: {TEST_DATA_PATH}")
    
    with open(TEST_DATA_PATH, 'r') as f:
        return json.load(f)

@pytest.mark.parametrize("query,expected", [
    (case["query"], case["expected"]) 
    for category in load_test_cases().values() 
    for case in category
])
def test_query_classification(query, expected):
    """Test that queries are classified correctly"""
    result = classify_query(query, mock=True)
    assert result == expected, f"Query '{query}' was classified as '{result}' but expected '{expected}'"

# Test specific categories
@pytest.mark.parametrize("query", [case["query"] for case in load_test_cases().get("keyword_search", [])])
def test_keyword_search_queries(query):
    """Test that keyword search queries are classified correctly"""
    result = classify_query(query, mock=True)
    assert result == "keyword", f"Keyword query '{query}' was classified as '{result}'"

@pytest.mark.parametrize("query", [case["query"] for case in load_test_cases().get("semantic_search", [])])
def test_semantic_search_queries(query):
    """Test that semantic search queries are classified correctly"""
    result = classify_query(query, mock=True)
    assert result == "semantic", f"Semantic query '{query}' was classified as '{result}'"

@pytest.mark.parametrize("query", [case["query"] for case in load_test_cases().get("customer_support", [])])
def test_customer_support_queries(query):
    """Test that customer support queries are classified correctly"""
    result = classify_query(query, mock=True)
    assert result == "customer_support", f"Customer support query '{query}' was classified as '{result}'"

@pytest.mark.parametrize("query", [case["query"] for case in load_test_cases().get("image_based", [])])
def test_image_based_queries(query):
    """Test that image-based queries are classified correctly"""
    result = classify_query(query, mock=True)
    assert result == "image_based", f"Image-based query '{query}' was classified as '{result}'"

if __name__ == "__main__":
    # Run tests directly
    test_cases = load_test_cases()
    
    print(f"Testing {sum(len(category) for category in test_cases.values())} queries")
    
    for category, cases in test_cases.items():
        print(f"\nTesting {category} queries:")
        for case in cases:
            query = case["query"]
            expected = case["expected"]
            result = classify_query(query, mock=True)
            
            if result == expected:
                print(f"✓ '{query}' -> {result}")
            else:
                print(f"✗ '{query}' -> {result} (expected {expected})")
