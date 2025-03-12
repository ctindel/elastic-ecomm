"""
Utility functions for classifying search queries using Ollama.
"""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List

from app.config.settings import OLLAMA_HOST, OLLAMA_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Search method types
SEARCH_METHOD_BM25 = "bm25"
SEARCH_METHOD_VECTOR = "vector"
SEARCH_METHOD_CUSTOMER_SUPPORT = "customer_support"
SEARCH_METHOD_IMAGE = "image"

# Classification prompt template
CLASSIFICATION_PROMPT = """
You are an AI search agent tasked with classifying user search queries into the following categories:

1. BM25 (Precision Search): Exact product searches with specific model numbers, sizes, or precise product names.
   Examples:
   - "printer ink for deskjet 2734e"
   - "iphone 13 pro max case"
   - "samsung 65 inch qled tv"
   - "wireless headphones"

2. Vector Search (Semantic Search): Queries seeking recommendations, exploring product categories, or understanding intent.
   Examples:
   - "comfortable chair for long hours"
   - "waterproof case for hiking"
   - "something to keep drinks cold"
   - "best laptop for college students"

3. Customer Support: Queries related to returns, tracking orders, account management, or support issues.
   Examples:
   - "how do I return an item?"
   - "track my order"
   - "unsubscribe from emails"
   - "where is my package?"

Classify the following query and explain your reasoning:
Query: {query}

Response format:
CLASSIFICATION: [BM25/VECTOR/CUSTOMER_SUPPORT]
REASONING: Brief explanation of your classification
"""

def check_ollama_connection() -> bool:
    """
    Check if Ollama is available.
    
    Returns:
        bool: True if Ollama is available, False otherwise
    """
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.RequestException:
        return False

def classify_query(query: str) -> str:
    """
    Classify a search query using Ollama.
    
    Args:
        query: The search query to classify
        
    Returns:
        str: The classified search method (bm25, vector, customer_support)
    """
    if not query:
        logger.warning("Empty query provided for classification")
        return SEARCH_METHOD_VECTOR  # Default to vector search for empty queries
    
    try:
        # Prepare the prompt with the query
        prompt = CLASSIFICATION_PROMPT.format(query=query)
        
        # Prepare the request payload
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        # Make the request to Ollama generate API
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            # Extract the classification from the response
            classification_text = response.json().get("response", "")
            
            if not classification_text:
                logger.warning("Empty classification returned from Ollama")
                return SEARCH_METHOD_VECTOR  # Default to vector search
            
            # Parse the classification
            classification = parse_classification(classification_text)
            
            if classification:
                logger.info(f"Query '{query}' classified as {classification}")
                return classification
            else:
                logger.warning(f"Failed to parse classification from Ollama response: {classification_text}")
                return SEARCH_METHOD_VECTOR  # Default to vector search
        else:
            logger.error(f"Failed to classify query: {response.text}")
            return SEARCH_METHOD_VECTOR  # Default to vector search
    
    except Exception as e:
        logger.error(f"Error classifying query: {str(e)}")
        return SEARCH_METHOD_VECTOR  # Default to vector search

def parse_classification(classification_text: str) -> str:
    """
    Parse the classification from the Ollama response.
    
    Args:
        classification_text: The text response from Ollama
        
    Returns:
        str: The parsed search method
    """
    # Convert to uppercase for case-insensitive matching
    text_upper = classification_text.upper()
    
    # Look for the classification in the response
    if "CLASSIFICATION:" in text_upper:
        # Extract the classification
        classification_line = [line for line in text_upper.split("\n") if "CLASSIFICATION:" in line]
        if classification_line:
            classification = classification_line[0].split("CLASSIFICATION:")[1].strip()
            
            # Map the classification to the search method
            if "BM25" in classification:
                return SEARCH_METHOD_BM25
            elif "VECTOR" in classification:
                return SEARCH_METHOD_VECTOR
            elif "CUSTOMER_SUPPORT" in classification or "CUSTOMER SUPPORT" in classification:
                return SEARCH_METHOD_CUSTOMER_SUPPORT
    
    # If we couldn't parse the classification, check for keywords in the full text
    if "BM25" in text_upper and ("PRECISION" in text_upper or "EXACT" in text_upper):
        return SEARCH_METHOD_BM25
    elif "VECTOR" in text_upper and ("SEMANTIC" in text_upper or "INTENT" in text_upper):
        return SEARCH_METHOD_VECTOR
    elif "CUSTOMER" in text_upper and "SUPPORT" in text_upper:
        return SEARCH_METHOD_CUSTOMER_SUPPORT
    
    # Default to vector search if we couldn't determine the classification
    return SEARCH_METHOD_VECTOR

def classify_query_with_fallback(query: str) -> str:
    """
    Classify a search query with fallback to a simple heuristic if Ollama is not available.
    
    Args:
        query: The search query to classify
        
    Returns:
        str: The classified search method (bm25, vector, customer_support)
    """
    # First try to classify using Ollama
    if check_ollama_connection():
        return classify_query(query)
    
    # Fallback to a simple heuristic if Ollama is not available
    logger.warning("Ollama is not available, falling back to simple heuristic classification")
    
    query_lower = query.lower()
    
    # Check for customer support queries
    support_keywords = ["how to", "return", "refund", "cancel", "help", "support", 
                        "contact", "track", "order", "unsubscribe", "password"]
    if any(keyword in query_lower for keyword in support_keywords):
        return SEARCH_METHOD_CUSTOMER_SUPPORT
    
    # Check for precise model numbers or specific product identifiers
    if any(char.isdigit() for char in query) and any(char.isalpha() for char in query):
        # Queries with alphanumeric patterns are likely precise searches
        return SEARCH_METHOD_BM25
    
    # Default to vector search for semantic understanding
    return SEARCH_METHOD_VECTOR
