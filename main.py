"""CLI entry point for Automaton Auditor."""
import argparse
import json
import os
import sys
import warnings
from pathlib import Path

# Suppress noisy warnings from LangChain/Pydantic when using with_structured_output(JudicialOpinion)
warnings.filterwarnings(
    "ignore",
    message=".*serialized value may not be as expected.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*Pydantic V1 functionality isn't compatible with Python 3.14.*",
    category=UserWarning,
)

from src.config import load_rubric, load_env_config, list_available_rubrics
from src.graph import build_auditor_graph
from src.paths import DEFAULT_RUBRIC_PATH, REPORT_ON_SELF, ensure_dirs
from src.state import AgentState
from src.tools.pdf_parser import is_pdf_url, download_pdf_from_url
from src.utils.report_serializer import serialize_report_to_markdown
from src.utils.logger import setup_logger


def validate_repo_url(url: str) -> bool:
    """Validate GitHub repository URL format."""
    return url.startswith("https://github.com/") or url.startswith("git@github.com:")


def resolve_pdf_input(pdf_value: str) -> str:
    """Resolve PDF to a local path: download from URL or use path as-is.

    Returns:
        Local path to the PDF file.
    """
    if is_pdf_url(pdf_value):
        from src.paths import TEMP_DIR
        ensure_dirs()
        return download_pdf_from_url(pdf_value, str(TEMP_DIR))
    path = Path(pdf_value)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"PDF file not found or not a file: {pdf_value}")
    return str(path.resolve())


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Automaton Auditor - Deep LangGraph Swarms for Autonomous Governance"
    )
    
    parser.add_argument(
        "--repo", "-r",
        help="GitHub repository URL to audit"
    )
    parser.add_argument(
        "--pdf", "-p",
        help="Path or URL to PDF report to analyze (e.g. https://example.com/report.pdf or ./reports/report.pdf)"
    )
    parser.add_argument(
        "--list-rubrics",
        action="store_true",
        help="List available rubric files in rubric/ and exit"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output directory for audit report (default: audit/report_onself_generated/)"
    )
    parser.add_argument(
        "--rubric", "-R",
        default=None,
        help="Path to rubric JSON file (default: rubric/week2_rubric.json). Use --list-rubrics to see options."
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

    # List rubrics and exit
    if args.list_rubrics:
        rubrics = list_available_rubrics()
        if not rubrics:
            print("No rubric files found in rubric/", file=sys.stderr)
            sys.exit(1)
        print("Available rubric files:")
        for p in rubrics:
            print(f"  rubric/{p.name}")
        sys.exit(0)

    # Require repo and pdf for audit
    if not args.repo or not args.pdf:
        parser.error("--repo and --pdf are required to run an audit (or use --list-rubrics)")

    # Setup logging
    logger = setup_logger(verbose=args.verbose)
    logger.info("Automaton Auditor starting...")

    # Input validation
    if not validate_repo_url(args.repo):
        print(f"ERROR: Repository: Invalid GitHub URL format: {args.repo}", file=sys.stderr)
        sys.exit(1)

    try:
        pdf_path = resolve_pdf_input(args.pdf)
        if args.verbose and is_pdf_url(args.pdf):
            print(f"✓ Downloaded PDF from URL to {pdf_path}")
    except FileNotFoundError as e:
        print(f"ERROR: PDF: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"ERROR: PDF download: {e}", file=sys.stderr)
        sys.exit(1)

    rubric_path = args.rubric or str(DEFAULT_RUBRIC_PATH)
    output_dir = args.output or str(REPORT_ON_SELF)
    ensure_dirs()

    # Load and validate rubric
    try:
        rubric = load_rubric(rubric_path)
        if args.verbose:
            print(f"✓ Loaded rubric: {rubric_path} ({len(rubric['dimensions'])} dimensions)")
    except FileNotFoundError as e:
        print(f"ERROR: Rubric: {e}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: Rubric: Invalid rubric file - {e}", file=sys.stderr)
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
        "pdf_path": pdf_path,
        "rubric_path": rubric_path,
        "rubric_dimensions": rubric["dimensions"],
        "synthesis_rules": rubric.get("synthesis_rules", {}),
        "evidences": {},
        "opinions": [],
        "errors": [],
        "final_report": None,
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
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            debug_path = out_dir / "debug_state.json"

            def _to_dict(obj):
                return obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()

            with open(debug_path, "w", encoding="utf-8") as f:
                json.dump({
                    "evidences": {k: [_to_dict(e) for e in v] for k, v in final_state["evidences"].items()},
                    "opinions": [_to_dict(o) for o in final_state["opinions"]],
                    "errors": final_state["errors"],
                }, f, indent=2)
            
            print(f"Partial state saved to: {debug_path}", file=sys.stderr)
            sys.exit(1)
        
        # Serialize AuditReport to Markdown
        markdown_content = serialize_report_to_markdown(audit_report)
        
        # Save report
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / "audit_report.md"
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        # Also save JSON version for programmatic access
        json_path = Path(output_dir) / "audit_report.json"
        report_dict = audit_report.model_dump() if hasattr(audit_report, "model_dump") else audit_report.dict()
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)
        
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
