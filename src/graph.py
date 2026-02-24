"""LangGraph StateGraph definition for Automaton Auditor."""
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


def build_auditor_graph():
    """Build the hierarchical StateGraph for the Automaton Auditor.
    
    Architecture:
    - Layer 1: Detectives (parallel fan-out from start)
    - Synchronization: Evidence Aggregator (fan-in)
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
    
    # After aggregation, fan-out to judges (parallel)
    workflow.add_edge("evidence_aggregator", "prosecutor")
    workflow.add_edge("evidence_aggregator", "defense")
    workflow.add_edge("evidence_aggregator", "tech_lead")
    
    # After all judges, synthesize (all judges must complete before chief_justice)
    workflow.add_edge("prosecutor", "chief_justice")
    workflow.add_edge("defense", "chief_justice")
    workflow.add_edge("tech_lead", "chief_justice")
    
    workflow.add_edge("chief_justice", END)
    
    return workflow.compile()
