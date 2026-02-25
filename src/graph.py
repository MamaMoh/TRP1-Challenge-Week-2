"""LangGraph StateGraph definition for Automaton Auditor."""
from typing import Literal

from langgraph.graph import StateGraph, END

from src.state import AgentState
from src.nodes.detectives import (
    repo_investigator_node,
    doc_analyst_node,
    vision_inspector_node,
    evidence_aggregator_node
)
from src.nodes.judges import (
    prosecutor_node,
    defense_node,
    tech_lead_node
)
from src.nodes.justice import chief_justice_node


def start_node(state: AgentState) -> AgentState:
    """Entry node that passes state through unchanged for parallel fan-out."""
    return state


def to_judges_node(state: AgentState) -> AgentState:
    """Passthrough node after evidence aggregation when evidence is sufficient (no failure)."""
    return state


def handle_failure_or_missing_node(state: AgentState) -> AgentState:
    """Handle Evidence Missing or Node Failure: record degradation and proceed with partial audit.
    
    Invoked when detectives reported errors or no evidence was collected.
    Judges and Chief Justice still run so the report can reflect the failure.
    """
    msg = (
        "Audit degraded: evidence missing or node failure during detective phase; "
        "proceeding with partial evaluation."
    )
    errors = list(state.get("errors") or [])
    if msg not in errors:
        errors.append(msg)
    return {"errors": errors}


def route_after_aggregator(
    state: AgentState,
) -> Literal["to_judges", "handle_failure_or_missing"]:
    """Conditional edge: route to judges or to failure/missing handler.
    
    Node Failure: any errors were recorded during detective execution.
    Evidence Missing: no evidence was collected for any rubric dimension.
    """
    errors = state.get("errors") or []
    evidences = state.get("evidences") or {}
    # Node failure: one or more detectives reported an error
    if len(errors) > 0:
        return "handle_failure_or_missing"
    # Evidence missing: no evidence collected at all
    if not evidences or len(evidences) == 0:
        return "handle_failure_or_missing"
    return "to_judges"


def build_auditor_graph():
    """Build the hierarchical StateGraph for the Automaton Auditor.
    
    Architecture:
    - Layer 1: Detectives (parallel fan-out from start)
    - Synchronization: Evidence Aggregator (fan-in)
    - Conditional: Evidence Missing / Node Failure -> handle_failure_or_missing; else -> to_judges
    - Layer 2: Judges (parallel fan-out)
    - Layer 3: Chief Justice (synthesis)
    """
    workflow = StateGraph(AgentState)
    
    # Entry node for parallel fan-out
    workflow.add_node("start", start_node)
    
    # Layer 1: Detective Layer (Parallel Fan-Out)
    workflow.add_node("repo_investigator", repo_investigator_node)
    workflow.add_node("doc_analyst", doc_analyst_node)
    workflow.add_node("vision_inspector", vision_inspector_node)
    
    # Synchronization: Evidence Aggregation (Fan-In)
    workflow.add_node("evidence_aggregator", evidence_aggregator_node)
    
    # Conditional routing: Evidence Missing / Node Failure handling (rubric requirement)
    workflow.add_node("to_judges", to_judges_node)
    workflow.add_node("handle_failure_or_missing", handle_failure_or_missing_node)
    workflow.add_conditional_edges(
        "evidence_aggregator",
        route_after_aggregator,
        path_map={
            "to_judges": "to_judges",
            "handle_failure_or_missing": "handle_failure_or_missing",
        },
    )
    
    # Layer 2: Judicial Layer (Parallel Fan-Out)
    workflow.add_node("prosecutor", prosecutor_node)
    workflow.add_node("defense", defense_node)
    workflow.add_node("tech_lead", tech_lead_node)
    
    # Layer 3: Supreme Court (Synthesis)
    workflow.add_node("chief_justice", chief_justice_node)
    
    # Define the flow - start node fans out to all detectives in parallel
    workflow.set_entry_point("start")
    
    # Parallel execution of detectives (fan-out from start)
    workflow.add_edge("start", "repo_investigator")
    workflow.add_edge("start", "doc_analyst")
    workflow.add_edge("start", "vision_inspector")
    
    # All detectives converge at evidence aggregator (fan-in)
    workflow.add_edge("repo_investigator", "evidence_aggregator")
    workflow.add_edge("doc_analyst", "evidence_aggregator")
    workflow.add_edge("vision_inspector", "evidence_aggregator")
    
    # From both conditional paths, fan-out to judges (parallel)
    workflow.add_edge("to_judges", "prosecutor")
    workflow.add_edge("to_judges", "defense")
    workflow.add_edge("to_judges", "tech_lead")
    workflow.add_edge("handle_failure_or_missing", "prosecutor")
    workflow.add_edge("handle_failure_or_missing", "defense")
    workflow.add_edge("handle_failure_or_missing", "tech_lead")
    
    # After all judges, synthesize (all judges must complete before chief_justice)
    workflow.add_edge("prosecutor", "chief_justice")
    workflow.add_edge("defense", "chief_justice")
    workflow.add_edge("tech_lead", "chief_justice")
    
    workflow.add_edge("chief_justice", END)
    
    return workflow.compile()
