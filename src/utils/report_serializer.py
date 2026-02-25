"""Utility to serialize AuditReport to Markdown."""
from src.state import AuditReport, CriterionResult


def serialize_report_to_markdown(report: AuditReport) -> str:
    """Convert AuditReport Pydantic model to Markdown string.
    
    Args:
        report: AuditReport model instance
        
    Returns:
        Markdown-formatted string
    """
    sections = []
    
    # Header
    sections.append("# Automaton Auditor Report\n")
    sections.append(report.executive_summary)
    sections.append("\n")
    
    # Criterion Breakdown
    sections.append("## Criterion Breakdown\n\n")
    
    for criterion in report.criteria:
        sections.append("### " + str(criterion.dimension_name) + " (" + str(criterion.dimension_id) + ")\n\n")
        sections.append("**Final Score:** " + str(criterion.final_score) + "/5\n\n")

        # Judge Opinions (use concatenation so LLM output with { } doesn't break format)
        sections.append("**Judge Opinions:**\n\n")
        for opinion in criterion.judge_opinions:
            sections.append("- **" + str(opinion.judge) + "** (Score: " + str(opinion.score) + "/5): " + str(opinion.argument) + "\n")
            if opinion.cited_evidence:
                sections.append("  - Cited Evidence: " + ", ".join(str(x) for x in opinion.cited_evidence[:5]) + "\n")
        sections.append("\n")

        # Dissent Summary
        if criterion.dissent_summary:
            sections.append("**Dissent Summary:** " + str(criterion.dissent_summary) + "\n\n")

        # Remediation for this criterion
        sections.append("**Remediation:** " + str(criterion.remediation) + "\n\n")
        sections.append("---\n\n")
    
    # Consolidated Remediation Plan
    sections.append(report.remediation_plan)
    
    return "\n".join(sections)
