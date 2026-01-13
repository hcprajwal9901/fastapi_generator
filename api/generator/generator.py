"""
Project Generator - Enhanced with Features #1, #3, #8, #9, #11

This generator creates FastAPI projects from CPS using Jinja2 templates.
All generation is deterministic and template-based.

Rules:
- CPS remains the single source of truth
- All outputs are template-driven
- No AI-written backend logic
- Enhancements are optional and explicit
"""
from jinja2 import Environment, FileSystemLoader
import os
import json
from typing import Dict, Any, Optional
from .models import CPS


TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def generate_project(cps: CPS) -> Dict[str, str]:
    """
    Generate a complete FastAPI project from CPS.
    
    This is the main entry point for code generation.
    All outputs are deterministic and derived from CPS.
    
    Args:
        cps: Canonical Project Specification
        
    Returns:
        Dictionary mapping file paths to content
    """
    files: Dict[str, str] = {}
    cps_dict = cps.model_dump()
    
    # =========================================================================
    # Feature #1: Contract-First (OpenAPI) Mode
    # =========================================================================
    if cps.generation_options.openapi_first:
        from .openapi_generator import generate_openapi_spec, openapi_to_json
        try:
            import yaml
            from .openapi_generator import openapi_to_yaml
            spec = generate_openapi_spec(cps_dict)
            files[f"{cps.project_name}/openapi.json"] = openapi_to_json(spec)
            files[f"{cps.project_name}/openapi.yaml"] = openapi_to_yaml(spec)
        except ImportError:
            # PyYAML not available, only generate JSON
            from .openapi_generator import generate_openapi_spec, openapi_to_json
            spec = generate_openapi_spec(cps_dict)
            files[f"{cps.project_name}/openapi.json"] = openapi_to_json(spec)
    
    # =========================================================================
    # Feature #3: Environment & Deployment Profiles
    # =========================================================================
    if cps.environment.generate_dockerfile:
        try:
            dockerfile_template = env.get_template("Dockerfile.jinja")
            files[f"{cps.project_name}/Dockerfile"] = dockerfile_template.render(cps=cps_dict)
        except Exception as e:
            # Fallback to code-based generation
            from .environment_generator import generate_dockerfile
            files[f"{cps.project_name}/Dockerfile"] = generate_dockerfile(cps_dict)
    
    if cps.environment.generate_compose:
        try:
            compose_template = env.get_template("docker-compose.yml.jinja")
            files[f"{cps.project_name}/docker-compose.yml"] = compose_template.render(cps=cps_dict)
        except Exception as e:
            # Fallback to code-based generation
            from .environment_generator import generate_docker_compose
            files[f"{cps.project_name}/docker-compose.yml"] = generate_docker_compose(cps_dict)
    
    # =========================================================================
    # Core Templates
    # =========================================================================
    templates = [
        ("app/main.py.jinja", f"{cps.project_name}/app/main.py"),
        ("app/core/llm.py.jinja", f"{cps.project_name}/app/core/llm.py"),
        ("app/schemas.py.jinja", f"{cps.project_name}/app/schemas.py"),
        ("app/__init__.py.jinja", f"{cps.project_name}/app/__init__.py"),
        ("requirements.txt.jinja", f"{cps.project_name}/requirements.txt"),
        ("README.md.jinja", f"{cps.project_name}/README.md"),
        (".env.example.jinja", f"{cps.project_name}/.env.example"),
    ]
    
    # =========================================================================
    # Feature #8: Feature Flags at Code Level
    # =========================================================================
    # Always generate feature flags module
    templates.append(("app/core/feature_flags.py.jinja", f"{cps.project_name}/app/core/feature_flags.py"))
    
    # Add core __init__.py
    files[f"{cps.project_name}/app/core/__init__.py"] = '# Core module\n'
    files[f"{cps.project_name}/app/api/__init__.py"] = '# API module\n'
    
    # =========================================================================
    # Mode-Specific Templates
    # =========================================================================
    if cps.mode == "rag_only":
        templates += [
            ("app/api/ingest.py.jinja", f"{cps.project_name}/app/api/ingest.py"),
            ("app/api/query.py.jinja", f"{cps.project_name}/app/api/query.py"),
            ("app/core/vector_store.py.jinja", f"{cps.project_name}/app/core/vector_store.py"),
        ]
    elif cps.features.chat:
        templates.append(("app/api/chat.py.jinja", f"{cps.project_name}/app/api/chat.py"))
    
    # =========================================================================
    # Dynamic Modules
    # =========================================================================
    for module in cps.modules:
        templates.append((
            "app/api/module.py.jinja",
            f"{cps.project_name}/app/api/{module}.py",
            {"module": module}
        ))
    
    # =========================================================================
    # Render All Templates
    # =========================================================================
    for template_info in templates:
        if len(template_info) == 2:
            template_path, output_path = template_info
            context = {"cps": cps_dict}
        else:
            template_path, output_path, extra_context = template_info
            context = {"cps": cps_dict, **extra_context}
        
        try:
            template = env.get_template(template_path)
            rendered = template.render(**context)
            files[output_path] = rendered
        except Exception as e:
            # Handle missing or optional templates
            if "chat.py" in template_path and not cps.features.chat:
                continue
            if "__init__.py" in template_path:
                files[output_path] = ""
                continue
            
            # Log the error but don't fail completely
            print(f"Warning: Error rendering {template_path}: {e}")
    
    # =========================================================================
    # Feature #11: Failure-First Design
    # =========================================================================
    if cps.generation_options.failure_first:
        # Add TODO comments file
        files[f"{cps.project_name}/TODO.md"] = generate_todo_file(cps_dict)
    
    # =========================================================================
    # Feature #9: Test Generation
    # =========================================================================
    if cps.generation_options.generate_tests:
        from .test_generator import generate_tests
        test_files = generate_tests(cps_dict)
        files.update(test_files)
    
    return files


