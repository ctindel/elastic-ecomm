#!/usr/bin/env python3
"""
Direct Kafka producer for e-commerce data using Docker exec to call kafka-console-producer
This avoids dependency issues with the kafka-python library
"""
import os
import json
import time
import argparse
import subprocess
from pathlib import Path
import sys

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    KAFKA_HOST,
    KAFKA_TOPIC_PRODUCTS,
    KAFKA_TOPIC_PRODUCT_IMAGES
)

def process_file(file_path, topic):
    """Process a file and send records to Kafka directly in the container"""
    print(f"Processing {file_path} to topic {topic}")
    
    try:
        # Create a temporary directory for processing
        temp_dir = "/tmp/ecommerce_data_processing"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Copy the file to the Docker container
        print(f"Copying {file_path} to Kafka container")
        copy_cmd = f"docker cp {file_path} kafka:/tmp/{os.path.basename(file_path)}"
        subprocess.run(copy_cmd, shell=True, check=True)
        
        # Process the file directly in the Kafka container
        print(f"Processing {file_path} in Kafka container")
        
        # Create a shell script to process the file
        script_path = f"{temp_dir}/process_{topic}.sh"
        with open(script_path, 'w') as script_file:
            script_file.write(f'''#!/bin/bash
# Create topics if they don't exist
kafka-topics --create --if-not-exists --topic {topic} --partitions 3 --replication-factor 1 --bootstrap-server localhost:9092

# Process the file and send to Kafka
cat /tmp/{os.path.basename(file_path)} | kafka-console-producer --broker-list localhost:9092 --topic {topic}
''')
        
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        # Copy the script to the container
        copy_script_cmd = f"docker cp {script_path} kafka:/tmp/process_{topic}.sh"
        subprocess.run(copy_script_cmd, shell=True, check=True)
        
        # Run the script in the container
        process_cmd = f"docker exec kafka bash /tmp/process_{topic}.sh"
        
        subprocess.run(process_cmd, shell=True)
        
        print(f"Completed processing {file_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Process e-commerce data files and send to Kafka')
    parser.add_argument('--file', required=True, help='Path to JSON file to process')
    parser.add_argument('--topic', required=True, help='Kafka topic to send to')
    args = parser.parse_args()
    
    # Process the file
    process_file(args.file, args.topic)

if __name__ == "__main__":
    main()
