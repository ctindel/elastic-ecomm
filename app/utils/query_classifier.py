#!/usr/bin/env python3
"""
Query classifier for e-commerce search
Uses Ollama to classify search queries into different types:
- keyword: Precise product searches (e.g., model numbers, specific products)
- semantic: Conceptual searches that benefit from vector search
- customer_support: Questions about orders, returns, etc.
- image_based: Queries that reference an uploaded image
"""
import os
import sys
import json
import logging
import requests
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import OLLAMA_API_URL, OLLAMA_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Classification types
CLASSIFICATION_TYPES = ["keyword", "semantic", "customer_support", "image_based"]

def classify_query(query, mock=False):
    """
    Classify a search query using Ollama
    
    Args:
        query: The search query to classify
        mock: Whether to use mock classification (for testing)
    
    Returns:
        str: The classification type (keyword, semantic, customer_support, image_based)
    """
    if mock:
        # For testing purposes - improved to handle mixed intent queries
        query_lower = query.lower()
        
        # Check for customer support patterns first (highest priority)
        if any(term in query_lower for term in ["return", "order", "subscription", "refund", "track", "warranty", "policy"]):
            return "customer_support"
        
        # Check for image-based patterns
        elif any(term in query_lower for term in ["picture", "image", "photo", "school supply list", "similar", "compare"]):
            return "image_based"
        
        # Check for keyword patterns
        elif any(term in query_lower for term in ["model", "printer", "iphone", "samsung", "logitech", "hp"]) and not "best" in query_lower:
            return "keyword"
        
        # Check for semantic patterns
        elif any(term in query_lower for term in ["best", "comfortable", "waterproof", "lightweight", "efficient", "price"]):
            return "semantic"
        
        # Default to semantic search
        else:
            return "semantic"
    
    try:
        # Prepare the prompt for Ollama
        prompt = f"""
        You are an e-commerce search query classifier. Your task is to classify the following search query into one of these categories:
        
        1. keyword: Precise product searches (e.g., model numbers, specific products)
        2. semantic: Conceptual searches that benefit from vector search (e.g., "best laptop for graphic design")
        3. customer_support: Questions about orders, returns, etc.
        4. image_based: Queries that reference an uploaded image or request visual comparison
        
        Examples:
        - "deskjet 2734e printer ink" -> keyword
        - "comfortable office chair for long hours" -> semantic
        - "how do I return an item?" -> customer_support
        - "find items in this picture" -> image_based
        
        Query: "{query}"
        
        Respond with ONLY ONE of these words: keyword, semantic, customer_support, image_based
        """
        
        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error calling Ollama API: {response.text}")
            return "semantic"  # Default to semantic search on error
        
        # Parse the response
        result = response.json()
        response_text = result.get("response", "").strip().lower()
        
        # Extract the classification type
        for classification_type in CLASSIFICATION_TYPES:
            if classification_type in response_text:
                return classification_type
        
        # Default to semantic search if no match
        logger.warning(f"Could not classify query: {query}, response: {response_text}")
        return "semantic"
    
    except Exception as e:
        logger.error(f"Error classifying query: {str(e)}")
        return "semantic"  # Default to semantic search on error

if __name__ == "__main__":
    # Test the classifier with some example queries
    test_queries = [
        "deskjet 2734e printer ink",
        "comfortable office chair for long hours",
        "how do I return an item?",
        "find items in this picture"
    ]
    
    for query in test_queries:
        classification = classify_query(query, mock=True)
        print(f"Query: '{query}' -> {classification}")
