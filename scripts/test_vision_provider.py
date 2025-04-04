#!/usr/bin/env python3
"""
Script to test the vision provider configuration.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.validation import check_vision_provider
from app.config.settings import settings

def main():
    """Main function."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    
    # Check vision provider
    logger.info(f"Testing vision provider: {settings.VISION_PROVIDER}")
    
    # Check if vision provider is available
    vision_status = check_vision_provider()
    if vision_status["available"]:
        logger.info(f"✅ Vision provider '{settings.VISION_PROVIDER}' is available")
        return 0
    else:
        logger.error(f"❌ Vision provider '{settings.VISION_PROVIDER}' is not available: {vision_status['error']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
