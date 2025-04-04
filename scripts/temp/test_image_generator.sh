#!/bin/bash
# Script to test image generation with TRUE infinite retry
PARTITION_FILE="/tmp/test_products.json"
PARTITION_NUM="test"
LOG_FILE="/tmp/image_generation_partition_${PARTITION_NUM}.log"

echo "Starting test image generation using ${PARTITION_FILE}"
echo "Logs will be written to ${LOG_FILE}"

# Run the script once with output to console for testing
OPENAI_API_KEY=$OPENAI_APIKEY python3 /home/ubuntu/elastic-ecomm/scripts/generate_partition_images.py ${PARTITION_FILE} ${PARTITION_NUM}

echo "Test completed. Check ${LOG_FILE} for details."
