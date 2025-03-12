#!/usr/bin/env python3
"""
Settings for the e-commerce search demo
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()

# Elasticsearch settings
ELASTICSEARCH_HOST = os.environ.get("ELASTICSEARCH_HOST", "http://localhost:9200")
ELASTICSEARCH_INDEX_PRODUCTS = os.environ.get("ELASTICSEARCH_INDEX_PRODUCTS", "products")
ELASTICSEARCH_INDEX_PERSONAS = os.environ.get("ELASTICSEARCH_INDEX_PERSONAS", "personas")
ELASTICSEARCH_INDEX_QUERIES = os.environ.get("ELASTICSEARCH_INDEX_QUERIES", "queries")

# Ollama settings
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama2")

# OpenAI settings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4-turbo")

# Kafka settings
KAFKA_HOST = os.environ.get("KAFKA_HOST", "localhost:9092")
KAFKA_TOPIC_PRODUCTS = os.environ.get("KAFKA_TOPIC_PRODUCTS", "products")
KAFKA_TOPIC_PRODUCT_IMAGES = os.environ.get("KAFKA_TOPIC_PRODUCT_IMAGES", "product_images")
KAFKA_TOPIC_FAILED_INGESTION = os.environ.get("KAFKA_TOPIC_FAILED_INGESTION", "failed_ingestion")
KAFKA_GROUP_ID = os.environ.get("KAFKA_GROUP_ID", "ecommerce-search")

# Redis settings
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")

# Circuit breaker settings
CIRCUIT_BREAKER_THRESHOLD = int(os.environ.get("CIRCUIT_BREAKER_THRESHOLD", "5"))
CIRCUIT_BREAKER_TIMEOUT = int(os.environ.get("CIRCUIT_BREAKER_TIMEOUT", "60"))
CIRCUIT_BREAKER_STORAGE = os.environ.get("CIRCUIT_BREAKER_STORAGE", "memory")  # memory or redis

# Vector embedding dimensions
TEXT_EMBEDDING_DIMS = 384
IMAGE_EMBEDDING_DIMS = 512

# Data paths
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
