#!/usr/bin/env python3
"""
Script to partition office supplies products into 10 sets and run parallel image generation.
"""
import os
import sys
import json
import subprocess
import time
from pathlib import Path
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("office_supplies_partitioning.log")
    ]
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def identify_office_supplies():
    """Identify office and school supplies products."""
    # Load products
    with open("data/products.json", "r") as f:
        products = json.load(f)
    
    if not products:
        logger.error("No products found in data/products.json")
        return []
    
    # Find all office and school related products
    office_products = []
    for product in products:
        category = product.get('category', '').lower()
        subcategory = product.get('subcategory', '').lower()
        name = product.get('name', '').lower()
        
        if ('office' in category or 'school' in category or 
            'office' in subcategory or 'school' in subcategory or
            'pen' in subcategory or 'paper' in subcategory or
            'desk' in subcategory or 'stationery' in subcategory or
            'office' in name or 'school' in name or
            'pen' in name or 'pencil' in name or
            'notebook' in name or 'binder' in name or
            'stapler' in name or 'paper' in name):
            office_products.append(product)
    
    logger.info(f"Found {len(office_products)} office and school related products")
    return office_products

def partition_products(products, num_partitions=10):
    """Partition products into specified number of sets."""
    # Shuffle products to ensure even distribution
    random.shuffle(products)
    
    # Calculate partition size
    partition_size = len(products) // num_partitions
    remainder = len(products) % num_partitions
    
    partitions = []
    start_idx = 0
    
    for i in range(num_partitions):
        # Add one extra item to some partitions if there's a remainder
        current_size = partition_size + (1 if i < remainder else 0)
        end_idx = start_idx + current_size
        
        partitions.append(products[start_idx:end_idx])
        start_idx = end_idx
    
    return partitions

def save_partitions(partitions):
    """Save partitions to temporary JSON files."""
    partition_files = []
    
    for i, partition in enumerate(partitions):
        partition_file = f"/tmp/office_supplies_partition_{i+1}.json"
        with open(partition_file, "w") as f:
            json.dump(partition, f, indent=2)
        
        logger.info(f"Saved partition {i+1} with {len(partition)} products to {partition_file}")
        partition_files.append(partition_file)
    
    return partition_files

def create_runner_script():
    """Create a script to run image generation with TRUE infinite retry."""
    runner_script = "/tmp/run_image_generator.sh"
    
    script_content = """#!/bin/bash
# Script to run image generation with TRUE infinite retry
PARTITION_FILE=$1
PARTITION_NUM=$2
LOG_FILE="/tmp/image_generation_partition_${PARTITION_NUM}.log"

echo "Starting image generation for partition ${PARTITION_NUM} using ${PARTITION_FILE}"
echo "Logs will be written to ${LOG_FILE}"

# True infinite retry - never exit, always keep trying
while true; do
    echo "$(date) - Attempt to run image generation for partition ${PARTITION_NUM}" >> ${LOG_FILE}
    OPENAI_API_KEY=$OPENAI_APIKEY python3 /home/ubuntu/elastic-ecomm/scripts/generate_partition_images.py ${PARTITION_FILE} ${PARTITION_NUM} >> ${LOG_FILE} 2>&1
    
    # Always continue running, regardless of exit code
    # This ensures we keep trying even if the script exits with success (0)
    # because we want to make sure ALL images are generated
    echo "$(date) - Image generation for partition ${PARTITION_NUM} completed or encountered an error, continuing in 10 seconds..." >> ${LOG_FILE}
    sleep 10
done
"""
    
    with open(runner_script, "w") as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod(runner_script, 0o755)
    
    logger.info(f"Created runner script at {runner_script}")
    return runner_script

