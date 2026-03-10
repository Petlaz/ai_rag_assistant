# Ollama Integration

This module provides seamless integration with Ollama for local LLM inference, featuring automatic model fallback, health monitoring, and optimized error handling.

## Overview

The Ollama integration enables cost-effective, privacy-focused language model operations by running models locally while maintaining production-grade reliability and performance.

## Features

- **Multi-Model Support**: Primary and fallback model configuration
- **Health Monitoring**: Real-time connection status and latency tracking
- **Automatic Fallback**: Smart switching between models on failures
- **Timeout Management**: Configurable request timeouts with graceful handling
- **Error Recovery**: Robust error handling with detailed logging

## Supported Models

### Recommended Models
- **mistral**: General-purpose, balanced performance
- **gemma3:1b**: Lightweight, fast responses
- **phi3:mini**: Ultra-low memory usage

### Memory Requirements
- **8GB RAM**: phi3:mini, gemma3:1b recommended
- **16GB RAM**: mistral, llama3 supported
- **32GB+ RAM**: All models with optimal performance

## Configuration

### Environment Variables

```bash
# Primary model for responses
OLLAMA_MODEL=mistral

# Fallback model (optional)
OLLAMA_FALLBACK_MODEL=phi3:mini

# Request timeout in seconds
OLLAMA_TIMEOUT=120

# Ollama server endpoint
OLLAMA_BASE_URL=http://localhost:11434
```

### Model Installation

```bash
# Install recommended models
ollama pull mistral
ollama pull gemma3:1b
ollama pull phi3:mini

# Verify installation
ollama list
```

## Usage

### Basic Client Usage

```python
from llm_ollama.client import OllamaClient

# Initialize client
client = OllamaClient(
    model="mistral",
    fallback_model="phi3:mini",
    timeout=120
)

# Generate response
response = client.chat([
    {"role": "user", "content": "Explain quantum computing"}
])
```

### Adapter Integration

```python
from llm_ollama.adapters import OllamaChatAdapter

# Initialize adapter
adapter = OllamaChatAdapter(
    primary_model="mistral",
    fallback_model="phi3:mini"
)

# Health check
status = adapter.health_check()
print(f"Status: {status['status']}")
```

## Health Monitoring

The integration provides comprehensive health monitoring:

- **Connection Status**: Real-time Ollama server connectivity
- **Model Availability**: Verification of installed models
- **Latency Tracking**: Response time monitoring with thresholds
- **Automatic Recovery**: Smart fallback on model failures

## Performance Optimization

### Response Caching
- Aggressive 24-hour caching for repeated queries
- Cache key generation based on prompt content
- Automatic cache invalidation

### Memory Management
- Model switching based on available memory
- Garbage collection optimization
- Connection pooling for sustained usage

## Error Handling

### Connection Errors
- Automatic retry with exponential backoff
- Fallback model activation on primary model failures
- Graceful degradation with informative error messages

### Timeout Management
- Configurable timeout thresholds
- Progressive timeout increases for heavy queries
- User-friendly timeout notifications

## Production Deployment

### Docker Configuration
```yaml
environment:
  - OLLAMA_MODEL=mistral
  - OLLAMA_FALLBACK_MODEL=phi3:mini
  - OLLAMA_TIMEOUT=120
  - OLLAMA_BASE_URL=http://ollama:11434
```

### Monitoring Integration
- Health check endpoints for load balancers
- Metrics export for monitoring systems
- Structured logging for observability

## Troubleshooting

### Common Issues

**Connection Refused**
```bash
# Verify Ollama is running
ollama list
systemctl status ollama  # Linux
brew services list | grep ollama  # macOS
```

**Model Not Found**
```bash
# Install missing models
ollama pull mistral
ollama pull phi3:mini
```

**Memory Issues**
```bash
# Check available memory
free -h  # Linux
vm_stat | head -5  # macOS

# Switch to lighter model
export OLLAMA_MODEL=phi3:mini
```

### Performance Tuning

**For Development**
- Use phi3:mini for fastest iteration
- Enable aggressive caching
- Set shorter timeouts (60s)

**For Production**
- Use mistral for quality responses
- Implement proper fallback chains
- Monitor response latencies

## Integration Points

### RAG Pipeline
- Seamless integration with retrieval components
- Context-aware prompt formatting
- Citation handling and source attribution

### Gradio Interface
- Real-time health status display
- Model switching in UI settings
- User-friendly error messaging

### AWS Deployment
- Lambda-compatible configurations
- Container deployment support
- Auto-scaling considerations

## Development Notes

### Testing
```bash
# Run integration tests
python -m pytest tests/test_ollama_client.py

# Test model availability
 
```

### Debugging
```python
import logging
logging.getLogger('llm_ollama').setLevel(logging.DEBUG)
```

## Security Considerations

- Local model execution (no external API calls)
- No data transmission to third parties
- Configurable request validation
- Rate limiting support

## Future Enhancements

- Multi-GPU support for larger models
- Advanced caching strategies
- Model performance analytics
- Automated model updates
