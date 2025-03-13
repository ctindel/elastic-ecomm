#!/usr/bin/env python3
"""
Prepare S3 upload manifest
This script prepares a manifest file for uploading product images to S3
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
    Prepare S3 upload manifest
    
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
            "images_dir": images_dir,
            "total_images": len(image_files),
            "images": []
        }
        
        # Calculate total size
        total_size = 0
        
        # Add images to manifest
        for image_file in image_files:
            # Get file size
            file_size = os.path.getsize(image_file)
            total_size += file_size
            
            # Get product ID from file name
            product_id = os.path.splitext(os.path.basename(image_file))[0]
            
            # Get content type
            content_type = None
            ext = os.path.splitext(image_file)[1].lower()
            
            if ext == ".jpg" or ext == ".jpeg":
                content_type = "image/jpeg"
            elif ext == ".png":
                content_type = "image/png"
            elif ext == ".gif":
                content_type = "image/gif"
            
            # Add image to manifest
            manifest["images"].append({
                "product_id": product_id,
                "file_path": image_file,
                "file_size": file_size,
                "content_type": content_type
            })
        
        # Add total size to manifest
        manifest["total_size_mb"] = total_size / (1024 * 1024)
        
        # Save manifest
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Generated S3 upload manifest at {output_file}")
        
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
