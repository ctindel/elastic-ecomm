#!/usr/bin/env python3
"""
Main entry point for the E-Commerce Search Demo API.
"""
import os
import sys
from fastapi import FastAPI, HTTPException, Depends, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from elasticsearch import Elasticsearch

# Import our custom logger
from app.utils.logger import logger

from app.config.settings import settings
from app.api.search import router as search_router
from app.utils.validation import check_vision_provider, check_openai_connection
from app.utils.embedding import check_ollama_connection
from app.utils.image_processor import process_image_query

# Create FastAPI app
app = FastAPI(
    title="E-Commerce Search Demo API",
    description="API for the E-Commerce Search Demo",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Add custom middleware to handle CORS headers
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Add OPTIONS route handler for all paths
@app.options("/{path:path}")
async def options_handler(path: str):
    return {"status": "ok"}

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent.parent / "data")), name="static")

# Add routers
app.include_router(search_router, prefix="/api/search", tags=["search"])

# Dependency to get Elasticsearch client
def get_elasticsearch_client():
    """Get Elasticsearch client."""
    try:
        es = Elasticsearch(settings.ELASTICSEARCH_HOST)
        yield es
    finally:
        es.close()

@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the E-Commerce Search Demo API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    # Initialize response
    response = {
        "status": "healthy",
        "elasticsearch": {
            "status": "unknown",
            "cluster_name": "unknown",
            "number_of_nodes": 0,
            "connection": False,
            "indices": {}
        },
        "ollama": {
            "available": False
        },
        "openai": {
            "configured": False
        }
    }
    
    # Check Elasticsearch connection
    try:
        es = Elasticsearch(settings.ELASTICSEARCH_HOST)
        es_health = es.cluster.health()
        response["elasticsearch"]["status"] = es_health.get("status", "unknown")
        response["elasticsearch"]["cluster_name"] = es_health.get("cluster_name", "unknown")
        response["elasticsearch"]["number_of_nodes"] = es_health.get("number_of_nodes", 0)
        response["elasticsearch"]["connection"] = True
        
        # Get index stats
        indices_info = {}
        indices = [settings.ELASTICSEARCH_INDEX_PRODUCTS, settings.ELASTICSEARCH_INDEX_PERSONAS, settings.ELASTICSEARCH_INDEX_QUERIES]
        
        for index in indices:
            try:
                if es.indices.exists(index=index):
                    # Get document count
                    count_response = es.count(index=index)
                    doc_count = count_response.get("count", 0)
                    
                    # Get index stats
                    stats = es.indices.stats(index=index)
                    index_stats = stats.get("indices", {}).get(index, {})
                    
                    # Get mapping to check for vector fields
                    mapping = es.indices.get_mapping(index=index)
                    properties = mapping.get(index, {}).get("mappings", {}).get("properties", {})
                    
                    # Count vector fields
                    vector_fields = [
                        field for field, config in properties.items() 
                        if config.get("type") == "dense_vector"
                    ]
                    
                    # Count documents with vectors
                    vector_docs_count = 0
                    if vector_fields and doc_count > 0:
                        for field in vector_fields:
                            try:
                                # Query for documents that have this vector field
                                vector_query = {
                                    "query": {
                                        "exists": {
                                            "field": field
                                        }
                                    }
                                }
                                vector_count = es.count(index=index, body=vector_query)
                                vector_docs_count = max(vector_docs_count, vector_count.get("count", 0))
                            except Exception:
                                # If query fails, continue with next field
                                pass
                    
                    # Add to indices info
                    indices_info[index] = {
                        "exists": True,
                        "document_count": doc_count,
                        "vector_fields": vector_fields,
                        "vector_fields_count": len(vector_fields),
                        "documents_with_vectors": vector_docs_count,
                        "size_in_bytes": index_stats.get("total", {}).get("store", {}).get("size_in_bytes", 0)
                    }
                else:
                    indices_info[index] = {
                        "exists": False,
                        "document_count": 0,
                        "vector_fields": [],
                        "vector_fields_count": 0,
                        "documents_with_vectors": 0,
                        "size_in_bytes": 0
                    }
            except Exception as e:
                indices_info[index] = {
                    "exists": False,
                    "error": str(e),
                    "document_count": 0,
                    "vector_fields": [],
                    "vector_fields_count": 0,
                    "documents_with_vectors": 0,
                    "size_in_bytes": 0
                }
        
        response["elasticsearch"]["indices"] = indices_info
        es.close()
    except Exception as e:
        logger.warning(f"Elasticsearch health check failed: {str(e)}")
        response["elasticsearch"]["error"] = str(e)
    
    # Check Ollama connection
    try:
        ollama_available = check_ollama_connection()
        response["ollama"]["available"] = ollama_available
    except Exception as e:
        logger.warning(f"Ollama health check failed: {str(e)}")
        response["ollama"]["error"] = str(e)
    
    # Check OpenAI API key and connectivity
    try:
        openai_status = check_openai_connection()
        response["openai"] = openai_status
    except Exception as e:
        logger.warning(f"OpenAI API key check failed: {str(e)}")
        response["openai"]["error"] = str(e)
    
    # Check vision provider
    try:
        vision_status = check_vision_provider()
        response["vision"] = {
            "provider": settings.VISION_PROVIDER,
            "available": vision_status["available"],
            "error": vision_status["error"]
        }
    except Exception as e:
        logger.warning(f"Vision provider check failed: {str(e)}")
        response["vision"] = {
            "provider": settings.VISION_PROVIDER,
            "available": False,
            "error": str(e)
        }
    
    return response

@app.post("/process-image", tags=["image"])
async def process_image(file: bytes = File(...)):
    """Process an image and return search results."""
    # Process image-based search
    if file:
        try:
            # Process the image and get search results
            if settings.VISION_PROVIDER == "openai":
                search_results = await process_image_query(file, es_client)
                return {"results": search_results}
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported vision provider: {settings.VISION_PROVIDER}"
                )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Verify vision provider at startup
    vision_status = check_vision_provider()
    if not vision_status["available"]:
        if settings.VISION_PROVIDER == "openai":
            error_msg = "ERROR: OpenAI API key is missing or invalid. Please set a valid OPENAI_API_KEY environment variable."
        else:
            error_msg = f"ERROR: Vision provider '{settings.VISION_PROVIDER}' is not available: {vision_status['error']}"
        logger.error(error_msg)
        sys.exit(1)
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
