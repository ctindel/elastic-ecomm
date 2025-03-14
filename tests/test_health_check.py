"""
Tests for the health check endpoint.
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.utils.validation import check_openai_connection

client = TestClient(app)

@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch client."""
    with patch("app.main.Elasticsearch") as mock_es:
        mock_instance = MagicMock()
        mock_instance.cluster.health.return_value = {
            "status": "green",
            "cluster_name": "test-cluster",
            "number_of_nodes": 1
        }
        mock_instance.indices.exists.return_value = True
        mock_instance.count.return_value = {"count": 100}
        mock_instance.indices.stats.return_value = {
            "indices": {
                "products": {
                    "total": {
                        "store": {
                            "size_in_bytes": 1000000
                        }
                    }
                }
            }
        }
        mock_instance.indices.get_mapping.return_value = {
            "products": {
                "mappings": {
                    "properties": {
                        "text_embedding": {
                            "type": "dense_vector"
                        }
                    }
                }
            }
        }
        mock_es.return_value = mock_instance
        yield mock_es

@pytest.fixture
def mock_check_ollama_connection():
    """Mock check_ollama_connection function."""
    with patch("app.utils.embedding.check_ollama_connection") as mock_check:
        mock_check.return_value = True
        yield mock_check

@pytest.fixture
def mock_check_openai_connection():
    """Mock check_openai_connection function."""
    with patch("app.utils.validation.check_openai_connection") as mock_check:
        mock_check.return_value = {
            "configured": True,
            "connected": True,
            "api_key_valid": True,
            "models_available": ["gpt-4", "gpt-3.5-turbo"],
            "error": None
        }
        yield mock_check

def test_health_check_success(mock_elasticsearch, mock_check_ollama_connection, mock_check_openai_connection):
    """Test successful health check."""
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = "test_key"
    
    # Make request to health check endpoint
    response = client.get("/health")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Check overall status
    assert data["status"] == "healthy"
    
    # Check Elasticsearch status
    assert data["elasticsearch"]["status"] == "green"
    assert data["elasticsearch"]["connection"] == True
    
    # Check Ollama status
    assert data["ollama"]["available"] == True
    
    # Check OpenAI status
    assert data["openai"]["configured"] == True
    assert data["openai"]["connected"] == True
    assert data["openai"]["api_key_valid"] == True

def test_health_check_elasticsearch_failure(mock_check_ollama_connection, mock_check_openai_connection):
    """Test health check with Elasticsearch failure."""
    # Mock Elasticsearch failure
    with patch("app.main.Elasticsearch") as mock_es:
        mock_es.side_effect = Exception("Connection refused")
        
        # Make request to health check endpoint
        response = client.get("/health")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check overall status
        assert data["status"] == "degraded"
        
        # Check Elasticsearch status
        assert data["elasticsearch"]["connection"] == False
        assert "error" in data["elasticsearch"]

def test_health_check_ollama_failure(mock_elasticsearch, mock_check_openai_connection):
    """Test health check with Ollama failure."""
    # Mock Ollama failure
    with patch("app.utils.embedding.check_ollama_connection") as mock_check:
        mock_check.return_value = False
        
        # Make request to health check endpoint
        response = client.get("/health")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check overall status
        assert data["status"] == "healthy"  # Elasticsearch is still up
        
        # Check Ollama status
        assert data["ollama"]["available"] == False

def test_health_check_openai_missing_key(mock_elasticsearch, mock_check_ollama_connection):
    """Test health check with missing OpenAI API key."""
    # Remove environment variable
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    
    # Mock OpenAI check
    with patch("app.utils.validation.check_openai_connection") as mock_check:
        mock_check.return_value = {
            "configured": False,
            "connected": False,
            "api_key_valid": False,
            "models_available": [],
            "error": "API key not configured"
        }
        
        # Make request to health check endpoint
        response = client.get("/health")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check OpenAI status
        assert data["openai"]["configured"] == False
        assert data["openai"]["connected"] == False
        assert data["openai"]["api_key_valid"] == False

def test_health_check_openai_invalid_key(mock_elasticsearch, mock_check_ollama_connection):
    """Test health check with invalid OpenAI API key."""
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = "invalid_key"
    
    # Mock OpenAI check
    with patch("app.utils.validation.check_openai_connection") as mock_check:
        mock_check.return_value = {
            "configured": True,
            "connected": True,
            "api_key_valid": False,
            "models_available": [],
            "error": "Invalid API key"
        }
        
        # Make request to health check endpoint
        response = client.get("/health")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check OpenAI status
        assert data["openai"]["configured"] == True
        assert data["openai"]["connected"] == True
        assert data["openai"]["api_key_valid"] == False
