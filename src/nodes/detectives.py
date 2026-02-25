"""Detective layer nodes for forensic evidence collection."""
import os
import tempfile
from typing import Dict, Any, List

from src.state import AgentState, Evidence
from src.tools.git_tools import clone_repo, analyze_git_history, get_repo_file_list
from src.tools.ast_parser import (
    verify_state_models,
    analyze_graph_structure,
    verify_safe_tool_engineering,
    verify_structured_output
)
from src.tools.pdf_parser import parse_pdf, extract_keywords, verify_file_claims
from src.utils.context_builder import build_detective_context
from src.utils.logger import get_logger

logger = get_logger("detectives")


def repo_investigator_node(state: AgentState) -> AgentState:
    """Forensic analysis of the GitHub repository.
    
    Collects evidence for all rubric dimensions targeting github_repo.
    Handles retries up to 3 times on failure.
    """
    repo_dimensions = [
        d for d in state["rubric_dimensions"]
        if d.get("target_artifact") == "github_repo"
    ]
    
    evidences = {}
    max_retries = 3
    repo_path = None
    
    # Retry logic for git clone
    for attempt in range(max_retries):
        try:
            logger.info(f"RepoInvestigator: Attempt {attempt + 1}/{max_retries} - Cloning {state['repo_url']}")
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_path = clone_repo(state["repo_url"], tmpdir)
                logger.info(f"RepoInvestigator: Successfully cloned repository to {repo_path}")
                
                # Run all forensic analyses
                git_evidence_data = analyze_git_history(repo_path)
                state_evidence_data = verify_state_models(repo_path)
                graph_evidence_data = analyze_graph_structure(repo_path)
                safety_evidence_data = verify_safe_tool_engineering(repo_path)
                structured_output_data = verify_structured_output(repo_path)
                
                # Create evidence for each dimension based on criterion_id
                for dimension in repo_dimensions:
                    criterion_id = dimension["id"]
                    evidence_list = []
                    
                    # Map criterion_id to appropriate evidence
                    if criterion_id == "git_forensic_analysis":
                        evidence_list.append(Evidence(
                            goal="Git Forensic Analysis",
                            found=git_evidence_data["has_progression"],
                            content=f"Commits: {git_evidence_data['commit_count']}\n{git_evidence_data['commit_summary']}",
                            location=state["repo_url"],
                            rationale=git_evidence_data["rationale"],
                            confidence=git_evidence_data["confidence"]
                        ))
                    
                    elif criterion_id == "state_management_rigor":
                        evidence_list.append(Evidence(
                            goal="State Management Rigor",
                            found=state_evidence_data["has_pydantic_state"],
                            content=state_evidence_data["code_snippet"],
                            location=state_evidence_data["file_path"],
                            rationale=state_evidence_data["rationale"],
                            confidence=state_evidence_data["confidence"]
                        ))
                    
                    elif criterion_id == "graph_orchestration":
                        evidence_list.append(Evidence(
                            goal="Graph Orchestration Architecture",
                            found=graph_evidence_data["has_parallel_execution"],
                            content=graph_evidence_data["graph_structure"],
                            location=graph_evidence_data["file_path"],
                            rationale=graph_evidence_data["rationale"],
                            confidence=graph_evidence_data["confidence"]
                        ))
                    
                    elif criterion_id == "safe_tool_engineering":
                        evidence_list.append(Evidence(
                            goal="Safe Tool Engineering",
                            found=safety_evidence_data["is_safe"],
                            content=f"Sandboxing: {safety_evidence_data['uses_sandboxing']}, "
                                   f"Subprocess: {safety_evidence_data['uses_subprocess']}, "
                                   f"os.system: {safety_evidence_data['has_os_system']}",
                            location=safety_evidence_data["file_path"],
                            rationale=safety_evidence_data["rationale"],
                            confidence=safety_evidence_data["confidence"]
                        ))
                    
                    elif criterion_id == "structured_output_enforcement":
                        evidence_list.append(Evidence(
                            goal="Structured Output Enforcement",
                            found=structured_output_data["has_structured_output"],
                            content=f"Uses Pydantic: {structured_output_data['uses_pydantic']}, "
                                   f"Has retry: {structured_output_data['has_retry']}",
                            location=structured_output_data["file_path"],
                            rationale=structured_output_data["rationale"],
                            confidence=structured_output_data["confidence"]
                        ))
                    
                    elif criterion_id == "judicial_nuance":
                        # Check for distinct judge prompts (basic check)
                        judges_file = os.path.join(repo_path, "src/nodes/judges.py")
                        if os.path.exists(judges_file):
                            with open(judges_file, "r", encoding="utf-8") as f:
                                judges_content = f.read()
                            
                            has_prosecutor = "prosecutor" in judges_content.lower() and "critical" in judges_content.lower()
                            has_defense = "defense" in judges_content.lower() and ("charitable" in judges_content.lower() or "forgiving" in judges_content.lower())
                            has_tech_lead = "tech" in judges_content.lower() and "lead" in judges_content.lower()
                            
                            # Full file so judges see persona prompts and get_judicial_logic
                            snippet_len = 3500
                            evidence_list.append(Evidence(
                                goal="Judicial Nuance and Dialectics",
                                found=has_prosecutor and has_defense and has_tech_lead,
                                content=judges_content[:snippet_len] if len(judges_content) > snippet_len else judges_content,
                                location="src/nodes/judges.py",
                                rationale=f"Prosecutor: {has_prosecutor}, Defense: {has_defense}, Tech Lead: {has_tech_lead}",
                                confidence=0.8 if (has_prosecutor and has_defense and has_tech_lead) else 0.4
                            ))
                    
                    elif criterion_id == "chief_justice_synthesis":
                        justice_file = os.path.join(repo_path, "src/nodes/justice.py")
                        if os.path.exists(justice_file):
                            with open(justice_file, "r", encoding="utf-8") as f:
                                justice_content = f.read()
                            
                            has_hardcoded_rules = (
                                "if" in justice_content and
                                "security" in justice_content.lower() and
                                "fact" in justice_content.lower() and
                                "deterministic" in justice_content.lower()
                            )
                            
                            # Full file so judges see synthesis rules, dissent, and report structure
                            snippet_len = 4000
                            evidence_list.append(Evidence(
                                goal="Chief Justice Synthesis Engine",
                                found=has_hardcoded_rules,
                                content=justice_content[:snippet_len] if len(justice_content) > snippet_len else justice_content,
                                location="src/nodes/justice.py",
                                rationale=f"Hardcoded deterministic rules: {has_hardcoded_rules}",
                                confidence=0.9 if has_hardcoded_rules else 0.3
                            ))
                    
                    if evidence_list:
                        evidences[criterion_id] = evidence_list
                
                logger.info(f"RepoInvestigator: Collected evidence for {len(evidences)} criteria")
                break  # Success, exit retry loop
                
        except Exception as e:
            logger.warning(f"RepoInvestigator: Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                continue  # Retry
            else:
                # Final attempt failed, log error
                error_msg = f"RepoInvestigator failed after {max_retries} attempts: {str(e)}"
                logger.error(error_msg)
                return {
                    "evidences": evidences,  # Partial evidence if any
                    "errors": [error_msg]
                }
    
    return {"evidences": evidences}


def doc_analyst_node(state: AgentState) -> AgentState:
    """Forensic analysis of the PDF report.
    
    Collects evidence for all rubric dimensions targeting pdf_report.
    Handles retries up to 3 times on failure.
    """
    pdf_dimensions = [
        d for d in state["rubric_dimensions"]
        if d.get("target_artifact") == "pdf_report"
    ]
    
    evidences = {}
    max_retries = 3
    
    # Retry logic for PDF parsing
    for attempt in range(max_retries):
        try:
            pdf_content = parse_pdf(state["pdf_path"])
            
            # Extract keywords mentioned in rubric
            keywords = ["Dialectical Synthesis", "Fan-In", "Fan-Out", "Metacognition", "State Synchronization"]
            keyword_results = extract_keywords(pdf_content, keywords)
            
            # Get repo file list for cross-referencing (clone so we can verify paths mentioned in PDF)
            repo_files = get_repo_file_list(state["repo_url"])
            
            # Create evidence for each dimension
            for dimension in pdf_dimensions:
                criterion_id = dimension["id"]
                evidence_list = []
                
                if criterion_id == "theoretical_depth":
                    # Keyword search evidence
                    found_keywords = []
                    for keyword in keywords:
                        if keyword_results[keyword]:
                            found_keywords.extend(keyword_results[keyword])
                    
                    if found_keywords:
                        evidence_list.append(Evidence(
                            goal="Theoretical Depth Analysis",
                            found=True,
                            content="\n".join(found_keywords[:5]),  # First 5 matches
                            location=state["pdf_path"],
                            rationale=f"Found {len(found_keywords)} keyword matches in PDF with context",
                            confidence=0.8 if len(found_keywords) >= 2 else 0.5
                        ))
                    else:
                        evidence_list.append(Evidence(
                            goal="Theoretical Depth Analysis",
                            found=False,
                            content=None,
                            location=state["pdf_path"],
                            rationale="No theoretical keywords found in PDF",
                            confidence=0.7
                        ))
                
                elif criterion_id == "report_accuracy":
                    # Cross-reference file paths mentioned in PDF against actual repo files
                    mentioned_files = verify_file_claims(pdf_content, repo_files)
                    verified_count = sum(1 for v in mentioned_files.values() if v)
                    hallucinated_count = sum(1 for v in mentioned_files.values() if not v)
                    evidence_list.append(Evidence(
                        goal="Report Accuracy (Cross-Reference)",
                        found=hallucinated_count == 0,
                        content=f"Verified paths: {verified_count}, Hallucinated paths: {hallucinated_count}",
                        location=state["pdf_path"],
                        rationale=f"Cross-referenced {len(mentioned_files)} file paths mentioned in PDF",
                        confidence=0.9 if hallucinated_count == 0 else 0.5
                    ))

                if evidence_list:
                    evidences[criterion_id] = evidence_list

            break  # Success, exit retry loop after processing all dimensions

        except Exception as e:
            if attempt < max_retries - 1:
                continue  # Retry
            else:
                # Final attempt failed, log error
                error_msg = f"DocAnalyst failed after {max_retries} attempts: {str(e)}"
                return {
                    "evidences": evidences,  # Partial evidence if any
                    "errors": [error_msg]
                }
    
    return {"evidences": evidences}


def _repo_has_architecture_diagram(repo_url: str) -> tuple[bool, str]:
    """Check if repo contains an architectural diagram (e.g. docs/architecture.md or README with Mermaid)."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = clone_repo(repo_url, tmpdir)
            for rel_path in ("docs/architecture.md", "README.md"):
                full = os.path.join(repo_path, rel_path)
                if os.path.exists(full):
                    with open(full, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if "flowchart" in content or "graph " in content or "stateDiagram" in content:
                        snippet = content[:600] if len(content) > 600 else content
                        return True, f"Diagram in {rel_path}: " + snippet
    except Exception:
        pass
    return False, ""


def vision_inspector_node(state: AgentState) -> AgentState:
    """Check repo for architectural diagram (e.g. Mermaid in docs/architecture.md or README)."""
    visual_dimensions = [
        d for d in state["rubric_dimensions"]
        if d.get("target_artifact") == "pdf_images" or d.get("id") == "swarm_visual"
    ]
    evidences = {}
    found_diagram, diagram_content = _repo_has_architecture_diagram(state["repo_url"])
    for dimension in visual_dimensions:
        criterion_id = dimension["id"]
        evidences[criterion_id] = [Evidence(
            goal="Architectural Diagram Analysis",
            found=found_diagram,
            content=diagram_content or None,
            location="docs/architecture.md or README.md",
            rationale="StateGraph diagram (Mermaid flowchart) in repo" if found_diagram else "No diagram found in repo",
            confidence=0.9 if found_diagram else 0.3
        )]
    return {"evidences": evidences}


def evidence_aggregator_node(state: AgentState) -> AgentState:
    """Synchronization point: aggregate all evidence before judicial review.
    
    All evidences are already merged via operator.ior reducer.
    This node validates completeness.
    """
    # All evidences are already merged via operator.ior
    # This node can validate completeness or perform additional aggregation logic
    return state
