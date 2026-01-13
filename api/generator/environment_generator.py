"""
Environment Profile Generator - Feature #3

Generates environment-specific configuration files.

Rules:
- Profiles must be explicitly selected by user
- No cloud provider assumptions
- No auto-deployment
- All generation is template-based and deterministic
"""
from typing import Dict, Any


def generate_dockerfile(cps_data: Dict[str, Any]) -> str:
    """
    Generate Dockerfile only if explicitly requested.
    
    Args:
        cps_data: CPS model as dictionary
        
    Returns:
        Dockerfile content as string
        
    Raises:
        ValueError: If Dockerfile generation not enabled
    """
    environment = cps_data.get("environment", {})
    if not environment.get("generate_dockerfile"):
        raise ValueError(
            "Dockerfile generation not enabled in CPS. "
            "Set environment.generate_dockerfile to true to enable."
        )
    
    project_name = cps_data.get("project_name", "app")
    features = cps_data.get("features", {})
    
    dockerfile = f'''# Generated Dockerfile for {project_name}
# Environment: {environment.get("type", "docker")}
# 
# This Dockerfile is deterministically generated from CPS.
# Modify CPS to change the configuration.

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Feature flags from CPS (deterministic)
ENV FEATURE_CHAT={"true" if features.get("chat") else "false"}
ENV FEATURE_RAG={"true" if features.get("rag") else "false"}
ENV FEATURE_STREAMING={"true" if features.get("streaming") else "false"}
ENV FEATURE_EMBEDDINGS={"true" if features.get("embeddings") else "false"}

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
    return dockerfile


def generate_docker_compose(cps_data: Dict[str, Any]) -> str:
    """
    Generate docker-compose.yml only if explicitly requested.
    
    Args:
        cps_data: CPS model as dictionary
        
    Returns:
        docker-compose.yml content as string
        
    Raises:
        ValueError: If Docker Compose generation not enabled
    """
    environment = cps_data.get("environment", {})
    if not environment.get("generate_compose"):
        raise ValueError(
            "Docker Compose generation not enabled in CPS. "
            "Set environment.generate_compose to true to enable."
        )
    
    project_name = cps_data.get("project_name", "app").lower().replace(" ", "_")
    features = cps_data.get("features", {})
    
    compose = f'''# Generated docker-compose.yml for {project_name}
# Environment: {environment.get("type", "docker")}
#
# This file is deterministically generated from CPS.
# Modify CPS to change the configuration.

version: "3.8"

services:
  {project_name}:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - FEATURE_CHAT={"true" if features.get("chat") else "false"}
      - FEATURE_RAG={"true" if features.get("rag") else "false"}
      - FEATURE_STREAMING={"true" if features.get("streaming") else "false"}
      - FEATURE_EMBEDDINGS={"true" if features.get("embeddings") else "false"}
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
'''
    
    # Add vector store service for RAG mode
    if features.get("rag") and cps_data.get("vector_store"):
        vector_store = cps_data.get("vector_store", "").lower()
        if "chroma" in vector_store:
            compose += f'''
  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma

volumes:
  chroma_data:
'''
    
    return compose


def generate_env_template(cps_data: Dict[str, Any]) -> str:
    """
    Generate environment variable template file.
    
    Args:
        cps_data: CPS model as dictionary
        
    Returns:
        .env.example content as string
    """
    features = cps_data.get("features", {})
    llm_provider = cps_data.get("llm_provider", {})
    environment = cps_data.get("environment", {})
    
    # Determine provider type
    if isinstance(llm_provider, str):
        provider_type = llm_provider
    else:
        provider_type = llm_provider.get("type", "openai")
    
    env_content = f'''# Environment Configuration for {cps_data.get("project_name", "API")}
# Environment Type: {environment.get("type", "local")}
#
# This file is generated from CPS. Copy to .env and fill in values.

# =============================================================================
# LLM Provider Configuration
# =============================================================================
'''
    
    if provider_type == "openai":
        env_content += '''
# OpenAI API Key (required)
OPENAI_API_KEY=your_api_key_here
'''
    elif provider_type == "azure_openai":
        env_content += '''
# Azure OpenAI Configuration (required)
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
'''
    elif provider_type == "local":
        env_content += '''
# Local LLM Configuration
# NOTE: LocalProvider is a placeholder. Configure your local LLM here.
LOCAL_LLM_ENDPOINT=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama2
'''
    
    # Feature-specific env vars
    if features.get("rag"):
        env_content += '''
# =============================================================================
# RAG Configuration
# =============================================================================

# Vector store connection
DATABASE_URL=sqlite:///./data.db

# Embedding configuration
EMBEDDING_MODEL=text-embedding-3-small
'''
    
    env_content += '''
# =============================================================================
# Feature Flags (set by CPS, override if needed)
# =============================================================================

'''
    env_content += f'''FEATURE_CHAT={"true" if features.get("chat") else "false"}
FEATURE_RAG={"true" if features.get("rag") else "false"}
FEATURE_STREAMING={"true" if features.get("streaming") else "false"}
FEATURE_EMBEDDINGS={"true" if features.get("embeddings") else "false"}
'''
    
    return env_content


def generate_production_config(cps_data: Dict[str, Any]) -> str:
    """
    Generate production configuration notes.
    
    This does NOT configure any specific cloud provider.
    It provides generic production guidance.
    """
    environment = cps_data.get("environment", {})
    if environment.get("type") != "production":
        raise ValueError(
            "Production config generation requires environment.type to be 'production'"
        )
    
    project_name = cps_data.get("project_name", "API")
    features = cps_data.get("features", {})
    
    config = f'''# Production Configuration Notes for {project_name}
#
# This file provides generic production deployment guidance.
# No specific cloud provider is assumed.

## Required Environment Variables

The following environment variables MUST be set in your production environment:

'''
    
    # List required env vars based on features
    llm_provider = cps_data.get("llm_provider", {})
    if isinstance(llm_provider, str):
        provider_type = llm_provider
    else:
        provider_type = llm_provider.get("type", "openai")
    
    if provider_type == "openai":
        config += "- `OPENAI_API_KEY`: Your OpenAI API key\n"
    elif provider_type == "azure_openai":
        config += """- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Your deployment name
"""
    
    if features.get("rag"):
        config += "- `DATABASE_URL`: Production database connection string\n"
    
    config += '''
## Security Checklist

- [ ] API keys are stored securely (not in code)
- [ ] HTTPS is enabled
- [ ] CORS is properly configured
- [ ] Rate limiting is enabled
- [ ] Logging is configured
- [ ] Health checks are in place

## Scaling Considerations

- Stateless design allows horizontal scaling
- Consider connection pooling for database
- Use CDN for static assets if applicable
'''
    
    return config
