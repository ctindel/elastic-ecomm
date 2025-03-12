# Docker Configuration for E-Commerce Search Demo

This directory contains Docker configuration files for the E-Commerce Search Demo.

## Components

- **Elasticsearch**: Used for both keyword-based (BM25) and vector-based search
- **Ollama**: Used for generating vector embeddings
- **Kibana**: Optional web UI for Elasticsearch management and visualization

## Configuration

### Elasticsearch

Elasticsearch is configured with:
- BM25 indexing enabled (default in Elasticsearch)
- Vector search enabled via dense_vector type
- Pre-configured index mappings for products and buyer personas

### Ollama

Ollama is used for generating vector embeddings for:
- Product text descriptions
- Product images

## Usage

Start the Docker containers using Docker Compose:

```bash
docker-compose up -d
```

This will start Elasticsearch, Ollama, and Kibana containers.

## Mappings

The `elasticsearch/mappings` directory contains JSON files with index mappings:

- `products.json`: Mapping for the products index
- `personas.json`: Mapping for the buyer personas index

These mappings are automatically applied when running the `setup_elasticsearch.py` script.

## Volumes

The Docker Compose configuration creates persistent volumes for:
- Elasticsearch data
- Ollama models

This ensures that data is preserved between container restarts.
