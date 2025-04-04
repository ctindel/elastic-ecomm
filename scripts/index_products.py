#!/usr/bin/env python3
"""
Script to index products into Elasticsearch.
"""
import json
import sys
from elasticsearch import Elasticsearch
from pathlib import Path

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Check if Elasticsearch is running
if not es.ping():
    print("Error: Could not connect to Elasticsearch")
    sys.exit(1)

# Load products from JSON file
products_file = Path("data/products.json")
if not products_file.exists():
    print(f"Error: Products file not found at {products_file}")
    sys.exit(1)

with open(products_file, "r") as f:
    products = json.load(f)

print(f"Loaded {len(products)} products from {products_file}")

# Index products in bulk
bulk_data = []
for product in products:
    # Add index action
    bulk_data.append({"index": {"_index": "products", "_id": product["id"]}})
    # Add product data
    bulk_data.append(product)
    
    # Process in batches of 1000
    if len(bulk_data) >= 2000:
        print(f"Indexing batch of {len(bulk_data)//2} products...")
        es.bulk(index="products", operations=bulk_data, refresh=True)
        bulk_data = []

# Index any remaining products
if bulk_data:
    print(f"Indexing final batch of {len(bulk_data)//2} products...")
    es.bulk(index="products", operations=bulk_data, refresh=True)

# Verify index count
count = es.count(index="products")
print(f"Successfully indexed {count['count']} products")
