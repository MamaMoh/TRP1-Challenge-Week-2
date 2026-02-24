"""Chief Justice node for deterministic conflict resolution and report synthesis."""
from typing import Dict, Any, List, Optional

from src.config import load_rubric
from src.state import AgentState, JudicialOpinion, CriterionResult, AuditReport
from src.utils.logger import get_logger

logger = get_logger("justice")


def chief_justice_node(state: AgentState) -> AgentState:
    """Synthesize dialectical conflict into final verdict using hardcoded deterministic rules.
    
    Applies synthesis rules:
    - Security flaws cap score at 3
    - Facts override opinions
    - Tech Lead breaks ties
    - Documents dissent when scores differ >2 points
    - Variance re-evaluation when variance > 2
    """
    logger.info(f"ChiefJustice: Synthesizing verdict from {len(state['opinions'])} opinions")
    # Get synthesis rules from rubric
    # Try to load from config (default path)
    try:
        rubric = load_rubric()
        synthesis_rules = rubric.get("synthesis_rules", {})
    except Exception:
        # Fallback to default rules if rubric loading fails
        synthesis_rules = {
            "security_override": "Confirmed security flaws cap total score at 3.",
            "fact_supremacy": "Forensic evidence (facts) always overrules Judicial opinion (interpretation).",
            "functionality_weight": "Tech Lead assessment carries highest weight for architecture criteria.",
            "dissent_requirement": "The Chief Justice must summarize why the Prosecutor and Defense disagreed.",
            "variance_re_evaluation": "If score variance > 2, re-evaluate specific evidence cited by each judge."
        }
    
    # Group opinions by criterion
    opinions_by_criterion: Dict[str, List[JudicialOpinion]] = {}
    for opinion in state["opinions"]:
        if opinion.criterion_id not in opinions_by_criterion:
            opinions_by_criterion[opinion.criterion_id] = []
        opinions_by_criterion[opinion.criterion_id].append(opinion)
    
    criteria_results: List[CriterionResult] = []
    total_score = 0.0
    criterion_count = 0
    
    for dimension in state["rubric_dimensions"]:
        criterion_id = dimension["id"]
        criterion_name = dimension["name"]
        
        opinions = opinions_by_criterion.get(criterion_id, [])
        prosecutor = next((o for o in opinions if o.judge == "Prosecutor"), None)
        defense = next((o for o in opinions if o.judge == "Defense"), None)
        tech_lead = next((o for o in opinions if o.judge == "TechLead"), None)
        
        if not all([prosecutor, defense, tech_lead]):
            # Missing opinions - use lowest score
            final_score = 1
            criteria_results.append(CriterionResult(
                dimension_id=criterion_id,
                dimension_name=criterion_name,
                final_score=final_score,
                judge_opinions=opinions,
                dissent_summary="Missing judge opinions - incomplete evaluation.",
                remediation="Ensure all three judges (Prosecutor, Defense, Tech Lead) provide opinions for this criterion."
            ))
            total_score += final_score
            criterion_count += 1
            continue
        
        # Conflict resolution logic (hardcoded deterministic rules)
        scores = [prosecutor.score, defense.score, tech_lead.score]
        score_variance = max(scores) - min(scores)
        
        # Rule 1: Security Override
        has_security_issue = (
            prosecutor and (
                "security" in prosecutor.argument.lower() or
                "vulnerability" in prosecutor.argument.lower() or
                "os.system" in prosecutor.argument.lower() or
                "shell injection" in prosecutor.argument.lower()
            )
        )
        
        if has_security_issue:
            final_score = min(3, tech_lead.score if tech_lead else 3)
            rationale = "Security flaw detected - score capped at 3 per security_override rule."
        # Rule 2: Variance Re-Evaluation (when variance > 2)
        elif score_variance > 2:
            # High variance - re-evaluate based on evidence
            # Tech Lead breaks tie, but consider evidence quality
            prosecutor_evidence_count = len(prosecutor.cited_evidence) if prosecutor else 0
            defense_evidence_count = len(defense.cited_evidence) if defense else 0
            tech_lead_evidence_count = len(tech_lead.cited_evidence) if tech_lead else 0
            
            # Fact Supremacy: More evidence citations = more weight
            if prosecutor_evidence_count > defense_evidence_count and prosecutor_evidence_count > tech_lead_evidence_count:
                final_score = prosecutor.score
                rationale = f"High variance ({score_variance} points) - Prosecutor cited more evidence, fact supremacy applied."
            elif tech_lead_evidence_count >= prosecutor_evidence_count and tech_lead_evidence_count >= defense_evidence_count:
                final_score = tech_lead.score
                rationale = f"High variance ({score_variance} points) - Tech Lead assessment used as tie-breaker based on evidence quality."
            else:
                final_score = tech_lead.score if tech_lead else (sum(scores) // len(scores))
                rationale = f"High variance ({score_variance} points) - Tech Lead assessment used as tie-breaker."
        # Rule 3: Functionality Weight (for architecture criteria)
        elif "architecture" in criterion_id.lower() or "orchestration" in criterion_id.lower():
            final_score = tech_lead.score if tech_lead else (sum(scores) // len(scores))
            rationale = "Architecture criterion - Tech Lead assessment carries highest weight per functionality_weight rule."
        # Rule 4: Default - Tech Lead breaks ties
        else:
            final_score = tech_lead.score if tech_lead else (sum(scores) // len(scores))
            rationale = "Scores are consistent - Tech Lead assessment confirmed."
        
        # Generate dissent summary if variance > 2
        dissent_summary: Optional[str] = None
        if prosecutor and defense and abs(prosecutor.score - defense.score) > 2:
            dissent_summary = (
                f"Prosecutor ({prosecutor.score}/5) vs Defense ({defense.score}/5) - "
                f"{score_variance} point variance. "
                f"Prosecutor: {prosecutor.argument[:150]}... "
                f"Defense: {defense.argument[:150]}... "
                f"Resolution: {rationale}"
            )
        
        # Generate remediation from Tech Lead opinion
        remediation = tech_lead.argument if tech_lead else "No remediation advice available."
        if final_score < 3:
            remediation += f"\n\nPriority: Address issues identified by Tech Lead. Focus on: {criterion_name}"
        
        criteria_results.append(CriterionResult(
            dimension_id=criterion_id,
            dimension_name=criterion_name,
            final_score=final_score,
            judge_opinions=[prosecutor, defense, tech_lead],
            dissent_summary=dissent_summary,
            remediation=remediation
        ))
        
        total_score += final_score
        criterion_count += 1
    
    # Calculate overall score
    overall_score = total_score / criterion_count if criterion_count > 0 else 0.0
    
    # Generate executive summary
    executive_summary = (
        f"**Automaton Auditor Report**\n\n"
        f"**Target Repository:** {state['repo_url']}\n"
        f"**PDF Report:** {state['pdf_path']}\n\n"
        f"**Overall Score:** {overall_score:.2f}/5.0\n\n"
        f"**Summary:** Evaluated {criterion_count} criteria across forensic accuracy, judicial nuance, "
        f"graph orchestration, and documentation quality. "
    )
    
    # Add summary of key findings
    low_scores = [cr for cr in criteria_results if cr.final_score < 3]
    if low_scores:
        executive_summary += (
            f"{len(low_scores)} criteria scored below 3/5, indicating areas requiring remediation. "
        )
    
    high_scores = [cr for cr in criteria_results if cr.final_score >= 4]
    if high_scores:
        executive_summary += (
            f"{len(high_scores)} criteria scored 4/5 or higher, indicating strong implementation. "
        )
    
    # Generate consolidated remediation plan
    remediation_plan = "## Remediation Plan\n\n"
    for cr in criteria_results:
        if cr.final_score < 3:
            remediation_plan += f"### {cr.dimension_name} (Score: {cr.final_score}/5)\n\n"
            remediation_plan += f"{cr.remediation}\n\n"
    
    if not any(cr.final_score < 3 for cr in criteria_results):
        remediation_plan += "No critical remediation required. All criteria scored 3/5 or higher.\n"
    
    # Create AuditReport
    audit_report = AuditReport(
        repo_url=state["repo_url"],
        executive_summary=executive_summary,
        overall_score=overall_score,
        criteria=criteria_results,
        remediation_plan=remediation_plan
    )
    
    return {"final_report": audit_report}
