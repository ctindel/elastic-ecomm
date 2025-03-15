# Elastic E-Commerce Demo

This repository contains an e-commerce demo application based on Elasticsearch and Kafka.

## Setup Instructions

### 1. Start Docker Containers

```bash
# Start all required services (Elasticsearch, Kafka, Zookeeper)
docker compose up -d
```

### 2. Initialize Kafka Topics

```bash
# Create required Kafka topics
scripts/kafka/init_kafka.sh
```

### 3. Start Backend API

```bash
# Set Python path and start the FastAPI backend
cd app
PYTHONPATH=/home/ubuntu/elastic-ecomm python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Frontend Application

```bash
# Start the React frontend application
cd frontend/elastic-ecomm-ui
npm run dev
```

## Image Generation

The repository includes scripts for generating product images using OpenAI's DALL-E API:

```bash
# Generate images for all products
OPENAI_API_KEY=your_api_key python scripts/generate_product_image.py

# Generate images for office supplies in parallel
python scripts/partition_office_supplies.py
```

## Architecture

- **Backend**: FastAPI application with Elasticsearch for product search
- **Frontend**: React application with Material UI components
- **Data Pipeline**: Kafka for event streaming and data ingestion
