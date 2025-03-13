#!/usr/bin/env python3
"""
Check S3 upload readiness
This script checks if the system is ready for S3 upload
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

def check_aws_credentials():
    """
    Check if AWS credentials are configured
    
    Returns:
        bool: True if AWS credentials are configured, False otherwise
    """
    try:
        # Check if AWS CLI is installed
        import subprocess
        process = subprocess.run(["aws", "--version"], capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error("AWS CLI is not installed")
            return False
        
        # Check if AWS credentials are configured
        process = subprocess.run(["aws", "sts", "get-caller-identity"], capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error("AWS credentials are not configured")
            return False
        
        logger.info("AWS credentials are configured")
        return True
    
    except Exception as e:
        logger.error(f"Error checking AWS credentials: {str(e)}")
        return False

def check_s3_bucket(bucket_name):
    """
    Check if S3 bucket exists and is accessible
    
    Args:
        bucket_name: S3 bucket name
    
    Returns:
        bool: True if S3 bucket exists and is accessible, False otherwise
    """
    try:
        # Check if S3 bucket exists
        import subprocess
        process = subprocess.run(["aws", "s3", "ls", f"s3://{bucket_name}"], capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"S3 bucket {bucket_name} does not exist or is not accessible")
            return False
        
        logger.info(f"S3 bucket {bucket_name} exists and is accessible")
        return True
    
    except Exception as e:
        logger.error(f"Error checking S3 bucket: {str(e)}")
        return False

def check_image_generation_status(images_dir):
    """
    Check the status of image generation
    
    Args:
        images_dir: Directory containing product images
    
    Returns:
        dict: Status data
    """
    try:
        # Check if the images directory exists
        if not os.path.exists(images_dir):
            logger.error(f"Images directory {images_dir} does not exist")
            return None
        
        # Get all image files
        image_files = []
        for root, _, files in os.walk(images_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    image_files.append(os.path.join(root, file))
        
        # Calculate total size
        total_size = sum(os.path.getsize(image_file) for image_file in image_files)
        
        # Create status data
        status = {
            "total_images": len(image_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "average_size_mb": total_size / (1024 * 1024) / len(image_files) if image_files else 0,
            "is_complete": len(image_files) >= 100  # Assuming 100 images for the test batch
        }
        
        return status
    
    except Exception as e:
        logger.error(f"Error checking image generation status: {str(e)}")
        return None

def check_s3_readiness(bucket_name=None, images_dir="data/images"):
    """
    Check if the system is ready for S3 upload
    
    Args:
        bucket_name: S3 bucket name
        images_dir: Directory containing product images
    
    Returns:
        dict: Readiness data
    """
    try:
        # Check AWS credentials
        aws_credentials = check_aws_credentials()
        
        # Check S3 bucket if provided
        s3_bucket = check_s3_bucket(bucket_name) if bucket_name else False
        
        # Check image generation status
        image_status = check_image_generation_status(images_dir)
        
        # Create readiness data
        readiness = {
            "aws_credentials": aws_credentials,
            "s3_bucket": s3_bucket,
            "image_status": image_status,
            "is_ready": aws_credentials and s3_bucket and image_status and image_status["is_complete"]
        }
        
        return readiness
    
    except Exception as e:
        logger.error(f"Error checking S3 readiness: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Check S3 upload readiness")
    parser.add_argument("--bucket-name", help="S3 bucket name")
    parser.add_argument("--images-dir", default="data/images", help="Directory containing product images")
    parser.add_argument("--output-file", help="Output file for the readiness data")
    args = parser.parse_args()
    
    # Check S3 readiness
    readiness = check_s3_readiness(args.bucket_name, args.images_dir)
    
    if readiness:
        # Print readiness data
        print(json.dumps(readiness, indent=2))
        
        # Save readiness data to file
        if args.output_file:
            with open(args.output_file, "w") as f:
                json.dump(readiness, f, indent=2)
    
    # Return success or failure
    return 0 if readiness and readiness["is_ready"] else 1

if __name__ == "__main__":
    sys.exit(main())
