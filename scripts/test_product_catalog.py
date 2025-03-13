#!/usr/bin/env python3
"""
Test the large product catalog generator
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

def test_product_catalog(catalog_file):
    """
    Test the product catalog for diversity and specific examples
    
    Args:
        catalog_file: Path to the product catalog JSON file
    """
    logger.info(f"Testing product catalog: {catalog_file}")
    
    # Load the products
    with open(catalog_file, "r") as f:
        products = json.load(f)
    
    # Check the number of products
    logger.info(f"Total products: {len(products)}")
    
    # Check for specific products
    specific_products = [
        "Premium Laundry Detergent",
        "Moisturizing Hand Soap",
        "Elementary School Supply Kit",
        "27-inch 4K UHD Computer Monitor",
        "Anti-Glare Screen Protector for Monitors"
    ]
    
    found_products = []
    for product in products:
        if product["name"] in specific_products:
            found_products.append(product["name"])
    
    # Print results
    logger.info(f"Found {len(found_products)} out of {len(specific_products)} specific products:")
    for product in found_products:
        logger.info(f"- {product}")
    
    # Check for missing products
    missing_products = set(specific_products) - set(found_products)
    if missing_products:
        logger.info("Missing products:")
        for product in missing_products:
            logger.info(f"- {product}")
    else:
        logger.info("All specific products were found!")
    
    # Check category distribution
    categories = {}
    for product in products:
        category = product["category"]
        if category not in categories:
            categories[category] = 0
        categories[category] += 1
    
    logger.info("Category distribution:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"- {category}: {count} products ({count/len(products)*100:.1f}%)")
    
    # Check subcategory distribution
    subcategories = {}
    for product in products:
        subcategory = product["subcategory"]
        if subcategory not in subcategories:
            subcategories[subcategory] = 0
        subcategories[subcategory] += 1
    
    logger.info("Top 10 subcategories:")
    for subcategory, count in sorted(subcategories.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"- {subcategory}: {count} products")
    
    # Check brand distribution
    brands = {}
    for product in products:
        brand = product["brand"]
        if brand not in brands:
            brands[brand] = 0
        brands[brand] += 1
    
    logger.info("Top 10 brands:")
    for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"- {brand}: {count} products")
    
    # Check price distribution
    prices = [product["price"] for product in products]
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    
    logger.info(f"Price distribution: min=${min_price:.2f}, avg=${avg_price:.2f}, max=${max_price:.2f}")
    
    return len(products), len(found_products), len(specific_products)

def main():
    """Main entry point"""
    # Generate a small test catalog
    logger.info("Generating test catalog...")
    os.system(f"python {os.path.join(project_root, 'scripts', 'generate_large_catalog.py')} --num-products 100 --output-file {os.path.join(project_root, 'data', 'test_products.json')}")
    
    # Test the catalog
    num_products, found_specific, total_specific = test_product_catalog(os.path.join(project_root, "data", "test_products.json"))
    
    # Report results
    logger.info(f"Test results: {num_products} products, {found_specific}/{total_specific} specific products found")
    
    if found_specific == total_specific:
        logger.info("TEST PASSED: All specific products were found")
    else:
        logger.error("TEST FAILED: Not all specific products were found")

if __name__ == "__main__":
    main()
