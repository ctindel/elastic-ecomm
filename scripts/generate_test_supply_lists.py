#!/usr/bin/env python3
"""
Script to generate multiple test school supply list images.
"""
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def create_supply_list_image(items, title, output_path):
    """Create a school supply list image with the given items."""
    try:
        # Create a new image with white background
        img = Image.new('RGB', (800, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font
        try:
            font = ImageFont.truetype("Arial", 20)
        except:
            font = ImageFont.load_default()
        
        # Draw a title
        draw.text((50, 50), title, fill=(0, 0, 0), font=font)
        
        # Draw a list of items
        for i, item in enumerate(items):
            draw.text((70, 100 + i * 30), f"• {item}", fill=(0, 0, 0), font=font)
        
        # Save the image
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
        logger.info(f"Generated image: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error generating image {output_path}: {str(e)}")
        return False

def main():
    """Generate multiple test school supply list images."""
    # Define the test images and their content
    test_images = [
        {
            "title": "Elementary School Supply List",
            "items": [
                "2 Boxes of Crayons (24 count)",
                "1 Pack of #2 Pencils",
                "1 Pack of Colored Pencils",
                "2 Glue Sticks",
                "1 Pair of Safety Scissors",
                "1 Box of Tissues",
                "1 Backpack",
                "1 Pencil Box",
                "1 Pack of Construction Paper",
                "1 Pack of Washable Markers"
            ],
            "filename": "elementary_supplies.png"
        },
        {
            "title": "High School Supply List",
            "items": [
                "5 College Ruled Notebooks",
                "2 Packs of #2 Pencils",
                "1 Scientific Calculator",
                "1 Pack of Graph Paper",
                "1 Pack of Highlighters",
                "1 USB Flash Drive",
                "1 Backpack",
                "1 Pack of Index Cards",
                "1 Pack of Binder Dividers",
                "1 Pack of Sticky Notes"
            ],
            "filename": "high_school_supplies.png"
        },
        {
            "title": "Art Class Supply List",
            "items": [
                "1 Sketchbook (9x12)",
                "1 Set of Drawing Pencils",
                "1 Pack of Erasers",
                "1 Pack of Colored Pencils (24 count)",
                "1 Pack of Watercolor Paints",
                "2 Paint Brushes",
                "1 Art Portfolio",
                "1 Pack of Construction Paper",
                "1 Pack of Markers",
                "1 Pack of Glue Sticks"
            ],
            "filename": "art_supplies.png"
        },
        {
            "title": "College Supply List",
            "items": [
                "3 College Ruled Notebooks",
                "1 Pack of Pens (Blue or Black)",
                "1 Laptop or Tablet",
                "1 Pack of Highlighters",
                "1 Scientific Calculator",
                "1 Backpack",
                "1 Pack of Index Cards",
                "1 Pack of Binder Dividers",
                "1 USB Flash Drive",
                "1 Pack of Sticky Notes"
            ],
            "filename": "college_supplies.png"
        }
    ]
    
    # Create output directory
    output_dir = Path("data/testimages")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate each image
    success_count = 0
    for test_image in test_images:
        output_path = output_dir / test_image["filename"]
        if create_supply_list_image(
            test_image["items"],
            test_image["title"],
            str(output_path)
        ):
            success_count += 1
    
    logger.info(f"Successfully generated {success_count} out of {len(test_images)} images")
    return success_count == len(test_images)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 