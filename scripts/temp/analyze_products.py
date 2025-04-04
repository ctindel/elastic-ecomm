#!/usr/bin/env python3
"""
Script to analyze products.json and identify office and school supplies.
"""
import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def analyze_products():
    """Analyze products.json to identify office and school supplies."""
    # Load products
    with open("data/products.json", "r") as f:
        products = json.load(f)
    
    if not products:
        print("No products found in data/products.json")
        return
    
    # Collect categories and subcategories
    categories = set()
    subcategories = {}
    
    for product in products:
        category = product.get('category')
        subcategory = product.get('subcategory')
        
        if category:
            categories.add(category)
            
            if category not in subcategories:
                subcategories[category] = set()
            
            if subcategory:
                subcategories[category].add(subcategory)
    
    # Print all categories
    print("All Categories:")
    for category in sorted(categories):
        print(f"- {category}")
    
    print("\nOffice & School Supplies related categories:")
    office_related = [cat for cat in categories if 'office' in cat.lower() or 'school' in cat.lower()]
    for category in sorted(office_related):
        print(f"- {category}")
        if category in subcategories:
            for subcat in sorted(subcategories[category]):
                print(f"  - {subcat}")
    
    # Find all office and school related products
    office_products = []
    for product in products:
        category = product.get('category', '').lower()
        subcategory = product.get('subcategory', '').lower()
        
        if ('office' in category or 'school' in category or 
            'office' in subcategory or 'school' in subcategory or
            'pen' in subcategory or 'paper' in subcategory or
            'desk' in subcategory or 'stationery' in subcategory):
            office_products.append(product)
    
    print(f"\nFound {len(office_products)} office and school related products out of {len(products)} total products")
    
    # Print first 5 office products as examples
    print("\nExample office products:")
    for i, product in enumerate(office_products[:5]):
        print(f"{i+1}. {product['name']} (ID: {product['id']})")
    
    return office_products

if __name__ == "__main__":
    analyze_products()
