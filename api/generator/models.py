from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator


# =============================================================================
# Feature #4: Pluggable LLM Provider Configuration
# =============================================================================

class LLMProviderConfig(BaseModel):
    """
    Configuration for LLM provider.
    
    Rules:
    - Provider must be explicitly declared
    - Unsupported providers fail validation
    - No dynamic provider guessing
    """
    type: Literal["openai", "azure_openai", "local"] = "openai"
    api_base: Optional[str] = None  # For Azure or custom endpoints
    api_version: Optional[str] = None  # For Azure (e.g., "2024-02-15-preview")
    deployment_name: Optional[str] = None  # For Azure deployment
    
    @model_validator(mode='after')
    def validate_azure_config(self):
        """Azure OpenAI requires additional configuration"""
        if self.type == "azure_openai":
            if not self.api_base:
                raise ValueError("api_base is required for Azure OpenAI provider")
            if not self.deployment_name:
                raise ValueError("deployment_name is required for Azure OpenAI provider")
        return self


# =============================================================================
# Feature #3: Environment & Deployment Profiles
# =============================================================================

class EnvironmentProfile(BaseModel):
    """
    Environment profile configuration.
    
    Rules:
    - Profiles must be explicitly selected by user
    - No cloud provider assumptions
    - No auto-deployment
    """
    type: Literal["local", "docker", "production"] = "local"
    generate_dockerfile: bool = False
    generate_compose: bool = False
    
    @model_validator(mode='after')
    def validate_docker_options(self):
        """Docker compose requires Dockerfile"""
        if self.generate_compose and not self.generate_dockerfile:
            raise ValueError("generate_dockerfile must be True if generate_compose is True")
        return self


# =============================================================================
# Feature #5: Editable Prompt Templates
# =============================================================================

class PromptConfig(BaseModel):
    """
    Editable prompt templates.
    
    Rules:
    - Prompts must be version-controlled
    - Prompts must be editable in preview UI
    - No hidden system prompts
    """
    chat_system_prompt: str = "You are a helpful assistant."
    rag_system_prompt: str = "You are a helpful assistant. Use the provided context to answer the user query."
    custom_prompts: Dict[str, str] = Field(default_factory=dict)


# =============================================================================
# Feature #1 & #9: Generation Options
# =============================================================================

class GenerationOptions(BaseModel):
    """
    Code generation configuration options.
    
    Rules:
    - All options are explicitly set
    - Defaults are conservative (off)
    """
    openapi_first: bool = False  # Feature #1: Generate OpenAPI spec first
    generate_tests: bool = True  # Feature #9: Generate test files
    failure_first: bool = True   # Feature #11: Add NotImplementedError/TODO patterns


# =============================================================================
# Core Models
# =============================================================================

class Features(BaseModel):
    """Feature flags that determine what code is generated"""
    chat: bool = False
    rag: bool = False
    streaming: bool = False
    embeddings: bool = False


class Endpoint(BaseModel):
    """API endpoint definition"""
    path: str
    method: Literal["GET", "POST"]
    uses_llm: bool
    description: Optional[str] = None  # For OpenAPI generation


class Auth(BaseModel):
    """Authentication configuration"""
    type: Literal["none", "api_key", "jwt"]


# =============================================================================
# Main CPS Model
# =============================================================================

class CPS(BaseModel):
    """
    Canonical Project Specification - The single source of truth.
    
    All code generation is derived deterministically from this schema.
    No inference, no guessing, no hallucination.
    """
    # Core fields
    project_name: str
    description: str
    
    # LLM Configuration - Feature #4: Now uses provider config object
    # Accepts both legacy string format and new config object for backward compatibility
    llm_provider: Union[Literal["openai"], LLMProviderConfig] = Field(
        default_factory=LLMProviderConfig
    )
    model: Optional[str] = None
    embedding_model: Optional[str] = None
    vector_store: Optional[str] = None
    
    # Mode
    mode: Literal["general", "rag_only"] = "general"
    
    # Features
    features: Features
    endpoints: List[Endpoint]
    auth: Auth
    modules: List[str] = []
    
    # New enhancement fields (all optional with defaults for backward compatibility)
    environment: EnvironmentProfile = Field(default_factory=EnvironmentProfile)
    prompts: PromptConfig = Field(default_factory=PromptConfig)
    generation_options: GenerationOptions = Field(default_factory=GenerationOptions)
    
    @model_validator(mode='after')
    def normalize_llm_provider(self):
        """Convert legacy string format to LLMProviderConfig"""
        if isinstance(self.llm_provider, str):
            self.llm_provider = LLMProviderConfig(type=self.llm_provider)
        return self
    
    def get_provider_type(self) -> str:
        """Helper to get provider type regardless of format"""
        if isinstance(self.llm_provider, str):
            return self.llm_provider
        return self.llm_provider.type
