"""Streamlit UI for Automaton Auditor."""
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
warnings.filterwarnings("ignore", category=UserWarning, module="langchain")

import json
import logging
import os
import tempfile
from pathlib import Path

import streamlit as st

logging.getLogger("RapidOCR").setLevel(logging.WARNING)

from src.config import load_rubric, load_env_config, list_available_rubrics
from src.graph import build_auditor_graph
from src.paths import DEFAULT_RUBRIC_PATH, REPORT_ON_SELF, ensure_dirs, TEMP_DIR
from src.state import AgentState
from src.tools.pdf_parser import is_pdf_url, download_pdf_from_url
from src.utils.report_serializer import serialize_report_to_markdown
from src.utils.logger import setup_logger


def validate_repo_url(url: str) -> bool:
    return url.startswith("https://github.com/") or url.startswith("git@github.com:")


def _render_report_and_downloads(markdown_content: str, report_json_str: str, score: float) -> None:
    """Render success message, download buttons, and report body. Used so downloads persist across re-runs."""
    st.success(f"Audit complete. Overall score: **{score:.2f}** / 5.0")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download report (Markdown)",
            markdown_content,
            file_name="audit_report.md",
            mime="text/markdown",
        )
    with col2:
        st.download_button(
            "Download report (JSON)",
            report_json_str,
            file_name="audit_report.json",
            mime="application/json",
        )
    st.subheader("Report")
    st.markdown(markdown_content)


def resolve_pdf_input(pdf_value: str, uploaded_file=None) -> tuple[str, str]:
    """Resolve PDF to a local path. Returns (local_path, display_label)."""
    if uploaded_file is not None:
        ensure_dirs()
        path = TEMP_DIR / f"upload_{uploaded_file.name}"
        path.write_bytes(uploaded_file.getvalue())
        return str(path.resolve()), uploaded_file.name
    if is_pdf_url(pdf_value):
        ensure_dirs()
        path = download_pdf_from_url(pdf_value, str(TEMP_DIR))
        return path, pdf_value
    p = Path(pdf_value)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"PDF not found or not a file: {pdf_value}")
    return str(p.resolve()), pdf_value


st.set_page_config(
    page_title="Automaton Auditor",
    page_icon="📋",
    layout="wide",
)

# Persist report in session so download buttons survive re-runs (Streamlit re-runs on any click)
if "audit_report_md" not in st.session_state:
    st.session_state.audit_report_md = None
if "audit_report_json" not in st.session_state:
    st.session_state.audit_report_json = None
if "audit_report_score" not in st.session_state:
    st.session_state.audit_report_score = None

st.title("Automaton Auditor")
st.caption("Deep LangGraph Swarms for Autonomous Governance")

with st.sidebar:
    st.header("Configuration")
    st.caption("Provide at least one: repo or PDF (audited explicitly, not together).")
    repo_url = st.text_input(
        "GitHub repository URL",
        placeholder="https://github.com/owner/repo",
        help="Repository to audit. Leave empty for PDF-only audit.",
    )
    pdf_mode = st.radio(
        "PDF input",
        ["Upload file", "URL or path"],
        horizontal=True,
    )
    pdf_path_or_url = None
    uploaded_pdf = None
    if pdf_mode == "Upload file":
        uploaded_pdf = st.file_uploader("PDF report", type=["pdf"], label_visibility="collapsed")
    else:
        pdf_path_or_url = st.text_input(
            "PDF URL or path",
            placeholder="https://example.com/report.pdf or ./reports/report.pdf",
            label_visibility="collapsed",
        )

    rubrics = list_available_rubrics()
    rubric_options = [str(DEFAULT_RUBRIC_PATH)]
    rubric_options += [str(p) for p in rubrics if str(p) != str(DEFAULT_RUBRIC_PATH)]
    rubric_labels = [Path(p).name for p in rubric_options]
    rubric_choice = st.selectbox(
        "Rubric",
        options=range(len(rubric_options)),
        format_func=lambda i: rubric_labels[i],
    )
    rubric_path = rubric_options[rubric_choice]

    output_dir = st.text_input(
        "Output directory (optional)",
        value=str(REPORT_ON_SELF),
        help="Where to save audit_report.md and audit_report.json.",
    )
    compare_upload = st.file_uploader(
        "Compare with peer report (optional)",
        type=["md", "markdown"],
        help="Upload a peer audit report to compare scores.",
    )
    verbose = st.checkbox("Verbose logging", value=False)
    trace = st.checkbox("LangSmith tracing", value=False)

