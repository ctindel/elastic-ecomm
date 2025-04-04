#!/usr/bin/env python3
"""
Script to generate product images for office and school supplies first.
"""
import os
import sys
import json
import requests
from pathlib import Path
import base64
import time
import random
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("office_supplies_image_generation.log")
    ]
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# OpenAI API key should be set in the environment
# Example: export OPENAI_API_KEY="your-api-key"

def is_office_or_school_supply(product):
    """
    Determine if a product is an office or school supply.
    
    Args:
        product: Product dictionary
        
    Returns:
        Boolean indicating if it's an office or school supply
    """
    category = product.get('category', '').lower()
    subcategory = product.get('subcategory', '').lower()
    
    return ('office' in category or 'school' in category or 
            'office' in subcategory or 'school' in subcategory or
            'pen' in subcategory or 'paper' in subcategory or
            'desk' in subcategory or 'stationery' in subcategory)

def generate_image_for_product(product, max_retries=5):
    """
    Generate an image for a product using OpenAI's DALL-E API.
    
    Args:
        product: Product dictionary with details
        max_retries: Maximum number of retry attempts for rate limiting
        
    Returns:
        Path to the saved image
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
                backoff_time = min(2 ** attempt + random.uniform(0, 1), 60)
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
                return None
                
        except Exception as e:
            logger.error(f"Unexpected error generating image: {e}")
            return None
    
    return None

def process_batch(batch, batch_num, total_batches, start_index):
    """Process a batch of products in parallel"""
    results = []
    
    for i, product in enumerate(batch):
        product_index = start_index + i
        logger.info(f"Processing product {product_index+1}/{len(batch)}: {product['name']} (Batch {batch_num+1}/{total_batches})")
        
        # Generate image
        image_path = generate_image_for_product(product)
        
        if image_path:
            logger.info(f"Success! Image saved to {image_path}")
            results.append(image_path)
        else:
            logger.error(f"Failed to generate image for product: {product['name']}")
    
    return results

def generate_office_supplies_images(num_workers=2, batch_size=5):
    """Generate images for office and school supplies first"""
    # Load products
    with open("data/products.json", "r") as f:
        products = json.load(f)
    
    if not products:
        logger.error("No products found in data/products.json")
        return
    
    # Filter for office and school supplies
    office_products = [p for p in products if is_office_or_school_supply(p)]
    
    # Get products that don't already have images
    image_dir = Path("data/images")
    existing_images = set(f.stem.replace("product_", "") for f in image_dir.glob("product_*.png"))
    
    office_products_without_images = [
        p for p in office_products 
        if p['id'] not in existing_images
    ]
    
    logger.info(f"Found {len(office_products)} office and school supplies products")
    logger.info(f"Of these, {len(office_products_without_images)} don't have images yet")
    
    if not office_products_without_images:
        logger.info("All office and school supplies already have images!")
        return
    
    # Process in batches to avoid overwhelming the API
    num_batches = (len(office_products_without_images) + batch_size - 1) // batch_size  # Ceiling division
    
    logger.info(f"Generating images for {len(office_products_without_images)} office products using {num_workers} parallel workers")
    logger.info(f"Using batch size of {batch_size} to avoid rate limits")
    
    # Create batches
    batches = []
    for batch_num in range(num_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, len(office_products_without_images))
        batches.append((
            office_products_without_images[batch_start:batch_end], 
            batch_num, 
            num_batches, 
            batch_start
        ))
    
    # Process batches in parallel with rate limiting
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {}
        
        # Submit initial batches (equal to number of workers)
        for i in range(min(num_workers, len(batches))):
            if i < len(batches):
                futures[executor.submit(process_batch, *batches[i])] = batches[i]
        
        # Process remaining batches with controlled submission
        next_batch_idx = num_workers
        for future in as_completed(futures):
            batch = futures[future]
            try:
                results = future.result()
                batch_num = batch[1]
                logger.info(f"Batch {batch_num+1}/{num_batches} completed. Generated {len(results)} images.")
                
                # Add a small delay between batches to avoid rate limits
                time.sleep(2)
                
                # Submit next batch if available
                if next_batch_idx < len(batches):
                    futures[executor.submit(process_batch, *batches[next_batch_idx])] = batches[next_batch_idx]
                    next_batch_idx += 1
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                
                # If a batch fails, still try to submit the next one
                if next_batch_idx < len(batches):
                    futures[executor.submit(process_batch, *batches[next_batch_idx])] = batches[next_batch_idx]
                    next_batch_idx += 1
    
    logger.info(f"\nAll office and school supplies images generated successfully!")
    return True

def generate_remaining_images(start_index=0, num_workers=2, batch_size=5):
    """Generate images for all remaining products after office supplies"""
    # Load products
    with open("data/products.json", "r") as f:
        products = json.load(f)
    
    if not products:
        logger.error("No products found in data/products.json")
        return
    
    # Filter out office and school supplies
    non_office_products = [p for p in products if not is_office_or_school_supply(p)]
    
    # Get products that don't already have images
    image_dir = Path("data/images")
    existing_images = set(f.stem.replace("product_", "") for f in image_dir.glob("product_*.png"))
    
    non_office_products_without_images = [
        p for p in non_office_products 
        if p['id'] not in existing_images
    ]
    
    logger.info(f"Found {len(non_office_products)} non-office products")
    logger.info(f"Of these, {len(non_office_products_without_images)} don't have images yet")
    
    if not non_office_products_without_images:
        logger.info("All non-office products already have images!")
        return
    
    # Process in batches to avoid overwhelming the API
    num_batches = (len(non_office_products_without_images) + batch_size - 1) // batch_size  # Ceiling division
    
    logger.info(f"Generating images for {len(non_office_products_without_images)} non-office products using {num_workers} parallel workers")
    logger.info(f"Using batch size of {batch_size} to avoid rate limits")
    
    # Create batches
    batches = []
    for batch_num in range(num_batches):
        batch_start = batch_num * batch_size
        batch_end = min(batch_start + batch_size, len(non_office_products_without_images))
        batches.append((
            non_office_products_without_images[batch_start:batch_end], 
            batch_num, 
            num_batches, 
            batch_start
        ))
    
    # Process batches in parallel with rate limiting
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {}
        
        # Submit initial batches (equal to number of workers)
        for i in range(min(num_workers, len(batches))):
            if i < len(batches):
                futures[executor.submit(process_batch, *batches[i])] = batches[i]
        
        # Process remaining batches with controlled submission
        next_batch_idx = num_workers
        for future in as_completed(futures):
            batch = futures[future]
            try:
                results = future.result()
                batch_num = batch[1]
                logger.info(f"Batch {batch_num+1}/{num_batches} completed. Generated {len(results)} images.")
                
                # Add a small delay between batches to avoid rate limits
                time.sleep(2)
                
                # Submit next batch if available
                if next_batch_idx < len(batches):
                    futures[executor.submit(process_batch, *batches[next_batch_idx])] = batches[next_batch_idx]
                    next_batch_idx += 1
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                
                # If a batch fails, still try to submit the next one
                if next_batch_idx < len(batches):
                    futures[executor.submit(process_batch, *batches[next_batch_idx])] = batches[next_batch_idx]
                    next_batch_idx += 1
    
    logger.info(f"\nAll non-office product images generated successfully!")
    return True

if __name__ == "__main__":
    # Check if API key is set in environment
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("Error: OPENAI_API_KEY environment variable is not set.")
        logger.error("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    # First generate office supplies images
    logger.info("=== PHASE 1: Generating Office & School Supplies Images ===")
    generate_office_supplies_images(num_workers=2, batch_size=5)
    
    # Then generate remaining images
    logger.info("\n=== PHASE 2: Generating Remaining Product Images ===")
    generate_remaining_images(num_workers=2, batch_size=5)
