#!/usr/bin/env python3
"""
Query classifier for the E-Commerce Search Demo.
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

from app.config.settings import (
    OLLAMA_MODEL,
    OLLAMA_API_URL
)

def classify_query(query):
    """
    Classify a search query using Ollama.
    
    Args:
        query: Search query to classify
    
    Returns:
        str: Query type (keyword, semantic, customer_support)
    """
    try:
        # Prepare the prompt
        prompt = f"""
        You are a query classifier for an e-commerce search system. Your task is to classify the following search query into one of three categories:

        1. "keyword" - Precise product searches that are best served by keyword matching (BM25). Examples:
           - "printer ink for deskjet 2734e"
           - "samsung galaxy s21 ultra case"
           - "nike air max 270 size 10"

        2. "semantic" - Intent-based searches that require understanding meaning. Examples:
           - "comfortable running shoes for marathon"
           - "best laptop for college student"
           - "screens for graphic designers"

        3. "customer_support" - Questions about orders, returns, or other customer service issues. Examples:
           - "how do I return an item?"
           - "where is my order?"
           - "how to cancel my subscription"

        Search query: "{query}"

        Respond with ONLY ONE of these three words: "keyword", "semantic", or "customer_support".
        """
        
        # Call Ollama API
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error calling Ollama API: {response.text}")
            return "keyword"  # Default to keyword search
        
        # Parse response
        result = response.json()
        response_text = result.get("response", "").strip().lower()
        
        # Extract the classification
        if "keyword" in response_text:
            return "keyword"
        elif "semantic" in response_text:
            return "semantic"
        elif "customer_support" in response_text or "customer support" in response_text:
            return "customer_support"
        else:
            logger.warning(f"Unexpected classification response: {response_text}")
            return "keyword"  # Default to keyword search
    
    except Exception as e:
        logger.error(f"Error classifying query: {str(e)}")
        return "keyword"  # Default to keyword search
