"""Configuration and rubric loading for Automaton Auditor."""
import json
import os
from pathlib import Path
from typing import Dict, List, Any

from src.paths import RUBRIC_DIR, DEFAULT_RUBRIC_PATH


def list_available_rubrics() -> List[Path]:
    """List available rubric JSON files in the rubric directory.

    Returns:
        List of Paths to rubric files (sorted by name).
    """
    if not RUBRIC_DIR.exists():
        return []
    return sorted(RUBRIC_DIR.glob("*.json"))


def load_rubric(rubric_path: str = None) -> Dict[str, Any]:
    """Load the machine-readable rubric JSON.

    Args:
        rubric_path: Path to rubric JSON file (default: paths.DEFAULT_RUBRIC_PATH).

    Returns:
        Dictionary containing rubric metadata, dimensions, and synthesis rules.

    Raises:
        FileNotFoundError: If rubric file doesn't exist.
        json.JSONDecodeError: If rubric is malformed JSON.
        ValueError: If rubric schema is invalid (missing required fields).
    """
    path = Path(rubric_path) if rubric_path else DEFAULT_RUBRIC_PATH

    if not path.exists():
        raise FileNotFoundError(f"Rubric file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        rubric = json.load(f)

    # Validate rubric schema
    required_keys = ["rubric_metadata", "dimensions", "synthesis_rules"]
    for key in required_keys:
        if key not in rubric:
            raise ValueError(f"Invalid rubric schema: missing '{key}'")

    # Validate dimensions
    if not isinstance(rubric["dimensions"], list) or len(rubric["dimensions"]) == 0:
        raise ValueError("Invalid rubric schema: 'dimensions' must be a non-empty list")

    for dim in rubric["dimensions"]:
        required_dim_keys = ["id", "name", "target_artifact", "forensic_instruction"]
        for key in required_dim_keys:
            if key not in dim:
                raise ValueError(f"Invalid dimension schema: missing '{key}'")

        # judicial_logic is optional (some rubrics only have forensic fields)
        if "judicial_logic" in dim:
            if not all(
                persona in dim["judicial_logic"]
                for persona in ["prosecutor", "defense", "tech_lead"]
            ):
                raise ValueError(
                    f"Invalid dimension '{dim['id']}': judicial_logic must have prosecutor, defense, tech_lead"
                )

    return rubric


def get_env_var(key: str, default: str = None, required: bool = False) -> str:
    """Get environment variable with optional default and required flag.
    
    Args:
        key: Environment variable name
        default: Default value if not set
        required: If True, raise error if variable not set
        
    Returns:
        Environment variable value or default
        
    Raises:
        ValueError: If required variable is not set
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable not set: {key}")
    
    return value


def load_env_config() -> Dict[str, str]:
    """Load configuration from environment variables.

    Loads .env first, then .env.example if no API key is set (so keys in .env.example work).
    Prefer putting secrets in .env (usually gitignored); .env.example is the template.
    """
    from dotenv import load_dotenv

    load_dotenv()  # .env
    openai_key = get_env_var("OPENAI_API_KEY", required=False)
    openrouter_key = get_env_var("OPENROUTER_API_KEY", required=False)

    if not openai_key and not openrouter_key:
        # Fallback: try .env.example (e.g. user put key there)
        load_dotenv(".env.example")
        openai_key = get_env_var("OPENAI_API_KEY", required=False)
        openrouter_key = get_env_var("OPENROUTER_API_KEY", required=False)

    if not openai_key and not openrouter_key:
        raise ValueError(
            "Either OPENAI_API_KEY or OPENROUTER_API_KEY must be set. "
            "Add one to a .env file (or .env.example) in the project root."
        )
    
    # Determine which provider to use (OpenRouter takes precedence if both are set)
    use_openrouter = bool(openrouter_key)
    api_key = openrouter_key if use_openrouter else openai_key
    
    return {
        "api_key": api_key,
        "use_openrouter": use_openrouter,
        "openrouter_base_url": get_env_var("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "model": get_env_var("LLM_MODEL", "gpt-4o"),  # Default model, can be overridden
        "langchain_tracing_v2": get_env_var("LANGCHAIN_TRACING_V2", "false").lower() == "true",
        "langchain_api_key": get_env_var("LANGCHAIN_API_KEY", ""),
        "langchain_project": get_env_var("LANGCHAIN_PROJECT", "automaton-auditor"),
    }
