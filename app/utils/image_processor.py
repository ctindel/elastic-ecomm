#!/usr/bin/env python3
import io
import json
import logging
from typing import List, Dict, Any, Optional
import base64
from fastapi import UploadFile
from elasticsearch import Elasticsearch
from app.models.search import SearchResult, SearchType
from app.config.settings import OPENAI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    try:
        # Read the image file
        contents = await image_file.read()
        
        # Convert to base64 for OpenAI API
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # Use OpenAI to extract text and identify items
        import openai
        
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # Define the system prompt
        system_prompt = """
        You are an assistant that analyzes images of shopping lists or product requests.
        Extract all items from the image and return them in the following JSON format:
        {
            "items": [
                {
                    "name": "item name",
                    "quantity": "quantity (if specified)",
                    "attributes": "any attributes like color, size, etc."
                }
            ]
        }
        Only include items that are clearly visible in the image. If quantities are specified, include them.
        """
        
        # Make the API call
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What items are in this shopping list? Extract them according to the format."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_file.content_type.split('/')[-1]};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Extract the JSON response
        try:
            content = response.choices[0].message.content
            # Extract JSON from the response (it might be wrapped in markdown code blocks)
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].strip()
            else:
                json_str = content.strip()
                
            items_data = json.loads(json_str)
            
            # Log the extracted items
            logger.info(f"Extracted items: {items_data}")
            
            # Search for products based on extracted items
            results = []
            
            for item in items_data.get("items", []):
                # Construct search query
                item_name = item.get("name", "")
                attributes = item.get("attributes", "")
                search_query = f"{item_name} {attributes}".strip()
                
                if not search_query:
                    continue
                
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
                    "size": limit // len(items_data.get("items", [1]))  # Distribute limit among items
                }
                
                try:
                    search_response = elasticsearch_client.search(index="products", body=query)
                    
                    # Process search results
                    for hit in search_response["hits"]["hits"]:
                        source = hit["_source"]
                        
                        # Create SearchResult object
                        result = SearchResult(
                            query=search_query,
                            product_id=source.get("id", ""),
                            product_name=source.get("name", ""),
                            product_description=source.get("description", ""),
                            price=source.get("price", 0.0),
                            image_url=source.get("image", {}).get("url", ""),
                            score=hit["_score"],
                            search_type=SearchType.BM25,
                            explanation=f"Found based on your request for: {item_name}"
                        )
                        
                        results.append(result)
                
                except Exception as e:
                    logger.error(f"Error searching for products: {str(e)}")
            
            # If no results were found, return an empty list with explanation
            if not results:
                logger.warning("No products found for the extracted items")
                
            return results
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from OpenAI response: {content}")
            raise ValueError("Failed to parse items from the image")
            
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise
