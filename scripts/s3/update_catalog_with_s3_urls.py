#!/usr/bin/env python3
"""
Update product catalog with S3 URLs
This script updates the product catalog with S3 URLs for product images
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def update_catalog(catalog_file, mapping_file, output_file=None):
    """
    Update product catalog with S3 URLs
    
    Args:
        catalog_file: Path to the product catalog file
        mapping_file: Path to the S3 URL mapping file
        output_file: Output file for the updated catalog
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if the catalog file exists
        if not os.path.exists(catalog_file):
            logger.error(f"Catalog file {catalog_file} does not exist")
            return False
        
        # Check if the mapping file exists
        if not os.path.exists(mapping_file):
            logger.error(f"Mapping file {mapping_file} does not exist")
            return False
        
        # Load catalog
        with open(catalog_file, "r") as f:
            catalog = json.load(f)
        
        # Load mapping
        with open(mapping_file, "r") as f:
            mapping = json.load(f)
        
        logger.info(f"Updating {len(catalog)} products with S3 URLs")
        
        # Update catalog with S3 URLs
        updated_count = 0
        for product in catalog:
            # Get product ID
            product_id = product["id"]
            
            # Check if product ID is in mapping
            if product_id in mapping:
                # Update product with S3 URL
                if "image" not in product:
                    product["image"] = {}
                
                product["image"]["url"] = mapping[product_id]
                updated_count += 1
        
        logger.info(f"Updated {updated_count}/{len(catalog)} products with S3 URLs")
        
        # Save updated catalog
        if output_file:
            with open(output_file, "w") as f:
                json.dump(catalog, f, indent=2)
            
            logger.info(f"Saved updated catalog to {output_file}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating catalog: {str(e)}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Update product catalog with S3 URLs")
    parser.add_argument("--catalog-file", required=True, help="Path to the product catalog file")
    parser.add_argument("--mapping-file", required=True, help="Path to the S3 URL mapping file")
    parser.add_argument("--output-file", help="Output file for the updated catalog")
    args = parser.parse_args()
    
    # Update catalog
    update_catalog(args.catalog_file, args.mapping_file, args.output_file)

if __name__ == "__main__":
    main()
