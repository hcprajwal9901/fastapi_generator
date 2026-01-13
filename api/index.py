"""
FastAPI Generator API - Enhanced with Features #1-11

This API provides endpoints for:
- CPS extraction and validation
- Code generation with OpenAPI-first mode
- Cost estimation
- Pre-flight validation
- Schema visualization
- Diff computation for regeneration
- Prompt management
"""
import os
import json
import zipfile
import io
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .generator.models import CPS
from .extraction.extraction import extract_cps, refine_code
from .generator.generator import generate_project

app = FastAPI(
    title="FastAPI Generator API",
    description="AI-powered FastAPI project generator with CPS-based code generation",
    version="2.0.0"
)

# Vercel requires CORS to be handled correctly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("GENERATOR_API_KEY", "fastapi-gen-secret")


async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key


# =============================================================================
# Health & Status Endpoints
# =============================================================================

@app.get("/api/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "version": "2.0.0"}


# =============================================================================
# Core Generation Endpoints
# =============================================================================

@app.post("/api/analyze")
async def analyze(data: dict):
    """Extract CPS from natural language description"""
    text = data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing text input")
    
    extracted = await extract_cps(text)
    return extracted


@app.post("/api/validate")
async def validate_cps(cps: CPS):
    """Validate CPS configuration"""
    errors = []
    
    if cps.mode == "rag_only":
        if not cps.features.rag:
            errors.append("features.rag MUST be true in RAG-only mode")
        if not cps.features.embeddings:
            errors.append("features.embeddings MUST be true in RAG-only mode")
        if cps.features.chat:
            errors.append("Chat-only endpoints are not allowed in RAG-only specialization.")
        if not cps.vector_store:
            errors.append("Vector store configuration is required for RAG.")
        if not cps.embedding_model:
            errors.append("Missing embedding model")
    
    # Validate provider configuration
    provider_type = cps.get_provider_type()
    if provider_type == "azure_openai":
        if isinstance(cps.llm_provider, dict) or hasattr(cps.llm_provider, 'api_base'):
            provider = cps.llm_provider
            if hasattr(provider, 'api_base') and not provider.api_base:
                errors.append("api_base is required for Azure OpenAI provider")
            if hasattr(provider, 'deployment_name') and not provider.deployment_name:
                errors.append("deployment_name is required for Azure OpenAI provider")
    
    if errors:
        raise HTTPException(status_code=400, detail=", ".join(errors))
    
    return {"status": "success", "data": cps.model_dump()}


@app.post("/api/generate")
async def generate(cps: CPS):
    """Generate FastAPI project from CPS"""
    files = generate_project(cps)
    return {"files": files}


@app.post("/api/refine")
async def refine(data: dict):
    """Refine generated code based on feedback"""
    cps = data.get("cps")
    files = data.get("files")
    feedback = data.get("feedback")
    
    if not cps or not files or not feedback:
        raise HTTPException(status_code=400, detail="Missing required fields: cps, files, or feedback")
    
    refined_files = await refine_code(cps, files, feedback)
    return {"files": refined_files}


@app.post("/api/export")
async def export_zip(data: dict):
    """Export project as ZIP file"""
    files = data.get("files")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for path, content in files.items():
            zip_file.writestr(path, content)
    
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": "attachment; filename=project.zip"}
    )


