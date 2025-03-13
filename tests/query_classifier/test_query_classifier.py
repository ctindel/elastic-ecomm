#!/usr/bin/env python3
"""
Test cases for the query classifier
This script tests the query classifier with different types of queries
"""
import os
import sys
import json
import logging
import unittest
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.query_classifier import classify_query

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class TestQueryClassifier(unittest.TestCase):
    """Test cases for the query classifier"""
    
    def setUp(self):
        """Set up test cases"""
        # Define test queries for each type
        self.keyword_queries = [
            "printer ink for deskjet 2734e",
            "samsung galaxy s21 ultra case",
            "logitech mx master 3 mouse",
            "airpods pro 2nd generation",
            "dyson v11 absolute filter"
        ]
        
        self.semantic_queries = [
            "screens for graphic designers",
            "comfortable office chair for long hours",
            "waterproof bluetooth speaker for shower",
            "lightweight laptop for college student",
            "eco-friendly laundry detergent"
        ]
        
        self.customer_support_queries = [
            "how do I unsubscribe from emails?",
            "where is my order?",
            "how do I return an item?",
            "can I change my shipping address?",
            "what is your refund policy?"
        ]
        
        self.ambiguous_queries = [
            "laundry soap",
            "apple",
            "monitor",
            "mouse",
            "tablet"
        ]
    
    def test_keyword_queries(self):
        """Test keyword queries"""
        for query in self.keyword_queries:
            query_type = classify_query(query)
            self.assertEqual(query_type, "keyword", f"Query '{query}' should be classified as 'keyword'")
    
    def test_semantic_queries(self):
        """Test semantic queries"""
        for query in self.semantic_queries:
            query_type = classify_query(query)
            self.assertEqual(query_type, "semantic", f"Query '{query}' should be classified as 'semantic'")
    
    def test_customer_support_queries(self):
        """Test customer support queries"""
        for query in self.customer_support_queries:
            query_type = classify_query(query)
            self.assertEqual(query_type, "customer_support", f"Query '{query}' should be classified as 'customer_support'")
    
    def test_ambiguous_queries(self):
        """Test ambiguous queries"""
        for query in self.ambiguous_queries:
            query_type = classify_query(query)
            self.assertIn(query_type, ["keyword", "semantic"], f"Query '{query}' should be classified as 'keyword' or 'semantic'")

if __name__ == "__main__":
    unittest.main()
