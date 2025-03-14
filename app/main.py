#!/usr/bin/env python3
"""
Main entry point for the E-Commerce Search Demo API.
"""
import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from app.config.settings import (
    ELASTICSEARCH_HOST,
    API_HOST,
    API_PORT,
    API_DEBUG,
    API_RELOAD
)
from app.api.search import router as search_router

# Create FastAPI app
app = FastAPI(
    title="E-Commerce Search Demo API",
    description="API for the E-Commerce Search Demo",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(search_router, prefix="/api/search", tags=["search"])

# Dependency to get Elasticsearch client
def get_elasticsearch_client():
    """Get Elasticsearch client."""
    try:
        es = Elasticsearch(ELASTICSEARCH_HOST)
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
    from app.config.settings import ELASTICSEARCH_INDEX_PRODUCTS, ELASTICSEARCH_INDEX_PERSONAS, ELASTICSEARCH_INDEX_QUERIES
    
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
        es = Elasticsearch(ELASTICSEARCH_HOST)
        es_health = es.cluster.health()
        response["elasticsearch"]["status"] = es_health.get("status", "unknown")
        response["elasticsearch"]["cluster_name"] = es_health.get("cluster_name", "unknown")
        response["elasticsearch"]["number_of_nodes"] = es_health.get("number_of_nodes", 0)
        response["elasticsearch"]["connection"] = True
        
        # Get index stats
        indices_info = {}
        indices = [ELASTICSEARCH_INDEX_PRODUCTS, ELASTICSEARCH_INDEX_PERSONAS, ELASTICSEARCH_INDEX_QUERIES]
        
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
        from app.utils.embedding import check_ollama_connection
        ollama_available = check_ollama_connection()
        response["ollama"]["available"] = ollama_available
    except Exception as e:
        logger.warning(f"Ollama health check failed: {str(e)}")
        response["ollama"]["error"] = str(e)
    
    # Check OpenAI API key and connectivity
    try:
        from app.utils.validation import check_openai_connection
        openai_status = check_openai_connection()
        response["openai"] = openai_status
    except Exception as e:
        logger.warning(f"OpenAI API key check failed: {str(e)}")
        response["openai"]["error"] = str(e)
    
    # Determine overall status
    if not response["elasticsearch"]["connection"]:
        response["status"] = "degraded"
        
    return response

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD
    )
