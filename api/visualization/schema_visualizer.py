"""
Schema Visualizer - Feature #6: Request/Response Schema Visualization

Exposes generated Pydantic models and JSON Schema representations.

Rules:
- Visualization must reflect actual generated schemas
- No hand-written examples
- No undocumented fields
- All schemas derived from CPS
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class SchemaVisualization:
    """
    Container for schema visualization data.
    
    Contains both Pydantic model definitions and JSON Schema representations.
    """
    pydantic_models: Dict[str, str]  # Model name -> Python code
    json_schemas: Dict[str, Dict[str, Any]]  # Model name -> JSON Schema
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pydantic_models": self.pydantic_models,
            "json_schemas": self.json_schemas,
        }


def extract_schemas_from_cps(cps_data: Dict[str, Any]) -> SchemaVisualization:
    """
    Generate schema visualizations directly from CPS.
    
    This creates both Pydantic model code and JSON Schema representations
    based on the CPS configuration.
    
    Args:
        cps_data: CPS model as dictionary
        
    Returns:
        SchemaVisualization with models and schemas
    """
    pydantic_models = {}
    json_schemas = {}
    
    features = cps_data.get("features", {})
    modules = cps_data.get("modules", [])
    
    # =========================================================================
    # Base Models
    # =========================================================================
    
    # MessageResponse (always included)
    pydantic_models["MessageResponse"] = '''class MessageResponse(BaseModel):
    """Standard message response"""
    message: str'''
    
    json_schemas["MessageResponse"] = {
        "type": "object",
        "title": "MessageResponse",
        "description": "Standard message response",
        "properties": {
            "message": {"type": "string"}
        },
        "required": ["message"]
    }
    
    # =========================================================================
    # Chat Schemas
    # =========================================================================
    
    if features.get("chat"):
        pydantic_models["ChatRequest"] = '''class ChatRequest(BaseModel):
    """Chat request with user message"""
    message: str
    stream: Optional[bool] = False'''
        
        json_schemas["ChatRequest"] = {
            "type": "object",
            "title": "ChatRequest",
            "description": "Chat request with user message",
            "properties": {
                "message": {"type": "string", "description": "User message"},
                "stream": {"type": "boolean", "default": False, "description": "Enable streaming response"}
            },
            "required": ["message"]
        }
        
        pydantic_models["ChatResponse"] = '''class ChatResponse(BaseModel):
    """Chat response with AI reply"""
    reply: str'''
        
        json_schemas["ChatResponse"] = {
            "type": "object",
            "title": "ChatResponse",
            "description": "Chat response with AI reply",
            "properties": {
                "reply": {"type": "string", "description": "AI-generated response"}
            },
            "required": ["reply"]
        }
    
    # =========================================================================
    # RAG Schemas
    # =========================================================================
    
    if features.get("rag"):
        pydantic_models["IngestRequest"] = '''class IngestRequest(BaseModel):
    """Request to ingest content into knowledge base"""
    content: str
    metadata: Optional[Dict[str, str]] = None'''
        
        json_schemas["IngestRequest"] = {
            "type": "object",
            "title": "IngestRequest",
            "description": "Request to ingest content into knowledge base",
            "properties": {
                "content": {"type": "string", "description": "Content to ingest"},
                "metadata": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Optional metadata"
                }
            },
            "required": ["content"]
        }
        
        pydantic_models["IngestResponse"] = '''class IngestResponse(BaseModel):
    """Response after content ingestion"""
    status: str
    message: str'''
        
        json_schemas["IngestResponse"] = {
            "type": "object",
            "title": "IngestResponse",
            "description": "Response after content ingestion",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["status", "message"]
        }
        
        pydantic_models["QueryRequest"] = '''class QueryRequest(BaseModel):
    """Request to query the knowledge base"""
    query: str
    top_k: Optional[int] = 5'''
        
        json_schemas["QueryRequest"] = {
            "type": "object",
            "title": "QueryRequest",
            "description": "Request to query the knowledge base",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "default": 5, "description": "Number of results to return"}
            },
            "required": ["query"]
        }
        
        pydantic_models["QueryResponse"] = '''class QueryResponse(BaseModel):
    """Response from knowledge base query"""
    reply: str
    context_used: List[str]'''
        
        json_schemas["QueryResponse"] = {
            "type": "object",
            "title": "QueryResponse",
            "description": "Response from knowledge base query",
            "properties": {
                "reply": {"type": "string", "description": "AI-generated answer"},
                "context_used": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Retrieved context documents"
                }
            },
            "required": ["reply", "context_used"]
        }
    
    # =========================================================================
    # Module Schemas
    # =========================================================================
    
    for module in modules:
        model_name = f"{module.capitalize()}Base"
        
        pydantic_models[model_name] = f'''class {model_name}(BaseModel):
    """Base model for {module}"""
    name: str
    description: Optional[str] = None'''
        
        json_schemas[model_name] = {
            "type": "object",
            "title": model_name,
            "description": f"Base model for {module}",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string", "nullable": True}
            },
            "required": ["name"]
        }
    
    return SchemaVisualization(
        pydantic_models=pydantic_models,
        json_schemas=json_schemas,
    )


def generate_json_schema(cps_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate complete JSON Schema document from CPS.
    
    Returns a JSON Schema document with all request/response models
    defined as components.
    
    Args:
        cps_data: CPS model as dictionary
        
    Returns:
        JSON Schema document
    """
    visualization = extract_schemas_from_cps(cps_data)
    
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": f"{cps_data.get('project_name', 'API')} Schemas",
        "description": f"Request/response schemas for {cps_data.get('project_name', 'API')}",
        "definitions": visualization.json_schemas,
    }


def get_schema_summary(cps_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a summary of all schemas that will be generated.
    
    Useful for preview without full schema generation.
    
    Args:
        cps_data: CPS model as dictionary
        
    Returns:
        Summary with model names and basic info
    """
    visualization = extract_schemas_from_cps(cps_data)
    
    summary = {
        "total_models": len(visualization.pydantic_models),
        "models": []
    }
    
    for name, code in visualization.pydantic_models.items():
        # Extract field count from code
        field_count = code.count(":") - 1  # Approximate
        summary["models"].append({
            "name": name,
            "field_count": max(1, field_count),
        })
    
    return summary
