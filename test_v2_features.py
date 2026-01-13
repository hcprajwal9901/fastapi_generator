import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8001"
API_KEY = "fastapi-gen-secret"

# Test Data
CPS = {
    "project_name": "TestProject",
    "description": "A test project for new features",
    "llm_provider": {
        "type": "openai"
    },
    "features": {
        "chat": True,
        "rag": True,
        "streaming": True,
        "embeddings": True
    },
    "modules": ["users", "reports"],
    "environment": {
        "type": "docker",
        "generate_dockerfile": True,
        "generate_compose": True
    },
    "endpoints": [],
    "auth": {
        "type": "api_key"
    },
    "generation_options": {
        "openapi_first": True,
        "generate_tests": True,
        "failure_first": True
    }
}

def test_endpoint(name, method, endpoint, data=None):
    print(f"Testing {name} ({endpoint})...", end=" ")
    url = f"{BASE_URL}{endpoint}"
    headers = {"X-Api-Key": API_KEY}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, json=data, headers=headers)
            
        if response.status_code == 200:
            print("âœ… OK")
            return response.json()
        else:
            print(f"âŒ FAILED ({response.status_code})")
            print(response.text)
            return None
    except Exception as e:
        print(f"âŒ ERROR: {e}")
        return None

def main():
    print(f"Running tests against {BASE_URL}\n")
    
    # 1. Health
    test_endpoint("Health Check", "GET", "/api/health")
    
    # 2. Providers (Feature #4)
    test_endpoint("List Providers", "GET", "/api/providers")
    
    # 3. Prompts (Feature #5)
    test_endpoint("List Prompts", "GET", "/api/prompts")
    
    # 4. OpenAPI Preview (Feature #1)
    test_endpoint("OpenAPI Preview", "POST", "/api/openapi-preview", CPS)
    
    # 5. Cost Estimation (Feature #2)
    test_endpoint("Cost Estimation", "POST", "/api/estimate-costs", CPS)
    
    # 6. Schemas (Feature #6)
    test_endpoint("Schema Visualization", "POST", "/api/schemas", CPS)
    
    # 7. Pre-flight Check (Feature #7)
    test_endpoint("Pre-flight Validation", "POST", "/api/preflight", {"cps": CPS})
    
    # 8. Generation (Features #3, #8, #9, #11)
    gen_result = test_endpoint("Code Generation", "POST", "/api/generate", CPS)
    
    if gen_result and "files" in gen_result:
        files = gen_result["files"]
        print(f"   Generated {len(files)} files")
        
        # Check for specific files
        expected_files = [
            "TestProject/openapi.json",
            "TestProject/Dockerfile",
            "TestProject/app/core/feature_flags.py",
            "TestProject/tests/test_health.py",
            "TestProject/TODO.md"
        ]
        
        for f in expected_files:
            if f in files:
                print(f"   âœ… Found {f}")
            else:
                print(f"   âŒ Missing {f}")
        
        # 9. Diff (Feature #10)
        # Create 'old' files which are slightly different
        old_files = files.copy()
        if "TestProject/Dockerfile" in old_files:
            old_files["TestProject/Dockerfile"] = "# Old content"
            
        test_endpoint("Diff Computation", "POST", "/api/diff", {
            "old_files": old_files,
            "new_files": files
        })

    print("\nTests completed.")

if __name__ == "__main__":
    main()
