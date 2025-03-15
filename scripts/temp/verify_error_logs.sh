#!/bin/bash
# Script to verify error logs include filenames and product IDs
export OPENAI_API_KEY=$OPENAI_APIKEY
LOG_FILE="/tmp/verify_error_logs.log"

echo "Testing updated error logs..."
echo "Logs will be written to ${LOG_FILE}"

# Run the script with test products
python /home/ubuntu/elastic-ecomm/scripts/generate_partition_images.py /tmp/test_products.json test > ${LOG_FILE} 2>&1

# Display the error log messages
echo -e "\nERROR Log Messages:"
grep -i "Error generating image:" ${LOG_FILE} | head -3
