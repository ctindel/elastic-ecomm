"""
Search API endpoints for the E-Commerce Search Demo.
"""
import os
import traceback
import json
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from elasticsearch import Elasticsearch

# Import our custom logger
from app.utils.logger import logger

from app.models.search import SearchResult, SearchType
from app.utils.search_agent import determine_search_method, perform_search
from app.utils.image_processor import process_image_query
from app.config.settings import ELASTICSEARCH_HOST, ELASTICSEARCH_INDEX_PRODUCTS

router = APIRouter()

def get_elasticsearch_client():
    """Get Elasticsearch client."""
    try:
        es = Elasticsearch(ELASTICSEARCH_HOST)
        yield es
    except Exception as e:
        # Return a mock client for testing
        yield None

class SearchQuery(BaseModel):
    """Search query model."""
    query: str
    user_id: Optional[str] = None
    limit: int = 10

@router.post("/")
async def search_products(
    query: SearchQuery,
    es_client: Elasticsearch = Depends(get_elasticsearch_client)
):
    """Search products using either keyword or semantic search."""
    try:
        logger.info(f"Received search query: {query.query}")
        
        # Determine search method
        search_type = determine_search_method(query.query)
        logger.info(f"Determined search type: {search_type}")
        
        # Perform search
        results = perform_search(
            query.query,
            search_type,
            es_client
        )
        
        # Exclude vector fields from results
        for result in results:
            if 'text_embedding' in result:
                del result['text_embedding']
            if 'image' in result and 'vector_embedding' in result['image']:
                del result['image']['vector_embedding']
        
        return results
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/image", response_model=List[SearchResult])
async def image_search(
    image_file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    limit: int = Form(10)
):
    """
    Process an image (e.g., school supply list) and return relevant product suggestions.
    
    This endpoint accepts an uploaded image, extracts text using OpenAI's API,
    identifies required items, and suggests alternatives at different price points.
    """
    logger.info(f"Received image search request - File: {image_file.filename}, User: {user_id}, Limit: {limit}")
    
    # Validate image file
    if not image_file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type: {image_file.content_type}")
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check if OpenAI API key is available
    from app.config.settings import OPENAI_API_KEY
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key is missing")
        raise HTTPException(
            status_code=503, 
            detail="Image-based search is currently unavailable. OpenAI API key is missing or invalid."
        )
    
    try:
        # Get Elasticsearch client
        from elasticsearch import Elasticsearch
        from app.config.settings import ELASTICSEARCH_HOST
        es_client = Elasticsearch(ELASTICSEARCH_HOST)
        
        logger.debug("Processing image to extract text and identify items...")
        # Process the image to extract text and identify items
        results = await process_image_query(
            image_file=image_file,
            user_id=user_id,
            limit=limit,
            elasticsearch_client=es_client
        )
        
        logger.info(f"Found {len(results)} results for image '{image_file.filename}'")
        for result in results:
            logger.debug(f"Image search result - ID: {result.product_id}, Name: {result.product_name}, Score: {result.score}")
        
        return results
    except Exception as e:
        logger.error(f"Image search failed for file '{image_file.filename}': {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")

@router.get("/classify")
async def classify_search_query(
    query: str = Query(..., description="Search query to classify")
):
    """
    Classify a search query to determine the best search method.
    """
    logger.info(f"Received query classification request - Query: '{query}'")
    
    try:
        # Import the query classifier
        from app.utils.query_classifier import classify_query
        
        # Get the full classification
        classification = classify_query(query)
        logger.info(f"Query '{query}' classified as {classification['type']}")
        
        return classification
    
    except Exception as e:
        logger.error(f"Error classifying query '{query}': {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error classifying query: {str(e)}")

@router.get("/methods", response_model=List[str])
async def search_methods():
    """
    Get available search methods.
    
    Returns:
        List[str]: List of available search methods
    """
    logger.debug("Received request for available search methods")
    methods = [method.value for method in SearchType]
    logger.debug(f"Returning available methods: {methods}")
    return methods

@router.post("/upload", response_model=List[SearchResult])
async def upload_image(
    image_file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    limit: int = Form(10),
    es_client: Elasticsearch = Depends(get_elasticsearch_client)
):
    """
    Process an uploaded image containing a list of supplies and return recommended products.
    
    This endpoint accepts an uploaded image, extracts text using the configured vision provider,
    identifies required items, and suggests products from the catalog.
    """
    logger.info(f"Received image upload request - File: {image_file.filename}, User: {user_id}, Limit: {limit}")
    
    import traceback
    from app.config.settings import VISION_PROVIDER
    from app.utils.validation import check_vision_provider
    
    # Validate image file
    valid_mime_types = ["image/jpeg", "image/png", "application/pdf"]
    if image_file.content_type not in valid_mime_types:
        logger.warning(f"Invalid file type: {image_file.content_type}")
        raise HTTPException(status_code=400, detail=f"File must be one of: {', '.join(valid_mime_types)}")
    
    # Check if vision provider is available
    vision_status = check_vision_provider()
    if not vision_status["available"]:
        logger.error(f"Vision provider '{VISION_PROVIDER}' is not available: {vision_status['error']}")
        raise HTTPException(
            status_code=503, 
            detail=f"Image-based search is currently unavailable. Vision provider '{VISION_PROVIDER}' is not available: {vision_status['error']}"
        )
    
    try:
        # Process the image to extract text and identify items
        logger.debug(f"Processing image using {VISION_PROVIDER} provider...")
        from app.utils.image_processor import process_image_query
        results = await process_image_query(
            image_file=image_file,
            user_id=user_id,
            limit=limit,
            elasticsearch_client=es_client
        )
        
        logger.info(f"Found {len(results)} results for uploaded image '{image_file.filename}'")
        for result in results:
            logger.debug(f"Upload result - ID: {result.product_id}, Name: {result.product_name}, Score: {result.score}")
        
        return results
    except Exception as e:
        # Log the full traceback for debugging
        logger.error(f"Image processing failed for file '{image_file.filename}': {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

@router.get("/random")
async def get_random_products(
    count: int = 4,
    es_client: Elasticsearch = Depends(get_elasticsearch_client)
):
    """Get featured products from the catalog."""
    try:
        logger.info(f"Fetching {count} featured products")
        
        # Query for specific products that we know have images
        query = {
            "size": count,
            "_source": {
                "excludes": ["text_embedding", "image.vector_embedding"]
            },
            "query": {
                "terms": {
                    "_id": [
                        "1",  # Staples 20/6 Stapler
                        "2",  # HP LaserJet Pro
                        "3",  # Dell XPS 13
                        "4"   # Apple Magic Mouse
                    ]
                }
            }
        }
        
        logger.debug(f"Elasticsearch query: {json.dumps(query, indent=2)}")
        response = es_client.search(
            index=ELASTICSEARCH_INDEX_PRODUCTS,
            body=query
        )
        
        # Convert response to dict for logging
        response_dict = dict(response)
        logger.debug(f"Elasticsearch response: {json.dumps(response_dict, indent=2)}")
        
        products = []
        for hit in response['hits']['hits']:
            product = hit['_source']
            product['product_id'] = hit['_id']
            products.append(product)
            
        logger.info(f"Found {len(products)} featured products")
        return products
    except Exception as e:
        logger.error(f"Error fetching featured products: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
