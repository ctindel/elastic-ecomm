"""
Tests for the validation functionality.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from app.utils.validation import validate_api_keys

@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch client."""
    with patch("app.utils.validation.Elasticsearch") as mock_es:
        mock_instance = MagicMock()
        mock_instance.ping.return_value = True
        mock_es.return_value = mock_instance
        yield mock_es

@pytest.fixture
def mock_requests():
    """Mock requests module."""
    with patch("app.utils.validation.requests") as mock_req:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_req.get.return_value = mock_response
        yield mock_req

def test_validate_api_keys_success(mock_elasticsearch, mock_requests):
    """Test successful API key validation."""
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = "test_key"
    
    # Should not raise an exception
    validate_api_keys()
    
    # Verify Elasticsearch and Ollama connections were checked
    mock_elasticsearch.assert_called_once()
    mock_requests.get.assert_called_once()

def test_validate_api_keys_missing_openai(mock_elasticsearch, mock_requests):
    """Test validation with missing OpenAI API key."""
    # Remove environment variable
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    
    # Should not raise an exception, but log a warning
    with patch("app.utils.validation.logger.warning") as mock_warning:
        validate_api_keys()
        mock_warning.assert_called_once()

def test_validate_api_keys_elasticsearch_failure(mock_requests):
    """Test validation with Elasticsearch connection failure."""
    # Mock Elasticsearch failure
    with patch("app.utils.validation.Elasticsearch") as mock_es:
        mock_instance = MagicMock()
        mock_instance.ping.return_value = False
        mock_es.return_value = mock_instance
        
        # Should raise an exception
        with pytest.raises(Exception) as excinfo:
            validate_api_keys()
        
        assert "Elasticsearch connection failed" in str(excinfo.value)

def test_validate_api_keys_ollama_failure(mock_elasticsearch):
    """Test validation with Ollama connection failure."""
    # Mock requests failure
    with patch("app.utils.validation.requests") as mock_req:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_req.get.return_value = mock_response
        
        # Should raise an exception
        with pytest.raises(Exception) as excinfo:
            validate_api_keys()
        
        assert "Ollama connection failed" in str(excinfo.value)
