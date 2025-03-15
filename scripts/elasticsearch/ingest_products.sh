#!/bin/bash
# Script to ingest products into Elasticsearch via Kafka

# Set up error handling
set -e
trap 'echo "Error: Command failed at line $LINENO"' ERR

# Define variables
PRODUCTS_FILE="data/products.json"
MAPPING_FILE="config/elasticsearch/mappings/products.json"
ES_HOST="http://localhost:9200"
OLLAMA_HOST="http://localhost:11434"
OLLAMA_MODEL="llama3"
BATCH_SIZE=100
MAX_PRODUCTS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --products-file)
      PRODUCTS_FILE="$2"
      shift 2
      ;;
    --mapping-file)
      MAPPING_FILE="$2"
      shift 2
      ;;
    --es-host)
      ES_HOST="$2"
      shift 2
      ;;
    --ollama-host)
      OLLAMA_HOST="$2"
      shift 2
      ;;
    --ollama-model)
      OLLAMA_MODEL="$2"
      shift 2
      ;;
    --batch-size)
      BATCH_SIZE="$2"
      shift 2
      ;;
    --max-products)
      MAX_PRODUCTS="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check if Elasticsearch is running
echo "Checking if Elasticsearch is running..."
if ! curl -s "$ES_HOST" > /dev/null; then
  echo "Error: Elasticsearch is not running or not reachable at $ES_HOST"
  exit 1
fi

# Run the ingestion script
echo "Starting ingestion process..."
PYTHONPATH=$(pwd) python scripts/elasticsearch/ingest_products.py \
  --products-file "$PRODUCTS_FILE" \
  --mapping-file "$MAPPING_FILE" \
  --es-host "$ES_HOST" \
  --ollama-host "$OLLAMA_HOST" \
  --ollama-model "$OLLAMA_MODEL" \
  --batch-size "$BATCH_SIZE" \
  ${MAX_PRODUCTS:+--max-products "$MAX_PRODUCTS"}

echo "Ingestion process completed"
