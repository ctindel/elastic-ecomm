#!/usr/bin/env python3
"""
Configuration settings for the E-Commerce Search Demo.
"""
import os
from pydantic_settings import BaseSettings
from typing import List, ClassVar

class Settings(BaseSettings):
    # API Configuration
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # CORS Configuration
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    
    @property
    def allowed_origins(self) -> List[str]:
        """Get list of allowed CORS origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Elasticsearch settings
    ELASTICSEARCH_HOST: str = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
    ELASTICSEARCH_INDEX_PRODUCTS: str = os.getenv("ELASTICSEARCH_INDEX_PRODUCTS", "products")
    ELASTICSEARCH_INDEX_PERSONAS: str = os.getenv("ELASTICSEARCH_INDEX_PERSONAS", "personas")
    ELASTICSEARCH_INDEX_QUERIES: str = os.getenv("ELASTICSEARCH_INDEX_QUERIES", "queries")

    # Ollama settings
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    OLLAMA_API_URL: str = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")
    OLLAMA_VISION_MODEL: str = os.getenv("OLLAMA_VISION_MODEL", "llava")

    # Vision provider settings
    VISION_PROVIDER: str = os.getenv("VISION_PROVIDER", "openai")  # Options: "openai" or "ollama"

    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_URL: str = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1")

    # Embedding dimensions
    TEXT_EMBEDDING_DIMS: int = int(os.getenv("TEXT_EMBEDDING_DIMS", "4096"))
    IMAGE_EMBEDDING_DIMS: int = int(os.getenv("IMAGE_EMBEDDING_DIMS", "512"))

    # Kafka settings
    KAFKA_HOST: str = os.getenv("KAFKA_HOST", "localhost:9092")
    KAFKA_TOPIC_PRODUCTS: str = os.getenv("KAFKA_TOPIC_PRODUCTS", "products")
    KAFKA_TOPIC_PRODUCT_IMAGES: str = os.getenv("KAFKA_TOPIC_PRODUCT_IMAGES", "product-images")
    KAFKA_TOPIC_FAILED_INGESTION: str = os.getenv("KAFKA_TOPIC_FAILED_INGESTION", "failed-ingestion")

    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_DEBUG: bool = os.getenv("API_DEBUG", "True").lower() in ("true", "1", "t")
    API_RELOAD: bool = os.getenv("API_RELOAD", "True").lower() in ("true", "1", "t")

    # Data generation settings
    NUM_PRODUCTS: int = 10000
    NUM_PERSONAS: int = 5

settings = Settings()
