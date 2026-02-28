"""Chief Justice Synthesis Engine — deterministic conflict resolution and report synthesis.

CHIEF JUSTICE SYNTHESIS (rubric: chief_justice_synthesis):
Conflict resolution uses hardcoded deterministic Python logic (no LLM). Rules applied in order:

1. Rule of Security (security_override): If Prosecutor identifies a confirmed security vulnerability
   (e.g. os.system detected, shell injection), score is capped at 3 regardless of Defense/Tech Lead.
2. Rule of Evidence (fact_supremacy): Forensic evidence overrules judicial opinion; when variance > 2,
   Tech Lead and evidence count (cited_evidence) determine the final score.
3. Rule of Functionality (functionality_weight): For architecture/orchestration criteria,
   Tech Lead assessment carries highest weight.
4. Variance re-evaluation: When score variance > 2 between judges, re-evaluate using Tech Lead
   as tie-breaker; dissent summary is required in the report.

Output is a structured AuditReport (Pydantic), not console print.
"""
from typing import Dict, Any, List, Optional, Tuple, Callable

from src.config import load_rubric
from src.state import AgentState, JudicialOpinion, CriterionResult, AuditReport
from src.utils.logger import get_logger

logger = get_logger("justice")

# Expected number of judge personas (Prosecutor, Defense, TechLead)
NUM_JUDGES = 3


def _security_override_condition(
    prosecutor: JudicialOpinion,
    _defense: JudicialOpinion,
    _tech_lead: JudicialOpinion,
    _criterion_id: str,
) -> bool:
    """True only when Prosecutor explicitly identifies a confirmed security flaw.
    Requires concrete language (os.system detected, shell injection, or confirmed
    security vulnerability) to avoid capping on vague 'security' wording.
    """
    if not prosecutor or not prosecutor.argument:
        return False
    arg = prosecutor.argument.lower()
    # Explicit security findings only
    if "shell injection" in arg or "command injection" in arg:
        return True
    if "security vulnerability" in arg or "security flaw" in arg:
        return True
    if "os.system" in arg and any(
        w in arg for w in ("detected", "found", "used", "present", "violation", "call")
    ):
        return True
    return False


def _apply_security_override(
    prosecutor: JudicialOpinion,
    defense: JudicialOpinion,
    tech_lead: JudicialOpinion,
    _criterion_id: str,
) -> Tuple[int, str]:
    """Rule 1: Confirmed security flaw caps score at 3."""
    score = min(3, tech_lead.score if tech_lead else 3)
    return score, "Security flaw detected - score capped at 3 per security_override rule."


