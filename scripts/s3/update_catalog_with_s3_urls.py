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
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def update_catalog_with_s3_urls(catalog_file, s3_results_file, output_file=None):
    """
    Update product catalog with S3 URLs
    
    Args:
        catalog_file: Path to the product catalog file
        s3_results_file: Path to the S3 upload results file
        output_file: Path to the output file
    
    Returns:
        dict: Updated catalog
    """
    try:
        # Check if the catalog file exists
        if not os.path.exists(catalog_file):
            logger.error(f"Catalog file {catalog_file} does not exist")
            return None
        
        # Check if the S3 results file exists
        if not os.path.exists(s3_results_file):
            logger.error(f"S3 results file {s3_results_file} does not exist")
            return None
        
        # Load the catalog file
        with open(catalog_file, "r") as f:
            catalog = json.load(f)
        
        # Load the S3 results file
        with open(s3_results_file, "r") as f:
            s3_results = json.load(f)
        
        # Get S3 URLs
        s3_urls = s3_results.get("s3_urls", {})
        
        # Update catalog
        updated_count = 0
        
        for product in catalog:
            product_id = product.get("id")
            
            if product_id in s3_urls:
                # Update product with S3 URL
                if "image" not in product:
                    product["image"] = {}
                
                product["image"]["s3_url"] = s3_urls[product_id]
                updated_count += 1
        
        # Save updated catalog
        if output_file:
            with open(output_file, "w") as f:
                json.dump(catalog, f, indent=2)
            
            logger.info(f"Saved updated catalog to {output_file}")
        
        # Log summary
        logger.info(f"Updated {updated_count}/{len(catalog)} products with S3 URLs")
        
        return catalog
    
    except Exception as e:
        logger.error(f"Error updating catalog with S3 URLs: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Update product catalog with S3 URLs")
    parser.add_argument("--catalog-file", default="data/sample_products.json", help="Path to the product catalog file")
    parser.add_argument("--s3-results-file", required=True, help="Path to the S3 upload results file")
    parser.add_argument("--output-file", help="Path to the output file")
    args = parser.parse_args()
    
    # Update catalog with S3 URLs
    update_catalog_with_s3_urls(args.catalog_file, args.s3_results_file, args.output_file)

if __name__ == "__main__":
    main()
