#!/usr/bin/env python3
"""
Monitor S3 upload progress
This script monitors the progress of S3 uploads
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
    handlers=[
        logging.FileHandler("s3_upload_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def count_objects_in_s3_bucket(bucket_name, prefix=None):
    """
    Count objects in an S3 bucket
    
    Args:
        bucket_name: S3 bucket name
        prefix: Prefix for S3 keys
    
    Returns:
        int: Number of objects
    """
    try:
        # Create the S3 ls command
        cmd = ["aws", "s3", "ls", f"s3://{bucket_name}/"]
        
        # Add prefix if provided
        if prefix:
            cmd[-1] = f"s3://{bucket_name}/{prefix}/"
        
        # Run the command
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Error listing objects in S3 bucket {bucket_name}: {process.stderr}")
            return 0
        
        # Count objects
        lines = process.stdout.strip().split("\n")
        count = len([line for line in lines if line.strip()])
        
        return count
    
    except Exception as e:
        logger.error(f"Error counting objects in S3 bucket {bucket_name}: {str(e)}")
        return 0

def monitor_s3_upload(bucket_name, manifest_file, prefix=None, interval=60):
    """
    Monitor S3 upload progress
    
    Args:
        bucket_name: S3 bucket name
        manifest_file: Path to the manifest file
        prefix: Prefix for S3 keys
        interval: Interval in seconds between checks
    """
    try:
        # Check if the manifest file exists
        if not os.path.exists(manifest_file):
            logger.error(f"Manifest file {manifest_file} does not exist")
            return
        
        # Load the manifest file
        with open(manifest_file, "r") as f:
            manifest = json.load(f)
        
        # Get total images
        total_images = manifest.get("total_images", 0)
        
        logger.info(f"Monitoring S3 upload progress for {total_images} images")
        
        # Monitor progress
        previous_count = 0
        
        while True:
            # Count objects in S3 bucket
            current_count = count_objects_in_s3_bucket(bucket_name, prefix)
            
            # Calculate progress
            progress_percentage = (current_count / total_images) * 100 if total_images > 0 else 0
            new_objects = current_count - previous_count
            
            # Log progress
            logger.info(f"S3 upload progress: {current_count}/{total_images} images ({progress_percentage:.2f}%)")
            
            if new_objects > 0:
                logger.info(f"Uploaded {new_objects} new images since last check")
            
            # Check if complete
            if current_count >= total_images:
                logger.info("S3 upload is complete")
                break
            
            # Update previous count
            previous_count = current_count
            
            # Wait for next check
            time.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("Monitoring stopped")
    
    except Exception as e:
        logger.error(f"Error monitoring S3 upload progress: {str(e)}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Monitor S3 upload progress")
    parser.add_argument("--bucket-name", required=True, help="S3 bucket name")
    parser.add_argument("--manifest-file", default="data/s3_upload_manifest.json", help="Path to the manifest file")
    parser.add_argument("--prefix", help="Prefix for S3 keys")
    parser.add_argument("--interval", type=int, default=60, help="Interval in seconds between checks")
    args = parser.parse_args()
    
    # Monitor S3 upload progress
    monitor_s3_upload(args.bucket_name, args.manifest_file, args.prefix, args.interval)

if __name__ == "__main__":
    main()
