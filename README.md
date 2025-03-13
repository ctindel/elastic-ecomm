# E-Commerce Search Demo - Kafka Ingestion Pipeline

This PR implements a Kafka-based ingestion pipeline for products and product images. It includes:

1. Circuit breaker pattern to prevent Ollama overload
2. Simple Kafka consumer implementation
3. Elasticsearch vectorization pipeline
4. Direct producer for efficient data ingestion
5. Test scripts for end-to-end validation

The implementation follows the structure of the elastic-courts repository and provides robust error handling and retry mechanisms.

## Image Generation Status
- Progress: 69% (69/100)
- Successful Images: 54
- Failed Images: 15
- Total Images: 61
- Average Size: 1.26 MB

## Next Steps
1. Complete image generation for all products
2. Upload images to S3 when bucket details are provided
3. Update product catalog with S3 image URLs
