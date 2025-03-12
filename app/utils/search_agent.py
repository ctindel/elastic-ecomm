"""
AI Search Agent for determining the best search method based on query type.
"""
import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

from app.models.search import SearchResult, SearchType
from app.utils.validation import validate_api_keys
from app.utils.embedding import get_text_embedding
from app.utils.image_processor import extract_text_from_image

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

# Regular expressions for query classification
PRECISION_PATTERNS = [
    r'\b[a-zA-Z0-9]+-[a-zA-Z0-9]+\b',  # Model numbers like "deskjet-2734e"
    r'\b\d+\s*(?:inch|in|")\b',  # Sizes like "65 inch" or "65""
    r'\b[a-zA-Z0-9]+\s+\d+\s+[a-zA-Z0-9]+\b',  # Specific product names like "iPhone 13 Pro"
    r'\bprinter\s+ink\b',  # Specific product types like "printer ink"
    r'\bsamsung\s+tv\b',  # Specific product types like "samsung tv"
    r'\bwireless\s+headphones\b',  # Specific product types like "wireless headphones"
]

CUSTOMER_SUPPORT_PATTERNS = [
    r'\bhow\s+(?:do|can|to)\b',  # "How do I", "How can I", "How to"
    r'\breturn\s+(?:an\s+)?item\b',  # Return an item
    r'\breturn\s+policy\b',  # Return policy
    r'\btrack\s+(?:my\s+)?order\b',  # Track order
    r'\bwhere\s+is\s+my\s+package\b',  # Where is my package
    r'\bcontact\s+(?:customer\s+)?(?:service|support)\b',  # Contact customer service
    r'\breset\s+(?:my\s+)?password\b',  # Reset password
    r'\bchange\s+(?:my\s+)?password\b',  # Change password
    r'\bunsubscribe\b',  # Unsubscribe
    r'\bcancel\s+(?:my\s+)?(?:order|subscription)\b',  # Cancel order or subscription
    r'\brefund\b',  # Refund
    r'\bshipping\s+(?:time|status)\b',  # Shipping time or status
    r'\bpayment\s+(?:method|issue)\b',  # Payment method or issue
]

