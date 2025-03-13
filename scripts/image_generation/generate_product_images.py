#!/usr/bin/env python3
"""
Generate product images using OpenAI DALL-E API
This script generates images for products in the catalog
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
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("image_generation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_image_prompt(product):
    """
    Generate a prompt for image generation
    
    Args:
        product: Product data
    
    Returns:
        str: Image generation prompt
    """
    try:
        # Get product details
        name = product.get("name", "")
        description = product.get("description", "")
        category = product.get("category", "")
        subcategory = product.get("subcategory", "")
        brand = product.get("brand", "")
        
        # Get product attributes
        attributes = product.get("attributes", {})
        color = attributes.get("color", "")
        material = attributes.get("material", "")
        
        # Create prompt
        prompt = f"A professional product photo of {name}, a {category} product"
        
        if subcategory:
            prompt += f" in the {subcategory} subcategory"
        
        if brand:
            prompt += f" by {brand}"
        
        if color:
            prompt += f", {color} color"
        
        if material:
            prompt += f", made of {material}"
        
        # Add description
        if description:
            prompt += f". {description}"
        
        # Add style guidance
        prompt += " Professional e-commerce product photography, white background, high resolution, detailed, realistic."
        
        return prompt
    
    except Exception as e:
        logger.error(f"Error generating image prompt: {str(e)}")
        return f"A professional product photo of {name}, white background, high resolution."

def generate_image_with_openai(prompt, product_id, output_dir, api_key=None):
    """
    Generate an image using OpenAI DALL-E API
    
    Args:
        prompt: Image generation prompt
        product_id: Product ID
        output_dir: Output directory for the image
        api_key: OpenAI API key
    
    Returns:
        str: Path to the generated image
    """
    try:
        # Get API key from environment if not provided
        if not api_key:
            api_key = os.environ.get("OPENAI_APIKEY")
        
        if not api_key:
            logger.error("OpenAI API key not provided")
            return None
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create output file path
        output_file = os.path.join(output_dir, f"{product_id}.jpg")
        
        # Check if image already exists
        if os.path.exists(output_file):
            logger.info(f"Image for {product_id} already exists at {output_file}")
            return output_file
        
        # Log prompt
        logger.info(f"Generating image for {product_id} with prompt: {prompt}")
        
        # Call OpenAI API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json"
        }
        
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            logger.error(f"Error generating image: {response.text}")
            return None
        
        # Parse response
        result = response.json()
        image_data = result["data"][0]["b64_json"]
        
        # Save image
        with open(output_file, "wb") as f:
            f.write(base64.b64decode(image_data))
        
        logger.info(f"Generated image for {product_id} at {output_file}")
        
        return output_file
    
    except Exception as e:
        logger.error(f"Error generating image with OpenAI: {str(e)}")
        return None

def generate_images_for_products(products_file, output_dir, start_index=0, end_index=None, batch_size=10, api_key=None):
    """
    Generate images for products in the catalog
    
    Args:
        products_file: Path to the product catalog file
        output_dir: Output directory for the images
        start_index: Start index for batch processing
        end_index: End index for batch processing
        batch_size: Batch size for processing
        api_key: OpenAI API key
    
    Returns:
        dict: Image generation results
    """
    try:
        # Load product catalog
        with open(products_file, "r") as f:
            products = json.load(f)
        
        logger.info(f"Loaded {len(products)} products from {products_file}")
        
        # Set end index if not provided
        if end_index is None:
            end_index = len(products)
        
        # Validate indices
        start_index = max(0, min(start_index, len(products) - 1))
        end_index = max(start_index + 1, min(end_index, len(products)))
        
        logger.info(f"Processing products from index {start_index} to {end_index}")
        
        # Create results
        results = {
            "start_time": datetime.now().isoformat(),
            "products_file": products_file,
            "output_dir": output_dir,
            "start_index": start_index,
            "end_index": end_index,
            "batch_size": batch_size,
            "total_products": len(products),
            "processed_products": 0,
            "successful_images": 0,
            "failed_images": 0,
            "image_paths": [],
            "errors": []
        }
        
        # Process products in batches
        for i in range(start_index, end_index, batch_size):
            # Get batch
            batch_end = min(i + batch_size, end_index)
            batch = products[i:batch_end]
            
            logger.info(f"Processing batch {i // batch_size + 1} ({i} to {batch_end - 1})")
            
            # Process batch
            for j, product in enumerate(batch):
                # Get product ID
                product_id = product.get("id")
                
                if not product_id:
                    logger.warning(f"Product at index {i + j} has no ID, skipping")
                    continue
                
                # Generate prompt
                prompt = generate_image_prompt(product)
                
                # Generate image
                image_path = generate_image_with_openai(prompt, product_id, output_dir, api_key)
                
                # Update results
                results["processed_products"] += 1
                
                if image_path:
                    results["successful_images"] += 1
                    results["image_paths"].append(image_path)
                else:
                    results["failed_images"] += 1
                    results["errors"].append({
                        "product_id": product_id,
                        "index": i + j,
                        "error": "Failed to generate image"
                    })
            
            # Save results
            results["end_time"] = datetime.now().isoformat()
            
            with open("data/image_generation_results.json", "w") as f:
                json.dump(results, f, indent=2)
            
            # Wait between batches to avoid rate limiting
            if batch_end < end_index:
                logger.info(f"Waiting 10 seconds before next batch")
                time.sleep(10)
        
        logger.info(f"Processed {results['processed_products']} products")
        logger.info(f"Generated {results['successful_images']} images")
        logger.info(f"Failed to generate {results['failed_images']} images")
        
        return results
    
    except Exception as e:
        logger.error(f"Error generating images for products: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate product images")
    parser.add_argument("--products-file", default="data/products.json", help="Path to the product catalog file")
    parser.add_argument("--output-dir", default="data/images", help="Output directory for the images")
    parser.add_argument("--start-index", type=int, default=0, help="Start index for batch processing")
    parser.add_argument("--end-index", type=int, help="End index for batch processing")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    parser.add_argument("--api-key", help="OpenAI API key")
    args = parser.parse_args()
    
    # Generate images for products
    generate_images_for_products(
        args.products_file,
        args.output_dir,
        args.start_index,
        args.end_index,
        args.batch_size,
        args.api_key
    )

if __name__ == "__main__":
    main()