def create_image_generator_script():
    """Create a script to generate images for a partition."""
    generator_script = "/home/ubuntu/elastic-ecomm/scripts/generate_partition_images.py"
    
    script_content = '''#!/usr/bin/env python3
"""
Script to generate images for a partition of products.
"""
import os
import sys
import json
import requests
from pathlib import Path
import base64
import time
import random
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def generate_image_for_product(product):
    """
    Generate an image for a product using OpenAI's DALL-E API with true infinite retry.
    """
    # Create directory for images if it doesn't exist
    image_dir = Path("data/images")
    image_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine image filename
    image_filename = f"product_{product['id']}.png"
    image_path = image_dir / image_filename
    
    # Skip if image already exists
    if image_path.exists():
        logger.info(f"Image already exists at {image_path}, skipping")
        return str(image_path)
    
    # Create a detailed prompt for the image
    prompt = f"A professional product photo of a {product['brand']} {product['subcategory']}"
    
    # Add color if available
    if 'attributes' in product and 'color' in product['attributes']:
        prompt += f", {product['attributes']['color']} color"
    
    # Add material if available
    if 'attributes' in product and 'material' in product['attributes']:
        prompt += f", made of {product['attributes']['material']}"
    
    # Add style context
    prompt += f". High-quality e-commerce product image with white background, professional lighting."
    
    logger.info(f"Generating image for: {product['name']}")
    logger.info(f"Prompt: {prompt}")
    
    # Call OpenAI API with true infinite retry logic
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
    }
    
    data = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json"
    }
    
    # Implement exponential backoff with jitter - TRUE INFINITE RETRIES
    attempt = 0
    while True:  # Loop forever until we succeed or explicitly return
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            # Extract image data
            image_data = response.json()["data"][0]["b64_json"]
            
            # Save image
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            
            logger.info(f"Success! Image saved to {image_path}")
            return str(image_path)
        
        except requests.RequestException as e:
            # Check if it's a rate limit error (429)
            if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                # Calculate backoff time with exponential increase and jitter
                backoff_time = min(2 ** min(attempt, 10) + random.uniform(0, 1), 60)
                logger.warning(f"Rate limit hit. Retrying in {backoff_time:.2f} seconds... (Attempt {attempt+1}/∞)")
                time.sleep(backoff_time)
            else:
                # For other request errors, log and retry with a delay
                logger.error(f"Error generating image: {e}")
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Response: {e.response.text}")
                # Wait before retrying
                backoff_time = min(10 + random.uniform(0, 5), 30)
                logger.warning(f"Request error. Retrying in {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
                
        except Exception as e:
            # For unexpected errors, log and retry with a delay
            logger.error(f"Unexpected error generating image: {e}")
            # Wait before retrying
            backoff_time = min(10 + random.uniform(0, 5), 30)
            logger.warning(f"Unexpected error. Retrying in {backoff_time:.2f} seconds...")
            time.sleep(backoff_time)
        
        # Increment attempt counter for backoff calculation
        attempt += 1

def generate_images_for_partition(partition_file, partition_num):
    """Generate images for products in a partition."""
    # Handle non-integer partition numbers safely
    try:
        partition_num = int(partition_num) if not isinstance(partition_num, int) else partition_num
    except ValueError:
        # If partition_num is not convertible to int, keep it as is
        pass
    
    logger.info(f"Processing partition {partition_num} from {partition_file}")
    
    # Load products from partition file
    with open(partition_file, "r") as f:
        products = json.load(f)
    
    if not products:
        logger.error(f"No products found in {partition_file}")
        return False
    
    # Create checkpoint file path
    checkpoint_file = f"/tmp/partition_{partition_num}_checkpoint.json"
    
    # Load checkpoint if exists
    processed_ids = set()
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r") as f:
                checkpoint_data = json.load(f)
                processed_ids = set(checkpoint_data.get("processed_ids", []))
                logger.info(f"Loaded checkpoint with {len(processed_ids)} processed products")
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            # Create an empty checkpoint file to ensure we can write to it
            try:
                with open(checkpoint_file, "w") as f:
                    json.dump({"processed_ids": []}, f)
                logger.info(f"Created new empty checkpoint file at {checkpoint_file}")
            except Exception as e2:
                logger.error(f"Failed to create checkpoint file: {e2}")
    else:
        # Create an empty checkpoint file
        try:
            with open(checkpoint_file, "w") as f:
                json.dump({"processed_ids": []}, f)
            logger.info(f"Created new empty checkpoint file at {checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to create checkpoint file: {e}")
    
    # Also check for existing images in the data/images directory
    image_dir = Path("data/images")
    for product in products:
        image_path = image_dir / f"product_{product['id']}.png"
        if image_path.exists():
            processed_ids.add(product["id"])
    
    # Filter products that haven't been processed yet
    remaining_products = [p for p in products if p["id"] not in processed_ids]
    
    logger.info(f"Generating images for {len(remaining_products)}/{len(products)} remaining products in partition {partition_num}")
    
    # Process products one by one with a small delay between each
    success_count = 0
    for i, product in enumerate(remaining_products):
        logger.info(f"Processing product {i+1}/{len(remaining_products)} in partition {partition_num}: {product['name']}")
        
        # Generate image with true infinite retry
        image_path = generate_image_for_product(product)
        
        if image_path:
            success_count += 1
            
            # Update checkpoint - write after each successful image generation
            processed_ids.add(product["id"])
            try:
                with open(checkpoint_file, "w") as f:
                    json.dump({"processed_ids": list(processed_ids)}, f)
                logger.info(f"Updated checkpoint file with {len(processed_ids)} processed products")
            except Exception as e:
                logger.error(f"Error writing checkpoint: {e}")
        
        # Add a small delay between products to avoid rate limits
        time.sleep(1)
    
    total_processed = len(processed_ids)
    logger.info(f"Completed image generation for partition {partition_num}. Generated {success_count}/{len(remaining_products)} images this run.")
    logger.info(f"Total progress: {total_processed}/{len(products)} products processed ({total_processed/len(products)*100:.2f}%)")
    
    # Return True only if all products have been processed
    return total_processed == len(products)

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) < 3:
        logger.error("Usage: python generate_partition_images.py <partition_file> <partition_num>")
        sys.exit(1)
    
    partition_file = sys.argv[1]
    partition_num = sys.argv[2]
    
    # Check if API key is set in environment
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("Error: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)
    
    try:
        # Generate images for the partition
        success = generate_images_for_partition(partition_file, partition_num)
        
        if success:
            logger.info(f"Successfully generated all images for partition {partition_num}")
            # Exit with non-zero code to indicate we need to keep running
            # This ensures the runner script will restart us to check for any missed images
            sys.exit(1)
        else:
            logger.info(f"Not all images were generated for partition {partition_num}, will continue in next run")
            # Exit with non-zero code to ensure the runner script keeps retrying
            # This ensures we keep trying until ALL images are generated
            sys.exit(1)
    except Exception as e:
        # Catch any unexpected exceptions to prevent the script from crashing
        logger.error(f"Unexpected error in main: {e}")
        # Exit with non-zero code to ensure the runner script keeps retrying
        # This ensures we keep trying until ALL images are generated
        sys.exit(1)
'''
    
    with open(generator_script, "w") as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod(generator_script, 0o755)
    
    logger.info(f"Created image generator script at {generator_script}")
    return generator_script

