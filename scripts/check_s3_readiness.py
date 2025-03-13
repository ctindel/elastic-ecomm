#!/usr/bin/env python3
"""
Check S3 readiness for product image upload
This script checks if AWS credentials are configured and if the S3 bucket is accessible
"""
import os
import sys
import json
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

def check_image_generation_completion(images_dir, products_file):
    """
    Check if image generation is complete
    
    Args:
        images_dir: Directory containing product images
        products_file: Path to the product catalog file
    
    Returns:
        bool: True if image generation is complete, False otherwise
    """
    try:
        # Check if the images directory exists
        if not os.path.exists(images_dir):
            logger.error(f"Images directory {images_dir} does not exist")
            return False
        
        # Check if the products file exists
        if not os.path.exists(products_file):
            logger.error(f"Products file {products_file} does not exist")
            return False
        
        # Load product catalog
        with open(products_file, "r") as f:
            products = json.load(f)
        
        # Get all image files
        image_files = []
        for root, _, files in os.walk(images_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    image_files.append(os.path.join(root, file))
        
        # Get product IDs
        product_ids = [product.get("id") for product in products if product.get("id")]
        
        # Calculate completion percentage
        total_products = len(product_ids)
        total_images = len(image_files)
        completion_percentage = (total_images / total_products) * 100 if total_products > 0 else 0
        
        logger.info(f"Image generation is {completion_percentage:.2f}% complete ({total_images}/{total_products} images)")
        
        return total_images >= total_products
    
    except Exception as e:
        logger.error(f"Error checking image generation completion: {str(e)}")
        return False

def generate_readiness_report(bucket_name, images_dir, products_file, output_file="data/s3_readiness_report.json"):
    """
    Generate a report about S3 upload readiness
    
    Args:
        bucket_name: S3 bucket name
        images_dir: Directory containing product images
        products_file: Path to the product catalog file
        output_file: Output file for the report
    
    Returns:
        dict: Readiness report
    """
    try:
        # Check AWS credentials
        aws_credentials_ready = check_aws_credentials()
        
        # Check S3 bucket access
        s3_bucket_ready = check_s3_bucket_access(bucket_name) if aws_credentials_ready else False
        
        # Check image generation completion
        image_generation_ready = check_image_generation_completion(images_dir, products_file)
        
        # Create report
        report = {
            "timestamp": datetime.now().isoformat(),
            "aws_credentials_ready": aws_credentials_ready,
            "s3_bucket_ready": s3_bucket_ready,
            "image_generation_ready": image_generation_ready,
            "overall_ready": aws_credentials_ready and s3_bucket_ready and image_generation_ready,
            "next_steps": []
        }
        
        # Add next steps
        if not aws_credentials_ready:
            report["next_steps"].append("Configure AWS credentials using `aws configure`")
        
        if not s3_bucket_ready and aws_credentials_ready:
            report["next_steps"].append(f"Check if S3 bucket {bucket_name} exists and if you have the necessary permissions")
        
        if not image_generation_ready:
            report["next_steps"].append("Wait for image generation to complete")
        
        if report["overall_ready"]:
            report["next_steps"].append(f"Run `python scripts/s3/upload_to_s3.py --manifest-file data/s3_upload_manifest.json --bucket-name {bucket_name}`")
        
        # Save report
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Generated readiness report at {output_file}")
        
        return report
    
    except Exception as e:
        logger.error(f"Error generating readiness report: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Check S3 readiness for product image upload")
    parser.add_argument("--bucket-name", required=True, help="S3 bucket name")
    parser.add_argument("--images-dir", default="data/images", help="Directory containing product images")
    parser.add_argument("--products-file", default="data/sample_products.json", help="Path to the product catalog file")
    parser.add_argument("--output-file", default="data/s3_readiness_report.json", help="Output file for the readiness report")
    args = parser.parse_args()
    
    # Generate readiness report
    generate_readiness_report(args.bucket_name, args.images_dir, args.products_file, args.output_file)

if __name__ == "__main__":
    main()
