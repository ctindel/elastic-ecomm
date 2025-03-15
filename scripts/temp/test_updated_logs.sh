#!/bin/bash
# Script to test the updated log messages
export OPENAI_API_KEY=$OPENAI_APIKEY
LOG_FILE="/tmp/test_log_messages_updated.log"

echo "Testing updated log messages..."
echo "Logs will be written to ${LOG_FILE}"

# Run the script with test products
python /home/ubuntu/elastic-ecomm/scripts/generate_partition_images.py /tmp/test_products.json test > ${LOG_FILE} 2>&1

# Display the log messages
echo -e "\n\nINFO Log Messages:"
grep -i "Attempting to generate image" ${LOG_FILE} | head -3

echo -e "\n\nERROR Log Messages:"
grep -i "Error generating image" ${LOG_FILE} | head -3
