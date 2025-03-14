#!/usr/bin/env python3
"""
Retry processor for failed Kafka ingestion messages

This script processes messages from retry topics, implementing exponential backoff
and limiting retry attempts.
"""
import os
import sys
import json
import time
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.kafka.circuit_breaker_manager import CircuitBreakerManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("retry-processor")

# Constants
MAX_RETRIES = 5
RETRY_TOPICS = ["products-retry", "product-images-retry"]
ORIGINAL_TOPICS = {
    "products-retry": "products",
    "product-images-retry": "product-images"
}

# Initialize circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()
kafka_circuit_breaker = circuit_breaker_manager.get_circuit_breaker("kafka")

def calculate_backoff(retry_count):
    """Calculate exponential backoff time in seconds"""
    # Base delay is 5 seconds, doubles with each retry
    # 5s, 10s, 20s, 40s, 80s
    base_delay = 5
    max_delay = 300  # 5 minutes max
    
    delay = min(base_delay * (2 ** retry_count), max_delay)
    
    # Add some jitter (±20%)
    jitter = delay * 0.2
    delay = delay - jitter + (jitter * 2 * (time.time() % 1))
    
    return delay

def send_to_topic(record, topic):
    """Send a record to a Kafka topic"""
    # Check if request is allowed by circuit breaker
    if not kafka_circuit_breaker.allow_request():
        logger.warning("Kafka circuit breaker is open, skipping send")
        return False
    
    try:
        # Create a temporary file for the record
        temp_file = f"/tmp/retry_record_{int(time.time())}.json"
        with open(temp_file, "w") as f:
            f.write(json.dumps(record) + "\n")
        
        # Send to Kafka using kafka-console-producer
        cmd = f"cat {temp_file} | docker exec -i kafka kafka-console-producer --broker-list localhost:9092 --topic {topic}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error sending to topic {topic}: {result.stderr}")
            kafka_circuit_breaker.record_failure()
            return False
        else:
            logger.info(f"Successfully sent record to topic {topic}")
            kafka_circuit_breaker.record_success()
            return True
    except Exception as e:
        logger.error(f"Error sending to topic {topic}: {e}")
        kafka_circuit_breaker.record_failure()
        return False
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)

def process_retry_message(message, topic):
    """Process a retry message"""
    try:
        # Parse the message
        record = json.loads(message)
        
        # Get retry information
        retry_info = record.get("_retry", {})
        retry_count = retry_info.get("count", 1)
        original_topic = retry_info.get("original_topic", ORIGINAL_TOPICS.get(topic))
        last_error = retry_info.get("error", "Unknown error")
        timestamp = retry_info.get("timestamp")
        
        # Skip if no original topic
        if not original_topic:
            logger.error(f"No original topic found for retry message: {message[:100]}...")
            return False
        
        # Check if max retries exceeded
        if retry_count >= MAX_RETRIES:
            logger.warning(f"Max retries exceeded for record, dropping: {message[:100]}...")
            return True  # Consider it processed
        
        # Calculate backoff time
        backoff = calculate_backoff(retry_count)
        
        # Check if enough time has passed since the last attempt
        if timestamp:
            try:
                last_attempt = datetime.fromisoformat(timestamp)
                now = datetime.now()
                elapsed = (now - last_attempt).total_seconds()
                
                if elapsed < backoff:
                    # Not enough time has passed, skip for now
                    logger.info(f"Skipping retry, not enough time elapsed: {elapsed:.1f}s < {backoff:.1f}s")
                    return False  # Not processed, will be retried later
            except Exception as e:
                logger.error(f"Error parsing timestamp: {e}")
        
        # Remove retry info before sending back to original topic
        if "_retry" in record:
            del record["_retry"]
        
        # Send back to original topic
        logger.info(f"Retrying record (attempt {retry_count}) after {backoff:.1f}s backoff")
        return send_to_topic(record, original_topic)
        
    except Exception as e:
        logger.error(f"Error processing retry message: {e}")
        return False

def consume_from_retry_topic(topic, batch_size=10, max_messages=None):
    """Consume messages from a retry topic"""
    logger.info(f"Starting retry consumer for topic {topic}")
    
    # Use kafka-console-consumer to get messages
    cmd = f"docker exec -i kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic {topic} --from-beginning"
    
    if max_messages:
        cmd += f" --max-messages {max_messages}"
    
    try:
        # Start the consumer process
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Process messages
        message_count = 0
        batch_count = 0
        success_count = 0
        failure_count = 0
        
        while True:
            line = process.stdout.readline()
            
            if not line and process.poll() is not None:
                break
            
            if line:
                line = line.strip()
                if line:
                    message_count += 1
                    
                    # Process the message
                    success = process_retry_message(line, topic)
                    
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                    
                    # Log progress
                    if message_count % batch_size == 0:
                        batch_count += 1
                        logger.info(f"Processed batch {batch_count} ({message_count} messages total, {success_count} successful, {failure_count} failed)")
                    
                    # Check if we've reached max_messages
                    if max_messages and message_count >= max_messages:
                        logger.info(f"Reached max messages limit ({max_messages})")
                        break
        
        # Log final stats
        logger.info(f"Completed processing {message_count} messages from topic {topic}")
        logger.info(f"Success: {success_count}, Failures: {failure_count}")
        
        return message_count, success_count, failure_count
    
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
        return message_count, success_count, failure_count
    except Exception as e:
        logger.error(f"Error consuming from topic {topic}: {e}")
        return 0, 0, 0

def run_retry_processor(interval=60, max_runtime=None):
    """Run the retry processor continuously"""
    logger.info(f"Starting retry processor with {interval}s interval")
    
    start_time = time.time()
    iteration = 0
    
    try:
        while True:
            iteration += 1
            logger.info(f"Starting retry processing iteration {iteration}")
            
            # Process each retry topic
            for topic in RETRY_TOPICS:
                try:
                    message_count, success_count, failure_count = consume_from_retry_topic(topic)
                    logger.info(f"Topic {topic}: {message_count} messages, {success_count} successful, {failure_count} failed")
                except Exception as e:
                    logger.error(f"Error processing retry topic {topic}: {e}")
            
            # Check if we've reached max runtime
            if max_runtime and (time.time() - start_time) >= max_runtime:
                logger.info(f"Reached max runtime of {max_runtime}s, exiting")
                break
            
            # Sleep until next iteration
            logger.info(f"Sleeping for {interval}s until next retry processing iteration")
            time.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("Retry processor interrupted by user")
    except Exception as e:
        logger.error(f"Error in retry processor: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process retry messages for failed Kafka ingestions")
    parser.add_argument("--topic", choices=RETRY_TOPICS + ["all"], default="all", help="Retry topic to process")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for logging progress")
    parser.add_argument("--max-messages", type=int, help="Maximum number of messages to consume")
    parser.add_argument("--interval", type=int, default=60, help="Interval in seconds between retry processing runs")
    parser.add_argument("--max-runtime", type=int, help="Maximum runtime in seconds")
    parser.add_argument("--daemon", action="store_true", help="Run as a daemon process")
    args = parser.parse_args()
    
    if args.daemon:
        # Run continuously
        run_retry_processor(args.interval, args.max_runtime)
    else:
        # Process once
        if args.topic == "all":
            for topic in RETRY_TOPICS:
                consume_from_retry_topic(topic, args.batch_size, args.max_messages)
        else:
            consume_from_retry_topic(args.topic, args.batch_size, args.max_messages)
    
    logger.info("Retry processor completed successfully!")

if __name__ == "__main__":
    main()
