#!/usr/bin/env python3
"""
Script to generate all synthetic data for the e-commerce search demo.
This script orchestrates the execution of specialized data generation scripts.
"""
import os
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def run_script(script_path):
    """Run a Python script and return its exit code."""
    logger.info(f"Running script: {script_path}")
    
    try:
        result = subprocess.run(
            ["python", script_path],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Script {script_path} completed successfully")
        logger.debug(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_path} failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return e.returncode

def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        "data",
        "data/images",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def main():
    """Main function to generate all synthetic data."""
    logger.info("Starting synthetic data generation")
    
    # Ensure required directories exist
    ensure_directories()
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Define the scripts to run in order
    scripts = [
        script_dir / "generate_products.py",
        script_dir / "generate_personas.py",
        script_dir / "generate_queries.py"
    ]
    
    # Run each script
    for script in scripts:
        exit_code = run_script(script)
        if exit_code != 0:
            logger.error(f"Data generation failed at script: {script}")
            return exit_code
    
    logger.info("All synthetic data generated successfully")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
