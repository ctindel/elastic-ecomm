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

def generate_image_for_product(product, max_retries=10, partition_num=0):
    """
    Generate an image for a product using OpenAI's DALL-E API.
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
    
    # Call OpenAI API with retry logic
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
    
    # Implement exponential backoff with jitter
    for attempt in range(max_retries):
        try:
            # Add a longer initial delay based on partition number to stagger requests
            initial_delay = partition_num * 5  # 5 seconds per partition
            if attempt == 0 and initial_delay > 0:
                logger.info(f"Initial delay of {initial_delay}s for partition {partition_num}")
                time.sleep(initial_delay)
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # Extract image data
            image_data = response.json()["data"][0]["b64_json"]
            
            # Save image
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            
            logger.info(f"Image saved to {image_path}")
            return str(image_path)
        
        except requests.RequestException as e:
            # Check if it's a rate limit error (429)
            if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                # Calculate backoff time with exponential increase and jitter
                backoff_time = min(30 + (2 ** attempt) + random.uniform(0, 10), 120)
                logger.warning(f"Rate limit hit. Retrying in {backoff_time:.2f} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(backoff_time)
                
                # If this is the last attempt, log and return None
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached for rate limiting. Failed to generate image for: {product['name']}")
                    return None
            else:
                # For other request errors, log and return None
                logger.error(f"Error generating image: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response: {e.response.text}")
                # Add a delay even for non-rate-limit errors
                time.sleep(10 + random.uniform(0, 5))
                if attempt == max_retries - 1:
                    return None
                
        except Exception as e:
            logger.error(f"Unexpected error generating image: {e}")
            time.sleep(10 + random.uniform(0, 5))
            if attempt == max_retries - 1:
                return None
    
    return None

def generate_images_for_partition(partition_file, partition_num):
    """Generate images for products in a partition."""
    partition_num = int(partition_num)
    logger.info(f"Processing partition {partition_num} from {partition_file}")
    
    # Load products from partition file
    with open(partition_file, "r") as f:
        products = json.load(f)
    
    if not products:
        logger.error(f"No products found in {partition_file}")
        return False
    
    logger.info(f"Generating images for {len(products)} products in partition {partition_num}")
    
    # Process products one by one with a small delay between each
    success_count = 0
    for i, product in enumerate(products):
        logger.info(f"Processing product {i+1}/{len(products)} in partition {partition_num}: {product['name']}")
        
        # Generate image
        image_path = generate_image_for_product(product, partition_num=partition_num)
        
        if image_path:
            logger.info(f"Success! Image saved to {image_path}")
            success_count += 1
        else:
            logger.error(f"Failed to generate image for product: {product['name']}")
        
        # Add a longer delay between products to avoid rate limits
        # Vary delay based on partition number to stagger requests
        delay = 5 + (partition_num % 3) * 2 + random.uniform(0, 3)
        logger.info(f"Waiting {delay:.2f}s before next product...")
        time.sleep(delay)
    
    logger.info(f"Completed image generation for partition {partition_num}. Generated {success_count}/{len(products)} images.")
    return True

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
    
    # Generate images for the partition
    success = generate_images_for_partition(partition_file, partition_num)
    
    if success:
        logger.info(f"Successfully generated images for partition {partition_num}")
        sys.exit(0)
    else:
        logger.error(f"Failed to generate images for partition {partition_num}")
        sys.exit(1)
