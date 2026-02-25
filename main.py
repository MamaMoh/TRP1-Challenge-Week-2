"""CLI entry point for Automaton Auditor."""
# Suppress third-party warnings (must run before langchain/pydantic are imported)
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=UserWarning, module="langchain")

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logging.getLogger("RapidOCR").setLevel(logging.WARNING)

from src.config import load_rubric, load_env_config, list_available_rubrics
from src.graph import build_auditor_graph
from src.paths import DEFAULT_RUBRIC_PATH, REPORT_ON_SELF, ensure_dirs
from src.state import AgentState
from src.tools.pdf_parser import is_pdf_url, download_pdf_from_url
from src.utils.report_serializer import serialize_report_to_markdown
from src.utils.logger import setup_logger


def _box(text: str, width: int = 52) -> str:
    """Return a simple box around one line of text."""
    t = text[: width - 4].center(width - 4)
    border = "+" + "-" * (width - 2) + "+"
    return border + "\n|" + t + "|\n" + border


def _step(msg: str, status: str = "") -> None:
    """Print a step line (optionally with status)."""
    if status:
        print(f"  [{status}] {msg}")
    else:
        print(f"  >> {msg}")


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

    if not args.repo or not args.pdf:
        parser.error("--repo and --pdf are required to run an audit (or use --list-rubrics)")

    logger = setup_logger(verbose=args.verbose)
    logger.info("Automaton Auditor starting...")

    print()
    print(_box("AUTOMATON AUDITOR"))
    print("  Deep LangGraph Swarms for Autonomous Governance")
    print()

    if not validate_repo_url(args.repo):
        print(f"ERROR: Invalid GitHub URL: {args.repo}", file=sys.stderr)
        sys.exit(1)

    _step("Resolving PDF input...")
    try:
        pdf_path = resolve_pdf_input(args.pdf)
        if is_pdf_url(args.pdf):
            _step("PDF downloaded from URL", "OK")
        else:
            _step("Using local PDF path", "OK")
    except FileNotFoundError as e:
        print(f"ERROR: PDF not found: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"ERROR: PDF download failed: {e}", file=sys.stderr)
        sys.exit(1)

    rubric_path = args.rubric or str(DEFAULT_RUBRIC_PATH)
    output_dir = args.output or str(REPORT_ON_SELF)
    ensure_dirs()

    _step("Loading rubric...")
    try:
        rubric = load_rubric(rubric_path)
        _step(f"Rubric loaded: {len(rubric['dimensions'])} dimensions", "OK")
    except FileNotFoundError as e:
        print(f"ERROR: Rubric file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: Invalid rubric: {e}", file=sys.stderr)
        sys.exit(1)

    _step("Loading environment configuration...")
    try:
        config = load_env_config()
        _step("API configuration ready", "OK")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)

    if args.trace or config.get("langchain_tracing_v2"):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        if config.get("langchain_api_key"):
            os.environ["LANGCHAIN_API_KEY"] = config["langchain_api_key"]
        os.environ["LANGCHAIN_PROJECT"] = config.get("langchain_project", "automaton-auditor")
        _step("LangSmith tracing enabled", "OK")
    
    # Initialize state (pdf_display = original URL/path for report; pdf_path = resolved path for processing)
    initial_state: AgentState = {
        "repo_url": args.repo,
        "pdf_path": pdf_path,
        "pdf_display": args.pdf,
        "rubric_path": rubric_path,
        "rubric_dimensions": rubric["dimensions"],
        "synthesis_rules": rubric.get("synthesis_rules", {}),
        "evidences": {},
        "opinions": [],
        "errors": [],
        "final_report": None,
    }
    
    print()
    _step("Building audit graph (detectives → judges → chief justice)...")
    graph = build_auditor_graph()
    _step("Running audit workflow (this may take a minute)...")
    print()

    try:
        final_state = graph.invoke(initial_state)
        audit_report = final_state.get("final_report")
        if not audit_report:
            print("ERROR: Synthesis failed - no report generated", file=sys.stderr)
            print("Saving partial state for debugging...", file=sys.stderr)
            
            # Save partial state
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            debug_path = out_dir / "debug_state.json"

            def _to_dict(obj):
                if isinstance(obj, dict):
                    return obj
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

        json_path = Path(output_dir) / "audit_report.json"
        report_dict = audit_report.model_dump() if hasattr(audit_report, "model_dump") else audit_report.dict()
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2)

        print(_box("AUDIT COMPLETE"))
        print()
        print("  Report (Markdown):  " + str(report_path))
        print("  Report (JSON):     " + str(json_path))
        print("  Overall score:     " + f"{audit_report.overall_score:.2f}" + " / 5.0")
        print()

        if args.compare:
            from src.utils.report_parser import compare_reports
            try:
                comparison = compare_reports(str(report_path), args.compare)
                print("  --- Comparison with peer report ---")
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
        
        if args.trace or config.get("langchain_tracing_v2"):
            print("  LangSmith: View trace in your LangSmith dashboard.")
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
