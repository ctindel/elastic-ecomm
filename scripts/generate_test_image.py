#!/usr/bin/env python3
"""
Script to generate a test image with a school supply list.
"""
import os
import sys
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def generate_test_image():
    """Generate a test image with a school supply list."""
    try:
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
        output_dir = Path("data/images")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "test_school_supply_list.png"
        img.save(output_path)
        
        logger.info(f"Generated test image: {output_path}")
        return str(output_path)
    
    except Exception as e:
        logger.error(f"Error generating test image: {str(e)}")
        return ""

def main():
    """Main function."""
    image_path = generate_test_image()
    if image_path:
        print(f"Successfully generated test image: {image_path}")
        return 0
    else:
        print("Failed to generate test image")
        return 1

if __name__ == "__main__":
    sys.exit(main())
