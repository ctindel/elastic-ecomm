#!/bin/bash
# Kafka initialization script for E-Commerce Search Demo
# This script creates the required Kafka topics for the application

# Wait for Kafka to be available
echo "Waiting for Kafka to be available..."
max_retries=30
retry_count=0

while ! docker exec -i kafka kafka-topics --list --bootstrap-server kafka:9092 &> /dev/null
do
  retry_count=$((retry_count+1))
  if [ $retry_count -ge $max_retries ]; then
    echo "Error: Kafka is not available after $max_retries attempts. Exiting."
    exit 1
  fi
  
  echo "Kafka is unavailable - sleeping (attempt $retry_count/$max_retries)"
  sleep 5
done

echo "Kafka is up - creating topics"

# Create topics with appropriate partitions and replication factor
echo "Creating Kafka topics..."

# Products topic
docker exec -i kafka kafka-topics --create --topic products \
  --partitions 10 --replication-factor 1 --if-not-exists \
  --bootstrap-server kafka:9092 \
  --config retention.ms=604800000 \
  --config cleanup.policy=delete

# Product images topic
docker exec -i kafka kafka-topics --create --topic product-images \
  --partitions 10 --replication-factor 1 --if-not-exists \
  --bootstrap-server kafka:9092 \
  --config retention.ms=604800000 \
  --config cleanup.policy=delete

# Failed ingestion topic
docker exec -i kafka kafka-topics --create --topic failed-ingestion \
  --partitions 10 --replication-factor 1 --if-not-exists \
  --bootstrap-server kafka:9092 \
  --config retention.ms=604800000 \
  --config cleanup.policy=delete

# Verify topics were created
echo "Verifying Kafka topics..."
docker exec -i kafka kafka-topics --list --bootstrap-server kafka:9092

echo "Kafka initialization completed successfully"
