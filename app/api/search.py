"""
Search API endpoints for the E-Commerce Search Demo.
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from elasticsearch import Elasticsearch

from app.models.search import SearchResult, SearchType
from app.utils.search_agent import determine_search_method, perform_search
from app.utils.image_processor import process_image_query
from app.config.settings import ELASTICSEARCH_HOST

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

@router.post("/text", response_model=List[SearchResult])
async def text_search(search_query: SearchQuery):
    """
    Perform a text-based search using the AI agent to determine the best search method.
    """
    try:
        # Determine the best search method for this query
        search_type = determine_search_method(search_query.query)
        
        # Perform the search using the determined method
        results = perform_search(
            query=search_query.query,
            search_type=search_type,
            user_id=search_query.user_id,
            limit=search_query.limit
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

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
    # Validate image file
    if not image_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check if OpenAI API key is available
    from app.config.settings import OPENAI_API_KEY
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503, 
            detail="Image-based search is currently unavailable. OpenAI API key is missing or invalid."
        )
    
    try:
        # Get Elasticsearch client
        from elasticsearch import Elasticsearch
        from app.config.settings import ELASTICSEARCH_HOST
        es_client = Elasticsearch(ELASTICSEARCH_HOST)
        
        # Process the image to extract text and identify items
        results = await process_image_query(
            image_file=image_file,
            user_id=user_id,
            limit=limit,
            elasticsearch_client=es_client
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")

@router.get("/classify")
async def classify_search_query(
    query: str = Query(..., description="Search query to classify")
):
    """
    Classify a search query to determine the best search method.
    """
    try:
        # Determine search method
        search_type = determine_search_method(query)
        
        return {"search_type": search_type}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error classifying query: {str(e)}")

@router.get("/methods", response_model=List[str])
async def search_methods():
    """
    Get available search methods.
    
    Returns:
        List[str]: List of available search methods
    """
    return [method.value for method in SearchType]

@router.post("/upload", response_model=List[SearchResult])
async def upload_image(
    image_file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    limit: int = Form(10),
    es_client: Elasticsearch = Depends(get_elasticsearch_client)
):
    """
    Process an uploaded image containing a list of supplies and return recommended products.
    
    This endpoint accepts an uploaded image, extracts text using OpenAI's API,
    identifies required items, and suggests products from the catalog.
    """
    # Validate image file
    valid_mime_types = ["image/jpeg", "image/png", "application/pdf"]
    if image_file.content_type not in valid_mime_types:
        raise HTTPException(status_code=400, detail=f"File must be one of: {', '.join(valid_mime_types)}")
    
    # Check if OpenAI API key is available
    from app.config.settings import OPENAI_API_KEY
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=503, 
            detail="Image-based search is currently unavailable. OpenAI API key is missing or invalid."
        )
    
    try:
        # Process the image to extract text and identify items
        results = await process_image_query(
            image_file=image_file,
            user_id=user_id,
            limit=limit,
            elasticsearch_client=es_client
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
