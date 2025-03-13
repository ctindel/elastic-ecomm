#!/usr/bin/env python3
"""
Test the product catalog generation
This script tests the generation of a small product catalog
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.product_catalog.generate_comprehensive_catalog import generate_product_catalog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_catalog_generation():
    """Test the product catalog generation"""
    try:
        # Generate a small product catalog
        output_file = "data/test_products.json"
        products = generate_product_catalog(num_products=100, output_file=output_file)
        
        if not products:
            logger.error("Failed to generate product catalog")
            return False
        
        # Check if the output file exists
        if not os.path.exists(output_file):
            logger.error(f"Output file {output_file} does not exist")
            return False
        
        # Load the product catalog
        with open(output_file, "r") as f:
            loaded_products = json.load(f)
        
        # Check if the product catalog has the correct number of products
        if len(loaded_products) != 100:
            logger.error(f"Product catalog has {len(loaded_products)} products, expected 100")
            return False
        
        # Check if the specific examples are included
        specific_examples = [
            "EcoClean Laundry Detergent",
            "NaturePure Organic Hand Soap",
            "ColorBright Colored Pencils Set",
            "DesignPro 27-inch 4K Monitor",
            "OfficePro 24-inch Anti-Glare Monitor"
        ]
        
        for example in specific_examples:
            found = False
            for product in loaded_products:
                if product["name"] == example:
                    found = True
                    break
            
            if not found:
                logger.error(f"Specific example '{example}' not found in product catalog")
                return False
        
        logger.info("Product catalog generation test passed")
        return True
    
    except Exception as e:
        logger.error(f"Error testing product catalog generation: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_catalog_generation()
    sys.exit(0 if success else 1)
