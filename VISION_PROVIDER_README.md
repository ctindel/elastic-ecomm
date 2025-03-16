# Vision Provider Configuration

The Elastic E-Commerce application supports multiple vision providers for processing image uploads. This allows you to choose between different AI services for OCR and image analysis.

## Available Providers

Currently, the application supports the following vision providers:

1. **OpenAI** (default) - Uses OpenAI's GPT-4o model for image analysis
2. **Ollama** - Uses Ollama's llava:34b model for local image analysis

## Configuration

You can configure the vision provider using environment variables:

```bash
# Set the vision provider (options: "openai" or "ollama")
export VISION_PROVIDER=openai

# If using Ollama, you can specify the vision model
export OLLAMA_VISION_MODEL=llava:34b
```

## Requirements

### OpenAI Provider

- Requires a valid OpenAI API key set in the `OPENAI_API_KEY` environment variable
- Internet connection to access OpenAI's API

### Ollama Provider

- Requires Ollama to be installed and running locally
- The llava:34b model must be installed in Ollama
- To install the model: `ollama pull llava:34b`

## Health Check

You can check the status of the configured vision provider by accessing the `/health` endpoint, which will show:

```json
{
  "vision": {
    "provider": "openai",
    "available": true,
    "error": null
  }
}
```

## Fallback Behavior

If the configured vision provider is not available, the application will:

1. Log an error message
2. Return a 503 Service Unavailable response when attempting to use image upload features
3. Continue to function for text-based search features

