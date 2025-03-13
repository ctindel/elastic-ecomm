#!/usr/bin/env python3
"""
Upload product images to S3
This script uploads product images to S3 using the AWS CLI
"""
import os
import sys
import json
import time
import logging
import argparse
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def upload_to_s3(manifest_file, bucket_name, prefix=None):
    """
    Upload product images to S3
    
    Args:
        manifest_file: Path to the manifest file
        bucket_name: S3 bucket name
        prefix: S3 key prefix
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if the manifest file exists
        if not os.path.exists(manifest_file):
            logger.error(f"Manifest file {manifest_file} does not exist")
            return False
        
        # Load manifest
        with open(manifest_file, "r") as f:
            manifest = json.load(f)
        
        logger.info(f"Uploading {manifest['total_images']} images to S3 bucket {bucket_name}")
        
        # Create S3 URL mapping
        s3_mapping = {}
        
        # Upload images to S3
        for i, image in enumerate(manifest["images"]):
            # Get image file path
            file_path = image["file_path"]
            
            # Get product ID
            product_id = image["product_id"]
            
            # Create S3 key
            s3_key = f"{prefix}/{product_id}.jpg" if prefix else f"{product_id}.jpg"
            
            # Upload image to S3
            cmd = f"aws s3 cp {file_path} s3://{bucket_name}/{s3_key} --content-type {image['content_type']}"
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if process.returncode != 0:
                logger.error(f"Error uploading {file_path} to S3: {process.stderr}")
                continue
            
            # Create S3 URL
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            
            # Add S3 URL to mapping
            s3_mapping[product_id] = s3_url
            
            # Log progress
            if (i + 1) % 10 == 0 or i == len(manifest["images"]) - 1:
                logger.info(f"Uploaded {i + 1}/{manifest['total_images']} images")
        
        # Save S3 URL mapping
        mapping_file = os.path.join(os.path.dirname(manifest_file), "s3_url_mapping.json")
        with open(mapping_file, "w") as f:
            json.dump(s3_mapping, f, indent=2)
        
        logger.info(f"Saved S3 URL mapping to {mapping_file}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Upload product images to S3")
    parser.add_argument("--manifest-file", required=True, help="Path to the manifest file")
    parser.add_argument("--bucket-name", required=True, help="S3 bucket name")
    parser.add_argument("--prefix", help="S3 key prefix")
    args = parser.parse_args()
    
    # Upload to S3
    upload_to_s3(args.manifest_file, args.bucket_name, args.prefix)

if __name__ == "__main__":
    main()
