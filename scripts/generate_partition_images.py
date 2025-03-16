#!/usr/bin/env python3
"""
Generate product images for a specific partition of products.
"""
import os
import sys
import json
import time
import random
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'/tmp/image_generation_partition_{os.getenv("PARTITION_NUM", "unknown")}.log')
    ]
)
logger = logging.getLogger()

# Import OpenAI
try:
    from openai import OpenAI
except ImportError:
    logger.error("OpenAI package not installed. Install with: pip install openai")
    sys.exit(1)

def setup_openai_client():
    """
    Set up the OpenAI client with API key from environment.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)
    
    return OpenAI(api_key=api_key)

def generate_product_image(client, product, output_dir, checkpoint_file):
    """
    Generate an image for a product using OpenAI's DALL-E API.
    
    Args:
        client: OpenAI client
        product: Product data dictionary
        output_dir: Directory to save the image
        checkpoint_file: Path to checkpoint file for tracking progress
    
    Returns:
        bool: True if successful, False otherwise
    """
    product_id = product.get("id")
    product_name = product.get("product_name", "")
    product_description = product.get("product_description", "")
    
    # Extract product attributes for better image generation
    attributes = []
    if "color" in product:
        attributes.append(f"{product['color']} color")
    if "material" in product:
        attributes.append(f"made of {product['material']}")
    
    # Define the output file path - always use the root data/images directory
    root_output_file = "/home/ubuntu/elastic-ecomm/data/images/product_{}.png".format(product_id)
    
    # Check if the image already exists in the root data/images directory
    if os.path.exists(root_output_file):
        logger.info(f"Image already exists at {root_output_file}, skipping generation")
        return True
    
    # Generate a prompt for the image
    prompt = f"A professional product photo of a {product_name}"
    if attributes:
        prompt += f", {', '.join(attributes)}"
    prompt += ". High-quality e-commerce product image with white background, professional lighting."
    
    logger.info(f"Prompt: {prompt}")
    
    # Use exponential backoff for retries
    max_retries = 10
    base_delay = 1  # Start with 1 second delay
    max_delay = 60  # Maximum delay of 60 seconds
    
    for attempt in range(max_retries):
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Get the image URL
            image_url = response.data[0].url
            
            # Download the image
            import requests
            response = requests.get(image_url)
            response.raise_for_status()
            
            # Save the image to the root data/images directory
            with open(root_output_file, "wb") as f:
                f.write(response.content)
                
            logger.info(f"Success! Image saved to {root_output_file}")
            
            # Update the checkpoint file
            with open(checkpoint_file, "w") as f:
                checkpoint_data = {
                    "last_processed_index": product.get("partition_index", 0),
                    "timestamp": datetime.now().isoformat(),
                    "product_id": product_id
                }
                json.dump(checkpoint_data, f)
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            
            # Calculate delay with exponential backoff and jitter
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
            
            # If we're rate limited, use a longer delay
            if "429" in str(e):
                delay = max(delay, 10)  # At least 10 seconds for rate limits
            
            logger.warning(f"Request error. Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
    
    logger.error(f"Failed to generate image after {max_retries} attempts")
    return False

def process_partition(partition_file, output_dir):
    """
    Process a partition of products and generate images.
    
    Args:
        partition_file: Path to the partition file
        output_dir: Directory to save the images
    """
    # Set up OpenAI client
    client = setup_openai_client()
    
    # Load the partition file
    with open(partition_file, "r") as f:
        products = json.load(f)
    
    logger.info(f"Processing {len(products)} products from {partition_file}")
    
    # Create checkpoint file path
    partition_num = os.environ.get("PARTITION_NUM", "unknown")
    checkpoint_file = f"/tmp/image_generation_checkpoint_partition_{partition_num}.json"
    
    # Load checkpoint if it exists
    start_index = 0
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r") as f:
                checkpoint_data = json.load(f)
                start_index = checkpoint_data.get("last_processed_index", 0) + 1
                logger.info(f"Resuming from index {start_index} (after product {checkpoint_data.get('product_id', 'unknown')})")
        except Exception as e:
            logger.warning(f"Error loading checkpoint file: {str(e)}")
    
    # Add partition index to each product
    for i, product in enumerate(products):
        product["partition_index"] = i
    
    # Process products starting from the checkpoint
    for i, product in enumerate(products[start_index:], start=start_index):
        logger.info(f"Processing product {i+1}/{len(products)} in partition {partition_num}: {product.get('product_name', 'Unknown')}")
        
        # Generate image with 1 second delay between requests to avoid rate limiting
        success = generate_product_image(client, product, output_dir, checkpoint_file)
        
        # Update checkpoint file with processed count
        logger.info(f"Updated checkpoint file with {i} processed products")
        
        # Add a small delay between requests to avoid rate limiting
        time.sleep(1)

def main():
    """
    Main function to process a partition file and generate images.
    """
    parser = argparse.ArgumentParser(description="Generate product images for a partition")
    parser.add_argument("partition_file", help="Path to the partition file")
    parser.add_argument("--output-dir", default="/home/ubuntu/elastic-ecomm/data/images", help="Directory to save images")
    
    args = parser.parse_args()
    
    # Process the partition
    process_partition(args.partition_file, args.output_dir)

if __name__ == "__main__":
    main()
