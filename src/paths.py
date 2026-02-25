"""Structured paths for Automaton Auditor.

All file and directory paths used by the auditor are defined here
so they can be changed in one place and stay consistent.
"""
from pathlib import Path

# Project root (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Rubric
RUBRIC_DIR = PROJECT_ROOT / "rubric"
DEFAULT_RUBRIC_PATH = RUBRIC_DIR / "week2_rubric.json"

# Audit output directories
AUDIT_DIR = PROJECT_ROOT / "audit"
REPORT_ON_SELF = AUDIT_DIR / "report_onself_generated"
REPORT_ON_PEER = AUDIT_DIR / "report_onpeer_generated"
REPORT_BY_PEER = AUDIT_DIR / "report_bypeer_received"

# Reports (PDFs committed to repo)
REPORTS_DIR = PROJECT_ROOT / "reports"

# Temporary files (e.g. downloaded PDFs)
TEMP_DIR = PROJECT_ROOT / "tmp"


def ensure_dirs() -> None:
    """Create standard directories if they do not exist."""
    for dir_path in (AUDIT_DIR, REPORT_ON_SELF, REPORT_ON_PEER, REPORT_BY_PEER, REPORTS_DIR, TEMP_DIR):
        dir_path.mkdir(parents=True, exist_ok=True)


def list_rubric_files() -> list[Path]:
    """Return list of JSON files in the rubric directory."""
    if not RUBRIC_DIR.exists():
        return []
    return sorted(RUBRIC_DIR.glob("*.json"))
