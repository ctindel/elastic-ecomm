#!/usr/bin/env python3
"""
Script to generate product images using OpenAI's DALL-E API.
"""
import os
import sys
import json
import requests
from pathlib import Path
import base64
import time

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# OpenAI API key should be set in the environment
# Example: export OPENAI_API_KEY="your-api-key"

def generate_image_for_product(product):
    """
    Generate an image for a product using OpenAI's DALL-E API.
    
    Args:
        product: Product dictionary with details
        
    Returns:
        Path to the saved image
    """
    # Create directory for images if it doesn't exist
    image_dir = Path("data/images")
    image_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine image filename
    image_filename = f"product_{product['id']}.png"
    image_path = image_dir / image_filename
    
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
    
    print(f"Generating image for: {product['name']}")
    print(f"Prompt: {prompt}")
    
    # Call OpenAI API
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
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Extract image data
        image_data = response.json()["data"][0]["b64_json"]
        
        # Save image
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(image_data))
        
        print(f"Image saved to {image_path}")
        return str(image_path)
    
    except requests.RequestException as e:
        print(f"Error generating image: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"Unexpected error generating image: {e}")
        return None

def generate_batch_images(start_index=0, count=5):
    """Generate images for a batch of products in products.json"""
    # Load products
    with open("data/products.json", "r") as f:
        products = json.load(f)
    
    if not products:
        print("No products found in data/products.json")
        return
    
    # Calculate end index
    end_index = min(start_index + count, len(products))
    batch = products[start_index:end_index]
    
    print(f"Generating images for products {start_index+1} to {end_index} (total: {len(batch)})")
    
    generated_images = []
    for i, product in enumerate(batch):
        print(f"\nProcessing product {start_index+i+1}/{end_index}: {product['name']}")
        
        # Generate image
        image_path = generate_image_for_product(product)
        
        if image_path:
            print(f"Success! Image saved to {image_path}")
            generated_images.append(image_path)
        else:
            print(f"Failed to generate image for product: {product['name']}")
        
        # Add a small delay to avoid rate limiting
        if i < len(batch) - 1:
            time.sleep(1)
    
    print(f"\nBatch processing complete. Generated {len(generated_images)} images.")
    return generated_images

def test_first_product():
    """Generate an image for the first product in products.json"""
    # Load products
    with open("data/products.json", "r") as f:
        products = json.load(f)
    
    if not products:
        print("No products found in data/products.json")
        return
    
    # Generate image for first product
    first_product = products[0]
    print(f"Testing image generation with first product: {first_product['name']}")
    
    image_path = generate_image_for_product(first_product)
    
    if image_path:
        print(f"Test successful! Image saved to {image_path}")
        print(f"Product details: {json.dumps(first_product, indent=2)}")
    else:
        print("Test failed. Could not generate image.")

def generate_all_remaining_products(start_index=6):
    """Generate images for all remaining products in products.json"""
    # Load products
    with open("data/products.json", "r") as f:
        products = json.load(f)
    
    if not products:
        print("No products found in data/products.json")
        return
    
    # Calculate total remaining products
    total_remaining = len(products) - start_index
    
    if total_remaining <= 0:
        print(f"No remaining products to process (starting from index {start_index})")
        return
    
    print(f"Generating images for {total_remaining} remaining products (starting from index {start_index})")
    
    # Process in batches to avoid overwhelming the API
    batch_size = 10
    num_batches = (total_remaining + batch_size - 1) // batch_size  # Ceiling division
    
    for batch_num in range(num_batches):
        batch_start = start_index + (batch_num * batch_size)
        batch_end = min(batch_start + batch_size, len(products))
        batch = products[batch_start:batch_end]
        
        print(f"\nProcessing batch {batch_num+1}/{num_batches}: products {batch_start+1} to {batch_end}")
        
        for i, product in enumerate(batch):
            print(f"\nProcessing product {batch_start+i+1}/{len(products)}: {product['name']}")
            
            # Skip if image already exists
            image_filename = f"product_{product['id']}.png"
            image_path = Path("data/images") / image_filename
            
            if image_path.exists():
                print(f"Image already exists at {image_path}, skipping")
                continue
            
            # Generate image
            image_path = generate_image_for_product(product)
            
            if image_path:
                print(f"Success! Image saved to {image_path}")
            else:
                print(f"Failed to generate image for product: {product['name']}")
            
            # Add a small delay to avoid rate limiting
            if i < len(batch) - 1:
                time.sleep(1)
        
        # Add a delay between batches to avoid rate limiting
        if batch_num < num_batches - 1:
            print(f"Waiting 5 seconds before next batch...")
            time.sleep(5)
    
    print(f"\nAll product images generated successfully!")
    return True

if __name__ == "__main__":
    # Check if API key is set in environment
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Generate all remaining products
    generate_all_remaining_products(start_index=6)
