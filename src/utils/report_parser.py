"""Utility to parse peer audit reports and extract remediation suggestions."""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


def _extract_remediation_after(content: str, start: int, max_chars: int = 2000) -> str:
    """Extract remediation text from #### Remediation block after start."""
    section = content[start : start + max_chars]
    rem_match = re.search(r"#### Remediation\n\n(.*?)(?=\n---|\n### |\n#### |\Z)", section, re.DOTALL | re.IGNORECASE)
    if not rem_match:
        return ""
    return rem_match.group(1).strip()


def parse_markdown_report(report_path: str) -> Dict[str, Any]:
    """Parse a Markdown audit report and extract structured information.
    
    Args:
        report_path: Path to Markdown audit report
        
    Returns:
        Dictionary with parsed report data
    """
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Overall score: support both metadata table (current) and legacy "**Overall Score:** X/5"
    overall_score = None
    table_score = re.search(r"\*\*Overall score\*\* \| \*\*([\d.]+)\s*/\s*5", content, re.IGNORECASE)
    if table_score:
        overall_score = float(table_score.group(1))
    if overall_score is None:
        legacy = re.search(r"\*\*Overall Score:\*\* ([\d.]+)/5", content)
        if legacy:
            overall_score = float(legacy.group(1))

    # Criterion breakdowns: support "### N. Name" + "**Final score:** ... X/5" (current) and legacy "### Name (id)" + "**Final Score:** X/5"
    criteria = []
    # Current format: ### 1. Git Forensic Analysis\n\n**Final score:** ■■■□□ 3/5
    current_pattern = re.compile(
        r"### \d+\. ([^\n]+)\n\n\*\*Final score:\*\* .*? (\d)/5",
        re.IGNORECASE,
    )
    for match in current_pattern.finditer(content):
        criterion_name = match.group(1).strip()
        score = int(match.group(2))
        criterion_id = criterion_name  # use name as id for comparison
        remediation = _extract_remediation_after(content, match.end(), 2000)
        criteria.append({
            "criterion_id": criterion_id,
            "criterion_name": criterion_name,
            "score": score,
            "remediation": remediation,
        })
    # Legacy format if no criteria found
    if not criteria:
        criterion_pattern = re.compile(r"### (.+?) \(([^)]+)\)\n\n\*\*Final Score:\*\* (\d)/5")
        for match in criterion_pattern.finditer(content):
            criterion_name = match.group(1)
            criterion_id = match.group(2)
            score = int(match.group(3))
            remediation_start = content.find(f"### {criterion_name}", match.end())
            remediation_section = content[remediation_start : remediation_start + 1000]
            remediation_match = re.search(r"\*\*Remediation:\*\* (.+?)(?=\n\n|$)", remediation_section, re.DOTALL)
            remediation = remediation_match.group(1).strip() if remediation_match else ""
            criteria.append({
                "criterion_id": criterion_id,
                "criterion_name": criterion_name,
                "score": score,
                "remediation": remediation,
            })
    
    # Extract remediation plan section (serializer uses "Remediation plan (consolidated)")
    remediation_plan_match = re.search(
        r"## Remediation plan \(consolidated\)\n\n(.+?)(?=\n\n---|$)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if not remediation_plan_match:
        remediation_plan_match = re.search(r"## Remediation Plan\n\n(.+?)(?=\n## |$)", content, re.DOTALL)
    remediation_plan = remediation_plan_match.group(1).strip() if remediation_plan_match else ""
    
    return {
        "overall_score": overall_score,
        "criteria": criteria,
        "remediation_plan": remediation_plan,
        "raw_content": content
    }


def extract_issues(report_data: Dict[str, Any], min_score: int = 3) -> List[Dict[str, Any]]:
    """Extract issues from parsed report where score is below threshold.
    
    Args:
        report_data: Parsed report data from parse_markdown_report
        min_score: Minimum acceptable score (default: 3)
        
    Returns:
        List of issues with criterion info and remediation
    """
    issues = []
    for criterion in report_data["criteria"]:
        if criterion["score"] < min_score:
            issues.append({
                "criterion_id": criterion["criterion_id"],
                "criterion_name": criterion["criterion_name"],
                "score": criterion["score"],
                "remediation": criterion["remediation"],
                "priority": "high" if criterion["score"] == 1 else "medium"
            })
    return issues


def compare_reports(current_report_path: str, peer_report_path: str) -> Dict[str, Any]:
    """Compare two audit reports and highlight differences.
    
    Args:
        current_report_path: Path to current audit report
        peer_report_path: Path to peer audit report
        
    Returns:
        Dictionary with comparison results
    """
    current = parse_markdown_report(current_report_path)
    peer = parse_markdown_report(peer_report_path)
    
    # Compare overall scores
    score_diff = None
    if current["overall_score"] and peer["overall_score"]:
        score_diff = peer["overall_score"] - current["overall_score"]
    
    # Compare criterion scores
    criterion_diffs = []
    current_criteria = {c["criterion_id"]: c for c in current["criteria"]}
    peer_criteria = {c["criterion_id"]: c for c in peer["criteria"]}
    
    for criterion_id in set(list(current_criteria.keys()) + list(peer_criteria.keys())):
        current_score = current_criteria.get(criterion_id, {}).get("score")
        peer_score = peer_criteria.get(criterion_id, {}).get("score")
        
        if current_score is not None and peer_score is not None:
            diff = peer_score - current_score
            if diff != 0:
                criterion_diffs.append({
                    "criterion_id": criterion_id,
                    "criterion_name": current_criteria.get(criterion_id, {}).get("criterion_name", criterion_id),
                    "current_score": current_score,
                    "peer_score": peer_score,
                    "difference": diff
                })
    
    return {
        "overall_score_difference": score_diff,
        "criterion_differences": criterion_diffs,
        "current_issues": extract_issues(current),
        "peer_issues": extract_issues(peer)
    }
