#!/usr/bin/env python3
"""
Monitor image generation progress
This script monitors the progress of image generation and reports status
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

def check_image_progress(images_dir):
    """
    Check the progress of image generation
    
    Args:
        images_dir: Directory containing product images
    
    Returns:
        dict: Progress data
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
        
        # Create progress data
        progress = {
            "timestamp": time.time(),
            "total_images": len(image_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "average_size_mb": total_size / (1024 * 1024) / len(image_files) if image_files else 0,
            "image_files": [os.path.basename(image_file) for image_file in image_files]
        }
        
        return progress
    
    except Exception as e:
        logger.error(f"Error checking image progress: {str(e)}")
        return None

def monitor_image_generation(images_dir, interval=60, output_file=None):
    """
    Monitor image generation progress
    
    Args:
        images_dir: Directory containing product images
        interval: Interval in seconds between checks
        output_file: Output file for the progress data
    """
    try:
        logger.info(f"Monitoring image generation in {images_dir}")
        
        # Create data directory if it doesn't exist
        data_dir = os.path.dirname(output_file) if output_file else "data"
        os.makedirs(data_dir, exist_ok=True)
        
        # Monitor progress
        while True:
            # Check progress
            progress = check_image_progress(images_dir)
            
            if progress:
                # Log progress
                logger.info(f"Generated {progress['total_images']} images ({progress['total_size_mb']:.2f} MB)")
                
                # Save progress to file
                if output_file:
                    with open(output_file, "w") as f:
                        json.dump(progress, f, indent=2)
            
            # Wait for next check
            time.sleep(interval)
    
    except KeyboardInterrupt:
        logger.info("Monitoring stopped")
    
    except Exception as e:
        logger.error(f"Error monitoring image generation: {str(e)}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Monitor image generation progress")
    parser.add_argument("--images-dir", default="data/images", help="Directory containing product images")
    parser.add_argument("--interval", type=int, default=60, help="Interval in seconds between checks")
    parser.add_argument("--output-file", default="data/image_progress.json", help="Output file for the progress data")
    args = parser.parse_args()
    
    # Monitor image generation
    monitor_image_generation(args.images_dir, args.interval, args.output_file)

if __name__ == "__main__":
    main()
