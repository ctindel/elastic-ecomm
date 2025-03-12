#!/usr/bin/env python3
"""
Script to test the image processing functionality.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.image_processor import extract_text_from_image, analyze_school_supply_list
from app.config.settings import OPENAI_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_extract_text_from_image(image_path: str) -> bool:
    """
    Test the text extraction from an image.
    
    Args:
        image_path: Path to the test image
        
    Returns:
        bool: True if the test passed, False otherwise
    """
    logger.info(f"Testing text extraction from image: {image_path}")
    
    # Check if OpenAI API key is available
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key is missing or invalid. Cannot process image.")
        return False
    
    # Extract text from the image
    extracted_text = extract_text_from_image(image_path)
    
    if not extracted_text:
        logger.error("Failed to extract text from image.")
        return False
    
    logger.info(f"Successfully extracted text from image:")
    logger.info(f"{extracted_text}")
    return True

def test_analyze_school_supply_list(image_path: str) -> bool:
    """
    Test the school supply list analysis.
    
    Args:
        image_path: Path to the test image
        
    Returns:
        bool: True if the test passed, False otherwise
    """
    logger.info(f"Testing school supply list analysis: {image_path}")
    
    # Check if OpenAI API key is available
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key is missing or invalid. Cannot process image.")
        return False
    
    # Analyze the school supply list
    analysis = analyze_school_supply_list(image_path)
    
    if not analysis:
        logger.error("Failed to analyze school supply list.")
        return False
    
    # Check if the analysis contains the expected structure
    if "items" not in analysis:
        logger.error("Analysis does not contain 'items' key.")
        return False
    
    # Check if any items were identified
    if not analysis["items"]:
        logger.warning("No items identified in the school supply list.")
        return False
    
    # Print the identified items and alternatives
    logger.info(f"Successfully analyzed school supply list. Identified {len(analysis['items'])} items:")
    for i, item in enumerate(analysis["items"]):
        logger.info(f"Item {i+1}: {item['name']}")
        if "alternatives" in item and item["alternatives"]:
            for alt in item["alternatives"]:
                logger.info(f"  - {alt['price_tier']}: {alt['product']}")
    
    return True

def generate_test_image() -> str:
    """
    Generate a test image with a sample school supply list.
    
    Returns:
        str: Path to the generated test image
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a new image
        img = Image.new('RGB', (800, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font
        try:
            font = ImageFont.truetype("Arial", 20)
        except:
            font = ImageFont.load_default()
        
        # Draw a title
        draw.text((50, 50), "School Supply List", fill=(0, 0, 0), font=font)
        
        # Draw a list of items
        items = [
            "5 Notebooks (college ruled)",
            "2 Packs of #2 Pencils",
            "1 Pack of Colored Pencils",
            "3 Glue Sticks",
            "1 Pair of Scissors",
            "2 Highlighters",
            "1 Backpack",
            "1 Pencil Case",
            "1 Scientific Calculator",
            "1 Pack of Graph Paper"
        ]
        
        for i, item in enumerate(items):
            draw.text((70, 100 + i * 30), f"• {item}", fill=(0, 0, 0), font=font)
        
        # Save the image
        output_path = "data/images/test_school_supply_list.png"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        
        logger.info(f"Generated test image: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error generating test image: {str(e)}")
        return ""

def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Test image processing functionality")
    parser.add_argument("--image", help="Path to the test image")
    parser.add_argument("--generate", action="store_true", help="Generate a test image")
    args = parser.parse_args()
    
    # Check if OpenAI API key is available
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key is missing or invalid. Set the OPENAI_API_KEY environment variable.")
        return 1
    
    # Generate a test image if requested
    if args.generate:
        image_path = generate_test_image()
        if not image_path:
            return 1
    else:
        # Use the provided image path or look for a default test image
        if args.image:
            image_path = args.image
        else:
            # Look for a test image in the data/images directory
            image_dir = Path("data/images")
            if not image_dir.exists() or not any(image_dir.iterdir()):
                logger.error("No images found in data/images directory. Use --generate to create a test image.")
                return 1
            
            # Use the first image file
            image_path = str(next(image_dir.glob("*.png")))
    
    logger.info(f"Using test image: {image_path}")
    
    # Run the tests
    passed = 0
    failed = 0
    
    # Test text extraction
    if test_extract_text_from_image(image_path):
        passed += 1
    else:
        failed += 1
    
    # Test school supply list analysis
    if test_analyze_school_supply_list(image_path):
        passed += 1
    else:
        failed += 1
    
    # Print summary
    logger.info(f"Tests completed: {passed} passed, {failed} failed")
    
    if failed > 0:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
