# Elastic E-Commerce Demo

This repository contains an e-commerce demo application based on Elasticsearch and Kafka, featuring a chat-based product search interface.

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

### 3. Generate Product Data

```bash
# Generate product data without vector embeddings
python scripts/generate_products.py
```

### 4. Initialize Ollama (Optional)

If you want to use Ollama for vision processing and embeddings:

```bash
# Install and initialize Ollama with required models
scripts/init_ollama.sh
```

This script will install the following models:
- `llama3`: Used for text embeddings and query classification
- `llava:34b`: Used for vision processing (image analysis)

### 5. Start Backend API

```bash
# Install dependencies
cd app
pip install -r requirements.txt

# Set OpenAI API key for image processing (required unless using Ollama)
export OPENAI_API_KEY=your_api_key

# Optionally use Ollama for vision processing instead of OpenAI
# export VISION_PROVIDER=ollama

# Set Python path and start the FastAPI backend
PYTHONPATH=/home/ubuntu/elastic-ecomm python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Start Frontend Application

```bash
# Install dependencies
cd frontend/elastic-ecomm-ui
npm install

# Start the React frontend application
npm run dev
```

The frontend will be available at http://localhost:3000

## Image Generation

The repository includes scripts for generating product images using OpenAI's DALL-E API with true infinite retry logic:

```bash
# Set your OpenAI API key as an environment variable (never store in code)
export OPENAI_API_KEY=your_api_key

# Generate images for all products
python scripts/generate_product_image.py

# Generate images for office supplies in parallel (10 partitions)
python scripts/partition_office_supplies.py
```

### Image Generation Features

- **True Infinite Retry**: Scripts will continuously retry image generation until successful, even across script restarts
- **Exponential Backoff**: Handles rate limiting with exponential backoff up to 60 seconds with jitter
- **Checkpoint Tracking**: Maintains progress in checkpoint files to resume after interruptions
- **Parallel Processing**: Partitions products for faster generation across multiple processes

## Vision Processing

The application supports multiple vision providers for processing image uploads:

- **OpenAI** (default): Uses OpenAI's GPT-4o model for image analysis
- **Ollama**: Uses Ollama's llava:34b model for local image analysis

To configure the vision provider:

```bash
# Use OpenAI (default)
export VISION_PROVIDER=openai
export OPENAI_API_KEY=your_api_key

# Use Ollama (requires running init_ollama.sh first)
export VISION_PROVIDER=ollama
```

## Architecture

- **Backend**: FastAPI application with Elasticsearch for product search
- **Frontend**: React application with Material UI components
  - Chat-based interface for product search
  - Dynamic Elasticsearch query display
  - Responsive product grid display
- **Data Pipeline**: Kafka for event streaming and data ingestion
- **Image Generation**: OpenAI DALL-E API integration with resilient retry mechanism
- **Vision Processing**: Configurable providers (OpenAI or Ollama) for image analysis

## Development Notes

- The frontend uses Vite and is configured to run on port 3000
- The backend API runs on port 8000
- Product images are stored in `data/images/` with naming pattern `product_<GUID>.png`
- The chat interface supports multiple search types (keyword, vector, image, customer support)
- The `/health` endpoint provides status information about all services
