#!/usr/bin/env python3
"""
Test cases for image processing functionality.
"""
import os
import sys
import pytest
import json
from pathlib import Path
from elasticsearch import Elasticsearch

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.utils.image_processor import extract_text_from_image, analyze_school_supply_list
from app.config.settings import settings

# Skip all tests if OpenAI API key is not available
@pytest.fixture(scope="module")
def check_openai():
    """Check if OpenAI API key is available."""
    if not settings.OPENAI_API_KEY:
        pytest.skip("OpenAI API key is not available")

@pytest.fixture
def test_image():
    """Fixture for test image."""
    # Create a test image if it doesn't exist
    test_image_path = "data/images/test_school_supply_list.png"
    if not os.path.exists(test_image_path):
        from scripts.generate_test_image import generate_test_image
        test_image_path = generate_test_image()
    return test_image_path

def test_text_extraction(test_image, check_openai):
    """Test text extraction from an image."""
    # Extract text from the image
    extracted_text = extract_text_from_image(test_image)
    
    # Check if text was extracted
    assert extracted_text is not None
    assert len(extracted_text) > 0
    
    # Check if the text contains expected keywords
    expected_keywords = ["school", "supplies", "list"]
    for keyword in expected_keywords:
        assert keyword.lower() in extracted_text.lower()

def test_school_supply_list_analysis(test_image, check_openai):
    """Test school supply list analysis."""
    # Analyze the school supply list
    analysis = analyze_school_supply_list(test_image)
    
    # Check if analysis was successful
    assert analysis is not None
    assert "items" in analysis
    assert len(analysis["items"]) > 0
    
    # Check if each item has the required fields
    for item in analysis["items"]:
        assert "name" in item
        assert len(item["name"]) > 0
        
        # Check if quantity is present (optional)
        if "quantity" in item:
            assert isinstance(item["quantity"], (str, int))
        
        # Check if attributes are present (optional)
        if "attributes" in item:
            assert isinstance(item["attributes"], str)

def test_text_extraction_invalid_image():
    """Test text extraction with an invalid image."""
    # Try to extract text from a non-existent image
    with pytest.raises(Exception):
        extract_text_from_image("nonexistent_image.png")

def test_school_supply_list_analysis_invalid_image():
    """Test school supply list analysis with an invalid image."""
    # Try to analyze a non-existent image
    with pytest.raises(Exception):
        analyze_school_supply_list("nonexistent_image.png")
