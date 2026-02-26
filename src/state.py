"""Pydantic state models for the Automaton Auditor."""
import operator
import uuid
from typing import Annotated, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Evidence(BaseModel):
    """Forensic evidence collected by detective agents - objective facts only."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier (UUID) for citation")
    goal: str = Field(description="The forensic goal being investigated")
    found: bool = Field(description="Whether the artifact exists")
    content: Optional[str] = Field(default=None, description="Extracted content or code snippet")
    location: str = Field(description="File path or commit hash")
    rationale: str = Field(description="Rationale for confidence in this evidence")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")


class JudicialOpinion(BaseModel):
    """Opinion rendered by a judge persona."""
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    criterion_id: str = Field(description="Rubric dimension ID")
    score: int = Field(ge=1, le=5, description="Score 1-5")
    argument: str = Field(description="Reasoning for this score")
    cited_evidence: List[str] = Field(default_factory=list, description="Evidence UUIDs referenced (must exist in state.evidences)")


class CriterionResult(BaseModel):
    """Final result for a single rubric criterion after synthesis."""
    dimension_id: str = Field(description="Rubric dimension ID")
    dimension_name: str = Field(description="Human-readable dimension name")
    final_score: int = Field(ge=1, le=5, description="Final score after conflict resolution")
    judge_opinions: List[JudicialOpinion] = Field(description="All three judge opinions for this criterion")
    dissent_summary: Optional[str] = Field(
        default=None,
        description="Required when score variance > 2, explains why Prosecutor and Defense disagreed"
    )
    remediation: str = Field(
        description="Specific file-level instructions for improvement"
    )


class AuditReport(BaseModel):
    """Final audit report structure."""
    repo_url: str = Field(description="Target repository URL")
    executive_summary: str = Field(description="High-level summary and overall score")
    overall_score: float = Field(ge=1.0, le=5.0, description="Average score across all criteria")
    criteria: List[CriterionResult] = Field(description="Criterion-by-criterion breakdown")
    remediation_plan: str = Field(description="Consolidated remediation plan")


class AgentState(TypedDict):
    """Main state for the Automaton Auditor graph.

    Uses reducers (operator.ior, operator.add) to safely handle parallel execution.
    Judges store opinions as dicts (model_dump) to avoid Pydantic serialization warnings
    when LangGraph merges state; chief_justice normalizes back to JudicialOpinion.
    """
    repo_url: str  # Empty string when auditing PDF only
    pdf_path: Optional[str]  # None when auditing repo only
    pdf_display: Optional[str]  # Original PDF URL or path for report (user-facing)
    rubric_path: Optional[str]
    rubric_dimensions: List[Dict]
    synthesis_rules: Dict

    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]
    opinions: Annotated[List[Dict], operator.add]  # Dicts from model_dump(); chief_justice converts to JudicialOpinion
    errors: Annotated[List[str], operator.add]

    final_report: Optional[AuditReport]
