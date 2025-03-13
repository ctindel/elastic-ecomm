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
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def upload_to_s3(manifest_file, bucket_name, prefix=None, output_file="data/s3_url_mapping.json"):
    """
    Upload product images to S3
    
    Args:
        manifest_file: Path to the S3 upload manifest file
        bucket_name: S3 bucket name
        prefix: S3 key prefix
        output_file: Output file for the S3 URL mapping
    
    Returns:
        dict: S3 URL mapping
    """
    try:
        # Check if the manifest file exists
        if not os.path.exists(manifest_file):
            logger.error(f"Manifest file {manifest_file} does not exist")
            return None
        
        # Load manifest
        with open(manifest_file, "r") as f:
            manifest = json.load(f)
        
        # Create S3 URL mapping
        s3_url_mapping = {
            "timestamp": datetime.now().isoformat(),
            "bucket_name": bucket_name,
            "prefix": prefix,
            "total_images": manifest["total_images"],
            "uploaded_images": 0,
            "failed_images": 0,
            "product_to_s3_url": {}
        }
        
        # Process images
        for i, image in enumerate(manifest["images"]):
            # Get image details
            product_id = image["product_id"]
            file_path = image["file_path"]
            content_type = image["content_type"]
            
            # Create S3 key
            s3_key = f"{prefix}/{product_id}.jpg" if prefix else f"{product_id}.jpg"
            
            # Create S3 URL
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            
            # Upload to S3
            logger.info(f"Uploading {file_path} to s3://{bucket_name}/{s3_key} ({i + 1}/{manifest['total_images']})")
            
            try:
                # Use AWS CLI to upload
                cmd = [
                    "aws", "s3", "cp",
                    file_path,
                    f"s3://{bucket_name}/{s3_key}",
                    "--content-type", content_type
                ]
                
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                if process.returncode != 0:
                    logger.error(f"Error uploading {file_path}: {process.stderr}")
                    s3_url_mapping["failed_images"] += 1
                else:
                    # Add to mapping
                    s3_url_mapping["product_to_s3_url"][product_id] = s3_url
                    s3_url_mapping["uploaded_images"] += 1
            
            except Exception as e:
                logger.error(f"Error uploading {file_path}: {str(e)}")
                s3_url_mapping["failed_images"] += 1
            
            # Save mapping after each upload
            with open(output_file, "w") as f:
                json.dump(s3_url_mapping, f, indent=2)
            
            # Wait between uploads to avoid rate limiting
            if i < len(manifest["images"]) - 1:
                time.sleep(0.1)
        
        logger.info(f"Uploaded {s3_url_mapping['uploaded_images']}/{manifest['total_images']} images to S3")
        
        return s3_url_mapping
    
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Upload product images to S3")
    parser.add_argument("--manifest-file", default="data/s3_upload_manifest.json", help="Path to the S3 upload manifest file")
    parser.add_argument("--bucket-name", required=True, help="S3 bucket name")
    parser.add_argument("--prefix", help="S3 key prefix")
    parser.add_argument("--output-file", default="data/s3_url_mapping.json", help="Output file for the S3 URL mapping")
    args = parser.parse_args()
    
    # Upload to S3
    upload_to_s3(args.manifest_file, args.bucket_name, args.prefix, args.output_file)

if __name__ == "__main__":
    main()
