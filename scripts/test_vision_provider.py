#!/usr/bin/env python3
"""
Test script to verify vision provider configuration and validation.
"""
import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import application modules
from app.utils.validation import check_vision_provider, check_openai_connection, check_ollama_vision_model
from app.config.settings import VISION_PROVIDER

def test_vision_provider_validation():
    """
    Test the vision provider validation functions.
    """
    print(f"Testing vision provider validation with VISION_PROVIDER={VISION_PROVIDER}")
    
    # Test OpenAI configuration
    print("\n=== Testing OpenAI Configuration ===")
    openai_status = check_openai_connection()
    print(f"OpenAI configured: {openai_status['configured']}")
    print(f"OpenAI API key valid: {openai_status['api_key_valid']}")
    if openai_status['error']:
        print(f"OpenAI error: {openai_status['error']}")
    
    # Test Ollama configuration
    print("\n=== Testing Ollama Configuration ===")
    ollama_status = check_ollama_vision_model()
    print(f"Ollama available: {ollama_status['available']}")
    print(f"Ollama vision model installed: {ollama_status['model_installed']}")
    if ollama_status['error']:
        print(f"Ollama error: {ollama_status['error']}")
    
    # Test current vision provider
    print("\n=== Testing Current Vision Provider ===")
    vision_status = check_vision_provider()
    print(f"Vision provider: {vision_status['provider']}")
    print(f"Vision provider available: {vision_status['available']}")
    if vision_status['error']:
        print(f"Vision provider error: {vision_status['error']}")
    
    # Test with different vision provider
    print("\n=== Testing with Different Vision Provider ===")
    original_provider = os.environ.get("VISION_PROVIDER", VISION_PROVIDER)
    
    # Test with OpenAI
    os.environ["VISION_PROVIDER"] = "openai"
    vision_status = check_vision_provider()
    print(f"OpenAI as provider - Available: {vision_status['available']}")
    if vision_status['error']:
        print(f"OpenAI as provider - Error: {vision_status['error']}")
    
    # Test with Ollama
    os.environ["VISION_PROVIDER"] = "ollama"
    vision_status = check_vision_provider()
    print(f"Ollama as provider - Available: {vision_status['available']}")
    if vision_status['error']:
        print(f"Ollama as provider - Error: {vision_status['error']}")
    
    # Restore original provider
    if original_provider:
        os.environ["VISION_PROVIDER"] = original_provider
    else:
        os.environ.pop("VISION_PROVIDER", None)

if __name__ == "__main__":
    test_vision_provider_validation()
