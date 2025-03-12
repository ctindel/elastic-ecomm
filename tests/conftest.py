"""
Pytest configuration file for the e-commerce search demo.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.query_classifier import SEARCH_METHOD_BM25, SEARCH_METHOD_VECTOR, SEARCH_METHOD_CUSTOMER_SUPPORT

# Mock for the query classifier
@pytest.fixture(autouse=True)
def mock_query_classifier():
    """
    Mock the query classifier to avoid calling Ollama during tests.
    """
    with patch('app.utils.query_classifier.classify_query') as mock_classify:
        # Define a mock implementation that returns expected values for test queries
        def mock_implementation(query):
            query_lower = query.lower()
            
            # Precision searches (BM25)
            if any(term in query_lower for term in [
                "printer ink", "deskjet", "iphone", "samsung tv", "inch", "qled"
            ]):
                return SEARCH_METHOD_BM25
            
            # Customer support queries
            elif any(term in query_lower for term in [
                "how do i", "return", "track", "order", "unsubscribe", "password"
            ]):
                return SEARCH_METHOD_CUSTOMER_SUPPORT
            
            # Default to vector search for semantic understanding
            else:
                return SEARCH_METHOD_VECTOR
        
        # Set the side effect of the mock
        mock_classify.side_effect = mock_implementation
        yield mock_classify

@pytest.fixture(autouse=True)
def mock_query_classifier_with_fallback():
    """
    Mock the query classifier with fallback to avoid calling Ollama during tests.
    """
    with patch('app.utils.query_classifier.classify_query_with_fallback') as mock_classify:
        # Define a mock implementation that returns expected values for test queries
        def mock_implementation(query):
            query_lower = query.lower()
            
            # Precision searches (BM25)
            if any(term in query_lower for term in [
                "printer ink", "deskjet", "iphone", "samsung tv", "inch", "qled"
            ]):
                return SEARCH_METHOD_BM25
            
            # Customer support queries
            elif any(term in query_lower for term in [
                "how do i", "return", "track", "order", "unsubscribe", "password"
            ]):
                return SEARCH_METHOD_CUSTOMER_SUPPORT
            
            # Default to vector search for semantic understanding
            else:
                return SEARCH_METHOD_VECTOR
        
        # Set the side effect of the mock
        mock_classify.side_effect = mock_implementation
        yield mock_classify

@pytest.fixture(autouse=True)
def mock_ollama_connection():
    """
    Mock the Ollama connection check to avoid calling Ollama during tests.
    """
    with patch('app.utils.query_classifier.check_ollama_connection') as mock_check:
        mock_check.return_value = True
        yield mock_check
