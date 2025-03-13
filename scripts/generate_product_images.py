#!/usr/bin/env python3
"""
Generate product images using OpenAI's DALL-E API
"""
import os
import sys
import json
import time
import base64
import logging
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_APIKEY")
OPENAI_API_URL = "https://api.openai.com/v1/images/generations"

def generate_image_prompt(product: Dict[str, Any]) -> str:
    """
    Generate a prompt for image generation based on product details
    
    Args:
        product: Product data dictionary
    
    Returns:
        str: Image generation prompt
    """
    name = product.get("name", "")
    description = product.get("description", "")
    category = product.get("category", "")
    subcategory = product.get("subcategory", "")
    brand = product.get("brand", "")
    
    # Extract key attributes
    attributes = product.get("attributes", {})
    color = attributes.get("color", "")
    
    # Build the prompt
    prompt_parts = [
        f"A professional product photo of a {name}",
        f"Category: {category}, Subcategory: {subcategory}",
    ]
    
    # Add brand if available
    if brand:
        prompt_parts.append(f"Brand: {brand}")
    
    # Add color if available
    if color:
        prompt_parts.append(f"Color: {color}")
    
    # Add a brief description
    if description:
        # Truncate description to avoid very long prompts
        short_desc = description.split(".")[0]
        prompt_parts.append(f"Description: {short_desc}")
    
    # Add style guidance
    prompt_parts.append("Professional e-commerce style product photography with white background, high resolution, detailed, realistic")
    
    # Join the prompt parts
    prompt = ". ".join(prompt_parts)
    
    return prompt

def generate_image(prompt: str, output_path: str) -> bool:
    """
    Generate an image using OpenAI's DALL-E API
    
    Args:
        prompt: Image generation prompt
        output_path: Path to save the generated image
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found in environment variables")
        return False
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json"
        }
        
        logger.info(f"Generating image with prompt: {prompt[:100]}...")
        
        response = requests.post(
            OPENAI_API_URL,
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            logger.error(f"Error generating image: {response.text}")
            return False
        
        # Parse the response
        response_data = response.json()
        
        # Extract the base64-encoded image
        image_data = response_data["data"][0]["b64_json"]
        
        # Decode the base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Save the image
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        
        logger.info(f"Image saved to {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return False

def generate_product_image(product: Dict[str, Any], output_dir: str) -> bool:
    """
    Generate an image for a product
    
    Args:
        product: Product data dictionary
        output_dir: Directory to save the generated image
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate the image prompt
    prompt = generate_image_prompt(product)
    
    # Generate the output path
    product_id = product.get("id", "unknown")
    output_path = os.path.join(output_dir, f"{product_id}.jpg")
    
    # Generate the image
    return generate_image(prompt, output_path)

def generate_product_images(catalog_file: str, output_dir: str, start_index: int = 0, count: int = 1) -> None:
    """
    Generate images for products in the catalog
    
    Args:
        catalog_file: Path to the product catalog JSON file
        output_dir: Directory to save the generated images
        start_index: Index of the first product to generate an image for
        count: Number of products to generate images for
    """
    logger.info(f"Generating images for products in {catalog_file}")
    
    # Load the products
    with open(catalog_file, "r") as f:
        products = json.load(f)
    
    # Check if there are enough products
    if start_index >= len(products):
        logger.error(f"Start index {start_index} is out of range (max: {len(products) - 1})")
        return
    
    # Calculate the end index
    end_index = min(start_index + count, len(products))
    
    # Generate images for the selected products
    for i in range(start_index, end_index):
        product = products[i]
        logger.info(f"Generating image for product {i+1}/{end_index} ({product.get('name')})")
        
        # Generate the image
        success = generate_product_image(product, output_dir)
        
        if not success:
            logger.error(f"Failed to generate image for product {product.get('id')}")
        
        # Add a delay to avoid rate limiting
        if i < end_index - 1:
            time.sleep(1)
    
    logger.info(f"Generated {end_index - start_index} product images")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate product images using OpenAI's DALL-E API")
    parser.add_argument("--catalog-file", type=str, default="data/products.json", help="Path to the product catalog JSON file")
    parser.add_argument("--output-dir", type=str, default="data/images", help="Directory to save the generated images")
    parser.add_argument("--start-index", type=int, default=0, help="Index of the first product to generate an image for")
    parser.add_argument("--count", type=int, default=1, help="Number of products to generate images for")
    args = parser.parse_args()
    
    # Check if the OpenAI API key is available
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not found in environment variables")
        logger.error("Please set the OPENAI_APIKEY environment variable")
        return
    
    # Generate the images
    generate_product_images(args.catalog_file, args.output_dir, args.start_index, args.count)

if __name__ == "__main__":
    main()
