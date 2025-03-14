#!/bin/bash
# Kafka initialization script for E-Commerce Search Demo
# This script creates the necessary Kafka topics for the ingestion pipeline

# Set up error handling
set -e
trap 'echo "Error: Command failed at line $LINENO"' ERR

# Check if Kafka is running
echo "Checking if Kafka is running..."
docker exec -i kafka bash -c "ls" > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Error: Kafka container is not running. Please start it with docker-compose up -d"
  exit 1
fi

# Create topics with appropriate configurations
echo "Creating Kafka topics..."

# Products topic - for product data
docker exec -i kafka kafka-topics --create --bootstrap-server localhost:9092 \
  --topic products \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --config cleanup.policy=delete \
  --if-not-exists

# Product images topic - for product image data
docker exec -i kafka kafka-topics --create --bootstrap-server localhost:9092 \
  --topic product-images \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --config cleanup.policy=delete \
  --if-not-exists

# Retry topics - for failed ingestion attempts
docker exec -i kafka kafka-topics --create --bootstrap-server localhost:9092 \
  --topic products-retry \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=1209600000 \
  --config cleanup.policy=delete \
  --if-not-exists

docker exec -i kafka kafka-topics --create --bootstrap-server localhost:9092 \
  --topic product-images-retry \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=1209600000 \
  --config cleanup.policy=delete \
  --if-not-exists

# Dead letter queue - for messages that failed after max retries
docker exec -i kafka kafka-topics --create --bootstrap-server localhost:9092 \
  --topic dead-letter-queue \
  --partitions 1 \
  --replication-factor 1 \
  --config retention.ms=2592000000 \
  --config cleanup.policy=delete \
  --if-not-exists

# List created topics
echo "Listing created topics:"
docker exec -i kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe topics to verify configurations
echo "Verifying topic configurations:"
for topic in products product-images products-retry product-images-retry dead-letter-queue; do
  echo "Topic: $topic"
  docker exec -i kafka kafka-topics --describe --bootstrap-server localhost:9092 --topic $topic
done

echo "Kafka initialization completed successfully!"
