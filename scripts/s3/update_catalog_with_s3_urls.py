#!/usr/bin/env python3
"""
Update product catalog with S3 URLs
This script updates the product catalog with S3 image URLs
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def update_catalog_with_s3_urls(catalog_file, s3_url_mapping_file, output_file=None):
    """
    Update product catalog with S3 image URLs
    
    Args:
        catalog_file: Path to the product catalog file
        s3_url_mapping_file: Path to the S3 URL mapping file
        output_file: Output file for the updated catalog
    
    Returns:
        list: Updated product catalog
    """
    try:
        # Check if the files exist
        if not os.path.exists(catalog_file):
            logger.error(f"Catalog file {catalog_file} does not exist")
            return None
        
        if not os.path.exists(s3_url_mapping_file):
            logger.error(f"S3 URL mapping file {s3_url_mapping_file} does not exist")
            return None
        
        # Load catalog
        with open(catalog_file, "r") as f:
            catalog = json.load(f)
        
        # Load S3 URL mapping
        with open(s3_url_mapping_file, "r") as f:
            s3_url_mapping = json.load(f)
        
        # Get product to S3 URL mapping
        product_to_s3_url = s3_url_mapping["product_to_s3_url"]
        
        # Update catalog
        updated_count = 0
        
        for product in catalog:
            # Get product ID
            product_id = product.get("id")
            
            if not product_id:
                continue
            
            # Check if product has an S3 URL
            if product_id in product_to_s3_url:
                # Update product image URL
                product["image"]["url"] = product_to_s3_url[product_id]
                updated_count += 1
        
        logger.info(f"Updated {updated_count}/{len(catalog)} products with S3 image URLs")
        
        # Save updated catalog
        if output_file:
            with open(output_file, "w") as f:
                json.dump(catalog, f, indent=2)
            
            logger.info(f"Saved updated catalog to {output_file}")
        
        return catalog
    
    except Exception as e:
        logger.error(f"Error updating catalog with S3 URLs: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Update product catalog with S3 image URLs")
    parser.add_argument("--catalog-file", default="data/products.json", help="Path to the product catalog file")
    parser.add_argument("--s3-url-mapping-file", default="data/s3_url_mapping.json", help="Path to the S3 URL mapping file")
    parser.add_argument("--output-file", help="Output file for the updated catalog")
    args = parser.parse_args()
    
    # Update catalog with S3 URLs
    update_catalog_with_s3_urls(args.catalog_file, args.s3_url_mapping_file, args.output_file)

if __name__ == "__main__":
    main()
