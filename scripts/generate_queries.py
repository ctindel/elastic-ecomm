#!/usr/bin/env python3
"""
Script to generate a synthetic query log for the e-commerce search demo.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def generate_query_log():
    """
    Generate a synthetic query log with various types of queries.
    
    Returns:
        list: List of generated queries with metadata
    """
    logger.info("Generating synthetic query log")
    
    # Sample queries representing different search behaviors
    queries = [
        # Keyword ambiguity queries
        {
            "query": "laundry soap",
            "type": "keyword_ambiguity",
            "description": "Could return laundry detergent or hand soap",
            "expected_search_type": "bm25",
            "expected_results": ["laundry detergent", "hand soap", "dish soap"]
        },
        {
            "query": "apple",
            "type": "keyword_ambiguity",
            "description": "Could return Apple products or actual apples",
            "expected_search_type": "vector",
            "expected_results": ["iPhone", "MacBook", "Apple Watch", "fruit"]
        },
        {
            "query": "mouse",
            "type": "keyword_ambiguity",
            "description": "Could return computer mouse or pet mouse",
            "expected_search_type": "vector",
            "expected_results": ["computer mouse", "wireless mouse", "gaming mouse"]
        },
        {
            "query": "tablet",
            "type": "keyword_ambiguity",
            "description": "Could return tablet computer or medicine tablet",
            "expected_search_type": "vector",
            "expected_results": ["iPad", "Samsung Galaxy Tab", "Android tablet"]
        },
        {
            "query": "glasses",
            "type": "keyword_ambiguity",
            "description": "Could return eyeglasses or drinking glasses",
            "expected_search_type": "vector",
            "expected_results": ["eyeglasses", "sunglasses", "drinking glasses", "wine glasses"]
        },
        
        # Semantic understanding queries
        {
            "query": "screens for graphic designers",
            "type": "semantic_understanding",
            "description": "Should return monitors with good color accuracy",
            "expected_search_type": "vector",
            "expected_results": ["4K monitor", "color-accurate display", "wide gamut monitor"]
        },
        {
            "query": "comfortable chair for long hours",
            "type": "semantic_understanding",
            "description": "Should return ergonomic office chairs",
            "expected_search_type": "vector",
            "expected_results": ["ergonomic chair", "office chair", "gaming chair"]
        },
        {
            "query": "waterproof case for hiking",
            "type": "semantic_understanding",
            "description": "Should return waterproof phone or camera cases",
            "expected_search_type": "vector",
            "expected_results": ["waterproof phone case", "waterproof camera case", "outdoor gear"]
        },
        {
            "query": "tools for home renovation",
            "type": "semantic_understanding",
            "description": "Should return power tools and DIY equipment",
            "expected_search_type": "vector",
            "expected_results": ["power drill", "saw", "hammer", "screwdriver set"]
        },
        {
            "query": "something to keep drinks cold",
            "type": "semantic_understanding",
            "description": "Should return coolers, insulated bottles, or refrigerators",
            "expected_search_type": "vector",
            "expected_results": ["cooler", "insulated bottle", "mini fridge"]
        },
        
        # Precision searches
        {
            "query": "printer ink for deskjet 2734e",
            "type": "precision_search",
            "description": "Should return exact ink cartridges for this printer model",
            "expected_search_type": "bm25",
            "expected_results": ["HP 67 ink cartridge", "HP 67XL ink cartridge"]
        },
        {
            "query": "iphone 13 pro max case",
            "type": "precision_search",
            "description": "Should return cases specifically for iPhone 13 Pro Max",
            "expected_search_type": "bm25",
            "expected_results": ["iPhone 13 Pro Max case", "iPhone 13 Pro Max cover"]
        },
        {
            "query": "samsung 65 inch qled tv",
            "type": "precision_search",
            "description": "Should return Samsung QLED TVs with 65-inch screen",
            "expected_search_type": "bm25",
            "expected_results": ["Samsung 65\" QLED TV", "Samsung 65-inch Smart TV"]
        },
        {
            "query": "logitech mx master 3 mouse",
            "type": "precision_search",
            "description": "Should return the exact Logitech mouse model",
            "expected_search_type": "bm25",
            "expected_results": ["Logitech MX Master 3", "Logitech wireless mouse"]
        },
        {
            "query": "nike air jordan 1 high og chicago",
            "type": "precision_search",
            "description": "Should return the exact Nike shoe model",
            "expected_search_type": "bm25",
            "expected_results": ["Nike Air Jordan 1", "Nike basketball shoes"]
        },
        
        # Customer support queries
        {
            "query": "how do I unsubscribe from emails?",
            "type": "customer_support",
            "description": "Should be routed to customer support information",
            "expected_search_type": "customer_support",
            "expected_results": ["email preferences", "unsubscribe instructions", "contact support"]
        },
        {
            "query": "return policy for electronics",
            "type": "customer_support",
            "description": "Should be routed to return policy information",
            "expected_search_type": "customer_support",
            "expected_results": ["return policy", "electronics returns", "refund information"]
        },
        {
            "query": "track my order",
            "type": "customer_support",
            "description": "Should be routed to order tracking information",
            "expected_search_type": "customer_support",
            "expected_results": ["order tracking", "shipping status", "delivery information"]
        },
        {
            "query": "contact customer service",
            "type": "customer_support",
            "description": "Should be routed to contact information",
            "expected_search_type": "customer_support",
            "expected_results": ["customer service", "contact information", "help center"]
        },
        {
            "query": "how to reset my password",
            "type": "customer_support",
            "description": "Should be routed to account help information",
            "expected_search_type": "customer_support",
            "expected_results": ["password reset", "account help", "login assistance"]
        },
        
        # Image-based queries (these would be processed differently in the actual system)
        {
            "query": "school supply list image",
            "type": "image_based",
            "description": "Should process an uploaded school supply list image",
            "expected_search_type": "image",
            "expected_results": ["notebooks", "pens", "pencils", "binders", "backpacks"]
        },
        {
            "query": "furniture assembly instructions image",
            "type": "image_based",
            "description": "Should process an uploaded furniture assembly instructions image",
            "expected_search_type": "image",
            "expected_results": ["screwdriver", "allen wrench", "screws", "furniture parts"]
        },
        {
            "query": "recipe ingredient list image",
            "type": "image_based",
            "description": "Should process an uploaded recipe ingredient list image",
            "expected_search_type": "image",
            "expected_results": ["flour", "sugar", "eggs", "butter", "baking powder"]
        },
        {
            "query": "shopping list image",
            "type": "image_based",
            "description": "Should process an uploaded shopping list image",
            "expected_search_type": "image",
            "expected_results": ["milk", "bread", "eggs", "cheese", "vegetables"]
        },
        {
            "query": "product barcode image",
            "type": "image_based",
            "description": "Should process an uploaded product barcode image",
            "expected_search_type": "image",
            "expected_results": ["exact product match", "similar products"]
        }
    ]
    
    # Save queries to file
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    with open(data_dir / "queries.json", "w") as f:
        json.dump(queries, f, indent=2)
    
    logger.info(f"Saved {len(queries)} queries to data/queries.json")
    return queries

if __name__ == "__main__":
    generate_query_log()
