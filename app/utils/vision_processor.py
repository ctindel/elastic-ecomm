#!/usr/bin/env python3
"""
Vision processing utilities for the E-Commerce Search Demo.
"""
import os
import sys
import json
import base64
import requests
import time
from typing import List, Dict, Any, Optional, Union
from fastapi import UploadFile
import logging
from pathlib import Path
import asyncio
import openai
import ollama

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger(__name__)

from app.config.settings import settings
from app.utils.embedding import get_image_embedding, get_text_embedding
from app.utils.search_agent import perform_search

# Import our custom logger
from app.utils.logger import logger

async def process_with_openai(image_file: UploadFile, contents: bytes) -> Dict[str, Any]:
    """
    Process an image using OpenAI's vision API.
    
    Args:
        image_file: The uploaded image file
        contents: The binary contents of the image file
        
    Returns:
        Dict containing the extracted items
    """
    logger.info(f"Processing image with OpenAI - File: {image_file.filename}, Size: {len(contents)} bytes")
    
    # Get API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment")
        raise ValueError("OpenAI API key not found in environment")
    
    # Convert to base64 for OpenAI API
    base64_image = base64.b64encode(contents).decode('utf-8')
    logger.debug("Successfully converted image to base64")
    
    client = openai.OpenAI(api_key=api_key)
    
    # Define the system prompt
    system_prompt = """
    You are an assistant that analyzes images of shopping lists or product requests.
    Extract all items from the image and return them in the following JSON format:
    {
        "items": [
            {
                "name": "item name",
                "quantity": "quantity (if specified)",
                "attributes": "any attributes like color, size, etc."
            }
        ]
    }
    Only include items that are clearly visible in the image. If quantities are specified, include them.
    """
    
    logger.debug("Sending request to OpenAI vision API...")
    
    # Make the API call
    response = client.chat.completions.create(
        model="gpt-4o",  # Using gpt-4o which supports vision
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What items are in this shopping list? Extract them according to the format."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_file.content_type.split('/')[-1]};base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )
    
    # Extract the JSON response
    content = response.choices[0].message.content
    logger.debug(f"Raw OpenAI response:\n{content}")
    
    # Extract JSON from the response (it might be wrapped in markdown code blocks)
    if "```json" in content:
        json_str = content.split("```json")[1].split("```")[0].strip()
        logger.debug("Extracted JSON from code block with 'json' tag")
    elif "```" in content:
        json_str = content.split("```")[1].strip()
        logger.debug("Extracted JSON from code block")
    else:
        json_str = content.strip()
        logger.debug("Using raw content as JSON")
    
    # Try to clean up the JSON string if it's not valid
    try:
        items_data = json.loads(json_str)
        logger.info(f"Successfully parsed response with {len(items_data.get('items', []))} items")
        logger.debug(f"Parsed items data:\n{json.dumps(items_data, indent=2)}")
        return items_data
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON response, attempting cleanup")
        
        # Sometimes the model returns extra text before or after the JSON
        # Try to find JSON-like structure with curly braces
        import re
        json_match = re.search(r'(\{.*\})', json_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            logger.debug("Found JSON-like structure in response")
            try:
                items_data = json.loads(json_str)
                logger.info(f"Successfully parsed cleaned response with {len(items_data.get('items', []))} items")
                logger.debug(f"Parsed items data:\n{json.dumps(items_data, indent=2)}")
                return items_data
            except json.JSONDecodeError:
                logger.error("Failed to parse cleaned JSON response")
        else:
            logger.error("Could not find JSON-like structure in response")
    
    # If all else fails, create a simple structure with the text as an item
    items_data = {
        "items": [
            {
                "name": "Unknown item from image",
                "quantity": "",
                "attributes": ""
            }
        ]
    }
    logger.warning(f"Using fallback structure. Raw content:\n{content}")
    return items_data

async def process_with_ollama(image_input: Union[UploadFile, str], contents: bytes) -> Dict[str, Any]:
    """
    Process an image using Ollama's llava vision model.
    
    Args:
        image_input: Either an UploadFile object or a file path string
        contents: The image file contents as bytes
        
    Returns:
        Dict containing the extracted items
    """
    logger.info(f"Processing with Ollama - Input: {image_input}")
    
    # Convert image to base64
    image_base64 = base64.b64encode(contents).decode('utf-8')
    
    # Construct prompt
    prompt = """Analyze this image and extract all visible items and their details.
    For each item, provide:
    1. A clear description
    2. The category it belongs to
    3. Any specific attributes (color, size, material, etc.)
    4. The brand if visible
    5. Any text visible on the item
    
    Format your response as a JSON object with an 'items' array containing each item's details."""
    
    # Make API call with retries
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = await ollama.chat(
                model=settings.OLLAMA_VISION_MODEL,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "image": image_base64}
                    ]}
                ]
            )
            
            # Extract and parse JSON from response
            content = response.message.content
            try:
                # Try to find JSON in the response
                json_str = content[content.find("{"):content.rfind("}")+1]
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from response, returning fallback structure")
                return {
                    "items": [{
                        "description": content,
                        "category": "unknown",
                        "attributes": [],
                        "brand": "unknown",
                        "text": ""
                    }]
                }
                
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error(f"Error processing image with Ollama: {str(e)}", exc_info=True)
                raise

async def process_image(image_file: UploadFile) -> Dict[str, Any]:
    """
    Process an image using the configured vision provider.
    
    Args:
        image_file: The uploaded image file
        
    Returns:
        Dict containing the extracted items
    """
    logger.info(f"Processing image - File: {image_file.filename}")
    
    # Read the file contents
    contents = await image_file.read()
    
    # Process based on configured provider
    if settings.VISION_PROVIDER == "openai":
        return await process_with_openai(image_file, contents)
    elif settings.VISION_PROVIDER == "ollama":
        return await process_with_ollama(image_file, contents)
    else:
        logger.error(f"Unsupported vision provider: {settings.VISION_PROVIDER}")
        raise ValueError(f"Unsupported vision provider: {settings.VISION_PROVIDER}")

async def process_image_from_path(image_path: str) -> Dict[str, Any]:
    """
    Process an image using the configured vision provider.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dict containing the extracted items
    """
    logger.info(f"Processing image - File: {image_path}")
    
    # Read the file contents
    with open(image_path, "rb") as f:
        contents = f.read()
    
    # Process based on configured provider
    if settings.VISION_PROVIDER == "openai":
        return await process_with_openai(image_path, contents)
    elif settings.VISION_PROVIDER == "ollama":
        return await process_with_ollama(image_path, contents)
    else:
        logger.error(f"Unsupported vision provider: {settings.VISION_PROVIDER}")
        raise ValueError(f"Unsupported vision provider: {settings.VISION_PROVIDER}")

async def process_image_query(image_path: str, query: str) -> Dict[str, Any]:
    """
    Process an image and perform a search query.
    
    Args:
        image_path: Path to the image file
        query: Search query
        
    Returns:
        Dict containing the search results
    """
    logger.info(f"Processing image query - File: {image_path}, Query: {query}")
    
    # Process the image
    items_data = await process_image_from_path(image_path)
    
    # Perform search
    results = await perform_search(query, SearchType.IMAGE)
    
    return {
        "items": items_data.get("items", []),
        "results": results
    }
