"""CLI entry point for Automaton Auditor."""
import argparse
import json
import os
import sys
from pathlib import Path

from src.config import load_rubric, load_env_config
from src.graph import build_auditor_graph
from src.state import AgentState
from src.utils.report_serializer import serialize_report_to_markdown
from src.utils.logger import setup_logger


def validate_repo_url(url: str) -> bool:
    """Validate GitHub repository URL format."""
    return url.startswith("https://github.com/") or url.startswith("git@github.com:")


def validate_pdf_path(pdf_path: str) -> bool:
    """Validate PDF file exists and is readable."""
    return Path(pdf_path).exists() and Path(pdf_path).is_file()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Automaton Auditor - Deep LangGraph Swarms for Autonomous Governance"
    )
    
    # Required arguments
    parser.add_argument(
        "--repo", "-r",
        required=True,
        help="GitHub repository URL to audit"
    )
    parser.add_argument(
        "--pdf", "-p",
        required=True,
        help="Path to PDF report to analyze"
    )
    
    # Optional arguments
    parser.add_argument(
        "--output", "-o",
        default="audit/report_onself_generated/",
        help="Output directory for audit report (default: audit/report_onself_generated/)"
    )
    parser.add_argument(
        "--rubric", "-R",
        default="rubric/week2_rubric.json",
        help="Path to rubric JSON file (default: rubric/week2_rubric.json)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--trace", "-t",
        action="store_true",
        help="Enable LangSmith tracing"
    )
    parser.add_argument(
        "--compare", "-c",
        help="Compare current audit with peer audit report (path to peer report)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logger(verbose=args.verbose)
    logger.info("Automaton Auditor starting...")
    
    # Input validation
    if not validate_repo_url(args.repo):
        print(f"ERROR: Repository: Invalid GitHub URL format: {args.repo}", file=sys.stderr)
        sys.exit(1)
    
    if not validate_pdf_path(args.pdf):
        print(f"ERROR: PDF: File not found or unreadable: {args.pdf}", file=sys.stderr)
        sys.exit(1)
    
    # Load and validate rubric
    try:
        rubric = load_rubric(args.rubric)
        if args.verbose:
            print(f"✓ Loaded rubric: {len(rubric['dimensions'])} dimensions")
    except FileNotFoundError as e:
        print(f"ERROR: Rubric: {e}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: Rubric: Invalid rubric file - {e}", file=sys.stderr)
        print("Rubric validation failed. Exiting before audit starts.", file=sys.stderr)
        sys.exit(1)
    
    # Load environment configuration
    try:
        config = load_env_config()
        if args.verbose:
            print("✓ Environment configuration loaded")
    except ValueError as e:
        print(f"ERROR: Configuration: {e}", file=sys.stderr)
        sys.exit(2)
    
    # Configure LangSmith tracing
    if args.trace or config["langchain_tracing_v2"]:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        if config["langchain_api_key"]:
            os.environ["LANGCHAIN_API_KEY"] = config["langchain_api_key"]
        os.environ["LANGCHAIN_PROJECT"] = config["langchain_project"]
        if args.verbose:
            print("✓ LangSmith tracing enabled")
    
    # Initialize state
    initial_state: AgentState = {
        "repo_url": args.repo,
        "pdf_path": args.pdf,
        "rubric_dimensions": rubric["dimensions"],  # Full rubric with synthesis_rules available via config
        "evidences": {},
        "opinions": [],
        "errors": [],
        "final_report": None
    }
    
    # Build and execute graph
    if args.verbose:
        print("Building auditor graph...")
    
    graph = build_auditor_graph()
    
    if args.verbose:
        print("Executing audit workflow...")
    
    try:
        final_state = graph.invoke(initial_state)
        
        # Check for synthesis failure
        audit_report = final_state.get("final_report")
        if not audit_report:
            print("ERROR: Synthesis failed - no report generated", file=sys.stderr)
            print("Saving partial state for debugging...", file=sys.stderr)
            
            # Save partial state
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            debug_path = output_dir / "debug_state.json"
            with open(debug_path, "w") as f:
                json.dump({
                    "evidences": {k: [e.dict() for e in v] for k, v in final_state["evidences"].items()},
                    "opinions": [o.dict() for o in final_state["opinions"]],
                    "errors": final_state["errors"]
                }, f, indent=2)
            
            print(f"Partial state saved to: {debug_path}", file=sys.stderr)
            sys.exit(1)
        
        # Serialize AuditReport to Markdown
        markdown_content = serialize_report_to_markdown(audit_report)
        
        # Save report
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "audit_report.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        # Also save JSON version for programmatic access
        json_path = output_dir / "audit_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(audit_report.dict(), f, indent=2)
        
        print(f"✓ Audit complete. Report saved to: {report_path}")
        print(f"✓ JSON report saved to: {json_path}")
        
        # Compare with peer report if requested
        if args.compare:
            from src.utils.report_parser import compare_reports
            try:
                comparison = compare_reports(str(report_path), args.compare)
                print("\n" + "="*60)
                print("COMPARISON WITH PEER REPORT")
                print("="*60)
                
                if comparison["overall_score_difference"] is not None:
                    diff = comparison["overall_score_difference"]
                    print(f"Overall Score Difference: {diff:+.2f} points")
                    if diff > 0:
                        print("  → Peer scored higher (your auditor may be too lenient)")
                    elif diff < 0:
                        print("  → Peer scored lower (your auditor may be too strict)")
                
                if comparison["criterion_differences"]:
                    print(f"\nCriterion Differences ({len(comparison['criterion_differences'])}):")
                    for diff in comparison["criterion_differences"]:
                        print(f"  - {diff['criterion_name']}: {diff['current_score']} → {diff['peer_score']} ({diff['difference']:+.1f})")
                
                if comparison["peer_issues"]:
                    print(f"\nIssues Found by Peer ({len(comparison['peer_issues'])}):")
                    for issue in comparison["peer_issues"][:5]:  # Top 5
                        print(f"  - {issue['criterion_name']} (Score: {issue['score']}/5) - {issue['priority']} priority")
                
            except Exception as e:
                print(f"⚠ Comparison failed: {str(e)}", file=sys.stderr)
        
        if args.trace or config["langchain_tracing_v2"]:
            print(f"[LangSmith Trace: Check LangSmith dashboard for trace URL]")
        
        if final_state.get("errors"):
            print(f"⚠ Warnings: {len(final_state['errors'])} errors encountered during execution", file=sys.stderr)
            if args.verbose:
                for error in final_state["errors"]:
                    print(f"  - {error}", file=sys.stderr)
        
    except Exception as e:
        print(f"ERROR: Execution failed: {str(e)}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
