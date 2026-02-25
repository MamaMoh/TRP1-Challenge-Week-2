"""Context builder for preparing agent context from rubric."""
from typing import Dict, List, Any


def filter_rubric_by_artifact(rubric: Dict[str, Any], target_artifact: str) -> List[Dict[str, Any]]:
    """Filter rubric dimensions by target artifact.
    
    Args:
        rubric: Loaded rubric dictionary
        target_artifact: Either "github_repo" or "pdf_report"
        
    Returns:
        List of dimensions that match the target artifact
    """
    return [
        dim for dim in rubric["dimensions"]
        if dim.get("target_artifact") == target_artifact
    ]


def get_forensic_instructions(rubric: Dict[str, Any], criterion_id: str) -> str:
    """Get forensic instruction for a specific criterion.
    
    Args:
        rubric: Loaded rubric dictionary
        criterion_id: Criterion ID to get instruction for
        
    Returns:
        Forensic instruction string
        
    Raises:
        ValueError: If criterion_id not found
    """
    for dim in rubric["dimensions"]:
        if dim["id"] == criterion_id:
            return dim["forensic_instruction"]
    
    raise ValueError(f"Criterion ID not found: {criterion_id}")


def get_judicial_logic(rubric: Dict[str, Any], criterion_id: str, persona: str) -> str:
    """Get judicial logic for a specific criterion and persona.

    Args:
        rubric: Loaded rubric dictionary (must have "dimensions" key).
        criterion_id: Criterion ID.
        persona: One of "prosecutor", "defense", "tech_lead".

    Returns:
        Judicial logic string for the persona. If dimension has no judicial_logic,
        returns a fallback built from success_pattern and failure_pattern.
    """
    for dim in rubric.get("dimensions", []):
        if dim.get("id") == criterion_id:
            logic = dim.get("judicial_logic")
            if logic and isinstance(logic, dict) and persona in logic:
                return logic[persona]
            # Fallback when rubric has no judicial_logic (e.g. forensic-only spec)
            success = dim.get("success_pattern", "Criteria met.")
            failure = dim.get("failure_pattern", "Criteria not met.")
            return f"Success: {success}. Failure: {failure}. Evaluate as {persona}."
    raise ValueError(f"Criterion ID not found: {criterion_id}")


def get_synthesis_rules(rubric: Dict[str, Any]) -> Dict[str, str]:
    """Get synthesis rules from rubric.
    
    Args:
        rubric: Loaded rubric dictionary
        
    Returns:
        Dictionary of synthesis rule names to descriptions
    """
    return rubric.get("synthesis_rules", {})


def build_detective_context(rubric: Dict[str, Any], target_artifact: str) -> List[Dict[str, Any]]:
    """Build context for detective agents based on target artifact.
    
    Args:
        rubric: Loaded rubric dictionary
        target_artifact: Either "github_repo" or "pdf_report"
        
    Returns:
        List of dimension contexts with forensic instructions
    """
    dimensions = filter_rubric_by_artifact(rubric, target_artifact)
    
    return [
        {
            "criterion_id": dim["id"],
            "criterion_name": dim["name"],
            "forensic_instruction": dim["forensic_instruction"],
        }
        for dim in dimensions
    ]


def build_judge_context(rubric: Dict[str, Any], criterion_id: str, persona: str) -> Dict[str, Any]:
    """Build context for judge persona evaluating a specific criterion.
    
    Args:
        rubric: Loaded rubric dictionary
        criterion_id: Criterion ID to evaluate
        persona: One of "prosecutor", "defense", "tech_lead"
        
    Returns:
        Dictionary with criterion info and judicial logic
    """
    for dim in rubric["dimensions"]:
        if dim["id"] == criterion_id:
            return {
                "criterion_id": dim["id"],
                "criterion_name": dim["name"],
                "judicial_logic": get_judicial_logic(rubric, criterion_id, persona),
            }
    
    raise ValueError(f"Criterion ID not found: {criterion_id}")
