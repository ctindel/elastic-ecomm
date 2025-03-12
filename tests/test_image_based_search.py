#!/usr/bin/env python3
"""
Test cases for image-based search functionality.
"""
import os
import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import UploadFile
import asyncio
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app
from app.utils.image_processor import process_image_query, extract_text_from_image, analyze_school_supply_list
from app.models.search import SearchResult, SearchType
from app.config.settings import OPENAI_API_KEY

# Create a test client
client = TestClient(app)

# Path to test image
TEST_IMAGE_PATH = "data/images/test_school_supply_list.png"

@pytest.fixture
def test_image():
    """Fixture to ensure test image exists."""
    if not os.path.exists(TEST_IMAGE_PATH):
        pytest.skip(f"Test image not found: {TEST_IMAGE_PATH}")
    return TEST_IMAGE_PATH

def test_extract_text_from_image(test_image):
    """Test text extraction from an image."""
    # Skip if OpenAI API key is not available
    if not OPENAI_API_KEY:
        pytest.skip("OpenAI API key not available")
    
    # Extract text from the image
    extracted_text = extract_text_from_image(test_image)
    
    # Check if text was extracted
    assert extracted_text is not None
    assert len(extracted_text) > 0
    
    # Check if the extracted text contains expected content
    assert "Notebooks" in extracted_text or "notebooks" in extracted_text.lower()
    assert "Pencils" in extracted_text or "pencils" in extracted_text.lower()

def test_analyze_school_supply_list(test_image):
    """Test school supply list analysis."""
    # Skip if OpenAI API key is not available
    if not OPENAI_API_KEY:
        pytest.skip("OpenAI API key not available")
    
    # Analyze the school supply list
    analysis = analyze_school_supply_list(test_image)
    
    # Check if analysis was performed
    assert analysis is not None
    assert "items" in analysis
    assert len(analysis["items"]) > 0
    
    # Check if items have the expected structure
    for item in analysis["items"]:
        assert "name" in item
        if "alternatives" in item:
            for alt in item["alternatives"]:
                assert "price_tier" in alt
                assert "product" in alt

@pytest.mark.asyncio
async def test_process_image_query():
    """Test processing an image query."""
    # Skip if OpenAI API key is not available
    if not OPENAI_API_KEY:
        pytest.skip("OpenAI API key not available")
    
    # Skip if test image doesn't exist
    if not os.path.exists(TEST_IMAGE_PATH):
        pytest.skip(f"Test image not found: {TEST_IMAGE_PATH}")
    
    # Create a mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_school_supply_list.png"
    
    # Mock the file read method to return the actual file content
    async def mock_read():
        with open(TEST_IMAGE_PATH, "rb") as f:
            return f.read()
    
    mock_file.read = mock_read
    
    # Process the image query
    results = await process_image_query(mock_file)
    
    # Check if results were returned
    assert results is not None
    assert isinstance(results, list)
    
    # If results were found, check their structure
    if results:
        for result in results:
            assert isinstance(result, SearchResult)
            assert hasattr(result, "query")
            assert hasattr(result, "product_name")

def test_image_upload_api_validation():
    """Test API validation for image upload."""
    # Test with no file
    response = client.post("/api/search/image")
    assert response.status_code == 422  # Unprocessable Entity
    
    # Test with invalid file type
    with open("requirements.txt", "rb") as f:
        response = client.post(
            "/api/search/image",
            files={"image_file": ("requirements.txt", f, "text/plain")}
        )
        assert response.status_code in [400, 422]  # Bad Request or Unprocessable Entity

@pytest.mark.skipif(not OPENAI_API_KEY, reason="OpenAI API key not available")
def test_image_upload_api_with_mock():
    """Test the image upload API with mock data."""
    # Create a patch for the process_image_query function
    with patch("app.api.search.process_image_query") as mock_process:
        # Set up the mock to return a list of search results
        mock_results = [
            SearchResult(
                query="Notebooks",
                product_id="123",
                product_name="College Ruled Notebooks",
                product_description="Pack of 5 college ruled notebooks",
                price=12.99,
                image_url="http://example.com/notebook.jpg",
                score=0.95,
                search_type=SearchType.IMAGE,
                alternatives=[
                    {"price_tier": "budget", "product": "Generic Notebooks"},
                    {"price_tier": "premium", "product": "Moleskine Notebooks"}
                ]
            )
        ]
        mock_process.return_value = mock_results
        
        # Test with a valid image file
        with open(TEST_IMAGE_PATH, "rb") as f:
            response = client.post(
                "/api/search/image",
                files={"image_file": ("test_image.png", f, "image/png")}
            )
            
            # Check if the API call was successful
            assert response.status_code == 200
            
            # Check if the response contains the expected data
            data = response.json()
            # The API returns a list of search results directly
            assert isinstance(data, list)
            assert len(data) > 0
            assert "product_name" in data[0]
            assert "alternatives" in data[0]

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
