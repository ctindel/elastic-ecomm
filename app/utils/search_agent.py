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
from pathlib import Path

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger(__name__)

from app.config.settings import settings
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
        logger.debug(f"Initializing SearchAgent with Elasticsearch host: {settings.ELASTICSEARCH_HOST}")
        self.es = elasticsearch_client or Elasticsearch(settings.ELASTICSEARCH_HOST)
        self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY
    
    def determine_search_method(self, query):
        """
        Determine the best search method for a query.
        
        Args:
            query: Search query
        
        Returns:
            SearchType: Search type
        """
        logger.debug(f"Determining search method for query: '{query}'")
        
        # Classify the query
        classification = classify_query(query)
        logger.debug(f"Query classification result: {classification}")
        
        # Extract the type from the classification dictionary
        query_type = classification.get("type", "keyword")
        
        # Map query type to search type
        if query_type == "keyword":
            search_type = SearchType.BM25
        elif query_type == "semantic":
            search_type = SearchType.VECTOR
        elif query_type == "customer_support":
            search_type = SearchType.CUSTOMER_SUPPORT
        else:
            # Default to BM25
            search_type = SearchType.BM25
            
        logger.info(f"Selected search type {search_type} for query '{query}'")
        return search_type
    
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
        logger.info(f"Performing search - Query: '{query}', Type: {search_type}, User: {user_id}, Limit: {limit}")
        
        # Determine search type if not provided
        if search_type is None:
            search_type = self.determine_search_method(query)
            logger.debug(f"No search type provided, determined type: {search_type}")
        
        # Perform search based on type
        if search_type == SearchType.BM25:
            logger.debug("Using BM25 search method")
            search_results = self._perform_bm25_search(query, limit=limit)
        elif search_type == SearchType.VECTOR:
            logger.debug("Using vector search method")
            search_results = self._perform_vector_search(query, limit=limit)
        elif search_type == SearchType.CUSTOMER_SUPPORT:
            logger.debug("Using customer support search method")
            search_results = self._handle_customer_support_query(query)
        else:
            # Default to BM25
            logger.warning(f"Unknown search type {search_type}, defaulting to BM25")
            search_results = self._perform_bm25_search(query, limit=limit)
        
        # Convert to SearchResult objects
        results = []
        for hit in search_results.get("results", []):
            # Update image URL to use static file serving
            image_url = hit.get("image", {}).get("url", "")
            
            if image_url and image_url.startswith("data/"):
                # Get the project root directory (two levels up from this file)
                project_root = str(Path(__file__).parent.parent.parent.absolute())
                image_path = os.path.join(project_root, image_url)
                if os.path.exists(image_path):
                    # Convert data/images/product_xxx.png to /static/images/product_xxx.png
                    image_url = "/static/" + image_url[5:]
                    logger.debug(f"Converted image URL to: {image_url}")
                else:
                    # If image doesn't exist, set to empty string to use placeholder
                    logger.warning(f"Image not found at path: {image_path}")
                    image_url = ""
            
            result = SearchResult(
                query=query,
                product_id=hit.get("id", ""),
                product_name=hit.get("name", ""),
                product_description=hit.get("description", ""),
                price=hit.get("price", 0.0),
                image_url=image_url,
                score=hit.get("score", 0.0),
                search_type=search_type
            )
            results.append(result)
        
        logger.info(f"Found {len(results)} results for query '{query}'")
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
            
            logger.debug(f"Executing BM25 search query:\n{json.dumps(search_query, indent=2)}")
            
            # Execute the search
            response = self.es.search(
                index=settings.ELASTICSEARCH_INDEX_PRODUCTS,
                body=search_query
            )
            
            # Process the results
            hits = response.get("hits", {})
            total_hits = hits.get("total", {}).get("value", 0)
            results = []
            
            logger.debug(f"BM25 search found {total_hits} total hits")
            
            for hit in hits.get("hits", []):
                source = hit.get("_source", {})
                source["id"] = hit.get("_id", "")
                source["score"] = hit.get("_score", 0.0)
                results.append(source)
                logger.debug(f"BM25 hit - ID: {source['id']}, Score: {source['score']}, Name: {source.get('name', '')}")
            
            return {
                "total_hits": total_hits,
                "results": results
            }
        
        except Exception as e:
            logger.error(f"Error performing BM25 search: {str(e)}", exc_info=True)
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
            logger.debug(f"Generating embedding for query: '{query}'")
            query_embedding = get_text_embedding(query)
            logger.debug(f"Successfully generated query embedding with {len(query_embedding)} dimensions")
            
            # Prepare the search query
            search_query = {
                "_source": True,
                "knn": {
                    "field": "text_embedding",
                    "query_vector": query_embedding,
                    "k": limit,
                    "num_candidates": 100
                }
            }
            
            logger.debug(f"Executing vector search query: {json.dumps(search_query)}")
            
            # Execute the search
            response = self.es.search(
                index=settings.ELASTICSEARCH_INDEX_PRODUCTS,
                body=search_query
            )
            
            # Process the results
            hits = response.get("hits", {})
            total_hits = hits.get("total", {}).get("value", 0)
            results = []
            
            logger.debug(f"Vector search found {total_hits} total hits")
            
            for hit in hits.get("hits", []):
                source = hit.get("_source", {})
                source["id"] = hit.get("_id", "")
                source["score"] = hit.get("_score", 0.0)
                results.append(source)
                logger.debug(f"Vector hit - ID: {source['id']}, Score: {source['score']}, Name: {source.get('name', '')}")
            
            return {
                "total_hits": total_hits,
                "results": results
            }
        
        except Exception as e:
            logger.error(f"Error performing vector search: {str(e)}", exc_info=True)
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
            dict: Search results
        """
        try:
            # Search in customer support index
            search_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question^3", "answer^2", "category"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "size": 5
            }
            
            logger.debug(f"Executing customer support search query:\n{json.dumps(search_query, indent=2)}")
            
            # Execute the search
            response = self.es.search(
                index=settings.ELASTICSEARCH_INDEX_QUERIES,
                body=search_query
            )
            
            # Process the results
            hits = response.get("hits", {})
            total_hits = hits.get("total", {}).get("value", 0)
            results = []
            
            logger.debug(f"Customer support search found {total_hits} total hits")
            
            for hit in hits.get("hits", []):
                source = hit.get("_source", {})
                source["id"] = hit.get("_id", "")
                source["score"] = hit.get("_score", 0.0)
                results.append(source)
                logger.debug(f"Customer support hit - ID: {source['id']}, Score: {source['score']}, Question: {source.get('question', '')}")
            
            return {
                "total_hits": total_hits,
                "results": results
            }
        
        except Exception as e:
            logger.error(f"Error handling customer support query: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "total_hits": 0,
                "results": []
            }

def determine_search_method(query):
    """
    Determine the best search method for a query.
    
    Args:
        query: Search query
    
    Returns:
        SearchType: Search type
    """
    agent = SearchAgent()
    return agent.determine_search_method(query)

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
    agent = SearchAgent()
    return agent.perform_search(query, search_type, user_id, limit)
