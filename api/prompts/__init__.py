# Prompts module - Feature #5: Editable Prompt Templates
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """
    Load a prompt template from file.
    
    Args:
        name: Prompt name (without .txt extension)
        
    Returns:
        Prompt template content
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_path = PROMPTS_DIR / f"{name}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt template '{name}' not found at {prompt_path}. "
            f"Available prompts: {list_prompts()}"
        )
    return prompt_path.read_text(encoding="utf-8")


def list_prompts() -> list:
    """List all available prompt templates"""
    return [f.stem for f in PROMPTS_DIR.glob("*.txt")]


def save_prompt(name: str, content: str) -> None:
    """
    Save a prompt template to file.
    
    Args:
        name: Prompt name (without .txt extension)
        content: Prompt content
    """
    prompt_path = PROMPTS_DIR / f"{name}.txt"
    prompt_path.write_text(content, encoding="utf-8")
