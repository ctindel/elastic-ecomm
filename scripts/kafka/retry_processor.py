#!/usr/bin/env python3
"""
Retry processor for failed ingestion tasks
This script processes messages from the failed-ingestion topic and retries them
"""
import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import (
    KAFKA_HOST,
    KAFKA_TOPIC_FAILED_INGESTION,
    KAFKA_TOPIC_PRODUCTS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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
            logger.error(f"Failed to send data to Kafka: {process.stderr}")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error sending data to Kafka: {str(e)}")
        return False

def calculate_backoff(retry_count):
    """
    Calculate exponential backoff time in seconds.
    
    Args:
        retry_count: Current retry count
    
    Returns:
        int: Backoff time in seconds
    """
    # Exponential backoff with jitter
    # Base: 5 seconds, max: 5 minutes
    base_seconds = 5
    max_seconds = 300
    
    # Calculate exponential backoff
    backoff = min(base_seconds * (2 ** (retry_count - 1)), max_seconds)
    
    # Add some jitter (±20%)
    jitter = backoff * 0.2
    backoff = backoff + (jitter * (2 * (time.time() % 1) - 1))
    
    return max(1, int(backoff))

def should_retry_now(record):
    """
    Check if a record should be retried now based on its timestamp and retry count.
    
    Args:
        record: Record with retry information
    
    Returns:
        bool: True if the record should be retried now, False otherwise
    """
    # Get retry count and timestamp
    retry_count = record.get('retry_count', 1)
    timestamp = record.get('timestamp', 0)
    
    # Calculate backoff time
    backoff = calculate_backoff(retry_count)
    
    # Check if enough time has passed
    current_time = time.time()
    return current_time - timestamp >= backoff

def process_failed_ingestion(record):
    """
    Process a failed ingestion record.
    
    Args:
        record: Failed ingestion record
    
    Returns:
        bool: True if the record was processed successfully, False otherwise
    """
    try:
        # Check if the record should be retried now
        if not should_retry_now(record):
            logger.info(f"Skipping record {record.get('id', 'unknown')} - not ready for retry yet")
            return False
        
        # Get original topic
        original_topic = record.get('original_topic', KAFKA_TOPIC_PRODUCTS)
        
        # Remove retry information
        if 'retry_count' in record:
            del record['retry_count']
        if 'last_error' in record:
            del record['last_error']
        if 'timestamp' in record:
            del record['timestamp']
        if 'original_topic' in record:
            del record['original_topic']
        
        # Send back to original topic
        logger.info(f"Retrying record {record.get('id', 'unknown')} on topic {original_topic}")
        return send_to_kafka(record, original_topic)
    
    except Exception as e:
        logger.error(f"Error processing failed ingestion: {str(e)}")
        return False

def consume_from_kafka(topic, max_messages=None):
    """
    Consume messages from Kafka topic using subprocess.
    
    Args:
        topic: Kafka topic to consume from
        max_messages: Maximum number of messages to consume (None for unlimited)
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
        
        # Run the consumer in the background
        process = subprocess.Popen(cmd, shell=True)
        
        logger.info(f"Started Kafka consumer for topic {topic}")
        
        # Wait for some data to be available
        time.sleep(2)
        
        # Process messages as they arrive
        message_count = 0
        processed_count = 0
        
        while True:
            # Check if process is still running
            if process.poll() is not None:
                logger.info(f"Kafka consumer process exited with code {process.returncode}")
                break
            
            # Read new messages from the file
            with open(temp_file, 'r') as f:
                lines = f.readlines()
            
            # Process new messages
            for line in lines[message_count:]:
                message_count += 1
                
                # Skip empty lines
                if not line.strip():
                    continue
                
                try:
                    # Parse the message
                    record = json.loads(line.strip())
                    
                    # Process the record
                    if process_failed_ingestion(record):
                        processed_count += 1
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse message: {line.strip()}")
            
            # Sleep briefly before checking for new messages
            time.sleep(1)
        
        # Clean up
        os.remove(temp_file)
        
        logger.info(f"Processed {processed_count} of {message_count} messages from topic {topic}")
    
    except Exception as e:
        logger.error(f"Error consuming from Kafka: {str(e)}")

def main():
    """Main function to process failed ingestions."""
    logger.info("Starting retry processor")
    
    # Consume from failed-ingestion topic
    consume_from_kafka(KAFKA_TOPIC_FAILED_INGESTION)
    
    logger.info("Retry processor completed")

if __name__ == "__main__":
    main()
