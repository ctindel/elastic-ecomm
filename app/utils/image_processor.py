#!/usr/bin/env python3
"""
Image processing utilities for the E-Commerce Search Demo.
"""
import os
import sys
import json
import logging
import requests
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import UploadFile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from app.config.settings import (
    OPENAI_API_KEY,
    OPENAI_API_URL,
    ELASTICSEARCH_INDEX_PRODUCTS
)
from app.models.search import SearchResult, SearchType

async def process_image_query(
    image_file: UploadFile,
    user_id: Optional[str] = None,
    limit: int = 10,
    elasticsearch_client = None
) -> List[SearchResult]:
    """
    Process an image query (e.g., school supply list) and return relevant product suggestions.
    
    Args:
        image_file: Uploaded image file
        user_id: User ID for personalization
        limit: Maximum number of results to return
        elasticsearch_client: Elasticsearch client
    
    Returns:
        List[SearchResult]: List of search results
    """
    try:
        # Save the uploaded image to a temporary file
        temp_file_path = f"/tmp/{image_file.filename}"
        with open(temp_file_path, "wb") as f:
            content = await image_file.read()
            f.write(content)
        
        # Extract text from the image
        extracted_text = extract_text_from_image(temp_file_path)
        
        # Analyze the extracted text
        if "school" in extracted_text.lower() and "supply" in extracted_text.lower():
            # This appears to be a school supply list
            analysis = analyze_school_supply_list(temp_file_path)
            
            # Convert analysis to search results
            results = []
            for item in analysis.get("items", []):
                result = SearchResult(
                    query=item.get("name", ""),
                    product_id=f"school-supply-{len(results)}",
                    product_name=item.get("name", ""),
                    price=item.get("price", 0.0),
                    image_url=item.get("image_url", ""),
                    score=1.0,
                    search_type=SearchType.IMAGE,
                    alternatives=item.get("alternatives", []),
                    explanation=f"Found on school supply list: {item.get('name', '')}"
                )
                results.append(result)
            
            # Clean up
            os.remove(temp_file_path)
            
            return results[:limit]
        
        # For other types of images, perform a general search
        # This is a placeholder for future implementation
        results = []
        
        # Clean up
        os.remove(temp_file_path)
        
        return results
    
    except Exception as e:
        logger.error(f"Error processing image query: {str(e)}")
        return []

def extract_text_from_image(image_path):
    """
    Extract text from an image using OpenAI's API.
    
    Args:
        image_path: Path to image file
    
    Returns:
        str: Extracted text
    """
    try:
        # Check if OpenAI API key is available
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key is missing")
            return ""
        
        # Read image file
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Encode image data as base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        # Call OpenAI API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this image. Return only the extracted text, nothing else."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }
        
        response = requests.post(
            f"{OPENAI_API_URL}/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"Error calling OpenAI API: {response.text}")
            return ""
        
        # Parse response
        result = response.json()
        extracted_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return extracted_text
    
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        return ""

def analyze_school_supply_list(image_path):
    """
    Analyze a school supply list image and identify required items.
    
    Args:
        image_path: Path to image file
    
    Returns:
        dict: Analysis results
    """
    try:
        # Check if OpenAI API key is available
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key is missing")
            return {"items": []}
        
        # Read image file
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Encode image data as base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        # Call OpenAI API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        
        prompt = """
        Analyze this school supply list image and identify all required items.
        For each item, provide:
        1. The name of the item
        2. The quantity required
        3. Any specific requirements (e.g., color, size)
        4. Alternative options at different price points (budget, mid-range, premium)
        
        Return the results as a JSON object with the following structure:
        {
            "items": [
                {
                    "name": "Item name",
                    "quantity": "Quantity",
                    "requirements": "Specific requirements",
                    "alternatives": [
                        {"price_tier": "budget", "product": "Budget option"},
                        {"price_tier": "mid-range", "product": "Mid-range option"},
                        {"price_tier": "premium", "product": "Premium option"}
                    ]
                }
            ]
        }
        """
        
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000
        }
        
        response = requests.post(
            f"{OPENAI_API_URL}/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"Error calling OpenAI API: {response.text}")
            return {"items": []}
        
        # Parse response
        result = response.json()
        analysis_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Extract JSON from response
        import re
        json_match = re.search(r'```json\n(.*?)\n```', analysis_text, re.DOTALL)
        if json_match:
            analysis_json = json_match.group(1)
        else:
            analysis_json = analysis_text
        
        # Parse JSON
        try:
            analysis = json.loads(analysis_json)
        except json.JSONDecodeError:
            logger.error(f"Error parsing analysis JSON: {analysis_json}")
            return {"items": []}
        
        return analysis
    
    except Exception as e:
        logger.error(f"Error analyzing school supply list: {str(e)}")
        return {"items": []}
