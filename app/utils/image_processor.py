import os
import sys
import json
from typing import List, Dict, Any, Optional
import base64
from fastapi import UploadFile
from elasticsearch import Elasticsearch
from app.models.search import SearchResult, SearchType

# Import our custom logger
from app.utils.logger import logger

# Import vision processor
from app.utils.vision_processor import process_image
from app.config.settings import VISION_PROVIDER

async def process_image_query(
    image_file: UploadFile,
    user_id: Optional[str],
    limit: int,
    elasticsearch_client: Elasticsearch
) -> List[SearchResult]:
    """
    Process an uploaded image to extract text and identify items.
    
    Args:
        image_file: The uploaded image file
        user_id: Optional user ID for tracking
        limit: Maximum number of results to return
        elasticsearch_client: Elasticsearch client
        
    Returns:
        List of SearchResult objects with recommended products
    """
    logger.info(f"Processing image query - File: {image_file.filename}, User: {user_id}, Limit: {limit}")
    
    try:
        # Process the image using the configured vision provider
        logger.debug(f"Sending image to {VISION_PROVIDER} for processing...")
        items_data = await process_image(image_file)
        
        # Log the extracted items
        logger.info(f"Extracted {len(items_data.get('items', []))} items using {VISION_PROVIDER} provider")
        logger.debug(f"Extracted items data:\n{json.dumps(items_data, indent=2)}")
        
        # Search for products based on extracted items
        results = []
        
        # Create a list to store item matching information
        item_matches = []
        
        for item in items_data.get("items", []):
            # Construct search query
            item_name = item.get("name", "")
            quantity = item.get("quantity", "")
            attributes = item.get("attributes", "")
            search_query = f"{item_name} {attributes}".strip()
            
            if not search_query:
                logger.warning(f"Empty search query for item: {item}")
                continue
            
            logger.debug(f"Processing item - Name: '{item_name}', Quantity: '{quantity}', Attributes: '{attributes}'")
            
            # Create item match entry
            item_match = {
                "item": item_name,
                "quantity": quantity,
                "attributes": attributes,
                "matched_product_id": "",  # Empty string instead of None
                "matched_product_name": ""  # Empty string instead of None
            }
            
            # Search in Elasticsearch
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"category": "Office Supplies"}},
                            {
                                "multi_match": {
                                    "query": search_query,
                                    "fields": ["name^3", "description^2", "subcategory"],
                                    "fuzziness": "AUTO"
                                }
                            }
                        ]
                    }
                },
                "size": max(1, limit // len(items_data.get("items", [1])))  # Distribute limit among items
            }
            
            logger.debug(f"Executing Elasticsearch query for '{search_query}':\n{json.dumps(query, indent=2)}")
            
            try:
                search_response = elasticsearch_client.search(index="products", body=query)
                total_hits = search_response["hits"]["total"]["value"]
                logger.debug(f"Found {total_hits} potential matches for '{search_query}'")
                
                # Process search results
                if search_response["hits"]["hits"]:
                    # Get the top match
                    top_hit = search_response["hits"]["hits"][0]
                    source = top_hit["_source"]
                    
                    logger.debug(f"Best match for '{item_name}' - Product: {source.get('name', '')}, Score: {top_hit['_score']}")
                    
                    # Update item match with product info
                    item_match["matched_product_id"] = source.get("id", "")
                    item_match["matched_product_name"] = source.get("name", "")
                    
                    # Create SearchResult object
                    result = SearchResult(
                        query=search_query,
                        product_id=source.get("id", ""),
                        product_name=source.get("name", ""),
                        product_description=source.get("description", ""),
                        price=source.get("price", 0.0),
                        image_url=source.get("image", {}).get("url", ""),
                        score=top_hit["_score"],
                        search_type=SearchType.IMAGE,
                        explanation=f"Found based on your request for: {item_name}",
                        alternatives=[item_match]  # Include item match info in alternatives
                    )
                    
                    results.append(result)
                else:
                    logger.warning(f"No matches found for item '{item_name}'")
                    # No match found, still add item to matches
                    item_match["matched_product_id"] = ""  # Empty string instead of None
                    item_match["matched_product_name"] = ""  # Empty string instead of None
                    
                    # Create a placeholder result for unmatched items
                    result = SearchResult(
                        query=search_query,
                        product_id="not_found",
                        product_name=f"No match found for: {item_name}",
                        product_description=f"Could not find a matching product for {item_name} {attributes}",
                        price=0.0,
                        image_url=None,
                        score=0.0,
                        search_type=SearchType.IMAGE,
                        explanation=f"No matching product found for: {item_name}",
                        alternatives=[item_match]  # Include item match info in alternatives
                    )
                    
                    results.append(result)
                
                # Add item match to the list
                item_matches.append(item_match)
            
            except Exception as e:
                logger.error(f"Error searching for products matching '{item_name}': {str(e)}", exc_info=True)
                
                # Add error information to item match
                item_match["error"] = str(e)
                item_matches.append(item_match)
        
        # Add item matches to the first result's alternatives if there are results
        if results:
            logger.info(f"Successfully processed {len(item_matches)} items from image")
            # Create a summary result with all item matches
            summary_result = SearchResult(
                query="Image Upload Analysis",
                product_id="summary",
                product_name="Image Analysis Results",
                product_description=f"Analysis of items found in the uploaded image (using {VISION_PROVIDER})",
                price=0.0,
                image_url=None,
                score=1.0,
                search_type=SearchType.IMAGE,
                explanation=f"Found {len(item_matches)} items in the uploaded image",
                alternatives=item_matches  # Include all item matches
            )
            
            # Insert summary at the beginning
            results.insert(0, summary_result)
        
        # If no results were found, return an empty list with explanation
        if not results:
            logger.warning(f"No products found for any of the {len(item_matches)} extracted items")
            
            # Create a summary result with all item matches
            summary_result = SearchResult(
                query="Image Upload Analysis",
                product_id="summary",
                product_name="No Matching Products Found",
                product_description="No matching products were found for the items in the uploaded image",
                price=0.0,
                image_url=None,
                score=0.0,
                search_type=SearchType.IMAGE,
                explanation="No matching products found",
                alternatives=item_matches  # Include all item matches
            )
            
            results.append(summary_result)
            
        return results
        
    except Exception as e:
        logger.error(f"Error processing image '{image_file.filename}': {str(e)}", exc_info=True)
        raise
