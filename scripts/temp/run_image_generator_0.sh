#!/bin/bash
# Script to run image generation with true infinite retry
PARTITION_FILE=$1
PARTITION_NUM=$2
LOG_FILE="/tmp/image_generation_partition_${PARTITION_NUM}.log"

echo "Starting image generation for partition ${PARTITION_NUM} using ${PARTITION_FILE}"
echo "Logs will be written to ${LOG_FILE}"

# True infinite retry - never exit, always keep trying
while true; do
    echo "$(date) - Attempt to run image generation for partition ${PARTITION_NUM}" >> ${LOG_FILE}
    OPENAI_API_KEY=$OPENAI_APIKEY python3 /home/ubuntu/elastic-ecomm/scripts/generate_partition_images.py ${PARTITION_FILE} ${PARTITION_NUM} >> ${LOG_FILE} 2>&1
    
    # Always continue running, regardless of exit code
    # This ensures we keep trying even if the script exits with success (0)
    # because we want to make sure ALL images are generated
    echo "$(date) - Image generation for partition ${PARTITION_NUM} completed or encountered an error, continuing in 10 seconds..." >> ${LOG_FILE}
    sleep 10
done
