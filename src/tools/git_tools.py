"""Git tools for forensic repository analysis.

All git operations use sandboxed temp dirs, subprocess.run with error handling,
and explicit handling of repo edge cases: invalid URL, auth failure, empty repo,
non-git path, timeout.
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

# Safe URL pattern: http(s) or git@ (SSH); avoid file:// and shell metacharacters
REPO_URL_PATTERN = re.compile(
    r"^(https?://[^\s<>'\"]+|git@[a-zA-Z0-9.-]+:[a-zA-Z0-9_.-/]+\.git?)$"
)


def is_valid_repo_url(url: str) -> bool:
    """Return True if url looks like a safe repo URL (http(s) or git@)."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if " " in url or "\n" in url or ";" in url or "|" in url:
        return False
    return bool(REPO_URL_PATTERN.match(url))


def _ensure_sandbox_dir(target_dir: Optional[str]) -> tuple[str, bool]:
    """Return (repo_parent_dir, is_temp). Never use cwd as repo parent."""
    if target_dir is None or not target_dir.strip():
        return tempfile.mkdtemp(), True
    abs_path = os.path.abspath(target_dir)
    cwd = os.getcwd()
    if os.path.normpath(abs_path) == os.path.normpath(cwd):
        # Caller passed cwd: use a temp dir instead to avoid cloning into live dir
        return tempfile.mkdtemp(), True
    os.makedirs(abs_path, exist_ok=True)
    return abs_path, False


def _classify_clone_error(stderr: str) -> str:
    """Classify clone failure for clearer error messages."""
    err_lower = (stderr or "").lower()
    if "authentication" in err_lower or "permission denied" in err_lower or "403" in err_lower:
        return "Git authentication failed. Use a public repo URL or set credentials (e.g. token)."
    if "repository not found" in err_lower or "404" in err_lower:
        return "Repository not found or not accessible."
    if "could not read from remote" in err_lower or "failed to connect" in err_lower:
        return "Network or remote read failed. Check URL and connectivity."
    return (stderr or "Unknown git error").strip() or "Git clone failed."


def clone_repo(repo_url: str, target_dir: Optional[str] = None) -> str:
    """Safely clone a repository into a temporary (or provided) directory.

    - Never clones into the current working directory; uses temp if target_dir is cwd.
    - Validates repo URL to avoid injection; rejects file:// and shell metacharacters.
    - Uses subprocess.run with timeout and capture; no os.system().
    - Raises RuntimeError with clear message for auth, timeout, invalid URL.

    Args:
        repo_url: Git repository URL (https or git@).
        target_dir: Optional parent dir for clone; if None or cwd, uses tempfile.

    Returns:
        Path to cloned repository (subdir named "repo" under parent).

    Raises:
        ValueError: If repo_url is invalid or empty.
        RuntimeError: If clone fails (auth, timeout, not found, etc.).
    """
    if not is_valid_repo_url(repo_url):
        raise ValueError(
            "Invalid or unsafe repo URL. Use https://... or git@host:path.git; "
            "no file:// or shell metacharacters."
        )

    parent_dir, _ = _ensure_sandbox_dir(target_dir)
    repo_path = os.path.join(parent_dir, "repo")

    try:
        subprocess.run(
            ["git", "clone", repo_url, repo_path],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.CalledProcessError as e:
        classified = _classify_clone_error(e.stderr or "")
        raise RuntimeError(f"Git clone failed: {classified}") from e
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git clone timed out after 120 seconds.") from None

    if not _is_git_repo(repo_path):
        raise RuntimeError("Clone completed but path is not a valid git repository.")

    return repo_path


def _is_git_repo(path: str) -> bool:
    """Return True if path exists and is a git repository (has .git)."""
    if not path or not os.path.isdir(path):
        return False
    git_dir = os.path.join(path, ".git")
    return os.path.isdir(git_dir) or os.path.isfile(git_dir)


def get_repo_file_list(repo_url: str) -> List[str]:
    """Clone repo to a temp dir and return relative file paths (normalized with forward slashes).

    Used for cross-referencing PDF claims. Returns [] on clone failure, invalid URL,
    auth error, or non-git path. Never writes outside a temp dir.
    """
    if not is_valid_repo_url(repo_url):
        return []
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = clone_repo(repo_url, tmpdir)
            if not _is_git_repo(repo_path):
                return []
            out: List[str] = []
            for root, _dirs, files in os.walk(repo_path):
                for f in files:
                    abs_path = os.path.join(root, f)
                    rel = os.path.relpath(abs_path, repo_path)
                    out.append(rel.replace("\\", "/"))
            return out
    except (ValueError, RuntimeError, OSError):
        return []


def analyze_git_history(repo_path: str) -> Dict[str, Any]:
    """Analyze git commit history for progression evidence.

    Handles edge cases: non-git path, empty repo (no commits), and git command failures.
    """
    if not repo_path or not _is_git_repo(repo_path):
        return {
            "has_progression": False,
            "commit_count": 0,
            "commit_summary": "Not a git repository or path missing.",
            "timestamps": [],
            "rationale": "Path is not a valid git repository.",
            "confidence": 0.2,
        }

    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "log", "--oneline", "--reverse"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        commits = [line.strip() for line in (result.stdout or "").strip().split("\n") if line.strip()]

        # Empty repo: no commits
        if not commits:
            return {
                "has_progression": False,
                "commit_count": 0,
                "commit_summary": "Repository has no commits.",
                "timestamps": [],
                "rationale": "Empty repository (no commit history).",
                "confidence": 0.2,
            }

        timestamp_result = subprocess.run(
            ["git", "-C", repo_path, "log", "--format=%ai", "--reverse"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        timestamps = [
            line.strip()
            for line in (timestamp_result.stdout or "").strip().split("\n")
            if line.strip()
        ]

        has_progression = len(commits) > 3
        single_init = len(commits) == 1 and ("init" in commits[0].lower() or "initial" in commits[0].lower())
        bulk_pattern = any("bulk" in c.lower() for c in commits[:3])
        is_atomic = len(commits) > 1 and not single_init and not bulk_pattern

        rationale = (
            f"Found {len(commits)} commits. "
            f"{'Shows progression with atomic commits' if has_progression and is_atomic else 'Monolithic, empty, or single init/bulk commit history'}."
        )
        confidence = 0.9 if (has_progression and is_atomic) else 0.3

        return {
            "has_progression": has_progression and is_atomic,
            "commit_count": len(commits),
            "commit_summary": "\n".join(commits[:10]),
            "timestamps": timestamps[:10],
            "rationale": rationale,
            "confidence": confidence,
        }
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip() or str(e)
        return {
            "has_progression": False,
            "commit_count": 0,
            "commit_summary": f"Git log failed: {stderr}",
            "timestamps": [],
            "rationale": f"Git history analysis failed: {stderr}",
            "confidence": 0.1,
        }
    except subprocess.TimeoutExpired:
        return {
            "has_progression": False,
            "commit_count": 0,
            "commit_summary": "Git log timed out.",
            "timestamps": [],
            "rationale": "Git history analysis timed out.",
            "confidence": 0.1,
        }
    except (OSError, ValueError) as e:
        return {
            "has_progression": False,
            "commit_count": 0,
            "commit_summary": str(e),
            "timestamps": [],
            "rationale": f"Repo edge case or failure: {e}",
            "confidence": 0.1,
        }
