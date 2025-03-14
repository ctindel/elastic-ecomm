#!/usr/bin/env python3
"""
Search agent for the E-Commerce Search Demo.
"""
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_INDEX_PRODUCTS,
    ELASTICSEARCH_INDEX_PERSONAS,
    ELASTICSEARCH_INDEX_QUERIES,
    OPENAI_API_KEY
)
from app.models.search import SearchResult, SearchType
from app.utils.query_classifier import classify_query
from app.utils.embedding import get_text_embedding

class SearchAgent:
    """Search agent for the E-Commerce Search Demo."""
    
    def __init__(self, elasticsearch_client=None, openai_api_key=None):
        """
        Initialize the search agent.
        
        Args:
            elasticsearch_client: Elasticsearch client
            openai_api_key: OpenAI API key
        """
        self.es = elasticsearch_client or Elasticsearch(ELASTICSEARCH_HOST)
        self.openai_api_key = openai_api_key or OPENAI_API_KEY
    
    def determine_search_method(self, query):
        """
        Determine the best search method for a query.
        
        Args:
            query: Search query
        
        Returns:
            SearchType: Search type
        """
        # Classify the query
        query_type = classify_query(query)
        
        # Map query type to search type
        if query_type == "keyword":
            return SearchType.BM25
        elif query_type == "semantic":
            return SearchType.VECTOR
        elif query_type == "customer_support":
            return SearchType.CUSTOMER_SUPPORT
        else:
            # Default to BM25
            return SearchType.BM25
    
    def perform_search(self, query, search_type=None, user_id=None, limit=10):
        """
        Perform a search using the specified method.
        
        Args:
            query: Search query
            search_type: Search type
            user_id: User ID for personalization
            limit: Maximum number of results to return
        
        Returns:
            List[SearchResult]: List of search results
        """
        # Determine search type if not provided
        if search_type is None:
            search_type = self.determine_search_method(query)
        
        # Perform search based on type
        if search_type == SearchType.BM25:
            search_results = self._perform_bm25_search(query, limit=limit)
        elif search_type == SearchType.VECTOR:
            search_results = self._perform_vector_search(query, limit=limit)
        elif search_type == SearchType.CUSTOMER_SUPPORT:
            search_results = self._handle_customer_support_query(query)
        else:
            # Default to BM25
            search_results = self._perform_bm25_search(query, limit=limit)
        
        # Convert to SearchResult objects
        results = []
        for hit in search_results.get("results", []):
            result = SearchResult(
                query=query,
                product_id=hit.get("id", ""),
                product_name=hit.get("name", ""),
                product_description=hit.get("description", ""),
                price=hit.get("price", 0.0),
                image_url=hit.get("image", {}).get("url", ""),
                score=hit.get("score", 0.0),
                search_type=search_type
            )
            results.append(result)
        
        return results
    
    def _perform_bm25_search(self, query, limit=10):
        """
        Perform a BM25 search.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
        
        Returns:
            dict: Search results
        """
        try:
            # Prepare the search query
            search_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^3", "description^2", "category", "brand"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "size": limit
            }
            
            # Execute the search
            response = self.es.search(
                index=ELASTICSEARCH_INDEX_PRODUCTS,
                body=search_query
            )
            
            # Process the results
            hits = response.get("hits", {})
            total_hits = hits.get("total", {}).get("value", 0)
            results = []
            
            for hit in hits.get("hits", []):
                source = hit.get("_source", {})
                source["id"] = hit.get("_id", "")
                source["score"] = hit.get("_score", 0.0)
                results.append(source)
            
            return {
                "total_hits": total_hits,
                "results": results
            }
        
        except Exception as e:
            logger.error(f"Error performing BM25 search: {str(e)}")
            return {
                "error": str(e),
                "total_hits": 0,
                "results": []
            }
    
    def _perform_vector_search(self, query, limit=10):
        """
        Perform a vector search.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
        
        Returns:
            dict: Search results
        """
        try:
            # Generate query embedding
            query_embedding = get_text_embedding(query)
            
            # Prepare the search query
            search_query = {
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'text_embedding') + 1.0",
                            "params": {"query_vector": query_embedding}
                        }
                    }
                },
                "size": limit
            }
            
            # Execute the search
            response = self.es.search(
                index=ELASTICSEARCH_INDEX_PRODUCTS,
                body=search_query
            )
            
            # Process the results
            hits = response.get("hits", {})
            total_hits = hits.get("total", {}).get("value", 0)
            results = []
            
            for hit in hits.get("hits", []):
                source = hit.get("_source", {})
                source["id"] = hit.get("_id", "")
                source["score"] = hit.get("_score", 0.0)
                results.append(source)
            
            return {
                "total_hits": total_hits,
                "results": results
            }
        
        except Exception as e:
            logger.error(f"Error performing vector search: {str(e)}")
            return {
                "error": str(e),
                "total_hits": 0,
                "results": []
            }
    
    def _handle_customer_support_query(self, query):
        """
        Handle a customer support query.
        
        Args:
            query: Customer support query
        
        Returns:
            dict: Support response
        """
        # This is a placeholder for actual customer support handling
        # In a real implementation, this would connect to a customer support system
        
        # Define some common customer support responses
        support_responses = {
            "return": "To return an item, please visit your order history and select 'Return Item'. Follow the instructions to print a return label.",
            "refund": "Refunds are processed within 5-7 business days after we receive your returned item.",
            "cancel": "To cancel an order, please visit your order history and select 'Cancel Order'. You can only cancel orders that haven't been shipped yet.",
            "shipping": "Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days.",
            "delivery": "You can track your delivery by visiting your order history and selecting 'Track Package'.",
            "order status": "To check your order status, please visit your order history.",
            "track": "You can track your package by visiting your order history and selecting 'Track Package'.",
            "payment": "We accept all major credit cards, PayPal, and Apple Pay.",
            "contact": "You can contact our customer support team at support@example.com or call 1-800-123-4567.",
            "help": "How can I help you today? You can ask about returns, refunds, shipping, or any other customer service issue."
        }
        
        # Find the most relevant response
        response_text = "I'm sorry, I don't have information about that. Please contact our customer support team at support@example.com or call 1-800-123-4567."
        query_lower = query.lower()
        
        for keyword, response in support_responses.items():
            if keyword in query_lower:
                response_text = response
                break
        
        # Create a mock result
        result = {
            "id": "support-1",
            "name": "Customer Support",
            "description": response_text,
            "score": 1.0
        }
        
        return {
            "total_hits": 1,
            "results": [result]
        }

# Create global search agent instance
search_agent = SearchAgent()

def determine_search_method(query):
    """
    Determine the best search method for a query.
    
    Args:
        query: Search query
    
    Returns:
        SearchType: Search type
    """
    return search_agent.determine_search_method(query)

def perform_search(query, search_type=None, user_id=None, limit=10):
    """
    Perform a search using the specified method.
    
    Args:
        query: Search query
        search_type: Search type
        user_id: User ID for personalization
        limit: Maximum number of results to return
    
    Returns:
        List[SearchResult]: List of search results
    """
    return search_agent.perform_search(query, search_type, user_id, limit)
