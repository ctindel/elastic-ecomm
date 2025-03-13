# E-Commerce Search Demo - Kafka Ingestion Pipeline

This PR implements a Kafka-based ingestion pipeline for products and product images. It includes:

1. Circuit breaker pattern to prevent Ollama overload
2. Simple Kafka consumer implementation
3. Elasticsearch vectorization pipeline

The implementation follows the structure of the elastic-courts repository and provides robust error handling and retry mechanisms.
