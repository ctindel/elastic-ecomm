# E-Commerce Search Demo

This project demonstrates advanced search capabilities for e-commerce applications using Elasticsearch and Ollama.

## Features

- BM25 keyword-based search
- Vector-based semantic search
- Ollama-powered query classification
- Image-based product search
- Synthetic product catalog generation
- Buyer persona simulation

## Setup

1. Clone this repository
2. Copy `.env.example` to `.env` and configure your API keys
3. Run `docker-compose up -d` to start Elasticsearch
4. Run `python -m scripts.generate_data` to generate test data
5. Run `python -m scripts.index_data` to index data in Elasticsearch
6. Run `python -m app.main` to start the API server

## Testing

Run tests with:

```bash
python -m pytest
```
