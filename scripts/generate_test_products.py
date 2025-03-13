#!/usr/bin/env python3
"""
Generate test products for Elasticsearch ingestion
"""
import os
import sys
import json
import random
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.config.settings import TEXT_EMBEDDING_DIMS, IMAGE_EMBEDDING_DIMS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def generate_test_products(num_products=100, output_file=None):
    """Generate test products for Elasticsearch ingestion"""
    # Create data directory
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Create images directory
    images_dir = os.path.join(data_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # Set default output file
    if output_file is None:
        output_file = os.path.join(data_dir, "test_products.json")
    
    # Generate products
    products = []
    categories = ["Electronics", "Clothing", "Home", "Books", "Toys"]
    brands = ["Brand A", "Brand B", "Brand C", "Brand D", "Brand E"]
    
    for i in range(num_products):
        product = {
            "id": f"PROD-{i+1:05d}",
            "name": f"Test Product {i+1}",
            "description": f"This is a test product {i+1} for Elasticsearch ingestion",
            "category": random.choice(categories),
            "price": round(random.uniform(10, 1000), 2),
            "brand": random.choice(brands),
            "rating": round(random.uniform(1, 5), 1),
            "review_count": random.randint(0, 1000),
            "stock_status": random.choice(["In Stock", "Low Stock", "Out of Stock"]),
            "attributes": {
                "color": random.choice(["Red", "Blue", "Green", "Black", "White"]),
                "weight": f"{round(random.uniform(0.1, 10), 1)} kg",
                "size": random.choice(["Small", "Medium", "Large", "XL"])
            },
            "image": {
                "url": f"data/images/product_{i+1}.jpg",
                "alt_text": f"Image of Test Product {i+1}"
            }
        }
        products.append(product)
    
    # Write to file
    with open(output_file, "w") as f:
        json.dump(products, f, indent=2)
    
    logger.info(f"Generated {num_products} test products in {output_file}")
    return output_file

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test products for Elasticsearch ingestion")
    parser.add_argument("--num-products", type=int, default=100, help="Number of products to generate")
    parser.add_argument("--output-file", help="Output file path")
    
    args = parser.parse_args()
    
    generate_test_products(args.num_products, args.output_file)
