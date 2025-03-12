#!/usr/bin/env python3
"""
Simple Kafka consumer for e-commerce data using subprocess to call kafka-console-consumer
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
    KAFKA_TOPIC_PRODUCT_IMAGES,
    KAFKA_TOPIC_FAILED_INGESTION
)

def consume_from_kafka(topic, max_messages=None, output_file=None):
    """
    Consume messages from Kafka topic using subprocess.
    
    Args:
        topic: Kafka topic to consume from
        max_messages: Maximum number of messages to consume (None for unlimited)
        output_file: File to write messages to (None for stdout)
    """
    try:
        # Create a temporary file for the consumer output
        temp_file = f"/tmp/kafka_consumer_{int(time.time())}.out"
        
        # Start Kafka consumer
        cmd = f"docker exec -i kafka kafka-console-consumer --bootstrap-server kafka:9092 --topic {topic} --from-beginning"
        
        if max_messages:
            cmd += f" --max-messages {max_messages}"
        
        # Redirect output to temporary file
        cmd += f" > {temp_file}"
        
        # Run the consumer
        print(f"Starting consumer for topic {topic}...")
        process = subprocess.run(cmd, shell=True)
        
        if process.returncode != 0:
            print(f"Error consuming from topic {topic}")
            return
        
        # Read the output
        with open(temp_file, 'r') as f:
            lines = f.readlines()
        
        # Process the output
        if output_file:
            # Write to output file
            with open(output_file, 'w') as f:
                for line in lines:
                    f.write(line)
            print(f"Wrote {len(lines)} messages to {output_file}")
        else:
            # Print to stdout
            for line in lines:
                try:
                    # Try to parse as JSON for pretty printing
                    data = json.loads(line.strip())
                    print(json.dumps(data, indent=2))
                except json.JSONDecodeError:
                    # Print raw line if not valid JSON
                    print(line.strip())
        
        # Clean up
        os.remove(temp_file)
        
        print(f"Consumed {len(lines)} messages from topic {topic}")
    
    except Exception as e:
        print(f"Error consuming from Kafka: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Consume e-commerce data from Kafka')
    parser.add_argument('--topic', required=True, help='Kafka topic to consume from')
    parser.add_argument('--max-messages', type=int, help='Maximum number of messages to consume')
    parser.add_argument('--output-file', help='File to write messages to')
    args = parser.parse_args()
    
    # Consume from the topic
    consume_from_kafka(args.topic, args.max_messages, args.output_file)

if __name__ == "__main__":
    main()