def _apply_variance_re_evaluation(
    prosecutor: JudicialOpinion,
    defense: JudicialOpinion,
    tech_lead: JudicialOpinion,
    _criterion_id: str,
) -> Tuple[int, str]:
    """Rule 2: Variance > 2 — Tech Lead tie-breaker; evidence count is secondary."""
    scores = [p.score for p in (prosecutor, defense, tech_lead) if p]
    score_variance = max(scores) - min(scores) if scores else 0
    # Prefer Tech Lead as tie-breaker (functionality weight); evidence count only if TL tied
    tl_score = tech_lead.score if tech_lead else (sum(scores) // len(scores) if scores else 1)
    p_ev = len(prosecutor.cited_evidence) if prosecutor else 0
    d_ev = len(defense.cited_evidence) if defense else 0
    tl_ev = len(tech_lead.cited_evidence) if tech_lead else 0
    if p_ev > d_ev and p_ev > tl_ev:
        return prosecutor.score, (
            f"High variance ({score_variance} points) - Prosecutor cited more evidence, fact supremacy applied."
        )
    return tl_score, (
        f"High variance ({score_variance} points) - Tech Lead assessment used as tie-breaker."
    )


def _apply_functionality_weight(
    _p: JudicialOpinion,
    _d: JudicialOpinion,
    tech_lead: JudicialOpinion,
    criterion_id: str,
) -> Tuple[int, str]:
    """Rule 3: Architecture/orchestration criteria — Tech Lead carries highest weight."""
    s = tech_lead.score if tech_lead else 3
    return s, "Architecture criterion - Tech Lead assessment carries highest weight per functionality_weight rule."


def _apply_default(
    _p: JudicialOpinion,
    _d: JudicialOpinion,
    tech_lead: JudicialOpinion,
    _criterion_id: str,
) -> Tuple[int, str]:
    """Rule 4: Default — Tech Lead breaks ties."""
    scores = [p.score for p in (_p, _d, tech_lead) if p]
    s = tech_lead.score if tech_lead else (sum(scores) // len(scores) if scores else 3)
    return s, "Scores consistent - Tech Lead assessment confirmed."


def _resolve_final_score(
    prosecutor: JudicialOpinion,
    defense: JudicialOpinion,
    tech_lead: JudicialOpinion,
    criterion_id: str,
) -> Tuple[int, str]:
    """Apply declarative rules in order; first match wins."""
    rules: List[Tuple[Callable[..., bool], Callable[..., Tuple[int, str]]]] = [
        (_security_override_condition, lambda p, d, t, c: _apply_security_override(p, d, t, c)),
        (
            lambda p, d, t, c: (max([p.score, d.score, t.score]) - min([p.score, d.score, t.score]) > 2)
            if all([p, d, t]) else False,
            _apply_variance_re_evaluation,
        ),
        (
            lambda p, d, t, c: "architecture" in c.lower() or "orchestration" in c.lower(),
            lambda p, d, t, c: _apply_functionality_weight(p, d, t, c),
        ),
    ]
    for condition, apply_fn in rules:
        if condition(prosecutor, defense, tech_lead, criterion_id):
            return apply_fn(prosecutor, defense, tech_lead, criterion_id)
    # Rule 4: Default — Tech Lead breaks ties
    return _apply_default(prosecutor, defense, tech_lead, criterion_id)


def chief_justice_node(state: AgentState) -> AgentState:
    """Synthesize dialectical conflict into final verdict using a declarative rule engine.

    Rules (security override, variance re-evaluation, functionality weight, default) are
    applied in order; first match wins. Runs only when all three judges have submitted
    opinions (one per dimension each).
    """
    opinions_raw = state.get("opinions") or []
    # Normalize: state stores dicts (from model_dump) to avoid Pydantic serialization warnings
    opinions: List[JudicialOpinion] = [
        JudicialOpinion(**o) if isinstance(o, dict) else o
        for o in opinions_raw
    ]
    dimensions = state.get("rubric_dimensions") or []
    expected_opinions = len(dimensions) * NUM_JUDGES

    if len(opinions) < expected_opinions:
        logger.info(
            f"ChiefJustice: Waiting for all judges (have {len(opinions)}/{expected_opinions} opinions), skipping synthesis"
        )
        return {}

    logger.info(f"ChiefJustice: Synthesizing verdict from {len(opinions)} opinions")

    synthesis_rules = state.get("synthesis_rules")
    if not synthesis_rules:
        try:
            rubric_path = state.get("rubric_path")
            rubric = load_rubric(rubric_path) if rubric_path else load_rubric()
            synthesis_rules = rubric.get("synthesis_rules", {})
        except Exception:
            pass
    if not synthesis_rules:
        synthesis_rules = {
            "security_override": "Confirmed security flaws cap total score at 3.",
            "fact_supremacy": "Forensic evidence (facts) always overrules Judicial opinion (interpretation).",
            "functionality_weight": "Tech Lead assessment carries highest weight for architecture criteria.",
            "dissent_requirement": "The Chief Justice must summarize why the Prosecutor and Defense disagreed.",
            "variance_re_evaluation": "If score variance > 2, re-evaluate specific evidence cited by each judge."
        }
    
    # Group opinions by criterion
    opinions_by_criterion: Dict[str, List[JudicialOpinion]] = {}
    for opinion in opinions:
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
            # Missing opinions - use lowest score (deterministic, no LLM)
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

        # Conflict resolution logic
        # Rule of Security, Rule of Evidence (fact supremacy), Rule of Functionality, variance re-evaluation (deterministic, no LLM)
        final_score, rationale = _resolve_final_score(prosecutor, defense, tech_lead, criterion_id)
        scores = [prosecutor.score, defense.score, tech_lead.score]
        score_variance = max(scores) - min(scores)
        
        # Generate dissent summary if variance > 2 (concatenation avoids brace-format errors)
        dissent_summary: Optional[str] = None
        if prosecutor and defense and abs(prosecutor.score - defense.score) > 2:
            p_arg = (prosecutor.argument[:150] + "...") if len(prosecutor.argument) > 150 else prosecutor.argument
            d_arg = (defense.argument[:150] + "...") if len(defense.argument) > 150 else defense.argument
            dissent_summary = (
                "Prosecutor (" + str(prosecutor.score) + "/5) vs Defense (" + str(defense.score) + "/5) - "
                + str(score_variance) + " point variance. "
                "Prosecutor: " + str(p_arg) + " "
                "Defense: " + str(d_arg) + " "
                "Resolution: " + str(rationale)
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
    
    # Use original PDF URL/path in report (pdf_display), not the resolved download path
    pdf_for_report = state.get("pdf_display") or state.get("pdf_path") or ""
    executive_summary = (
        "**Automaton Auditor Report**\n\n"
        "**Target Repository:** " + str(state.get("repo_url", "")) + "\n"
        "**PDF Report:** " + str(pdf_for_report) + "\n\n"
        "**Overall Score:** " + f"{overall_score:.2f}" + "/5.0\n\n"
        "**Summary:** Evaluated " + str(criterion_count) + " criteria across forensic accuracy, judicial nuance, "
        "graph orchestration, and documentation quality. "
    )

    low_scores = [cr for cr in criteria_results if cr.final_score < 3]
    if low_scores:
        executive_summary += str(len(low_scores)) + " criteria scored below 3/5, indicating areas requiring remediation. "

    high_scores = [cr for cr in criteria_results if cr.final_score >= 4]
    if high_scores:
        executive_summary += str(len(high_scores)) + " criteria scored 4/5 or higher, indicating strong implementation. "

    # Generate consolidated remediation plan (serializer adds the section heading)
    remediation_plan = ""
    for cr in criteria_results:
        if cr.final_score < 3:
            remediation_plan += "### " + str(cr.dimension_name) + " (Score: " + str(cr.final_score) + "/5)\n\n"
            remediation_plan += str(cr.remediation) + "\n\n"
    
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