def run_audit():
    has_repo = bool(repo_url and repo_url.strip())
    has_pdf = (pdf_mode == "Upload file" and uploaded_pdf is not None) or (
        pdf_mode == "URL or path" and pdf_path_or_url and pdf_path_or_url.strip()
    )
    if not has_repo and not has_pdf:
        st.error("Provide at least one: repository URL or PDF (audit repo and PDF explicitly, not together).")
        return
    if has_repo and not validate_repo_url(repo_url.strip()):
        st.error("Invalid GitHub URL. Use https://github.com/... or git@github.com:...")
        return

    pdf_path = None
    pdf_display = None
    if has_pdf:
        pdf_value = pdf_path_or_url.strip() if pdf_mode == "URL or path" else ""
        try:
            pdf_path, pdf_display = resolve_pdf_input(pdf_value, uploaded_pdf)
        except FileNotFoundError as e:
            st.error(str(e))
            return
        except RuntimeError as e:
            st.error(f"PDF download failed: {e}")
            return

    ensure_dirs()
    try:
        rubric = load_rubric(rubric_path)
    except FileNotFoundError as e:
        st.error(str(e))
        return
    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"Invalid rubric: {e}")
        return

    all_dims = rubric["dimensions"]
    if has_repo and pdf_path:
        rubric_dimensions = all_dims
    elif has_repo:
        rubric_dimensions = [d for d in all_dims if d.get("target_artifact") in ("github_repo", "pdf_images")]
    else:
        rubric_dimensions = [d for d in all_dims if d.get("target_artifact") == "pdf_report"]

    if not rubric_dimensions:
        st.error("No rubric dimensions match the provided artifact(s). Provide repo and/or PDF.")
        return

    try:
        config = load_env_config()
    except ValueError as e:
        st.error(str(e))
        return

    if trace or config.get("langchain_tracing_v2"):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        if config.get("langchain_api_key"):
            os.environ["LANGCHAIN_API_KEY"] = config["langchain_api_key"]
        os.environ["LANGCHAIN_PROJECT"] = config.get("langchain_project", "automaton-auditor")

    logger = setup_logger(verbose=verbose)
    logger.info("Automaton Auditor (Streamlit) starting...")

    initial_state: AgentState = {
        "repo_url": repo_url.strip() if has_repo else "",
        "pdf_path": pdf_path,
        "pdf_display": pdf_display,
        "rubric_path": rubric_path,
        "rubric_dimensions": rubric_dimensions,
        "synthesis_rules": rubric.get("synthesis_rules", {}),
        "evidences": {},
        "opinions": [],
        "errors": [],
        "final_report": None,
    }

    with st.spinner("Running audit (detectives → judges → chief justice)..."):
        graph = build_auditor_graph()
        final_state = graph.invoke(initial_state)

    audit_report = final_state.get("final_report")
    if not audit_report:
        st.error("Synthesis failed — no report generated.")
        if final_state.get("errors"):
            with st.expander("Errors"):
                for err in final_state["errors"]:
                    st.code(str(err))
        return

    markdown_content = serialize_report_to_markdown(audit_report)
    out_dir = Path(output_dir or str(REPORT_ON_SELF))
    out_dir.mkdir(parents=True, exist_ok=True)
    report_md_path = out_dir / "audit_report.md"
    report_json_path = out_dir / "audit_report.json"
    report_md_path.write_text(markdown_content, encoding="utf-8")
    report_dict = audit_report.model_dump() if hasattr(audit_report, "model_dump") else audit_report.dict()
    report_json_str = json.dumps(report_dict, indent=2)
    report_json_path.write_text(report_json_str, encoding="utf-8")

    # Persist in session so download buttons work after re-run (Streamlit re-runs on any click)
    st.session_state.audit_report_md = markdown_content
    st.session_state.audit_report_json = report_json_str
    st.session_state.audit_report_score = audit_report.overall_score

    _render_report_and_downloads(markdown_content, report_json_str, audit_report.overall_score)

    if compare_upload:
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
                f.write(compare_upload.read().decode("utf-8"))
                peer_path = f.name
            from src.utils.report_parser import compare_reports
            comparison = compare_reports(str(report_md_path), peer_path)
            os.unlink(peer_path)
        except Exception as e:
            st.warning(f"Comparison failed: {e}")
        else:
            st.subheader("Comparison with peer report")
            if comparison["overall_score_difference"] is not None:
                diff = comparison["overall_score_difference"]
                st.metric("Overall score difference (peer − current)", f"{diff:+.2f}")
                if diff > 0:
                    st.info("Peer scored higher (your auditor may be too lenient).")
                elif diff < 0:
                    st.info("Peer scored lower (your auditor may be too strict).")
            if comparison["criterion_differences"]:
                st.write("**Criterion differences**")
                for d in comparison["criterion_differences"]:
                    st.write(f"- **{d['criterion_name']}**: {d['current_score']} → {d['peer_score']} ({d['difference']:+.1f})")
            if comparison.get("peer_issues"):
                st.write("**Issues found by peer** (top 5)")
                for issue in comparison["peer_issues"][:5]:
                    st.write(f"- {issue['criterion_name']} (Score: {issue['score']}/5) — {issue['priority']} priority")

    if final_state.get("errors") and verbose:
        with st.expander("Warnings"):
            for err in final_state["errors"]:
                st.code(str(err))


if st.sidebar.button("Run audit", type="primary"):
    run_audit()
elif st.session_state.get("audit_report_md"):
    # Re-run after e.g. clicking Download: show report from session so download buttons work
    _render_report_and_downloads(
        st.session_state.audit_report_md,
        st.session_state.audit_report_json,
        st.session_state.audit_report_score,
    )
