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

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger(__name__)

from app.config.settings import settings

def classify_query(query):
    """
    Classify a search query using Ollama.
    
    Args:
        query: Search query to classify
    
    Returns:
        dict: Classification results including type and explanation
    """
    logger.debug(f"Received classification request for query: '{query}'")
    
    try:
        # Prepare the prompt
        prompt = f"""You are a query classifier for an e-commerce search system. Your task is to classify the following search query into one of three categories:

1. keyword: Precise product searches with specific product names, models, exact specifications, or generic product types/categories (e.g., "Staples 20/6 Stapler", "HP LaserJet Pro", "stapler", "paper", "desk chair")
2. semantic: Intent-based queries that describe needs or use cases (e.g., "something to write with", "comfortable office chair", "good for taking notes")
3. customer_support: Questions about returns, shipping, policies, or account issues (e.g., "how do I return an item", "shipping time", "track my order")

Key indicators for each type:
- keyword: Contains specific product names, models, exact specifications, or generic product types/categories
- semantic: Focuses on functionality, describes needs rather than specific products
- customer_support: Starts with "how", "what", "where", "when", "why" or contains support-related terms

Query to classify: "{query}"

Respond with a JSON object in this format:
{{
    "type": "keyword|semantic|customer_support",
    "explanation": "Brief explanation of why this classification was chosen",
    "confidence": "high|medium|low",
    "search_strategy": "Suggested search strategy",
    "examples": ["Example 1", "Example 2", "Example 3"],
    "support_answer": "If this is a customer support query, provide a helpful answer as if from internal documentation"
}}"""
        
        logger.debug(f"Sending request to Ollama API ({settings.OLLAMA_MODEL}):\nPrompt: {prompt}")
        
        # Call Ollama API
        response = requests.post(
            settings.OLLAMA_API_URL,
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Error calling Ollama API: Status {response.status_code}\nResponse: {response.text}")
            return {
                "type": "keyword",
                "explanation": "Failed to classify query, defaulting to keyword search",
                "confidence": "low",
                "search_strategy": "Use BM25 matching as fallback",
                "examples": []
            }
        
        # Parse response
        result = response.json()
        response_text = result.get("response", "").strip()
        logger.debug(f"Received response from Ollama:\n{response_text}")
        
        try:
            # Try to find JSON-like structure with curly braces first
            import re
            json_match = re.search(r'\{[^{]*"type":[^}]+\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                logger.debug(f"Extracted JSON structure:\n{json_str}")
                try:
                    analysis = json.loads(json_str)
                    if "type" in analysis and "explanation" in analysis:
                        logger.info(f"Successfully parsed classification for query '{query}' as {analysis['type']} with {analysis.get('confidence', 'unknown')} confidence")
                        return analysis
                except json.JSONDecodeError:
                    logger.warning(f"Found JSON-like structure but failed to parse it: {json_str}")
            
            # If that fails, try the original code block extraction
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                logger.debug("Extracted JSON from code block with 'json' tag")
            elif "```" in response_text:
                json_str = response_text.split("```")[1].strip()
                logger.debug("Extracted JSON from code block")
            else:
                # Try to find any JSON object in the text
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    logger.debug("Found JSON object in response text")
                else:
                    logger.warning("No JSON structure found in response")
                    raise ValueError("No JSON structure found in response")
            
            analysis = json.loads(json_str)
            logger.info(f"Successfully parsed classification for query '{query}' as {analysis['type']} with {analysis.get('confidence', 'unknown')} confidence")
            return analysis
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON response from Ollama. Raw response:\n{response_text}")
            
            # Analyze the text response to determine the type
            response_lower = response_text.lower()
            if '"type"' in response_lower and '"semantic"' in response_lower:
                logger.info(f"Fallback: Classified query '{query}' as semantic based on text analysis")
                return {
                    "type": "semantic",
                    "explanation": "Query requires understanding user intent",
                    "confidence": "medium",
                    "search_strategy": "Use vector search to understand query meaning",
                    "examples": []
                }
            elif '"type"' in response_lower and '"customer_support"' in response_lower:
                logger.info(f"Fallback: Classified query '{query}' as customer_support based on text analysis")
                return {
                    "type": "customer_support",
                    "explanation": "Query is asking for customer service assistance",
                    "confidence": "medium",
                    "search_strategy": "Route to customer support system",
                    "examples": []
                }
            else:
                logger.info(f"Fallback: Classified query '{query}' as keyword based on text analysis")
                return {
                    "type": "keyword",
                    "explanation": "Query appears to be a specific product search",
                    "confidence": "medium",
                    "search_strategy": "Use BM25 matching for exact keyword matches",
                    "examples": []
                }
    
    except Exception as e:
        logger.error(f"Error classifying query '{query}': {str(e)}", exc_info=True)
        return {
            "type": "keyword",
            "explanation": "Error during classification, defaulting to keyword search",
            "confidence": "low",
            "search_strategy": "Use BM25 matching as fallback",
            "examples": []
        }
