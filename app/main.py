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
async def health_check(es: Elasticsearch = Depends(get_elasticsearch_client)):
    """Health check endpoint."""
    try:
        # Check Elasticsearch connection
        es_health = es.cluster.health()
        
        # Check Ollama connection
        from app.utils.embedding import check_ollama_connection
        ollama_available = check_ollama_connection()
        
        # Check OpenAI API key
        from app.config.settings import OPENAI_API_KEY
        openai_configured = bool(OPENAI_API_KEY)
        
        return {
            "status": "healthy",
            "elasticsearch": {
                "status": es_health.get("status", "unknown"),
                "cluster_name": es_health.get("cluster_name", "unknown"),
                "number_of_nodes": es_health.get("number_of_nodes", 0)
            },
            "ollama": {
                "available": ollama_available
            },
            "openai": {
                "configured": openai_configured
            }
        }
    
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=API_RELOAD
    )
