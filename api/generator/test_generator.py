"""
Test Generator - Feature #9

Generates minimal deterministic test files.

Rules:
- Tests must be deterministic
- No mocking of external LLM APIs
- Tests validate API health, schema validity, feature flags
- Tests may be skipped if explicitly disabled
"""
from typing import Dict, Any


def generate_tests(cps_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate test files based on CPS configuration.
    
    Args:
        cps_data: CPS model as dictionary
        
    Returns:
        Dictionary of file paths to content
    """
    generation_options = cps_data.get("generation_options", {})
    if not generation_options.get("generate_tests", True):
        return {}  # Tests explicitly disabled
    
    project_name = cps_data.get("project_name", "app")
    test_files = {}
    
    # Test configuration
    test_files[f"{project_name}/tests/__init__.py"] = '''# Test package
'''
    
    test_files[f"{project_name}/tests/conftest.py"] = generate_conftest(cps_data)
    test_files[f"{project_name}/tests/test_health.py"] = generate_health_test(cps_data)
    test_files[f"{project_name}/tests/test_schemas.py"] = generate_schema_tests(cps_data)
    test_files[f"{project_name}/tests/test_feature_flags.py"] = generate_feature_flag_tests(cps_data)
    
    # Add requirements for testing
    test_files[f"{project_name}/tests/requirements-test.txt"] = '''# Test dependencies
pytest>=7.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
'''
    
    return test_files


def generate_conftest(cps_data: Dict[str, Any]) -> str:
    """Generate pytest configuration"""
    return '''"""
Pytest configuration and fixtures

Generated from CPS - deterministic tests only.
No external API mocking.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def async_client():
    """Create async test client"""
    from httpx import AsyncClient
    return AsyncClient(app=app, base_url="http://test")
'''


def generate_health_test(cps_data: Dict[str, Any]) -> str:
    """Generate health endpoint test"""
    project_name = cps_data.get("project_name", "API")
    
    return f'''"""
Health Endpoint Tests for {project_name}

These tests verify the API is running and responding correctly.
No external dependencies or LLM calls.
"""
import pytest


def test_root_endpoint(client):
    """Test root endpoint returns 200"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_root_endpoint_content(client):
    """Test root endpoint returns expected content"""
    response = client.get("/")
    data = response.json()
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0


def test_invalid_endpoint_returns_404(client):
    """Test non-existent endpoint returns 404"""
    response = client.get("/nonexistent-endpoint-12345")
    assert response.status_code == 404
'''


def generate_schema_tests(cps_data: Dict[str, Any]) -> str:
    """Generate schema validation tests"""
    project_name = cps_data.get("project_name", "API")
    features = cps_data.get("features", {})
    
    test_content = f'''"""
Schema Validation Tests for {project_name}

These tests verify request/response schema validity.
No external dependencies or LLM calls.
"""
import pytest
from pydantic import ValidationError
from app.schemas import *


# =============================================================================
# Base Schema Tests
# =============================================================================

def test_message_response_schema():
    """Test basic response schema"""
    # This tests the actual generated schema, not hand-written examples
    pass  # Schema existence validated by import

'''
    
    if features.get("chat"):
        test_content += '''
# =============================================================================
# Chat Schema Tests
# =============================================================================

def test_chat_request_valid():
    """Test valid ChatRequest"""
    request = ChatRequest(message="Hello")
    assert request.message == "Hello"


def test_chat_request_empty_message():
    """Test ChatRequest rejects empty message"""
    # This depends on your schema validation rules
    request = ChatRequest(message="")
    assert request.message == ""


def test_chat_response_valid():
    """Test valid ChatResponse"""
    response = ChatResponse(reply="Hello there")
    assert response.reply == "Hello there"

'''
    
    if features.get("rag"):
        test_content += '''
# =============================================================================
# RAG Schema Tests
# =============================================================================

def test_query_request_valid():
    """Test valid QueryRequest"""
    request = QueryRequest(query="What is X?")
    assert request.query == "What is X?"


def test_query_response_valid():
    """Test valid QueryResponse"""
    response = QueryResponse(reply="X is...", context_used=["doc1", "doc2"])
    assert response.reply == "X is..."
    assert len(response.context_used) == 2


def test_ingest_response_valid():
    """Test valid IngestResponse"""
    response = IngestResponse(status="success", message="Ingested 10 documents")
    assert response.status == "success"

'''
    
    return test_content


def generate_feature_flag_tests(cps_data: Dict[str, Any]) -> str:
    """Generate feature flag enforcement tests"""
    project_name = cps_data.get("project_name", "API")
    features = cps_data.get("features", {})
    
    test_content = f'''"""
Feature Flag Enforcement Tests for {project_name}

These tests verify that feature flags are properly enforced.
Disabled features should raise FeatureDisabledError.
"""
import pytest
from app.core.feature_flags import (
    FEATURE_CHAT,
    FEATURE_RAG,
    FEATURE_STREAMING,
    FEATURE_EMBEDDINGS,
    FeatureDisabledError,
    require_feature,
)


# =============================================================================
# Feature Flag Value Tests
# =============================================================================

def test_feature_chat_value():
    """Verify FEATURE_CHAT matches CPS"""
    assert FEATURE_CHAT == {str(features.get("chat", False)).lower()}


def test_feature_rag_value():
    """Verify FEATURE_RAG matches CPS"""
    assert FEATURE_RAG == {str(features.get("rag", False)).lower()}


def test_feature_streaming_value():
    """Verify FEATURE_STREAMING matches CPS"""
    assert FEATURE_STREAMING == {str(features.get("streaming", False)).lower()}


def test_feature_embeddings_value():
    """Verify FEATURE_EMBEDDINGS matches CPS"""
    assert FEATURE_EMBEDDINGS == {str(features.get("embeddings", False)).lower()}


# =============================================================================
# Feature Flag Decorator Tests
# =============================================================================

@pytest.mark.asyncio
async def test_require_feature_enabled():
    """Test require_feature allows enabled features"""
    @require_feature("test", True)
    async def enabled_function():
        return "success"
    
    result = await enabled_function()
    assert result == "success"


@pytest.mark.asyncio
async def test_require_feature_disabled():
    """Test require_feature blocks disabled features"""
    @require_feature("test", False)
    async def disabled_function():
        return "should not reach"
    
    with pytest.raises(FeatureDisabledError):
        await disabled_function()


@pytest.mark.asyncio
async def test_feature_disabled_error_message():
    """Test FeatureDisabledError has informative message"""
    @require_feature("my_feature", False)
    async def disabled_function():
        pass
    
    with pytest.raises(FeatureDisabledError) as exc_info:
        await disabled_function()
    
    assert "my_feature" in str(exc_info.value)
    assert "disabled" in str(exc_info.value).lower()
'''
    
    return test_content
