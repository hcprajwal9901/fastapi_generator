"""
Pluggable LLM Provider Abstraction - Feature #4

Rules:
- All LLM calls go through a provider interface
- Providers are swappable via CPS configuration
- Unsupported providers fail validation explicitly
- No dynamic provider guessing
- Provider must be declared in CPS
"""
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass


class ProviderNotSupportedError(Exception):
    """Raised when an unsupported provider is requested"""
    pass


class ProviderConfigurationError(Exception):
    """Raised when provider configuration is invalid"""
    pass


@dataclass
class ProviderValidationResult:
    """Result of provider configuration validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]


class LLMProviderInterface(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM interactions must go through implementations of this interface.
    This ensures consistent behavior and explicit provider selection.
    """
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> str:
        """
        Execute a chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier
            **kwargs: Additional provider-specific options
            
        Returns:
            The completion text response
        """
        pass
    
    @abstractmethod
    async def embedding(self, text: str, model: str) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Input text to embed
            model: Embedding model identifier
            
        Returns:
            List of embedding values
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> ProviderValidationResult:
        """
        Validate provider configuration.
        
        Returns:
            ProviderValidationResult with errors and warnings
        """
        pass
    
    @abstractmethod
    def get_required_env_vars(self) -> List[str]:
        """
        Get list of required environment variables for this provider.
        
        Returns:
            List of environment variable names
        """
        pass


class OpenAIProvider(LLMProviderInterface):
    """OpenAI API provider implementation"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            from openai import AsyncOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ProviderConfigurationError(
                    "OPENAI_API_KEY environment variable is required for OpenAI provider"
                )
            self._client = AsyncOpenAI(api_key=api_key)
        return self._client
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
    
    async def embedding(self, text: str, model: str) -> List[float]:
        client = self._get_client()
        response = await client.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding
    
    def validate_config(self) -> ProviderValidationResult:
        errors = []
        warnings = []
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            errors.append("OPENAI_API_KEY environment variable is not set")
        elif api_key == "your_api_key_here":
            errors.append("OPENAI_API_KEY has placeholder value 'your_api_key_here'")
        
        return ProviderValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get_required_env_vars(self) -> List[str]:
        return ["OPENAI_API_KEY"]


class AzureOpenAIProvider(LLMProviderInterface):
    """Azure OpenAI provider implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_base = config.get("api_base")
        self.api_version = config.get("api_version", "2024-02-15-preview")
        self.deployment_name = config.get("deployment_name")
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Azure OpenAI client"""
        if self._client is None:
            from openai import AsyncAzureOpenAI
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            if not api_key:
                raise ProviderConfigurationError(
                    "AZURE_OPENAI_API_KEY environment variable is required for Azure OpenAI provider"
                )
            self._client = AsyncAzureOpenAI(
                api_key=api_key,
                api_version=self.api_version,
                azure_endpoint=self.api_base
            )
        return self._client
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> str:
        client = self._get_client()
        # Azure uses deployment_name instead of model
        response = await client.chat.completions.create(
            model=self.deployment_name or model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
    
    async def embedding(self, text: str, model: str) -> List[float]:
        client = self._get_client()
        response = await client.embeddings.create(
            model=self.deployment_name or model,
            input=text
        )
        return response.data[0].embedding
    
    def validate_config(self) -> ProviderValidationResult:
        errors = []
        warnings = []
        
        if not self.api_base:
            errors.append("api_base is required for Azure OpenAI provider")
        if not self.deployment_name:
            errors.append("deployment_name is required for Azure OpenAI provider")
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not api_key:
            errors.append("AZURE_OPENAI_API_KEY environment variable is not set")
        
        return ProviderValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def get_required_env_vars(self) -> List[str]:
        return ["AZURE_OPENAI_API_KEY"]


class LocalProvider(LLMProviderInterface):
    """
    Placeholder local provider.
    
    This provider is for development/testing purposes and raises
    NotImplementedError for all operations with clear guidance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ) -> str:
        raise NotImplementedError(
            "LocalProvider is a placeholder. To use local LLM:\n"
            "1. Implement a custom provider extending LLMProviderInterface\n"
            "2. Configure your local LLM endpoint\n"
            "3. Register the provider in the factory function\n"
            "\n"
            "TODO: Implement local LLM integration"
        )
    
    async def embedding(self, text: str, model: str) -> List[float]:
        raise NotImplementedError(
            "LocalProvider embedding is not implemented. "
            "Configure a supported provider (openai, azure_openai) or "
            "implement a custom local embedding solution."
        )
    
    def validate_config(self) -> ProviderValidationResult:
        return ProviderValidationResult(
            valid=True,
            errors=[],
            warnings=[
                "LocalProvider is a placeholder and will raise NotImplementedError at runtime"
            ]
        )
    
    def get_required_env_vars(self) -> List[str]:
        return []  # No env vars required for placeholder


# =============================================================================
# Provider Factory
# =============================================================================

SUPPORTED_PROVIDERS = ["openai", "azure_openai", "local"]


def get_provider(config: Union[str, Dict[str, Any]]) -> LLMProviderInterface:
    """
    Factory function to get provider based on CPS config.
    
    Args:
        config: Either a provider type string or full config dict
        
    Returns:
        Configured LLMProviderInterface implementation
        
    Raises:
        ProviderNotSupportedError: If provider type is not supported
    """
    # Handle legacy string format
    if isinstance(config, str):
        provider_type = config
        provider_config = {}
    else:
        provider_type = config.get("type", "openai")
        provider_config = config
    
    # Explicit provider selection - no guessing
    if provider_type not in SUPPORTED_PROVIDERS:
        raise ProviderNotSupportedError(
            f"Provider '{provider_type}' is not supported. "
            f"Supported providers: {', '.join(SUPPORTED_PROVIDERS)}. "
            f"Provider must be explicitly declared in CPS."
        )
    
    if provider_type == "openai":
        return OpenAIProvider(provider_config)
    elif provider_type == "azure_openai":
        return AzureOpenAIProvider(provider_config)
    elif provider_type == "local":
        return LocalProvider(provider_config)
    
    # This should never be reached due to the check above
    raise ProviderNotSupportedError(f"Provider '{provider_type}' is not implemented")
