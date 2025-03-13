#!/usr/bin/env python3
"""
Test image generation for a single product
This script tests the image generation process
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.image_generation.generate_product_images import generate_image_prompt, generate_image_with_openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_image_generation(product_index=0, output_dir="data/test_images", api_key=None):
    """
    Test image generation for a single product
    
    Args:
        product_index: Index of the product to test
        output_dir: Output directory for the test image
        api_key: OpenAI API key
    
    Returns:
        str: Path to the generated image
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Load product catalog
        with open("data/sample_products.json", "r") as f:
            products = json.load(f)
        
        # Get product
        product = products[product_index]
        
        # Get product ID
        product_id = product.get("id")
        
        if not product_id:
            logger.error(f"Product at index {product_index} has no ID")
            return None
        
        # Generate prompt
        prompt = generate_image_prompt(product)
        
        # Generate image
        image_path = generate_image_with_openai(prompt, product_id, output_dir, api_key)
        
        return image_path
    
    except Exception as e:
        logger.error(f"Error testing image generation: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test image generation")
    parser.add_argument("--product-index", type=int, default=0, help="Index of the product to test")
    parser.add_argument("--output-dir", default="data/test_images", help="Output directory for the test image")
    parser.add_argument("--api-key", help="OpenAI API key")
    args = parser.parse_args()
    
    # Test image generation
    image_path = test_image_generation(args.product_index, args.output_dir, args.api_key)
    
    if image_path:
        logger.info(f"Generated test image at {image_path}")
    else:
        logger.error("Failed to generate test image")

if __name__ == "__main__":
    main()
