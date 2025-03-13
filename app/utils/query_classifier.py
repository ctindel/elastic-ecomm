#!/usr/bin/env python3
"""
Query classifier for e-commerce search
This module classifies search queries into different types
"""
import os
import sys
import json
import logging
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def classify_query_with_ollama(query):
    """
    Classify a query using Ollama
    
    Args:
        query: Search query to classify
    
    Returns:
        str: Query type (keyword, semantic, customer_support)
    """
    try:
        # Prepare the prompt
        prompt = f"""
        You are an e-commerce search query classifier. Your task is to classify the following search query into one of these categories:
        
        1. keyword: Precise searches for specific products or model numbers (e.g., "printer ink for deskjet 2734e")
        2. semantic: Searches that require understanding of user intent (e.g., "screens for graphic designers")
        3. customer_support: Questions about orders, returns, or policies (e.g., "how do I return an item?")
        
        Query: "{query}"
        
        Respond with ONLY ONE of these words: keyword, semantic, or customer_support.
        """
        
        # Call Ollama API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error calling Ollama API: {response.text}")
            return fallback_classify_query(query)
        
        # Parse response
        result = response.json()
        response_text = result.get("response", "").strip().lower()
        
        # Extract query type
        if "keyword" in response_text:
            return "keyword"
        elif "semantic" in response_text:
            return "semantic"
        elif "customer_support" in response_text:
            return "customer_support"
        else:
            logger.warning(f"Unexpected response from Ollama: {response_text}")
            return fallback_classify_query(query)
    
    except Exception as e:
        logger.error(f"Error classifying query with Ollama: {str(e)}")
        return fallback_classify_query(query)

def fallback_classify_query(query):
    """
    Fallback query classifier when Ollama is unavailable
    
    Args:
        query: Search query to classify
    
    Returns:
        str: Query type (keyword, semantic, customer_support)
    """
    # Convert query to lowercase
    query = query.lower()
    
    # Check if it's a customer support query
    customer_support_indicators = [
        "how do i", "where is", "when will", "can i", "what is",
        "return", "refund", "cancel", "shipping", "delivery",
        "order status", "track", "payment", "contact", "help"
    ]
    
    for indicator in customer_support_indicators:
        if indicator in query:
            return "customer_support"
    
    # Check if it's a keyword query (specific model numbers, product names)
    if any(char.isdigit() for char in query) or len(query.split()) >= 4:
        return "keyword"
    
    # Default to semantic query
    return "semantic"

def classify_query(query):
    """
    Classify a search query into different types
    
    Args:
        query: Search query to classify
    
    Returns:
        str: Query type (keyword, semantic, customer_support)
    """
    try:
        # Try to classify with Ollama
        return classify_query_with_ollama(query)
    except Exception as e:
        logger.error(f"Error classifying query: {str(e)}")
        return fallback_classify_query(query)
