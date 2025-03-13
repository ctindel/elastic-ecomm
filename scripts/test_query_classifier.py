#!/usr/bin/env python3
"""
Test script for the query classifier
This script tests the query classifier with various types of queries
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.query_classifier import classify_query, QueryType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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

def test_query_classifier():
    """Test the query classifier with various types of queries"""
    results = {
        "total": 0,
        "correct": 0,
        "by_type": {}
    }
    
    for query_type, queries in TEST_QUERIES.items():
        type_name = query_type.name
        results["by_type"][type_name] = {
            "total": len(queries),
            "correct": 0,
            "queries": []
        }
        
        for query in queries:
            results["total"] += 1
            
            # Classify the query
            classified_type = classify_query(query, mock=True)
            
            # Check if the classification is correct
            is_correct = classified_type == query_type
            if is_correct:
                results["correct"] += 1
                results["by_type"][type_name]["correct"] += 1
            
            # Add the query result
            results["by_type"][type_name]["queries"].append({
                "query": query,
                "expected": type_name,
                "classified": classified_type.name,
                "correct": is_correct
            })
    
    # Calculate accuracy
    overall_accuracy = results["correct"] / results["total"] * 100 if results["total"] > 0 else 0
    results["accuracy"] = overall_accuracy
    
    # Calculate accuracy by type
    for type_name, type_results in results["by_type"].items():
        type_accuracy = type_results["correct"] / type_results["total"] * 100 if type_results["total"] > 0 else 0
        results["by_type"][type_name]["accuracy"] = type_accuracy
    
    return results

def main():
    """Main entry point"""
    logger.info("Testing query classifier...")
    
    # Test the query classifier
    results = test_query_classifier()
    
    # Print the results
    print("\nQuery Classifier Test Results:")
    print(f"Overall Accuracy: {results['accuracy']:.2f}% ({results['correct']}/{results['total']})")
    print("\nAccuracy by Query Type:")
    
    for type_name, type_results in results["by_type"].items():
        print(f"  {type_name}: {type_results['accuracy']:.2f}% ({type_results['correct']}/{type_results['total']})")
    
    print("\nDetailed Results:")
    for type_name, type_results in results["by_type"].items():
        print(f"\n{type_name} Queries:")
        for query_result in type_results["queries"]:
            status = "✓" if query_result["correct"] else "✗"
            print(f"  {status} \"{query_result['query']}\" -> {query_result['classified']}")

if __name__ == "__main__":
    main()
