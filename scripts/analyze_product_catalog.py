#!/usr/bin/env python3
"""
Analyze the product catalog for diversity and specific examples
"""
import os
import sys
import json
import logging
from pathlib import Path
from collections import Counter

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

def analyze_product_catalog(catalog_file):
    """
    Analyze the product catalog for diversity and specific examples
    
    Args:
        catalog_file: Path to the product catalog JSON file
    """
    logger.info(f"Analyzing product catalog: {catalog_file}")
    
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
    categories = Counter()
    for product in products:
        categories[product["category"]] += 1
    
    logger.info("Category distribution:")
    for category, count in categories.most_common():
        logger.info(f"- {category}: {count} products ({count/len(products)*100:.1f}%)")
    
    # Check subcategory distribution
    subcategories = Counter()
    for product in products:
        subcategories[product["subcategory"]] += 1
    
    logger.info("Top 20 subcategories:")
    for subcategory, count in subcategories.most_common(20):
        logger.info(f"- {subcategory}: {count} products ({count/len(products)*100:.1f}%)")
    
    # Check brand distribution
    brands = Counter()
    for product in products:
        brands[product["brand"]] += 1
    
    logger.info("Top 20 brands:")
    for brand, count in brands.most_common(20):
        logger.info(f"- {brand}: {count} products ({count/len(products)*100:.1f}%)")
    
    # Check price distribution
    prices = [product["price"] for product in products]
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)
    
    # Price ranges
    price_ranges = {
        "< $10": 0,
        "$10 - $50": 0,
        "$50 - $100": 0,
        "$100 - $500": 0,
        "$500 - $1000": 0,
        "> $1000": 0
    }
    
    for price in prices:
        if price < 10:
            price_ranges["< $10"] += 1
        elif price < 50:
            price_ranges["$10 - $50"] += 1
        elif price < 100:
            price_ranges["$50 - $100"] += 1
        elif price < 500:
            price_ranges["$100 - $500"] += 1
        elif price < 1000:
            price_ranges["$500 - $1000"] += 1
        else:
            price_ranges["> $1000"] += 1
    
    logger.info(f"Price distribution: min=${min_price:.2f}, avg=${avg_price:.2f}, max=${max_price:.2f}")
    for range_name, count in price_ranges.items():
        logger.info(f"- {range_name}: {count} products ({count/len(products)*100:.1f}%)")
    
    # Check for vector embeddings (should not be present)
    vector_count = 0
    for product in products:
        if "vector_embedding" in product:
            vector_count += 1
        if "image" in product and "vector_embedding" in product["image"]:
            vector_count += 1
    
    if vector_count > 0:
        logger.warning(f"Found {vector_count} vector embeddings in the product catalog!")
    else:
        logger.info("No vector embeddings found in the product catalog (as expected)")
    
    return len(products), len(found_products), len(specific_products)

def main():
    """Main entry point"""
    # Analyze the catalog
    catalog_file = os.path.join(project_root, "data", "products.json")
    if not os.path.exists(catalog_file):
        logger.error(f"Product catalog not found: {catalog_file}")
        return
    
    num_products, found_specific, total_specific = analyze_product_catalog(catalog_file)
    
    # Report results
    logger.info(f"Analysis results: {num_products} products, {found_specific}/{total_specific} specific products found")
    
    if found_specific == total_specific:
        logger.info("VERIFICATION PASSED: All specific products were found")
    else:
        logger.error("VERIFICATION FAILED: Not all specific products were found")

if __name__ == "__main__":
    main()
