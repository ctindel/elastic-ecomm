#!/usr/bin/env python3
"""
Script to generate images for products in a partition file using OpenAI's DALL-E API.
Features true infinite retry logic with exponential backoff.
"""
import os
import sys
import json
import time
import random
import logging
from pathlib import Path
import requests
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 10
BASE_DELAY = 1
MAX_DELAY = 60
IMAGE_DIR = Path("/home/ubuntu/elastic-ecomm/data/images")
IMAGE_DIR.mkdir(exist_ok=True, parents=True)

def load_products(partition_file):
    """Load products from a partition file."""
    try:
        with open(partition_file, 'r') as f:
            products = json.load(f)
        logger.info(f"Loaded {len(products)} products from {partition_file}")
        return products
    except Exception as e:
        logger.error(f"Error loading products from {partition_file}: {e}")
        return []

def load_checkpoint(partition_num):
    """Load checkpoint of processed product IDs."""
    checkpoint_file = f"/tmp/partition_{partition_num}_checkpoint.json"
    try:
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            logger.info(f"Loaded checkpoint with {len(checkpoint.get('processed_ids', []))} processed products")
            return checkpoint
        else:
            logger.info(f"No checkpoint file found at {checkpoint_file}, creating new checkpoint")
            return {"processed_ids": []}
    except Exception as e:
        logger.error(f"Error loading checkpoint: {e}")
        return {"processed_ids": []}

def save_checkpoint(partition_num, processed_ids):
    """Save checkpoint of processed product IDs."""
    checkpoint_file = f"/tmp/partition_{partition_num}_checkpoint.json"
    try:
        with open(checkpoint_file, 'w') as f:
            json.dump({"processed_ids": processed_ids}, f)
        logger.info(f"Saved checkpoint with {len(processed_ids)} processed products")
    except Exception as e:
        logger.error(f"Error saving checkpoint: {e}")

def image_exists(product_id):
    """Check if image already exists for product."""
    image_path = IMAGE_DIR / f"product_{product_id}.png"
    return image_path.exists()

def calculate_backoff(retry_count):
    """Calculate exponential backoff with jitter."""
    delay = min(MAX_DELAY, BASE_DELAY * (2 ** retry_count))
    jitter = random.uniform(0, 0.1 * delay)
    return delay + jitter

def generate_image_for_product(product, client):
    """Generate image for a product with exponential backoff retry."""
    product_id = product['id']
    filename = f"product_{product_id}.png"
    image_path = IMAGE_DIR / filename
    
    # Skip if image already exists
    if image_path.exists():
        logger.info(f"Image already exists: {filename} for product ID: {product_id} - skipping")
        return True
    
    # Prepare prompt for image generation
    name = product.get('name', '')
    description = product.get('description', '')
    category = product.get('category', '')
    subcategory = product.get('subcategory', '')
    
    prompt = f"A professional product photo of {name}. {description}. Category: {category}, Subcategory: {subcategory}."
    
    # Attempt to generate image with exponential backoff
    retry_count = 0
    while True:
        try:
            logger.info(f"Attempting to generate image: {filename} for product ID: {product_id}")
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            
            # Download the image
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                with open(image_path, 'wb') as f:
                    f.write(image_response.content)
                logger.info(f"Successfully generated image: {filename} for product ID: {product_id}")
                return True
            else:
                logger.error(f"Error generating image: {filename} for product ID: {product_id} - HTTP error: {image_response.status_code}")
        
        except Exception as e:
            if "rate limit" in str(e).lower():
                logger.error(f"Error generating image: {filename} for product ID: {product_id} - Rate limit error: {e}")
            else:
                logger.error(f"Error generating image: {filename} for product ID: {product_id} - Exception: {e}")
            
            delay = calculate_backoff(retry_count)
            logger.info(f"Backing off for {delay:.2f} seconds before retrying image: {filename} for product ID: {product_id}")
            time.sleep(delay)
            retry_count = min(retry_count + 1, 10)  # Cap retry count for backoff calculation
            continue

def generate_images_for_partition(partition_file, partition_num):
    """Generate images for all products in a partition with true infinite retry."""
    # Load products and checkpoint
    products = load_products(partition_file)
    checkpoint = load_checkpoint(partition_num)
    processed_ids = set(checkpoint.get("processed_ids", []))
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return False
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Count products with and without images
    products_with_images = sum(1 for p in products if image_exists(p['id']))
    products_without_images = len(products) - products_with_images
    
    logger.info(f"Partition {partition_num}: {len(products)} total products, {products_with_images} with images, {products_without_images} without images")
    
    # Process each product
    for product in products:
        product_id = product['id']
        
        # Skip if already processed in this run
        if product_id in processed_ids:
            continue
        
        # Generate image for product (this will retry indefinitely until success)
        success = generate_image_for_product(product, client)
        
        if success:
            # Add to processed IDs and save checkpoint
            processed_ids.add(product_id)
            save_checkpoint(partition_num, list(processed_ids))
    
    # Check if all products have images
    missing_images = [p['id'] for p in products if not image_exists(p['id'])]
    
    if missing_images:
        logger.warning(f"Partition {partition_num}: {len(missing_images)} products still missing images: {missing_images[:5]}...")
        return False
    else:
        logger.info(f"Partition {partition_num}: All {len(products)} products have images")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        logger.error("Usage: python generate_partition_images.py <partition_file> <partition_num>")
        sys.exit(1)
    
    partition_file = sys.argv[1]
    partition_num = sys.argv[2]
    
    logger.info(f"Starting image generation for partition {partition_num} using {partition_file}")
    
    # Generate images with true infinite retry
    success = generate_images_for_partition(partition_file, partition_num)
    
    # Always exit with non-zero status if any images are missing
    # This ensures the wrapper script will continue retrying
    if not success:
        logger.warning(f"Partition {partition_num}: Not all products have images, exiting with status 1")
        sys.exit(1)
    else:
        logger.info(f"Partition {partition_num}: All products have images, exiting with status 0")
        sys.exit(0)
