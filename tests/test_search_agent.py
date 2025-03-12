"""
Tests for the search agent functionality.
"""
import pytest
from app.models.search import SearchType
from app.utils.search_agent import determine_search_method, perform_search

def test_determine_search_method():
    """Test the search method determination logic."""
    # Test customer support queries
    assert determine_search_method("how to return an item") == SearchType.CUSTOMER_SUPPORT
    assert determine_search_method("refund policy") == SearchType.CUSTOMER_SUPPORT
    
    # Test precise model number queries
    assert determine_search_method("printer ink for deskjet 2734e") == SearchType.BM25
    assert determine_search_method("iphone 13 pro max case") == SearchType.BM25
    
    # Test semantic queries
    assert determine_search_method("comfortable chair for long hours") == SearchType.VECTOR
    assert determine_search_method("waterproof case for hiking") == SearchType.VECTOR

def test_perform_search():
    """Test the search functionality."""
    # This is a placeholder test that will be expanded with actual search testing
    results = perform_search("test query", SearchType.BM25)
    assert isinstance(results, list)
