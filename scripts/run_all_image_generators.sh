#!/bin/bash
# Script to run image generation with TRUE infinite retry for all partitions

# Set absolute paths
REPO_ROOT="/home/ubuntu/elastic-ecomm"
SCRIPTS_DIR="${REPO_ROOT}/scripts"
DATA_DIR="${REPO_ROOT}/data"
IMAGES_DIR="${DATA_DIR}/images"
TEMP_DIR="${SCRIPTS_DIR}/temp"
LOG_DIR="/tmp"
CHECKPOINT_DIR="/tmp"

echo "Starting image generation for all partitions"
echo "Repository root: ${REPO_ROOT}"
echo "Images directory: ${IMAGES_DIR}"

# Create directories if they don't exist
mkdir -p "${IMAGES_DIR}"
mkdir -p "${CHECKPOINT_DIR}"

# Kill any existing image generation processes
pkill -f "python3 ${SCRIPTS_DIR}/generate_partition_images.py" || true

# Loop through all partitions and start the processes
for PARTITION_NUM in {1..10}; do
    PARTITION_FILE="${TEMP_DIR}/office_supplies_partition_${PARTITION_NUM}.json"
    LOG_FILE="${LOG_DIR}/image_generation_partition_${PARTITION_NUM}.log"
    
    echo "Starting image generation for partition ${PARTITION_NUM} using ${PARTITION_FILE}"
    echo "Logs will be written to ${LOG_FILE}"
    
    # Start the process in the background
    (
        # True infinite retry - never exit, always keep trying
        while true; do
            echo "$(date) - Attempt to run image generation for partition ${PARTITION_NUM}" >> ${LOG_FILE}
            
            # Export the partition number as an environment variable
            export PARTITION_NUM=${PARTITION_NUM}
            
            # Run the image generation script with absolute paths
            OPENAI_API_KEY=$OPENAI_APIKEY python3 ${SCRIPTS_DIR}/generate_partition_images.py \
                ${PARTITION_FILE} \
                --output-dir=${IMAGES_DIR} \
                --checkpoint-dir=${CHECKPOINT_DIR} \
                --partition-num=${PARTITION_NUM} \
                >> ${LOG_FILE} 2>&1
            
            # Always continue running, regardless of exit code
            # This ensures we keep trying even if the script exits with success (0)
            # because we want to make sure ALL images are generated
            echo "$(date) - Image generation for partition ${PARTITION_NUM} completed or encountered an error, continuing in 10 seconds..." >> ${LOG_FILE}
            sleep 10
        done
    ) &
    
    # Sleep briefly to stagger the starts
    sleep 1
done

echo "All image generation processes started. Check logs in ${LOG_DIR} for progress."
echo "Images are being saved to ${IMAGES_DIR}"
