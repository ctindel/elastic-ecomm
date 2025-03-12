#!/usr/bin/env python3
"""
Main entry point for the E-Commerce Search Demo application.
"""
import os
import logging
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.search import router as search_router
from app.utils.validation import validate_api_keys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="E-Commerce Search Demo",
    description="AI-powered e-commerce search system with Elasticsearch and Ollama",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_router, prefix="/api/search", tags=["search"])

@app.on_event("startup")
async def startup_event():
    """Validate API keys and connections on startup."""
    try:
        validate_api_keys()
        logger.info("API keys validated successfully")
    except Exception as e:
        logger.error(f"Failed to validate API keys: {str(e)}")
        # We'll continue running but some functionality may be limited

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