def generate_todo_file(cps_data: Dict[str, Any]) -> str:
    """
    Generate TODO.md with incomplete features and implementation notes.
    
    Feature #11: Failure-First Design
    """
    project_name = cps_data.get("project_name", "Project")
    features = cps_data.get("features", {})
    
    content = f"""# TODO: {project_name}

This file lists features that need implementation or review.
Generated from CPS - update this as you complete items.

## Required Implementations

"""
    
    if features.get("chat"):
        content += """### Chat Feature
- [ ] Implement actual LLM chat logic in `app/api/chat.py`
- [ ] Configure system prompts in `app/core/llm.py`
- [ ] Add error handling for API rate limits

"""
    
    if features.get("rag"):
        content += """### RAG Feature
- [ ] Implement document ingestion in `app/api/ingest.py`
- [ ] Configure vector store connection in `app/core/vector_store.py`
- [ ] Implement semantic search in `app/api/query.py`
- [ ] Add chunking strategy for large documents

"""
    
    if features.get("streaming"):
        content += """### Streaming Feature
- [ ] Implement SSE streaming in chat endpoint
- [ ] Add streaming response handling
- [ ] Test with various client libraries

"""
    
    if features.get("embeddings"):
        content += """### Embeddings Feature
- [ ] Configure embedding model
- [ ] Implement batch embedding generation
- [ ] Add caching for frequently used embeddings

"""
    
    content += """## General TODOs

- [ ] Review and update environment variables in `.env.example`
- [ ] Add production logging configuration
- [ ] Implement rate limiting
- [ ] Add API documentation
- [ ] Set up CI/CD pipeline
- [ ] Add monitoring and alerting

## Notes

Items marked with `NotImplementedError` in code require implementation.
See individual files for specific TODO comments.
"""
    
    return content


def generate_schemas_only(cps: CPS) -> Dict[str, str]:
    """
    Generate only schema files for visualization.
    
    Feature #6: Request/Response Schema Visualization
    """
    files = {}
    cps_dict = cps.model_dump()
    
    try:
        template = env.get_template("app/schemas.py.jinja")
        files[f"{cps.project_name}/app/schemas.py"] = template.render(cps=cps_dict)
    except Exception as e:
        print(f"Error generating schemas: {e}")
    
    return files

