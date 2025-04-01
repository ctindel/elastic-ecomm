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
from typing import List, Dict, Any, Optional
from fastapi import UploadFile

# Import our custom logger
from app.utils.logger import logger

from app.config.settings import (
    VISION_PROVIDER,
    OLLAMA_VISION_MODEL,
    OLLAMA_API_URL
)

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
    import openai
    
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

async def process_with_ollama(image_file: UploadFile, contents: bytes) -> Dict[str, Any]:
    """
    Process an image using Ollama's llava vision model.
    
    Args:
        image_file: The uploaded image file
        contents: The binary contents of the image file
        
    Returns:
        Dict containing the extracted items
    """
    logger.info(f"Processing image with Ollama - File: {image_file.filename}, Size: {len(contents)} bytes")
    
    # Convert to base64 for Ollama API
    base64_image = base64.b64encode(contents).decode('utf-8')
    logger.debug("Successfully converted image to base64")
    
    # Define the system prompt
    prompt = f"""
    You are an assistant that analyzes images of shopping lists or product requests.
    Extract all items from the image and return them in the following JSON format:
    {{
        "items": [
            {{
                "name": "item name",
                "quantity": "quantity (if specified)",
                "attributes": "any attributes like color, size, etc."
            }}
        ]
    }}
    Only include items that are clearly visible in the image. If quantities are specified, include them.
    
    <image>
    data:image/{image_file.content_type.split('/')[-1]};base64,{base64_image}
    </image>
    
    What items are in this shopping list? Extract them according to the format.
    """
    
    # Retry parameters
    retry_delay = 5
    max_delay = 60
    retries = 0
    
    while True:  # True infinite retry - will never give up
        try:
            logger.debug(f"Sending request to Ollama API (model: {OLLAMA_VISION_MODEL})...")
            # Call Ollama API
            response = requests.post(
                OLLAMA_API_URL,
                json={
                    "model": OLLAMA_VISION_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                # Parse response
                result = response.json()
                content = result.get("response", "")
                logger.debug(f"Raw Ollama response:\n{content}")
                
                # Extract JSON from the response (it might be wrapped in markdown code blocks)
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    logger.debug("Extracted JSON from code block with 'json' tag")
                elif "```" in content:
                    json_str = content.split("```")[1].strip()
                    logger.debug("Extracted JSON from code block")
                else:
                    # Try to find JSON-like structure with curly braces
                    import re
                    json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        logger.debug("Found JSON-like structure in response")
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
                    logger.warning("Failed to parse JSON response")
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
            else:
                retries += 1
                logger.error(f"Error calling Ollama API: Status {response.status_code}\nResponse: {response.text}")
                # Calculate delay with exponential backoff and jitter, capped at max_delay
                import random
                delay = min(retry_delay * (2 ** (retries - 1)) * (0.5 + random.random()), max_delay)
                logger.error(f"Ollama is not available. Retrying image processing (attempt {retries}, waiting {delay:.2f}s)")
                time.sleep(delay)
        
        except Exception as e:
            retries += 1
            logger.error(f"Error processing image with Ollama: {str(e)}", exc_info=True)
            # Calculate delay with exponential backoff and jitter, capped at max_delay
            import random
            delay = min(retry_delay * (2 ** (retries - 1)) * (0.5 + random.random()), max_delay)
            logger.error(f"Ollama is not available. Retrying image processing (attempt {retries}, waiting {delay:.2f}s)")
            time.sleep(delay)

async def process_image(image_file: UploadFile) -> Dict[str, Any]:
    """
    Process an image using the configured vision provider.
    
    Args:
        image_file: The uploaded image file
        
    Returns:
        Dict containing the extracted items
    """
    logger.info(f"Processing image with {VISION_PROVIDER} provider - File: {image_file.filename}")
    
    # Read the image file
    contents = await image_file.read()
    logger.debug(f"Read {len(contents)} bytes from image file")
    
    # Process with the configured provider
    if VISION_PROVIDER == "openai":
        logger.debug("Using OpenAI vision provider")
        return await process_with_openai(image_file, contents)
    elif VISION_PROVIDER == "ollama":
        logger.debug("Using Ollama vision provider")
        return await process_with_ollama(image_file, contents)
    else:
        error_msg = f"Unknown vision provider: {VISION_PROVIDER}"
        logger.error(error_msg)
        raise ValueError(error_msg)
