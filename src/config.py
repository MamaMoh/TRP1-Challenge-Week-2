"""Configuration and rubric loading for Automaton Auditor."""
import json
import os
from pathlib import Path
from typing import Dict, List, Any


def load_rubric(rubric_path: str = "rubric/week2_rubric.json") -> Dict[str, Any]:
    """Load the machine-readable rubric JSON.
    
    Args:
        rubric_path: Path to rubric JSON file
        
    Returns:
        Dictionary containing rubric metadata, dimensions, and synthesis rules
        
    Raises:
        FileNotFoundError: If rubric file doesn't exist
        json.JSONDecodeError: If rubric is malformed JSON
        ValueError: If rubric schema is invalid (missing required fields)
    """
    rubric_file = Path(rubric_path)
    
    if not rubric_file.exists():
        raise FileNotFoundError(f"Rubric file not found: {rubric_path}")
    
    with open(rubric_file, "r", encoding="utf-8") as f:
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
        required_dim_keys = ["id", "name", "target_artifact", "forensic_instruction", "judicial_logic"]
        for key in required_dim_keys:
            if key not in dim:
                raise ValueError(f"Invalid dimension schema: missing '{key}'")
        
        # Validate judicial_logic has all three personas
        if not all(persona in dim["judicial_logic"] for persona in ["prosecutor", "defense", "tech_lead"]):
            raise ValueError(f"Invalid dimension '{dim['id']}': judicial_logic must have prosecutor, defense, tech_lead")
    
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
    
    Returns:
        Dictionary with configuration values
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        "openai_api_key": get_env_var("OPENAI_API_KEY", required=True),
        "langchain_tracing_v2": get_env_var("LANGCHAIN_TRACING_V2", "false").lower() == "true",
        "langchain_api_key": get_env_var("LANGCHAIN_API_KEY", ""),
        "langchain_project": get_env_var("LANGCHAIN_PROJECT", "automaton-auditor"),
    }
