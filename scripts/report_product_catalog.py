#!/usr/bin/env python3
"""
Generate a summary report of the product catalog
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

def generate_report(catalog_file, output_file=None):
    """
    Generate a summary report of the product catalog
    
    Args:
        catalog_file: Path to the product catalog JSON file
        output_file: Path to the output report file (optional)
    """
    logger.info(f"Generating report for catalog: {catalog_file}")
    
    # Load the products
    with open(catalog_file, "r") as f:
        products = json.load(f)
    
    # Initialize the report
    report = []
    report.append("# Product Catalog Summary Report")
    report.append(f"\nTotal products: {len(products)}")
    
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
    
    # Add specific products to report
    report.append("\n## Specific Products")
    report.append(f"Found {len(found_products)} out of {len(specific_products)} specific products:")
    for product in found_products:
        report.append(f"- {product}")
    
    # Check category distribution
    categories = Counter()
    for product in products:
        categories[product["category"]] += 1
    
    # Add category distribution to report
    report.append("\n## Category Distribution")
    for category, count in categories.most_common():
        report.append(f"- {category}: {count} products ({count/len(products)*100:.1f}%)")
    
    # Check subcategory distribution
    subcategories = Counter()
    for product in products:
        subcategories[product["subcategory"]] += 1
    
    # Add subcategory distribution to report
    report.append("\n## Top 20 Subcategories")
    for subcategory, count in subcategories.most_common(20):
        report.append(f"- {subcategory}: {count} products ({count/len(products)*100:.1f}%)")
    
    # Check brand distribution
    brands = Counter()
    for product in products:
        brands[product["brand"]] += 1
    
    # Add brand distribution to report
    report.append("\n## Top 20 Brands")
    for brand, count in brands.most_common(20):
        report.append(f"- {brand}: {count} products ({count/len(products)*100:.1f}%)")
    
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
    
    # Add price distribution to report
    report.append("\n## Price Distribution")
    report.append(f"- Min price: ${min_price:.2f}")
    report.append(f"- Average price: ${avg_price:.2f}")
    report.append(f"- Max price: ${max_price:.2f}")
    report.append("\nPrice ranges:")
    for range_name, count in price_ranges.items():
        report.append(f"- {range_name}: {count} products ({count/len(products)*100:.1f}%)")
    
    # Join the report
    report_text = "\n".join(report)
    
    # Write the report to file if specified
    if output_file:
        with open(output_file, "w") as f:
            f.write(report_text)
        logger.info(f"Report saved to {output_file}")
    
    # Return the report
    return report_text

def main():
    """Main entry point"""
    # Generate the report
    catalog_file = os.path.join(project_root, "data", "products.json")
    output_file = os.path.join(project_root, "data", "product_catalog_report.md")
    
    if not os.path.exists(catalog_file):
        logger.error(f"Product catalog not found: {catalog_file}")
        return
    
    report = generate_report(catalog_file, output_file)
    
    # Print the report
    print(report)

if __name__ == "__main__":
    main()
