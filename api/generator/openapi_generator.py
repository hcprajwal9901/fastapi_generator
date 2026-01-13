"""
OpenAPI Generator - Feature #1: Contract-First Mode

Generates OpenAPI 3.0 specification strictly from CPS.

Rules:
- OpenAPI must be derived strictly from CPS
- No inferred endpoints
- No inferred schemas
- All paths and schemas are deterministic
"""
from typing import Dict, Any, List
import json


def generate_openapi_spec(cps_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification from CPS.
    
    All paths and schemas are derived deterministically from CPS.
    No inference or hallucination.
    
    Args:
        cps_data: CPS model as dictionary
        
    Returns:
        OpenAPI 3.0 specification as dictionary
    """
    project_name = cps_data.get("project_name", "API")
    description = cps_data.get("description", "")
    features = cps_data.get("features", {})
    endpoints = cps_data.get("endpoints", [])
    modules = cps_data.get("modules", [])
    mode = cps_data.get("mode", "general")
    auth = cps_data.get("auth", {})
    
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": project_name,
            "description": description,
            "version": "1.0.0"
        },
        "servers": [
            {"url": "http://localhost:8000", "description": "Local development server"}
        ],
        "paths": {},
        "components": {
            "schemas": _generate_schemas(cps_data),
            "securitySchemes": _generate_security_schemes(auth)
        }
    }
    
    # Add root endpoint
    spec["paths"]["/"] = {
        "get": {
            "summary": "Root endpoint",
            "operationId": "root",
            "responses": {
                "200": {
                    "description": "Welcome message",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/MessageResponse"}
                        }
                    }
                }
            }
        }
    }
    
    # Add mode-specific endpoints
    if mode == "rag_only":
        spec["paths"].update(_generate_rag_endpoints())
    elif features.get("chat"):
        spec["paths"].update(_generate_chat_endpoints())
    
    # Add endpoints from CPS
    for endpoint in endpoints:
        path = endpoint.get("path", "/")
        method = endpoint.get("method", "GET").lower()
        uses_llm = endpoint.get("uses_llm", False)
        endpoint_desc = endpoint.get("description", f"Endpoint for {path}")
        
        if path not in spec["paths"]:
            spec["paths"][path] = {}
        
        operation_id = path.strip("/").replace("/", "_") or "custom_endpoint"
        
        spec["paths"][path][method] = {
            "summary": endpoint_desc,
            "operationId": operation_id,
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/MessageResponse"}
                        }
                    }
                }
            }
        }
        
        if uses_llm:
            spec["paths"][path][method]["tags"] = ["llm"]
    
    # Add module endpoints
    for module in modules:
        module_path = f"/{module}"
        if module_path not in spec["paths"]:
            spec["paths"][module_path] = {}
        
        # GET list
        spec["paths"][module_path]["get"] = {
            "summary": f"List {module}",
            "operationId": f"list_{module}",
            "tags": [module],
            "responses": {
                "200": {
                    "description": f"List of {module}",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": f"#/components/schemas/{module.capitalize()}Base"}
                            }
                        }
                    }
                }
            }
        }
        
        # POST create
        spec["paths"][module_path]["post"] = {
            "summary": f"Create {module}",
            "operationId": f"create_{module}",
            "tags": [module],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{module.capitalize()}Base"}
                    }
                }
            },
            "responses": {
                "201": {
                    "description": f"{module.capitalize()} created",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{module.capitalize()}Base"}
                        }
                    }
                }
            }
        }
    
    # Apply security if auth is configured
    if auth.get("type") != "none":
        spec["security"] = [_get_security_requirement(auth)]
    
    return spec


def _generate_schemas(cps_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate JSON schemas from CPS configuration"""
    schemas = {
        "MessageResponse": {
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            },
            "required": ["message"]
        }
    }
    
    features = cps_data.get("features", {})
    modules = cps_data.get("modules", [])
    
    # Chat schemas
    if features.get("chat"):
        schemas["ChatRequest"] = {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "User message"},
                "stream": {"type": "boolean", "default": False}
            },
            "required": ["message"]
        }
        schemas["ChatResponse"] = {
            "type": "object",
            "properties": {
                "reply": {"type": "string", "description": "AI response"}
            },
            "required": ["reply"]
        }
    
    # RAG schemas
    if features.get("rag"):
        schemas["IngestRequest"] = {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Content to ingest"},
                "metadata": {
                    "type": "object",
                    "additionalProperties": {"type": "string"}
                }
            },
            "required": ["content"]
        }
        schemas["IngestResponse"] = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["status", "message"]
        }
        schemas["QueryRequest"] = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"}
            },
            "required": ["query"]
        }
        schemas["QueryResponse"] = {
            "type": "object",
            "properties": {
                "reply": {"type": "string"},
                "context_used": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["reply", "context_used"]
        }
    
    # Module schemas
    for module in modules:
        schemas[f"{module.capitalize()}Base"] = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string", "nullable": True}
            },
            "required": ["name"]
        }
    
    return schemas


def _generate_security_schemes(auth: Dict[str, Any]) -> Dict[str, Any]:
    """Generate security schemes based on auth configuration"""
    auth_type = auth.get("type", "none")
    
    if auth_type == "api_key":
        return {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            }
        }
    elif auth_type == "jwt":
        return {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    
    return {}


def _get_security_requirement(auth: Dict[str, Any]) -> Dict[str, List]:
    """Get security requirement for operations"""
    auth_type = auth.get("type", "none")
    
    if auth_type == "api_key":
        return {"ApiKeyAuth": []}
    elif auth_type == "jwt":
        return {"BearerAuth": []}
    
    return {}


def _generate_chat_endpoints() -> Dict[str, Any]:
    """Generate chat-related endpoints"""
    return {
        "/chat": {
            "post": {
                "summary": "Chat with AI",
                "operationId": "chat",
                "tags": ["chat"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ChatRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Chat response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ChatResponse"}
                            }
                        }
                    }
                }
            }
        }
    }


def _generate_rag_endpoints() -> Dict[str, Any]:
    """Generate RAG-related endpoints"""
    return {
        "/ingest": {
            "post": {
                "summary": "Ingest content into knowledge base",
                "operationId": "ingest",
                "tags": ["rag"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/IngestRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Ingestion result",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/IngestResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/query": {
            "post": {
                "summary": "Query the knowledge base",
                "operationId": "query",
                "tags": ["rag"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/QueryRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Query response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QueryResponse"}
                            }
                        }
                    }
                }
            }
        }
    }


def openapi_to_yaml(spec: Dict[str, Any]) -> str:
    """Convert OpenAPI spec to YAML format"""
    try:
        import yaml
        return yaml.dump(spec, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback to JSON if PyYAML not available
        return json.dumps(spec, indent=2)


def openapi_to_json(spec: Dict[str, Any]) -> str:
    """Convert OpenAPI spec to JSON format"""
    return json.dumps(spec, indent=2)
