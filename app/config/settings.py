"""
Configuration settings for the E-Commerce Search Demo.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Elasticsearch settings
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
ELASTICSEARCH_INDEX_PRODUCTS = "products"
ELASTICSEARCH_INDEX_PERSONAS = "buyer_personas"

# Ollama settings
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

# Vector embedding dimensions
TEXT_EMBEDDING_DIMS = 384
IMAGE_EMBEDDING_DIMS = 512

# Data generation settings
NUM_PRODUCTS = 500
NUM_PERSONAS = 5
