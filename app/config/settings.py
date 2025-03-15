#!/usr/bin/env python3
"""
Configuration settings for the E-Commerce Search Demo.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Elasticsearch settings
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
ELASTICSEARCH_INDEX_PRODUCTS = os.getenv("ELASTICSEARCH_INDEX_PRODUCTS", "products")
ELASTICSEARCH_INDEX_PERSONAS = os.getenv("ELASTICSEARCH_INDEX_PERSONAS", "personas")
ELASTICSEARCH_INDEX_QUERIES = os.getenv("ELASTICSEARCH_INDEX_QUERIES", "queries")

# Ollama settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/generate")

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1")

# Vector embedding dimensions
TEXT_EMBEDDING_DIMS = int(os.getenv("TEXT_EMBEDDING_DIMS", "384"))
IMAGE_EMBEDDING_DIMS = int(os.getenv("IMAGE_EMBEDDING_DIMS", "512"))

# Kafka settings
KAFKA_HOST = os.getenv("KAFKA_HOST", "localhost:9092")
KAFKA_TOPIC_PRODUCTS = os.getenv("KAFKA_TOPIC_PRODUCTS", "products")
KAFKA_TOPIC_PRODUCT_IMAGES = os.getenv("KAFKA_TOPIC_PRODUCT_IMAGES", "product-images")
KAFKA_TOPIC_FAILED_INGESTION = os.getenv("KAFKA_TOPIC_FAILED_INGESTION", "failed-ingestion")

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "True").lower() in ("true", "1", "t")
API_RELOAD = os.getenv("API_RELOAD", "True").lower() in ("true", "1", "t")

# Data generation settings
NUM_PRODUCTS = 5000
NUM_PERSONAS = 5