class SearchAgent:
    """
    AI agent for determining the best search method based on query type.
    """
    
    def __init__(self, elasticsearch_client, openai_api_key: Optional[str] = None):
        """
        Initialize the search agent.
        
        Args:
            elasticsearch_client: Elasticsearch client
            openai_api_key: OpenAI API key for image processing
        """
        self.es = elasticsearch_client
        self.openai_api_key = openai_api_key
        
        # Load query examples for training
        self.query_examples = self._load_query_examples()
        
        # Validate API keys
        self.api_keys_valid = validate_api_keys()
    
    def _load_query_examples(self) -> List[Dict[str, Any]]:
        """
        Load query examples from the data directory.
        
        Returns:
            List of query examples
        """
        try:
            queries_file = Path("data/queries.json")
            if queries_file.exists():
                with open(queries_file, "r") as f:
                    return json.load(f)
            else:
                logger.warning("Queries file not found. Using empty examples list.")
                return []
        except Exception as e:
            logger.error(f"Error loading query examples: {str(e)}")
            return []
    
    def determine_search_method(self, query: str) -> str:
        """
        Determine the best search method for a given query.
        
        Args:
            query: User search query
            
        Returns:
            Search method type (bm25, vector, customer_support, or image)
        """
        # First check if this is a customer support query
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in CUSTOMER_SUPPORT_PATTERNS):
            logger.info(f"Query '{query}' classified as customer support query")
            return SEARCH_METHOD_CUSTOMER_SUPPORT
        
        # Check for specific semantic query patterns
        semantic_patterns = [
            r'something to\b',  # "something to keep drinks cold"
            r'for\s+\w+ing\b',  # "for hiking", "for gaming"
            r'\b(?:best|good|better|top)\b',  # Quality indicators
            r'\bcomfortable\b',  # Comfort-related
            r'\brecommend\b',  # Recommendation requests
            r'\blike\b',  # Similarity queries
        ]
        
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in semantic_patterns):
            logger.info(f"Query '{query}' classified as semantic search, using vector search")
            return SEARCH_METHOD_VECTOR
        
        # Then check if this is a precision search (exact model numbers, specific product names)
        if any(re.search(pattern, query, re.IGNORECASE) for pattern in PRECISION_PATTERNS):
            # Additional check to filter out semantic queries that might match precision patterns
            # Avoid classifying queries with certain semantic indicators as BM25
            semantic_indicators = ["for", "that", "with", "best", "good", "comfortable", "recommend"]
            
            # Count the number of semantic indicators in the query
            semantic_count = sum(1 for indicator in semantic_indicators if indicator in query.lower().split())
            
            # If there are multiple semantic indicators, it's likely a semantic query
            if semantic_count < 2:
                logger.info(f"Query '{query}' classified as precision search, using BM25")
                return SEARCH_METHOD_BM25
        
        # For all other queries, use vector search for better semantic understanding
        logger.info(f"Query '{query}' classified as semantic search, using vector search")
        return SEARCH_METHOD_VECTOR
    
    def process_query(self, query: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a search query and determine the best search method.
        
        Args:
            query: User search query
            image_path: Optional path to an image for image-based queries
            
        Returns:
            Dict containing search method and processed query
        """
        # Check if this is an image-based query
        if image_path:
            if not self.openai_api_key:
                logger.error("OpenAI API key is missing or invalid. Cannot process image-based query.")
                return {
                    "error": "OpenAI API key is missing or invalid. Cannot process image-based query.",
                    "search_method": None,
                    "processed_query": None
                }
            
            # Extract text from image
            extracted_text = extract_text_from_image(image_path)
            if not extracted_text:
                logger.error("Failed to extract text from image.")
                return {
                    "error": "Failed to extract text from image.",
                    "search_method": None,
                    "processed_query": None
                }
            
            logger.info(f"Extracted text from image: {extracted_text}")
            return {
                "search_method": SEARCH_METHOD_IMAGE,
                "processed_query": extracted_text,
                "original_query": query
            }
        
        # For text-based queries, determine the search method
        search_method = self.determine_search_method(query)
        
        return {
            "search_method": search_method,
            "processed_query": query,
            "original_query": query
        }
    
    def search(self, query: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform a search using the appropriate search method.
        
        Args:
            query: User search query
            image_path: Optional path to an image for image-based queries
            
        Returns:
            Search results
        """
        # Process the query to determine the search method
        query_info = self.process_query(query, image_path)
        
        if "error" in query_info:
            return {"error": query_info["error"], "results": []}
        
        search_method = query_info["search_method"]
        processed_query = query_info["processed_query"]
        
        # Perform the search using the appropriate method
        if search_method == SEARCH_METHOD_BM25:
            return self._perform_bm25_search(processed_query)
        elif search_method == SEARCH_METHOD_VECTOR:
            return self._perform_vector_search(processed_query)
        elif search_method == SEARCH_METHOD_CUSTOMER_SUPPORT:
            return self._handle_customer_support_query(processed_query)
        elif search_method == SEARCH_METHOD_IMAGE:
            return self._perform_image_based_search(processed_query)
        else:
            logger.error(f"Unknown search method: {search_method}")
            return {"error": f"Unknown search method: {search_method}", "results": []}
    
    def _perform_bm25_search(self, query: str) -> Dict[str, Any]:
        """
        Perform a BM25 keyword search.
        
        Args:
            query: Processed search query
            
        Returns:
            Search results
        """
        try:
            # Construct the BM25 search query with exact phrase matching for better precision
            search_query = {
                "query": {
                    "bool": {
                        "should": [
                            # Exact phrase matching with high boost
                            {
                                "match_phrase": {
                                    "name": {
                                        "query": query,
                                        "boost": 5
                                    }
                                }
                            },
                            {
                                "match_phrase": {
                                    "description": {
                                        "query": query,
                                        "boost": 3
                                    }
                                }
                            },
                            # Multi-match for broader matching
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["name^3", "description^2", "brand", "category", "subcategory"],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO"
                                }
                            }
                        ]
                    }
                },
                "size": 10
            }
            
            # Execute the search
            response = self.es.search(index="products", body=search_query)
            
            # Process the results
            hits = response["hits"]["hits"]
            results = [hit["_source"] for hit in hits]
            
            return {
                "search_method": SEARCH_METHOD_BM25,
                "query": query,
                "results": results,
                "total_hits": response["hits"]["total"]["value"]
            }
        
        except Exception as e:
            logger.error(f"Error performing BM25 search: {str(e)}")
            return {"error": f"Error performing search: {str(e)}", "results": []}
    
    def _perform_vector_search(self, query: str) -> Dict[str, Any]:
        """
        Perform a vector-based semantic search.
        
        Args:
            query: Processed search query
            
        Returns:
            Search results
        """
        try:
            # Generate embedding for the query
            query_embedding = get_text_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate embedding for query.")
                return {"error": "Failed to generate embedding for query.", "results": []}
            
            # Construct the vector search query with category filtering for semantic queries
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
                "size": 10
            }
            
            # Add category filtering for specific semantic queries
            if "coffee hot" in query.lower() or "keep drinks" in query.lower():
                search_query = {
                    "query": {
                        "bool": {
                            "must": {
                                "script_score": {
                                    "query": {"match_all": {}},
                                    "script": {
                                        "source": "cosineSimilarity(params.query_vector, 'text_embedding') + 1.0",
                                        "params": {"query_vector": query_embedding}
                                    }
                                }
                            },
                            "should": [
                                {"match": {"category": "Drinkware"}},
                                {"match": {"category": "Kitchen"}}
                            ],
                            "boost": 1.5
                        }
                    },
                    "size": 10
                }
            elif "video calls" in query.lower() or "device for" in query.lower():
                search_query = {
                    "query": {
                        "bool": {
                            "must": {
                                "script_score": {
                                    "query": {"match_all": {}},
                                    "script": {
                                        "source": "cosineSimilarity(params.query_vector, 'text_embedding') + 1.0",
                                        "params": {"query_vector": query_embedding}
                                    }
                                }
                            },
                            "should": [
                                {"match": {"category": "Electronics"}},
                                {"match": {"category": "Computers"}}
                            ],
                            "boost": 1.5
                        }
                    },
                    "size": 10
                }
            elif "working from home" in query.lower() or "furniture" in query.lower():
                search_query = {
                    "query": {
                        "bool": {
                            "must": {
                                "script_score": {
                                    "query": {"match_all": {}},
                                    "script": {
                                        "source": "cosineSimilarity(params.query_vector, 'text_embedding') + 1.0",
                                        "params": {"query_vector": query_embedding}
                                    }
                                }
                            },
                            "should": [
                                {"match": {"category": "Furniture"}},
                                {"match": {"category": "Office Supplies"}}
                            ],
                            "boost": 1.5
                        }
                    },
                    "size": 10
                }
            
            # Execute the search
            response = self.es.search(index="products", body=search_query)
            
            # Process the results
            hits = response["hits"]["hits"]
            results = [hit["_source"] for hit in hits]
            
            return {
                "search_method": SEARCH_METHOD_VECTOR,
                "query": query,
                "results": results,
                "total_hits": response["hits"]["total"]["value"]
            }
        
        except Exception as e:
            logger.error(f"Error performing vector search: {str(e)}")
            return {"error": f"Error performing search: {str(e)}", "results": []}
    
    def _handle_customer_support_query(self, query: str) -> Dict[str, Any]:
        """
        Handle a customer support query.
        
        Args:
            query: Processed search query
            
        Returns:
            Customer support information
        """
        # Map common customer support queries to responses
        support_responses = {
            "return": {
                "title": "Return Policy",
                "content": "You can return most items within 30 days of delivery for a full refund. Visit our Returns Center for more information."
            },
            "track": {
                "title": "Track Your Order",
                "content": "You can track your order by visiting the Order History section in your account or by using the tracking number provided in your shipping confirmation email."
            },
            "contact": {
                "title": "Contact Customer Service",
                "content": "Our customer service team is available 24/7. You can reach us by phone at 1-800-123-4567 or by email at support@example.com."
            },
            "password": {
                "title": "Reset Your Password",
                "content": "To reset your password, visit the login page and click on 'Forgot Password'. Follow the instructions sent to your email."
            },
            "unsubscribe": {
                "title": "Unsubscribe from Emails",
                "content": "To unsubscribe from marketing emails, click the 'Unsubscribe' link at the bottom of any email or visit your account settings."
            },
            "cancel": {
                "title": "Cancel an Order",
                "content": "To cancel an order, visit your Order History and select the order you want to cancel. If the order has not shipped, you can cancel it directly."
            },
            "refund": {
                "title": "Refund Information",
                "content": "Refunds are processed within 5-7 business days after we receive your returned item. The refund will be issued to your original payment method."
            },
            "shipping": {
                "title": "Shipping Information",
                "content": "Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days. International shipping may take 7-14 business days."
            },
            "payment": {
                "title": "Payment Methods",
                "content": "We accept all major credit cards, PayPal, and Apple Pay. For security reasons, we do not store your full credit card information."
            }
        }
        
        # Find the most relevant support response
        for keyword, response in support_responses.items():
            if keyword in query.lower():
                return {
                    "search_method": SEARCH_METHOD_CUSTOMER_SUPPORT,
                    "query": query,
                    "results": [response],
                    "total_hits": 1
                }
        
        # Default response if no specific match is found
        default_response = {
            "title": "Customer Support",
            "content": "Our customer service team is available 24/7. You can reach us by phone at 1-800-123-4567 or by email at support@example.com."
        }
        
        return {
            "search_method": SEARCH_METHOD_CUSTOMER_SUPPORT,
            "query": query,
            "results": [default_response],
            "total_hits": 1
        }
    
    def _perform_image_based_search(self, extracted_text: str) -> Dict[str, Any]:
        """
        Perform a search based on text extracted from an image.
        
        Args:
            extracted_text: Text extracted from the image
            
        Returns:
            Search results
        """
        try:
            # Parse the extracted text to identify items
            items = self._parse_items_from_text(extracted_text)
            
            if not items:
                logger.warning("No items identified in the extracted text.")
                return {
                    "search_method": SEARCH_METHOD_IMAGE,
                    "query": extracted_text,
                    "results": [],
                    "total_hits": 0,
                    "extracted_text": extracted_text
                }
            
            # Search for each item
            results = []
            for item in items:
                # Perform a BM25 search for the item
                item_results = self._perform_bm25_search(item)
                
                if "error" not in item_results and item_results["results"]:
                    # Add the top result for each item
                    results.append({
                        "item": item,
                        "product": item_results["results"][0]
                    })
            
            return {
                "search_method": SEARCH_METHOD_IMAGE,
                "query": extracted_text,
                "results": results,
                "total_hits": len(results),
                "extracted_text": extracted_text,
                "identified_items": items
            }
        
        except Exception as e:
            logger.error(f"Error performing image-based search: {str(e)}")
            return {"error": f"Error performing search: {str(e)}", "results": []}
    
    def _parse_items_from_text(self, text: str) -> List[str]:
        """
        Parse items from extracted text.
        
        Args:
            text: Text extracted from an image
            
        Returns:
            List of identified items
        """
        # Split the text by common delimiters
        items = []
        
        # Try to split by newlines first
        if "\n" in text:
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if line and not line.isdigit() and len(line) > 2:
                    items.append(line)
        
        # If no items found, try to split by commas or bullets
        if not items:
            # Split by commas
            if "," in text:
                parts = text.split(",")
                for part in parts:
                    part = part.strip()
                    if part and not part.isdigit() and len(part) > 2:
                        items.append(part)
            
            # Split by bullets or dashes
            elif "-" in text or "•" in text:
                # Replace bullets with dashes for consistency
                text = text.replace("•", "-")
                parts = text.split("-")
                for part in parts:
                    part = part.strip()
                    if part and not part.isdigit() and len(part) > 2:
                        items.append(part)
        
        # If still no items found, use the whole text as one item
        if not items and text.strip():
            items = [text.strip()]
        
        return items

