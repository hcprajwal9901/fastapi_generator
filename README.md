# FastAPI Generator v2.0

An AI-powered tool that generates production-ready FastAPI projects from natural language descriptions.

## Features

### Core Features
- **AI-Powered Analysis**: Describe your project idea, and the AI extracts a structured specification (CPS).
- **Dynamic Code Generation**: Automatically generates project files tailored to your requirements.
- **Multi-Module Support**: Creates separate API modules based on your domain (e.g., users, billing, analytics).
- **RAG Support**: Specialized templates for Retrieval-Augmented Generation projects.
- **Review & Fix**: Iterate on generated code with natural language feedback.
- **ZIP Export**: Download your complete project as a ZIP file.

### v2.0 Enhancements

#### 1. Contract-First (OpenAPI) Mode
Generate an OpenAPI 3.0 specification before code generation:
- OpenAPI spec derived strictly from CPS (no inference)
- JSON and YAML format output
- Preview endpoint: `POST /api/openapi-preview`

#### 2. LLM Token & Cost Estimation
Pre-generation analysis of estimated costs:
- Token usage estimates per request type
- Monthly cost projections (informational only)
- Clear disclaimers that estimates are not guaranteed

#### 3. Environment & Deployment Profiles
Support for different deployment environments:
- **local**: Development configuration
- **docker**: Dockerfile and docker-compose.yml generation
- **production**: Production-ready configuration templates

#### 4. Pluggable LLM Provider Abstraction
Swap between different LLM providers:
- OpenAI (default)
- Azure OpenAI
- Local (placeholder for custom implementations)

#### 5. Editable Prompt Templates
All prompts moved to editable files:
- `api/prompts/chat.txt`: Chat system prompt
- `api/prompts/rag.txt`: RAG system prompt
- `api/prompts/extraction.txt`: CPS extraction prompt

#### 6. Request/Response Schema Visualization
View generated schemas:
- Pydantic model definitions
- JSON Schema representations
- Endpoint: `POST /api/schemas`

#### 7. Validation Simulation (Pre-Flight Check)
Pre-export validation:
- Check required environment variables
- Validate schema completeness
- Verify feature compatibility
- Endpoint: `POST /api/preflight`

#### 8. Feature Flags at Code Level
Explicit feature flags in generated code:
- `FEATURE_CHAT`, `FEATURE_RAG`, `FEATURE_STREAMING`, `FEATURE_EMBEDDINGS`
- Disabled features raise `FeatureDisabledError`

#### 9. Test Generation
Minimal deterministic tests:
- API health endpoint tests
- Schema validation tests
- Feature flag enforcement tests

#### 10. Diff-Aware Regeneration
Track changes on regeneration:
- File-level diffs in unified format
- Added, removed, modified status
- Endpoint: `POST /api/regenerate`

#### 11. Failure-First Design
Generated code fails explicitly:
- `NotImplementedError` for unimplemented features
- TODO comments for incomplete functionality
- Auto-generated `TODO.md` file

## API Endpoints

### Core Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/analyze` | POST | Analyze project idea |
| `/api/validate` | POST | Validate CPS configuration |
| `/api/generate` | POST | Generate code from CPS |
| `/api/refine` | POST | Refine code with feedback |
| `/api/export` | POST | Export project as ZIP |
| `/api/v1/generate` | POST | Unified generation (requires API key) |

### Enhancement Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/openapi-preview` | POST | Generate OpenAPI spec preview |
| `/api/estimate-costs` | POST | Get token/cost estimates |
| `/api/schemas` | POST | Get JSON Schema representations |
| `/api/preflight` | POST | Run pre-flight validation |
| `/api/diff` | POST | Compute file diffs |
| `/api/regenerate` | POST | Regenerate with diff |
| `/api/prompts` | GET | List available prompts |
| `/api/prompts/{name}` | GET/PUT | Get/update prompt template |
| `/api/providers` | GET | List supported providers |

## CPS Schema (v2.0)

```json
{
  "project_name": "string",
  "description": "string",
  "llm_provider": {
    "type": "openai | azure_openai | local",
    "api_base": "string | null",
    "api_version": "string | null",
    "deployment_name": "string | null"
  },
  "model": "string | null",
  "embedding_model": "string | null",
  "vector_store": "string | null",
  "mode": "general | rag_only",
  "features": {
    "chat": "boolean",
    "rag": "boolean",
    "streaming": "boolean",
    "embeddings": "boolean"
  },
  "endpoints": [...],
  "auth": {"type": "none | api_key | jwt"},
  "modules": ["string"],
  "environment": {
    "type": "local | docker | production",
    "generate_dockerfile": "boolean",
    "generate_compose": "boolean"
  },
  "prompts": {
    "chat_system_prompt": "string",
    "rag_system_prompt": "string"
  },
  "generation_options": {
    "openapi_first": "boolean",
    "generate_tests": "boolean",
    "failure_first": "boolean"
  }
}
```

## Deployment on Vercel

This project is configured for deployment on Vercel as a unified full-stack application.

### Prerequisites

- Node.js 18+
- Python 3.11
- Vercel CLI (`npm i -g vercel`)

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key for LLM operations | Yes |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key (if using Azure) | Conditional |
| `GENERATOR_API_KEY` | Secret key for unified endpoint | No (default: `fastapi-gen-secret`) |

### Project Structure

```
/
├── src/                 # Next.js frontend (App Router)
├── api/                 # FastAPI backend (Python Serverless)
│   ├── index.py         # Main entry point
│   ├── generator/       # Code generation logic
│   ├── extraction/      # LLM-based CPS extraction
│   ├── templates/       # Jinja2 templates
│   ├── providers/       # LLM provider abstraction
│   ├── prompts/         # Editable prompt templates
│   ├── analysis/        # Cost estimation
│   ├── validation/      # Pre-flight validation
│   ├── visualization/   # Schema visualization
│   ├── diff/            # Diff computation
│   └── requirements.txt # Python dependencies
├── vercel.json          # Vercel configuration
└── package.json         # Node.js dependencies
```

### Deployment Steps

1. **Clone the repository**
2. **Install Vercel CLI**: `npm i -g vercel`
3. **Link to Vercel**: `vercel link`
4. **Set environment variables**: `vercel env add OPENAI_API_KEY`
5. **Deploy**: `vercel --prod`

### Limitations

> [!WARNING]
> - **Stateless**: Vercel Serverless Functions do not persist files between requests.
> - **Execution Limits**: LLM calls must complete within Vercel's time limits (typically 10-60 seconds).
> - **RAG Workloads**: Heavy RAG workloads require external vector databases (e.g., Pinecone, Qdrant Cloud).

## Local Development

```bash
# Install frontend dependencies
npm install

# Run Next.js dev server
npm run dev

# In another terminal, run the backend
cd api && pip install -r requirements.txt
uvicorn api.index:app --reload --port 8000
```

## License

MIT

