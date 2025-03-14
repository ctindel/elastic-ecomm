#!/bin/bash

# Create the vectorization pipeline for products
curl -X PUT "http://localhost:9200/_ingest/pipeline/product-vectorization" -H "Content-Type: application/json" -d@- << "EOJSON"
{
  "description": "Pipeline to mark products for vectorization",
  "processors": [
    {
      "set": {
        "field": "text_for_vectorization",
        "value": "{{#name}}{{name}}{{/name}} - {{#description}}{{description}}{{/description}} {{#category}}Category: {{category}}{{/category}} {{#brand}}Brand: {{brand}}{{/brand}}"
      }
    },
    {
      "set": {
        "field": "vectorize",
        "value": true
      }
    }
  ]
}
EOJSON

echo "Created product vectorization pipeline"

# Create the vectorization pipeline for product images
curl -X PUT "http://localhost:9200/_ingest/pipeline/product-image-vectorization" -H "Content-Type: application/json" -d@- << "EOJSON"
{
  "description": "Pipeline to mark product images for vectorization",
  "processors": [
    {
      "set": {
        "field": "vectorize",
        "value": true
      }
    }
  ]
}
EOJSON

echo "Created product image vectorization pipeline"
