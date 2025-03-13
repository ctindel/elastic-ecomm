#!/usr/bin/env python3
"""
Query classifier for the e-commerce search demo
This module classifies search queries into different types
"""
import os
import sys
import enum
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

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

# Search method constants
SEARCH_METHOD_BM25 = "bm25"
SEARCH_METHOD_VECTOR = "vector"
SEARCH_METHOD_CUSTOMER_SUPPORT = "customer_support"
SEARCH_METHOD_IMAGE = "image"

class QueryType(enum.Enum):
    """Enum for query types"""
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    CUSTOMER_SUPPORT = "customer_support"
    IMAGE_BASED = "image_based"
    MIXED_INTENT = "mixed_intent"

def classify_query_with_ollama(query: str) -> QueryType:
    """
    Classify a query using Ollama
    
    Args:
        query: The query to classify
    
    Returns:
        QueryType: The classified query type
    """
    try:
        # Prepare the prompt for Ollama
        prompt = f"""
        You are a query classifier for an e-commerce search system. Your task is to classify the following query into one of these categories:
        
        1. KEYWORD: Precise product searches with specific model numbers, brands, or exact product names.
           Examples: "deskjet 2734e printer ink", "samsung galaxy s21 case", "nike air max size 10"
        
        2. SEMANTIC: Queries that describe product features, use cases, or benefits rather than exact names.
           Examples: "comfortable shoes for standing all day", "best laptop for college students", "waterproof jacket for hiking"
        
        3. CUSTOMER_SUPPORT: Questions about orders, returns, policies, or other customer service inquiries.
           Examples: "how do I return an item?", "where is my order?", "can I change my shipping address?"
        
        4. IMAGE_BASED: Queries that reference an uploaded image or request image-based search.
           Examples: "items in this picture", "find products similar to image", "what is this product in my photo?"
        
        5. MIXED_INTENT: Queries that combine multiple intents from the categories above.
           Examples: "return policy for nike shoes", "find headphones like the ones in this image"
        
        Query to classify: "{query}"
        
        Respond with ONLY ONE of these category names: KEYWORD, SEMANTIC, CUSTOMER_SUPPORT, IMAGE_BASED, MIXED_INTENT
        """
        
        # Send the request to Ollama
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error classifying query with Ollama: {response.text}")
            return QueryType.KEYWORD  # Default to keyword search if Ollama fails
        
        # Parse the response
        result = response.json()
        response_text = result.get("response", "").strip().upper()
        
        # Map the response to a QueryType
        if "KEYWORD" in response_text:
            return QueryType.KEYWORD
        elif "SEMANTIC" in response_text:
            return QueryType.SEMANTIC
        elif "CUSTOMER_SUPPORT" in response_text:
            return QueryType.CUSTOMER_SUPPORT
        elif "IMAGE_BASED" in response_text:
            return QueryType.IMAGE_BASED
        elif "MIXED_INTENT" in response_text:
            return QueryType.MIXED_INTENT
        else:
            logger.warning(f"Unexpected response from Ollama: {response_text}")
            return QueryType.KEYWORD  # Default to keyword search
    
    except Exception as e:
        logger.error(f"Error classifying query with Ollama: {str(e)}")
        return QueryType.KEYWORD  # Default to keyword search if Ollama fails

def classify_query_mock(query: str) -> QueryType:
    """
    Mock implementation of query classification for testing
    
    Args:
        query: The query to classify
    
    Returns:
        QueryType: The classified query type
    """
    query = query.lower()
    
    # Check for image-based queries first
    if any(phrase in query for phrase in ["image", "picture", "photo", "school supply list"]):
        # Check for mixed intent (image + product)
        if any(word in query for word in ["headphones", "shoes", "similar to"]):
            return QueryType.MIXED_INTENT
        return QueryType.IMAGE_BASED
    
    # Check for customer support queries
    if any(phrase in query for phrase in ["how do i", "where is", "can i", "policy", "return", "cancel", "subscription", "refund"]):
        # Check for mixed intent (customer support + product)
        if any(word in query for word in ["nike", "samsung", "apple", "sony", "macbook", "tv", "coupon"]):
            return QueryType.MIXED_INTENT
        return QueryType.CUSTOMER_SUPPORT
    
    # Check for semantic queries
    if any(phrase in query for phrase in ["best", "for", "comfortable", "waterproof", "noise cancelling", "energy efficient"]):
        # Check if it contains specific product identifiers (mixed intent)
        if any(identifier in query for identifier in ["2734e", "s21", "air max", "wh-1000xm4", "macbook pro"]):
            return QueryType.MIXED_INTENT
        return QueryType.SEMANTIC
    
    # Check for specific product identifiers (keyword search)
    if any(identifier in query for identifier in ["2734e", "s21", "air max", "wh-1000xm4", "macbook pro", "galaxy", "iphone", "sony"]):
        return QueryType.KEYWORD
    
    # Default to keyword search
    return QueryType.KEYWORD

def classify_query(query: str, mock: bool = False) -> QueryType:
    """
    Classify a query into a query type
    
    Args:
        query: The query to classify
        mock: Whether to use the mock implementation
    
    Returns:
        QueryType: The classified query type
    """
    if mock:
        return classify_query_mock(query)
    else:
        return classify_query_with_ollama(query)

def get_search_method(query_type: QueryType) -> str:
    """
    Get the search method for a query type
    
    Args:
        query_type: The query type
    
    Returns:
        str: The search method
    """
    if query_type == QueryType.KEYWORD:
        return SEARCH_METHOD_BM25
    elif query_type == QueryType.SEMANTIC:
        return SEARCH_METHOD_VECTOR
    elif query_type == QueryType.CUSTOMER_SUPPORT:
        return SEARCH_METHOD_CUSTOMER_SUPPORT
    elif query_type == QueryType.IMAGE_BASED:
        return SEARCH_METHOD_IMAGE
    elif query_type == QueryType.MIXED_INTENT:
        # For mixed intent, default to vector search
        return SEARCH_METHOD_VECTOR
    else:
        # Default to BM25
        return SEARCH_METHOD_BM25
