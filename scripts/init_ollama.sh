#!/bin/bash
# Initialize Ollama with required models for the Elastic E-Commerce Demo

set -e

echo "Initializing Ollama with required models..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Error: Ollama is not installed."
    echo "Please install Ollama first: https://ollama.ai/download"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/health &> /dev/null; then
    echo "Error: Ollama is not running."
    echo "Please start Ollama first and try again."
    exit 1
fi

# Pull required models
echo "Pulling llama3 model for text embeddings and query classification..."
ollama pull llama3

echo "Pulling llava:34b model for vision processing..."
ollama pull llava:34b

# Verify models were installed
echo "Verifying installed models..."
MODELS=$(curl -s http://localhost:11434/api/tags)

if echo "$MODELS" | grep -q "llama3"; then
    echo "✅ llama3 model installed successfully"
else
    echo "❌ Failed to install llama3 model"
    exit 1
fi

if echo "$MODELS" | grep -q "llava:34b"; then
    echo "✅ llava:34b model installed successfully"
else
    echo "❌ Failed to install llava:34b model"
    exit 1
fi

echo "Ollama initialization complete! The following models are now available:"
echo "- llama3: Used for text embeddings and query classification"
echo "- llava:34b: Used for vision processing (when VISION_PROVIDER=ollama)"

echo ""
echo "To use Ollama for vision processing, set the following environment variable:"
echo "export VISION_PROVIDER=ollama"
