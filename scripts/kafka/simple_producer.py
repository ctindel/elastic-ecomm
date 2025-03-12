#!/usr/bin/env python3
"""
Simple Kafka producer for e-commerce data using subprocess to call kafka-console-producer
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

def send_to_kafka(data, topic):
    """
    Send data to Kafka topic using subprocess.
    
    Args:
        data: Data to send (will be converted to JSON)
        topic: Kafka topic to send to
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create a temporary file for the data
        temp_file = f"/tmp/kafka_data_{int(time.time())}.json"
        with open(temp_file, 'w') as f:
            if isinstance(data, list):
                # Write each item on a separate line
                for item in data:
                    f.write(json.dumps(item) + '\n')
            else:
                # Write a single item
                f.write(json.dumps(data))
        
        # Send to Kafka using kafka-console-producer
        cmd = f"cat {temp_file} | docker exec -i kafka kafka-console-producer --broker-list kafka:9092 --topic {topic}"
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Clean up
        os.remove(temp_file)
        
        if process.returncode != 0:
            print(f"Failed to send data to Kafka: {process.stderr}")
            return False
        
        return True
    
    except Exception as e:
        print(f"Error sending data to Kafka: {str(e)}")
        return False

def process_file(file_path, topic):
    """Process a JSON file and send records to Kafka"""
    print(f"Processing {file_path} to topic {topic}")
    
    try:
        # Load the JSON file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Send to Kafka
        if isinstance(data, list):
            # Send each record individually
            success_count = 0
            for record in data:
                if send_to_kafka(record, topic):
                    success_count += 1
                    
                # Sleep briefly to avoid overwhelming Kafka
                time.sleep(0.01)
            
            print(f"Sent {success_count}/{len(data)} records to topic {topic}")
        else:
            # Send the entire object
            if send_to_kafka(data, topic):
                print(f"Successfully sent data to topic {topic}")
            else:
                print(f"Failed to send data to topic {topic}")
        
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
