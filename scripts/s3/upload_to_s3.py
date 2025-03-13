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
    handlers=[
        logging.FileHandler("s3_upload.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_aws_credentials():
    """
    Check if AWS credentials are configured
    
    Returns:
        bool: True if credentials are configured, False otherwise
    """
    try:
        # Check if AWS CLI is installed
        process = subprocess.run(["aws", "--version"], capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error("AWS CLI is not installed")
            return False
        
        # Check if AWS credentials are configured
        process = subprocess.run(["aws", "sts", "get-caller-identity"], capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error("AWS credentials are not configured")
            return False
        
        # Parse the response
        response = json.loads(process.stdout)
        
        # Log the caller identity
        logger.info(f"AWS credentials are configured for {response.get('Arn')}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking AWS credentials: {str(e)}")
        return False

def check_s3_bucket_access(bucket_name):
    """
    Check if the S3 bucket is accessible
    
    Args:
        bucket_name: S3 bucket name
    
    Returns:
        bool: True if the bucket is accessible, False otherwise
    """
    try:
        # Check if the bucket exists
        process = subprocess.run(["aws", "s3api", "head-bucket", "--bucket", bucket_name], capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"S3 bucket {bucket_name} is not accessible: {process.stderr}")
            return False
        
        # Check if we can list objects in the bucket
        process = subprocess.run(["aws", "s3", "ls", f"s3://{bucket_name}"], capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Cannot list objects in S3 bucket {bucket_name}: {process.stderr}")
            return False
        
        logger.info(f"S3 bucket {bucket_name} is accessible")
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking S3 bucket access: {str(e)}")
        return False

def upload_image_to_s3(file_path, bucket_name, s3_key, content_type=None):
    """
    Upload an image to S3
    
    Args:
        file_path: Path to the image file
        bucket_name: S3 bucket name
        s3_key: S3 key for the image
        content_type: Content type of the image
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if the file exists
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} does not exist")
            return False
        
        # Create the S3 upload command
        cmd = ["aws", "s3", "cp", file_path, f"s3://{bucket_name}/{s3_key}"]
        
        # Add content type if provided
        if content_type:
            cmd.extend(["--content-type", content_type])
        
        # Upload the file
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Error uploading {file_path} to S3: {process.stderr}")
            return False
        
        logger.info(f"Uploaded {file_path} to s3://{bucket_name}/{s3_key}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error uploading {file_path} to S3: {str(e)}")
        return False

def upload_images_to_s3(manifest_file, bucket_name, prefix=None, max_retries=3, retry_delay=5):
    """
    Upload images to S3 using a manifest file
    
    Args:
        manifest_file: Path to the manifest file
        bucket_name: S3 bucket name
        prefix: Prefix for S3 keys
        max_retries: Maximum number of retries for failed uploads
        retry_delay: Delay in seconds between retries
    
    Returns:
        dict: Upload results
    """
    try:
        # Check if the manifest file exists
        if not os.path.exists(manifest_file):
            logger.error(f"Manifest file {manifest_file} does not exist")
            return None
        
        # Load the manifest file
        with open(manifest_file, "r") as f:
            manifest = json.load(f)
        
        # Check if AWS credentials are configured
        if not check_aws_credentials():
            logger.error("AWS credentials are not configured")
            return None
        
        # Check if the S3 bucket is accessible
        if not check_s3_bucket_access(bucket_name):
            logger.error(f"S3 bucket {bucket_name} is not accessible")
            return None
        
        # Create results dictionary
        results = {
            "timestamp": datetime.now().isoformat(),
            "bucket_name": bucket_name,
            "prefix": prefix,
            "total_images": len(manifest.get("images", [])),
            "successful_uploads": 0,
            "failed_uploads": 0,
            "s3_urls": {},
            "failed_images": []
        }
        
        # Upload images
        for image in manifest.get("images", []):
            product_id = image.get("product_id")
            file_path = image.get("file_path")
            content_type = image.get("content_type")
            
            # Skip if product_id or file_path is missing
            if not product_id or not file_path:
                logger.warning(f"Skipping image with missing product_id or file_path: {image}")
                results["failed_uploads"] += 1
                results["failed_images"].append(image)
                continue
            
            # Create S3 key
            s3_key = f"{prefix}/{product_id}.{file_path.split('.')[-1]}" if prefix else f"{product_id}.{file_path.split('.')[-1]}"
            
            # Upload image with retries
            success = False
            retries = 0
            
            while not success and retries < max_retries:
                success = upload_image_to_s3(file_path, bucket_name, s3_key, content_type)
                
                if not success:
                    retries += 1
                    logger.warning(f"Retrying upload for {file_path} ({retries}/{max_retries})")
                    time.sleep(retry_delay)
            
            # Update results
            if success:
                results["successful_uploads"] += 1
                results["s3_urls"][product_id] = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            else:
                results["failed_uploads"] += 1
                results["failed_images"].append(image)
        
        # Save results
        results_file = f"data/s3_upload_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved upload results to {results_file}")
        
        # Log summary
        logger.info(f"Upload summary: {results['successful_uploads']}/{results['total_images']} images uploaded successfully")
        
        if results["failed_uploads"] > 0:
            logger.warning(f"{results['failed_uploads']} images failed to upload")
        
        return results
    
    except Exception as e:
        logger.error(f"Error uploading images to S3: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Upload product images to S3")
    parser.add_argument("--manifest-file", default="data/s3_upload_manifest.json", help="Path to the manifest file")
    parser.add_argument("--bucket-name", required=True, help="S3 bucket name")
    parser.add_argument("--prefix", help="Prefix for S3 keys")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum number of retries for failed uploads")
    parser.add_argument("--retry-delay", type=int, default=5, help="Delay in seconds between retries")
    args = parser.parse_args()
    
    # Upload images to S3
    upload_images_to_s3(args.manifest_file, args.bucket_name, args.prefix, args.max_retries, args.retry_delay)

if __name__ == "__main__":
    main()
