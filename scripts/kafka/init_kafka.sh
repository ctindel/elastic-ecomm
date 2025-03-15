#!/bin/bash
# Kafka initialization script for E-Commerce Search Demo
# This script creates the necessary Kafka topics for the ingestion pipeline

# Set up error handling
set -e
trap 'echo "Error: Command failed at line $LINENO"' ERR

# Define variables
KAFKA_HOST="localhost:9092"
KAFKA_PARTITIONS=3
RETENTION_MS=604800000  # Standardized retention period for all topics

# List of Kafka topics
KAFKA_TOPICS=("products" "product-images" "products-retry" "product-images-retry" "dead-letter-queue")

# Check if Kafka is running
echo "Checking if Kafka is running..."
IFS=':' read -r KAFKA_IP KAFKA_PORT <<< "$KAFKA_HOST"
kafka_test=$(echo "test" | nc -w 5 $KAFKA_IP $KAFKA_PORT > /dev/null 2>&1; echo $?)
if [ $kafka_test -ne 0 ]; then
  echo "Error: Kafka is not running or not reachable at $KAFKA_HOST. Please ensure it is started and accessible."
  exit 1
fi

# Create topics with appropriate configurations
echo "Creating Kafka topics..."
for topic in "${KAFKA_TOPICS[@]}"; do
  partitions=$KAFKA_PARTITIONS
  if [ "$topic" == "dead-letter-queue" ]; then
    partitions=1
  fi
  docker exec -i kafka kafka-topics --create --bootstrap-server kafka:9092 \
    --topic $topic \
    --partitions $partitions \
    --replication-factor 1 \
    --config retention.ms=$RETENTION_MS \
    --config cleanup.policy=delete \
    --if-not-exists
done

# List created topics
echo "Listing created topics:"
docker exec -i kafka kafka-topics --list --bootstrap-server $KAFKA_HOST

# Describe topics to verify configurations
echo "Verifying topic configurations:"
for topic in "${KAFKA_TOPICS[@]}"; do
  echo "Topic: $topic"
  docker exec -i kafka kafka-topics --describe --bootstrap-server $KAFKA_HOST --topic $topic
done

echo "Kafka initialization completed successfully!"