@app.post("/api/v1/generate")
async def unified_generate(data: dict, token: str = Depends(verify_api_key)):
    """Unified generation endpoint (requires API key)"""
    idea = data.get("idea")
    if not idea:
        raise HTTPException(status_code=400, detail="Missing idea input")
    
    # 1. Extraction
    extracted_data = await extract_cps(idea)
    if "error" in extracted_data:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {extracted_data['error']}")
    
    # 2. Validation (Internal)
    try:
        cps = CPS(**extracted_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Validation failed: {str(e)}")
    
    # 3. Generation
    files = generate_project(cps)
    return {"project_name": cps.project_name, "files": files}


# =============================================================================
# Feature #1: Contract-First (OpenAPI) Mode
# =============================================================================

@app.post("/api/openapi-preview")
async def openapi_preview(cps: CPS):
    """
    Generate OpenAPI 3.0 specification preview from CPS.
    
    The OpenAPI spec is derived strictly from CPS with no inference.
    """
    from .generator.openapi_generator import generate_openapi_spec, openapi_to_json
    
    try:
        spec = generate_openapi_spec(cps.model_dump())
        return {
            "openapi_spec": spec,
            "json": openapi_to_json(spec),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAPI generation failed: {str(e)}")


# =============================================================================
# Feature #2: LLM Token & Cost Estimation
# =============================================================================

@app.post("/api/estimate-costs")
async def estimate_costs(cps: CPS):
    """
    Estimate token usage and costs based on CPS configuration.
    
    DISCLAIMER: All estimates are informational only and not guaranteed.
    """
    from .analysis.cost_estimator import estimate_costs as do_estimate
    
    try:
        estimate = do_estimate(cps.model_dump())
        return estimate.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost estimation failed: {str(e)}")


# =============================================================================
# Feature #6: Request/Response Schema Visualization
# =============================================================================

@app.post("/api/schemas")
async def get_schemas(cps: CPS):
    """
    Get JSON Schema representations of request/response models.
    
    Schemas are derived deterministically from CPS.
    """
    from .visualization.schema_visualizer import extract_schemas_from_cps, generate_json_schema
    
    try:
        visualization = extract_schemas_from_cps(cps.model_dump())
        json_schema = generate_json_schema(cps.model_dump())
        return {
            "pydantic_models": visualization.pydantic_models,
            "json_schemas": visualization.json_schemas,
            "complete_schema": json_schema,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema visualization failed: {str(e)}")


# =============================================================================
# Feature #7: Validation Simulation (Pre-Flight Check)
# =============================================================================

@app.post("/api/preflight")
async def preflight_check(data: dict):
    """
    Run pre-flight validation before ZIP export.
    
    Checks:
    - Required environment variables
    - Schema completeness  
    - Enabled feature compatibility
    
    This simulation does NOT call external services.
    """
    from .validation.validation_simulator import simulate_preflight
    
    cps_data = data.get("cps")
    files = data.get("files")
    
    if not cps_data:
        raise HTTPException(status_code=400, detail="Missing cps in request body")
    
    try:
        result = simulate_preflight(cps_data, files)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pre-flight check failed: {str(e)}")


# =============================================================================
# Feature #10: Diff-Aware Regeneration
# =============================================================================

@app.post("/api/diff")
async def compute_diff(data: dict):
    """
    Compute file-level diffs between old and new file sets.
    
    Use this when regenerating a project to see what changed.
    """
    from .diff.diff_engine import compute_diff as do_diff
    
    old_files = data.get("old_files", {})
    new_files = data.get("new_files", {})
    
    if not new_files:
        raise HTTPException(status_code=400, detail="Missing new_files in request body")
    
    try:
        result = do_diff(old_files, new_files)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diff computation failed: {str(e)}")


@app.post("/api/regenerate")
async def regenerate_with_diff(data: dict):
    """
    Regenerate project and return diff against previous version.
    
    This allows users to see exactly what changed.
    """
    from .diff.diff_engine import compute_diff as do_diff
    
    cps_data = data.get("cps")
    old_files = data.get("old_files", {})
    
    if not cps_data:
        raise HTTPException(status_code=400, detail="Missing cps in request body")
    
    try:
        cps = CPS(**cps_data)
        new_files = generate_project(cps)
        diff_result = do_diff(old_files, new_files)
        
        return {
            "files": new_files,
            "diff": diff_result.to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


# =============================================================================
# Feature #5: Prompt Management
# =============================================================================

@app.get("/api/prompts")
async def list_prompts():
    """List available prompt templates"""
    from .prompts import list_prompts as do_list
    
    try:
        prompts = do_list()
        return {"prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@app.get("/api/prompts/{name}")
async def get_prompt(name: str):
    """Get a specific prompt template"""
    from .prompts import load_prompt
    
    try:
        content = load_prompt(name)
        return {"name": name, "content": content}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load prompt: {str(e)}")


@app.put("/api/prompts/{name}")
async def update_prompt(name: str, data: dict):
    """Update a prompt template"""
    from .prompts import save_prompt
    
    content = data.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Missing content in request body")
    
    try:
        save_prompt(name, content)
        return {"status": "success", "name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save prompt: {str(e)}")


# =============================================================================
# Feature #4: Provider Information
# =============================================================================

@app.get("/api/providers")
async def list_providers():
    """List supported LLM providers"""
    from .providers import SUPPORTED_PROVIDERS
    
    return {
        "providers": SUPPORTED_PROVIDERS,
        "default": "openai",
    }

