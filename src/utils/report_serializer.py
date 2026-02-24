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
        sections.append(f"### {criterion.dimension_name} ({criterion.dimension_id})\n\n")
        sections.append(f"**Final Score:** {criterion.final_score}/5\n\n")
        
        # Judge Opinions
        sections.append("**Judge Opinions:**\n\n")
        for opinion in criterion.judge_opinions:
            sections.append(f"- **{opinion.judge}** (Score: {opinion.score}/5): {opinion.argument}\n")
            if opinion.cited_evidence:
                sections.append(f"  - Cited Evidence: {', '.join(opinion.cited_evidence[:5])}\n")
        sections.append("\n")
        
        # Dissent Summary
        if criterion.dissent_summary:
            sections.append(f"**Dissent Summary:** {criterion.dissent_summary}\n\n")
        
        # Remediation for this criterion
        sections.append(f"**Remediation:** {criterion.remediation}\n\n")
        sections.append("---\n\n")
    
    # Consolidated Remediation Plan
    sections.append(report.remediation_plan)
    
    return "\n".join(sections)
