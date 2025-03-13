#!/usr/bin/env python3
"""
Simple Kafka consumer for e-commerce data
"""
import os
import json
import time
import argparse
import subprocess
from pathlib import Path
import sys

def consume_from_kafka(topic, max_messages=None, output_file=None):
    """Consume messages from Kafka topic using subprocess"""
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
