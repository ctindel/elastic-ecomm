#!/bin/bash

# Create a simple pipeline for products
curl -X PUT "http://localhost:9200/_ingest/pipeline/product-simple-pipeline" -H "Content-Type: application/json" -d'
{
  "description": "Simple pipeline for products",
  "processors": [
    {
      "set": {
        "field": "processed_by_pipeline",
        "value": true
      }
    }
  ]
}
'

echo "Created simple product pipeline"
