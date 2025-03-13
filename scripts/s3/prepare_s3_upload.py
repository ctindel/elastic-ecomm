#!/usr/bin/env python3
"""
Prepare product images for S3 upload
This script creates a manifest file for S3 upload
"""
import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def create_upload_manifest(images_dir, output_file=None):
    """
    Create a manifest file for S3 upload
    
    Args:
        images_dir: Directory containing product images
        output_file: Output file for the manifest
    
    Returns:
        dict: Manifest data
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
        
        logger.info(f"Found {len(image_files)} image files in {images_dir}")
        
        # Create manifest
        manifest = {
            "created_at": time.time(),
            "total_images": len(image_files),
            "images": []
        }
        
        # Add image data to manifest
        for image_file in image_files:
            # Get image file name
            file_name = os.path.basename(image_file)
            
            # Get product ID from file name
            product_id = os.path.splitext(file_name)[0]
            
            # Get image file size
            file_size = os.path.getsize(image_file)
            
            # Add image data to manifest
            manifest["images"].append({
                "product_id": product_id,
                "file_name": file_name,
                "file_path": image_file,
                "file_size": file_size,
                "content_type": "image/jpeg" if file_name.lower().endswith(('.jpg', '.jpeg')) else "image/png"
            })
        
        # Calculate total size
        total_size = sum(image["file_size"] for image in manifest["images"])
        manifest["total_size"] = total_size
        
        # Save manifest to file
        if output_file:
            with open(output_file, "w") as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Saved manifest to {output_file}")
        
        return manifest
    
    except Exception as e:
        logger.error(f"Error creating upload manifest: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Prepare product images for S3 upload")
    parser.add_argument("--images-dir", required=True, help="Directory containing product images")
    parser.add_argument("--output-file", default="data/s3_upload_manifest.json", help="Output file for the manifest")
    args = parser.parse_args()
    
    # Create upload manifest
    create_upload_manifest(args.images_dir, args.output_file)

if __name__ == "__main__":
    main()