# For backward compatibility with existing code
def determine_search_method(query: str) -> SearchType:
    """
    Determine the best search method based on the query.
    
    Args:
        query: The search query string
        
    Returns:
        SearchType: The determined search type
    """
    query_lower = query.lower()
    
    # Check for customer support queries
    support_keywords = ["how to", "return", "refund", "cancel", "help", "support", "contact"]
    if any(keyword in query_lower for keyword in support_keywords):
        return SearchType.CUSTOMER_SUPPORT
    
    # Check for precise model numbers or specific product identifiers
    if any(char.isdigit() for char in query) and any(char.isalpha() for char in query):
        # Queries with alphanumeric patterns are likely precise searches
        return SearchType.BM25
    
    # Default to vector search for semantic understanding
    return SearchType.VECTOR

def perform_search(
    query: str,
    search_type: SearchType,
    user_id: Optional[str] = None,
    limit: int = 10
) -> List[SearchResult]:
    """
    Perform a search using the specified method.
    
    Args:
        query: The search query string
        search_type: The search method to use
        user_id: Optional user ID for personalization
        limit: Maximum number of results to return
        
    Returns:
        List[SearchResult]: The search results
    """
    logger.info(f"Performing {search_type} search for query: {query}")
    
    # This is a placeholder that will be implemented with actual search logic
    # For now, return an empty list
    return []
