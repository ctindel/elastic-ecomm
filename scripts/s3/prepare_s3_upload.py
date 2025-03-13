#!/usr/bin/env python3
"""
Prepare S3 upload manifest for product images
This script creates a manifest file for S3 upload
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

def prepare_s3_upload_manifest(images_dir, output_file="data/s3_upload_manifest.json"):
    """
    Prepare S3 upload manifest for product images
    
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
        
        # Create manifest
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "total_images": len(image_files),
            "total_size_bytes": 0,
            "images": []
        }
        
        # Process image files
        for image_file in image_files:
            # Get file size
            file_size = os.path.getsize(image_file)
            
            # Get product ID from filename
            product_id = os.path.splitext(os.path.basename(image_file))[0]
            
            # Add to manifest
            manifest["images"].append({
                "product_id": product_id,
                "file_path": image_file,
                "file_size": file_size,
                "content_type": "image/jpeg" if image_file.lower().endswith(('.jpg', '.jpeg')) else "image/png"
            })
            
            # Update total size
            manifest["total_size_bytes"] += file_size
        
        # Add total size in MB
        manifest["total_size_mb"] = manifest["total_size_bytes"] / (1024 * 1024)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save manifest
        with open(output_file, "w") as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Created S3 upload manifest with {len(image_files)} images ({manifest['total_size_mb']:.2f} MB)")
        
        return manifest
    
    except Exception as e:
        logger.error(f"Error preparing S3 upload manifest: {str(e)}")
        return None

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Prepare S3 upload manifest")
    parser.add_argument("--images-dir", default="data/images", help="Directory containing product images")
    parser.add_argument("--output-file", default="data/s3_upload_manifest.json", help="Output file for the manifest")
    args = parser.parse_args()
    
    # Prepare S3 upload manifest
    prepare_s3_upload_manifest(args.images_dir, args.output_file)

if __name__ == "__main__":
    main()
