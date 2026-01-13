"""
Pre-Flight Validation Simulator - Feature #7

Checks project configuration before ZIP export.

Rules:
- No silent failures
- Simulation must not call external services
- All checks are deterministic
- Errors are visible and actionable
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Severity level for validation issues"""
    ERROR = "error"      # Must be fixed before deployment
    WARNING = "warning"  # Should be reviewed
    INFO = "info"        # Informational only


@dataclass
class ValidationError:
    """
    Structured validation error with actionable guidance.
    
    Provides clear information about what's wrong and how to fix it.
    """
    code: str           # Machine-readable error code
    message: str        # Human-readable description
    severity: Severity  # Error severity level
    field: Optional[str] = None  # Related CPS field if applicable
    suggestion: Optional[str] = None  # How to fix the issue
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "field": self.field,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of pre-flight validation"""
    valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    info: List[ValidationError]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [e.to_dict() for e in self.warnings],
            "info": [e.to_dict() for e in self.info],
            "summary": {
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
                "info_count": len(self.info),
            }
        }


def simulate_preflight(
    cps_data: Dict[str, Any],
    files: Optional[Dict[str, str]] = None
) -> ValidationResult:
    """
    Run pre-flight checks before ZIP export.
    
    This simulation:
    - Checks required environment variables
    - Validates schema completeness
    - Checks enabled feature compatibility
    - Does NOT call any external services
    
    Args:
        cps_data: CPS model as dictionary
        files: Optional generated files to validate
        
    Returns:
        ValidationResult with all issues found
    """
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    info: List[ValidationError] = []
    
    # =========================================================================
    # Environment Variable Checks
    # =========================================================================
    errors.extend(_check_required_env_vars(cps_data, files))
    
    # =========================================================================
    # Schema Completeness Checks
    # =========================================================================
    errors.extend(_check_schema_completeness(cps_data))
    
    # =========================================================================
    # Feature Compatibility Checks
    # =========================================================================
    warnings.extend(_check_feature_compatibility(cps_data))
    
    # =========================================================================
    # Configuration Checks
    # =========================================================================
    warnings.extend(_check_configuration(cps_data))
    
    # =========================================================================
    # Best Practice Checks
    # =========================================================================
    info.extend(_check_best_practices(cps_data))
    
    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        info=info,
    )


def _check_required_env_vars(
    cps_data: Dict[str, Any],
    files: Optional[Dict[str, str]] = None
) -> List[ValidationError]:
    """Check for required but potentially missing environment variables"""
    errors = []
    features = cps_data.get("features", {})
    llm_provider = cps_data.get("llm_provider", {})
    
    # Determine provider type
    if isinstance(llm_provider, str):
        provider_type = llm_provider
    else:
        provider_type = llm_provider.get("type", "openai")
    
    required_vars = []
    
    # LLM provider requirements
    if provider_type == "openai":
        required_vars.append(("OPENAI_API_KEY", "OpenAI API key for LLM operations"))
    elif provider_type == "azure_openai":
        required_vars.append(("AZURE_OPENAI_API_KEY", "Azure OpenAI API key"))
        required_vars.append(("AZURE_OPENAI_ENDPOINT", "Azure OpenAI endpoint URL"))
    
    # Feature-specific requirements
    if features.get("rag"):
        if cps_data.get("vector_store"):
            vector_store = cps_data.get("vector_store", "").lower()
            if "pinecone" in vector_store:
                required_vars.append(("PINECONE_API_KEY", "Pinecone API key for vector store"))
            elif "weaviate" in vector_store:
                required_vars.append(("WEAVIATE_API_KEY", "Weaviate API key"))
    
    # Check if env vars are documented in .env.example
    env_example_content = ""
    if files:
        for path, content in files.items():
            if ".env.example" in path:
                env_example_content = content
                break
    
    for var_name, description in required_vars:
        if env_example_content and var_name not in env_example_content:
            errors.append(ValidationError(
                code="MISSING_ENV_VAR_DOC",
                message=f"{var_name} is required but not documented in .env.example",
                severity=Severity.ERROR,
                field="environment",
                suggestion=f"Add {var_name}=your_value_here to .env.example"
            ))
        else:
            errors.append(ValidationError(
                code="REQUIRED_ENV_VAR",
                message=f"{var_name} is required: {description}",
                severity=Severity.ERROR,
                field="environment",
                suggestion=f"Ensure {var_name} is set in your deployment environment"
            ))
    
    return errors


def _check_schema_completeness(cps_data: Dict[str, Any]) -> List[ValidationError]:
    """Check that CPS schema is complete"""
    errors = []
    
    # Required fields
    if not cps_data.get("project_name"):
        errors.append(ValidationError(
            code="MISSING_PROJECT_NAME",
            message="project_name is required",
            severity=Severity.ERROR,
            field="project_name",
            suggestion="Provide a project_name in your CPS"
        ))
    
    if not cps_data.get("description"):
        errors.append(ValidationError(
            code="MISSING_DESCRIPTION",
            message="description is required",
            severity=Severity.ERROR,
            field="description",
            suggestion="Provide a description for your project"
        ))
    
    # Mode-specific requirements
    mode = cps_data.get("mode", "general")
    features = cps_data.get("features", {})
    
    if mode == "rag_only":
        if not features.get("rag"):
            errors.append(ValidationError(
                code="RAG_MODE_FEATURE_MISMATCH",
                message="features.rag must be true in rag_only mode",
                severity=Severity.ERROR,
                field="features.rag",
                suggestion="Set features.rag to true"
            ))
        
        if not cps_data.get("vector_store"):
            errors.append(ValidationError(
                code="RAG_MODE_MISSING_VECTOR_STORE",
                message="vector_store is required for rag_only mode",
                severity=Severity.ERROR,
                field="vector_store",
                suggestion="Specify a vector_store (e.g., 'chromadb', 'pinecone')"
            ))
        
        if not cps_data.get("embedding_model"):
            errors.append(ValidationError(
                code="RAG_MODE_MISSING_EMBEDDING_MODEL",
                message="embedding_model is required for rag_only mode",
                severity=Severity.ERROR,
                field="embedding_model",
                suggestion="Specify an embedding_model (e.g., 'text-embedding-3-small')"
            ))
    
    return errors


def _check_feature_compatibility(cps_data: Dict[str, Any]) -> List[ValidationError]:
    """Check for incompatible feature combinations"""
    warnings = []
    features = cps_data.get("features", {})
    
    # Streaming without chat
    if features.get("streaming") and not features.get("chat"):
        warnings.append(ValidationError(
            code="STREAMING_WITHOUT_CHAT",
            message="streaming is enabled but chat is disabled",
            severity=Severity.WARNING,
            field="features.streaming",
            suggestion="Enable features.chat to use streaming, or disable streaming"
        ))
    
    # Embeddings without RAG
    if features.get("embeddings") and not features.get("rag"):
        warnings.append(ValidationError(
            code="EMBEDDINGS_WITHOUT_RAG",
            message="embeddings is enabled but rag is disabled",
            severity=Severity.WARNING,
            field="features.embeddings",
            suggestion="Embeddings are typically used with RAG. Consider enabling features.rag"
        ))
    
    # Local provider warning
    llm_provider = cps_data.get("llm_provider", {})
    provider_type = llm_provider.get("type", "openai") if isinstance(llm_provider, dict) else llm_provider
    
    if provider_type == "local":
        warnings.append(ValidationError(
            code="LOCAL_PROVIDER_PLACEHOLDER",
            message="LocalProvider is a placeholder and will raise NotImplementedError",
            severity=Severity.WARNING,
            field="llm_provider.type",
            suggestion="Implement a custom local provider or use 'openai' or 'azure_openai'"
        ))
    
    return warnings


def _check_configuration(cps_data: Dict[str, Any]) -> List[ValidationError]:
    """Check for configuration issues"""
    warnings = []
    
    auth = cps_data.get("auth", {})
    environment = cps_data.get("environment", {})
    
    # No auth in production
    if auth.get("type") == "none" and environment.get("type") == "production":
        warnings.append(ValidationError(
            code="NO_AUTH_IN_PRODUCTION",
            message="No authentication configured for production environment",
            severity=Severity.WARNING,
            field="auth.type",
            suggestion="Consider enabling api_key or jwt authentication for production"
        ))
    
    # Docker compose without Dockerfile
    if environment.get("generate_compose") and not environment.get("generate_dockerfile"):
        warnings.append(ValidationError(
            code="COMPOSE_WITHOUT_DOCKERFILE",
            message="Docker Compose requested without Dockerfile",
            severity=Severity.WARNING,
            field="environment.generate_compose",
            suggestion="Enable environment.generate_dockerfile when using docker-compose"
        ))
    
    return warnings


def _check_best_practices(cps_data: Dict[str, Any]) -> List[ValidationError]:
    """Check for best practice recommendations"""
    info = []
    
    generation_options = cps_data.get("generation_options", {})
    
    # Tests disabled
    if not generation_options.get("generate_tests", True):
        info.append(ValidationError(
            code="TESTS_DISABLED",
            message="Test generation is disabled",
            severity=Severity.INFO,
            field="generation_options.generate_tests",
            suggestion="Consider enabling tests for better code quality"
        ))
    
    # OpenAPI not enabled
    if not generation_options.get("openapi_first", False):
        info.append(ValidationError(
            code="OPENAPI_NOT_ENABLED",
            message="OpenAPI-first generation is not enabled",
            severity=Severity.INFO,
            field="generation_options.openapi_first",
            suggestion="Enable openapi_first for contract-first API development"
        ))
    
    return info
