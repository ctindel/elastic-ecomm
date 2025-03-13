#!/usr/bin/env python3
"""
Test the product image generation script
"""
import os
import sys
import json
import logging
from pathlib import Path

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

def test_image_generation():
    """Test the product image generation script"""
    # Check if the OpenAI API key is available
    if not os.environ.get("OPENAI_APIKEY"):
        logger.error("OpenAI API key not found in environment variables")
        logger.error("Please set the OPENAI_APIKEY environment variable")
        return False
    
    # Create a test product
    test_product = {
        "id": "TEST-001",
        "name": "Premium Wireless Headphones",
        "description": "High-quality wireless headphones with noise cancellation and long battery life. Perfect for music lovers and travelers.",
        "category": "Electronics",
        "subcategory": "Audio",
        "price": 149.99,
        "brand": "Sony",
        "attributes": {
            "color": "Black",
            "weight": "0.5 lbs",
            "battery_life": "30 hours",
            "connectivity": "Bluetooth 5.0"
        },
        "image": {
            "url": "data/images/TEST-001.jpg",
            "alt_text": "Image of Premium Wireless Headphones"
        }
    }
    
    # Create a test directory
    test_dir = os.path.join(project_root, "data", "test_images")
    os.makedirs(test_dir, exist_ok=True)
    
    # Save the test product to a temporary file
    test_catalog_file = os.path.join(test_dir, "test_product.json")
    with open(test_catalog_file, "w") as f:
        json.dump([test_product], f)
    
    # Run the image generation script
    logger.info("Running image generation script...")
    cmd = f"python {os.path.join(project_root, 'scripts', 'generate_product_images.py')} --catalog-file {test_catalog_file} --output-dir {test_dir} --count 1"
    exit_code = os.system(cmd)
    
    if exit_code != 0:
        logger.error("Image generation script failed")
        return False
    
    # Check if the image was generated
    image_path = os.path.join(test_dir, "TEST-001.jpg")
    if not os.path.exists(image_path):
        logger.error(f"Image not found at {image_path}")
        return False
    
    # Check the image file size
    image_size = os.path.getsize(image_path)
    if image_size < 10000:  # Expect at least 10KB for a valid image
        logger.error(f"Image file size is too small: {image_size} bytes")
        return False
    
    logger.info(f"Successfully generated test image: {image_path} ({image_size} bytes)")
    return True

def main():
    """Main entry point"""
    success = test_image_generation()
    
    if success:
        logger.info("TEST PASSED: Product image generation works correctly")
    else:
        logger.error("TEST FAILED: Product image generation has issues")

if __name__ == "__main__":
    main()
