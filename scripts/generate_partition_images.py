#!/usr/bin/env python3
"""
Script to generate product images for a partition of products using OpenAI's DALL-E API.
Includes true infinite retry with exponential backoff.
"""
import os
import sys
import json
import time
import random
import logging
import requests
from pathlib import Path
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

def generate_image_for_product(product, client):
    """
    Generate an image for a product using OpenAI's DALL-E API.
    Uses exponential backoff for rate limiting.
    
    Args:
        product (dict): Product data
        client: OpenAI client
        
    Returns:
        bool: True if image was generated successfully, False otherwise
    """
    product_id = product['id']
    image_filename = f"product_{product_id}.png"
    image_path = Path("/home/ubuntu/elastic-ecomm/data/images") / image_filename
    name = product.get('name', '')
    
    # Skip if image already exists
    if image_path.exists():
        logger.info(f"Image already exists for product ID: {product_id}, filename: {image_filename}. Skipping.")
        return True
    
    # Prepare prompt based on product details
    category = product.get('category', '')
    subcategory = product.get('subcategory', '')
    description = product.get('description', '')
    attributes = product.get('attributes', {})
    
    # Create a detailed prompt
    prompt = f"A professional product photo of a {name}. "
    if category:
        prompt += f"Category: {category}. "
    if subcategory:
        prompt += f"Subcategory: {subcategory}. "
    if description:
        prompt += f"Description: {description}. "
    
    # Add attributes if available
    if attributes:
        for key, value in attributes.items():
            prompt += f"{key}: {value}. "
    
    # Add e-commerce styling
    prompt += "High-quality e-commerce product image with white background, professional lighting."
    
    # Ensure prompt is not too long
    if len(prompt) > 1000:
        prompt = prompt[:997] + "..."
    
    logger.info(f"Attempting to generate image: {image_filename} for product ID: {product_id}")
    logger.info(f"Prompt: {prompt}")
    
    # Maximum backoff time (in seconds)
    max_backoff = 60
    
    # Initial backoff time (in seconds)
    backoff_time = 1
    
    while True:
        try:
            # Generate image
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Get image URL
            image_url = response.data[0].url
            
            # Download image
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                # Create directory if it doesn't exist
                image_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save image
                with open(image_path, 'wb') as f:
                    f.write(image_response.content)
                
                logger.info(f"Successfully generated image: {image_filename} for product ID: {product_id}")
                return True
            else:
                logger.error(f"Error downloading image: {image_filename} for product ID: {product_id} - HTTP status: {image_response.status_code}")
                # Wait before retrying
                backoff_time = min(backoff_time * 2 + random.uniform(0, 1), max_backoff)
                logger.warning(f"Download error for product ID: {product_id}, filename: {image_filename}. Retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
        
        except Exception as e:
            # Check if it's a rate limit error
            if "429" in str(e) or "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                logger.error(f"Error generating image: {image_filename} for product ID: {product_id} - 429 Client Error: Too Many Requests")
                # Exponential backoff with jitter for rate limit errors
                backoff_time = min(backoff_time * 2 + random.uniform(0, 5), max_backoff)
                logger.warning(f"Rate limit hit for product ID: {product_id}, filename: {image_filename}. Retrying in {backoff_time:.2f} seconds...")
            else:
                logger.error(f"Error generating image: {image_filename} for product ID: {product_id} - {e}")
                # Wait before retrying
                backoff_time = min(backoff_time * 2 + random.uniform(0, 5), max_backoff)
                logger.warning(f"Unexpected error for product ID: {product_id}, filename: {image_filename}. Retrying in {backoff_time:.2f} seconds...")
            
            time.sleep(backoff_time)

def generate_images_for_partition(partition_file, partition_num):
    """
    Generate images for all products in a partition.
    
    Args:
        partition_file (str): Path to the partition file
        partition_num (str): Partition number
        
    Returns:
        bool: True if all images were generated successfully
    """
    logger.info(f"Processing partition {partition_num} from {partition_file}")
    
    # Load products from partition file
    try:
        with open(partition_file, 'r') as f:
            products = json.load(f)
    except Exception as e:
        logger.error(f"Error loading partition file {partition_file}: {e}")
        return False
    
    # Create OpenAI client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return False
    
    client = OpenAI(api_key=api_key)
    
    # Create checkpoint file path
    checkpoint_file = f"/tmp/partition_{partition_num}_checkpoint.json"
    
    # Load checkpoint if exists
    processed_products = set()
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
                processed_products = set(checkpoint_data.get('processed_products', []))
                logger.info(f"Loaded checkpoint with {len(processed_products)} processed products")
        except Exception as e:
            logger.error(f"Error loading checkpoint file {checkpoint_file}: {e}")
    
    # Count remaining products
    remaining_products = [p for p in products if p.get('id') not in processed_products]
    logger.info(f"Generating images for {len(remaining_products)}/{len(products)} remaining products in partition {partition_num}")
    
    # Process products
    for i, product in enumerate(remaining_products, 1):
        product_id = product.get('id')
        name = product.get('name', '')
        
        logger.info(f"Processing product {i}/{len(remaining_products)} in partition {partition_num}: {name}")
        
        # Generate image
        if generate_image_for_product(product, client):
            # Add to processed products
            processed_products.add(product_id)
            
            # Update checkpoint
            try:
                with open(checkpoint_file, 'w') as f:
                    json.dump({'processed_products': list(processed_products)}, f)
            except Exception as e:
                logger.error(f"Error updating checkpoint file {checkpoint_file}: {e}")
    
    # Check if all products have been processed
    if len(processed_products) == len(products):
        logger.info(f"All {len(products)} products in partition {partition_num} have been processed")
        return True
    else:
        logger.warning(f"Only {len(processed_products)} out of {len(products)} products in partition {partition_num} have been processed")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        logger.error("Usage: python generate_partition_images.py <partition_file> <partition_num>")
        sys.exit(1)
    
    partition_file = sys.argv[1]
    partition_num = sys.argv[2]
    
    logger.info(f"Starting image generation for partition {partition_num} using {partition_file}")
    
    # Generate images for partition
    success = generate_images_for_partition(partition_file, partition_num)
    
    if success:
        logger.info(f"Image generation for partition {partition_num} completed successfully")
        sys.exit(0)
    else:
        logger.error(f"Image generation for partition {partition_num} failed")
        sys.exit(1)
