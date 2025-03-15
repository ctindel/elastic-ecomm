#!/usr/bin/env python3
"""
Script to generate images for a partition of products.
"""
import os
import sys
import json
import requests
from pathlib import Path
import base64
import time
import random
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def generate_image_for_product(product):
    """
    Generate an image for a product using OpenAI's DALL-E API with true infinite retry.
    """
    # Create directory for images if it doesn't exist
    image_dir = Path("data/images")
    image_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine image filename
    image_filename = f"product_{product['id']}.png"
    image_path = image_dir / image_filename
    
    # Skip if image already exists
    if image_path.exists():
        logger.info(f"Image already exists at {image_path}, skipping")
        return str(image_path)
    
    # Create a detailed prompt for the image
    prompt = f"A professional product photo of a {product['brand']} {product['subcategory']}"
    
    # Add color if available
    if 'attributes' in product and 'color' in product['attributes']:
        prompt += f", {product['attributes']['color']} color"
    
    # Add material if available
    if 'attributes' in product and 'material' in product['attributes']:
        prompt += f", made of {product['attributes']['material']}"
    
    # Add style context
    prompt += f". High-quality e-commerce product image with white background, professional lighting."
    
    logger.info(f"Generating image for: {product['name']}")
    logger.info(f"Prompt: {prompt}")
    
    # Call OpenAI API with true infinite retry logic
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
    }
    
    data = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json"
    }
    
    # Implement exponential backoff with jitter - TRUE INFINITE RETRIES
    attempt = 0
    while True:  # Loop forever until we succeed or explicitly return
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # Extract image data
            image_data = response.json()["data"][0]["b64_json"]
            
            # Save image
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            
            # Only log success for newly generated images
            logger.info(f"Success! Generated new image for {product['name']} and saved to {image_path}")
            return str(image_path)
        
        except requests.RequestException as e:
            # Check if it's a rate limit error (429)
            if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                # Calculate backoff time with exponential increase and jitter
                # Cap at 60 seconds max backoff
                backoff_time = min(30 + (2 ** min(attempt, 10)) + random.uniform(0, 10), 60)
                logger.warning(f"Rate limit hit. Retrying in {backoff_time:.2f} seconds... (Attempt {attempt+1}/∞)")
                time.sleep(backoff_time)
            else:
                # For other request errors, log and retry with a delay
                logger.error(f"Error generating image: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response: {e.response.text}")
                # Wait before retrying
                backoff_time = min(10 + random.uniform(0, 5), 30)
                logger.warning(f"Request error. Retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
                
        except Exception as e:
            # For unexpected errors, log and retry with a delay
            logger.error(f"Unexpected error generating image: {e}")
            # Wait before retrying
            backoff_time = min(10 + random.uniform(0, 5), 30)
            logger.warning(f"Unexpected error. Retrying in {backoff_time:.2f} seconds...")
            time.sleep(backoff_time)
        
        # Increment attempt counter for backoff calculation
        attempt += 1

def generate_images_for_partition(partition_file, partition_num):
    """Generate images for products in a partition."""
    partition_num = int(partition_num) if not isinstance(partition_num, int) else partition_num
    logger.info(f"Processing partition {partition_num} from {partition_file}")
    
    # Load products from partition file
    with open(partition_file, "r") as f:
        products = json.load(f)
    
    if not products:
        logger.error(f"No products found in {partition_file}")
        return False
    
    # Create checkpoint file path
    checkpoint_file = f"/tmp/partition_{partition_num}_checkpoint.json"
    
    # Load checkpoint if exists
    processed_ids = set()
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r") as f:
                checkpoint_data = json.load(f)
                processed_ids = set(checkpoint_data.get("processed_ids", []))
                logger.info(f"Loaded checkpoint with {len(processed_ids)} processed products")
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            # Create an empty checkpoint file to ensure we can write to it
            try:
                with open(checkpoint_file, "w") as f:
                    json.dump({"processed_ids": []}, f)
                logger.info(f"Created new empty checkpoint file at {checkpoint_file}")
            except Exception as e2:
                logger.error(f"Failed to create checkpoint file: {e2}")
    else:
        # Create an empty checkpoint file
        try:
            with open(checkpoint_file, "w") as f:
                json.dump({"processed_ids": []}, f)
            logger.info(f"Created new empty checkpoint file at {checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to create checkpoint file: {e}")
    
    # Also check for existing images in the data/images directory
    image_dir = Path("data/images")
    for product in products:
        image_path = image_dir / f"product_{product['id']}.png"
        if image_path.exists():
            processed_ids.add(product["id"])
    
    # Filter products that haven't been processed yet
    remaining_products = [p for p in products if p["id"] not in processed_ids]
    
    logger.info(f"Generating images for {len(remaining_products)}/{len(products)} remaining products in partition {partition_num}")
    
    # Process products one by one with a small delay between each
    success_count = 0
    for i, product in enumerate(remaining_products):
        logger.info(f"Processing product {i+1}/{len(remaining_products)} in partition {partition_num}: {product['name']}")
        
        # Generate image
        image_path = generate_image_for_product(product)
        
        if image_path:
            # Don't log success here since it's already logged in generate_image_for_product
            success_count += 1
            
            # Update checkpoint - write after each successful image generation
            processed_ids.add(product["id"])
            try:
                with open(checkpoint_file, "w") as f:
                    json.dump({"processed_ids": list(processed_ids)}, f)
                logger.info(f"Updated checkpoint file with {len(processed_ids)} processed products")
            except Exception as e:
                logger.error(f"Error writing checkpoint: {e}")
                logger.error(f"Checkpoint file path: {checkpoint_file}")
                # Try to debug the issue
                try:
                    logger.info(f"Checking /tmp permissions: {os.access('/tmp', os.W_OK)}")
                    logger.info(f"Current working directory: {os.getcwd()}")
                except Exception as e2:
                    logger.error(f"Error checking permissions: {e2}")
        else:
            logger.error(f"Failed to generate image for product: {product['name']}")
        
        # Add a delay between products to avoid rate limits
        delay = 2 + random.uniform(0, 1)
        logger.info(f"Waiting {delay:.2f}s before next product...")
        time.sleep(delay)
    
    total_processed = len(processed_ids)
    logger.info(f"Completed image generation for partition {partition_num}. Generated {success_count}/{len(remaining_products)} images this run.")
    logger.info(f"Total progress: {total_processed}/{len(products)} products processed ({total_processed/len(products)*100:.2f}%)")
    
    # Return True only if all products have been processed
    return total_processed == len(products)

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) < 3:
        logger.error("Usage: python generate_partition_images.py <partition_file> <partition_num>")
        sys.exit(1)
    
    partition_file = sys.argv[1]
    partition_num = sys.argv[2]
    
    # Check if API key is set in environment
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)
    
    try:
        # Generate images for the partition
        success = generate_images_for_partition(partition_file, partition_num)
        
        if success:
            logger.info(f"Successfully generated all images for partition {partition_num}")
            # Exit with non-zero code to indicate we need to keep running
            # This ensures the runner script will restart us to check for any missed images
            sys.exit(1)
        else:
            logger.info(f"Not all images were generated for partition {partition_num}, will continue in next run")
            # Exit with non-zero code to ensure the runner script keeps retrying
            # This ensures we keep trying until ALL images are generated
            sys.exit(1)
    except Exception as e:
        # Catch any unexpected exceptions to prevent the script from crashing
        logger.error(f"Unexpected error in main: {e}")
        # Exit with non-zero code to ensure the runner script keeps retrying
        # This ensures we keep trying until ALL images are generated
        sys.exit(1)
