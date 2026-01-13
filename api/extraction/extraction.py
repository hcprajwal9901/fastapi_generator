"""
CPS Extraction Module

Extracts Canonical Project Specification from natural language using LLM.
Uses editable prompt templates from the prompts directory.
"""
import json
import os
from typing import Dict, Any
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key or api_key == "your_api_key_here":
    print("WARNING: OPENAI_API_KEY is not set or still has the placeholder value in .env")

client = AsyncOpenAI(api_key=api_key if api_key != "your_api_key_here" else "MISSING")

# Path to prompts directory
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load_extraction_prompt() -> str:
    """Load the extraction prompt from file, or use fallback"""
    prompt_file = PROMPTS_DIR / "extraction.txt"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    
    # Fallback to inline prompt if file doesn't exist
    return """Extract the information explicitly stated in the user input.
If a value is not present, infer a reasonable default based on context (especially for project_name and description).
For boolean features, default to false unless implied.
Output strictly valid JSON matching the CPS schema.

CPS Schema:
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
    "chat": boolean,
    "rag": boolean,
    "streaming": boolean,
    "embeddings": boolean
  },
  "endpoints": [
    {
      "path": "string",
      "method": "GET | POST",
      "uses_llm": boolean,
      "description": "string | null"
    }
  ],
  "auth": {
    "type": "none | api_key | jwt"
  },
  "modules": ["string"],
  "environment": {
    "type": "local | docker | production",
    "generate_dockerfile": boolean,
    "generate_compose": boolean
  },
  "generation_options": {
    "openapi_first": boolean,
    "generate_tests": boolean,
    "failure_first": boolean
  }
}

User Input:
{text}

Instructions:
- Identify logical domains or modules based on requirements (e.g., "users", "billing", "analytics").
- List them in the "modules" array.
- Ensure project_name and description are professional.
- For llm_provider, default to {"type": "openai"} unless specified otherwise.
- For environment, default to {"type": "local", "generate_dockerfile": false, "generate_compose": false}.
- For generation_options, default to {"openapi_first": false, "generate_tests": true, "failure_first": true}.
"""


async def extract_cps(text: str) -> Dict[str, Any]:
    """
    Extract CPS from natural language description.
    
    Uses the extraction prompt template from the prompts directory.
    """
    try:
        extraction_prompt = load_extraction_prompt()
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a structured data extractor."},
                {"role": "user", "content": extraction_prompt.replace("{text}", text)}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        # Fallback or error handling
        return {"error": str(e)}


async def refine_code(cps: Dict[str, Any], files: Dict[str, str], feedback: str) -> Dict[str, Any]:
    """
    Refine generated code based on user feedback.
    
    Note: This function uses LLM to modify code. The output should be
    reviewed by the user before deployment.
    """
    try:
        prompt = f"""
        You are an expert full-stack AI engineer. 
        A user has generated a FastAPI project and has some feedback or discovered bugs.
        
        Current project specification (CPS):
        {json.dumps(cps, indent=2)}
        
        Current generated files:
        {json.dumps(files, indent=2)}
        
        User Feedback/Issues:
        {feedback}
        
        Instruction:
        - Analyze the feedback and the current code.
        - Fix any bugs mentioned or implied.
        - Implement requested changes.
        - Return a complete JSON object where keys are the file paths and values are the NEW content for those files.
        - Include ALL files in the output (except unchanged binary files if any) to maintain a complete project state.
        - Return ONLY the JSON object.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a code refiner and bug fixer. Always return a full file map in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