def run_partitions(partition_files, runner_script):
    """Run image generation for all partitions in parallel."""
    processes = []
    
    for i, partition_file in enumerate(partition_files):
        partition_num = i + 1
        log_file = f"/tmp/image_generation_partition_{partition_num}.log"
        
        # Clear any existing log file
        with open(log_file, "w") as f:
            f.write(f"Starting image generation for partition {partition_num}\n")
        
        # Start the process
        cmd = f"{runner_script} {partition_file} {partition_num}"
        process = subprocess.Popen(cmd, shell=True)
        
        processes.append((process, partition_num, log_file))
        logger.info(f"Started process for partition {partition_num}")
        
        # Small delay to avoid starting all processes at exactly the same time
        time.sleep(1)
    
    return processes

def tail_logs(log_files):
    """Tail all log files."""
    cmd = "tail -f " + " ".join(log_files)
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    # Identify office supplies products
    office_products = identify_office_supplies()
    
    if not office_products:
        logger.error("No office supplies products found")
        sys.exit(1)
    
    # Partition products
    num_partitions = 10
    partitions = partition_products(office_products, num_partitions)
    
    # Save partitions to temporary files
    partition_files = save_partitions(partitions)
    
    # Create runner script
    runner_script = create_runner_script()
    
    # Create image generator script
    generator_script = create_image_generator_script()
    
    # Run partitions
    processes = run_partitions(partition_files, runner_script)
    
    # Collect log files
    log_files = [p[2] for p in processes]
    
    # Tail all log files
    logger.info(f"Tailing log files: {', '.join(log_files)}")
    tail_logs(log_files)
