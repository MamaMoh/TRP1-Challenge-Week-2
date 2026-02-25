"""Git tools for forensic repository analysis."""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List


def clone_repo(repo_url: str, target_dir: str = None) -> str:
    """Safely clone a repository into a temporary directory.
    
    Args:
        repo_url: GitHub repository URL
        target_dir: Optional target directory (if None, uses tempfile)
        
    Returns:
        Path to cloned repository
        
    Raises:
        subprocess.CalledProcessError: If git clone fails
        subprocess.TimeoutExpired: If git clone times out
    """
    if target_dir is None:
        # Use temporary directory that will be cleaned up
        temp_dir = tempfile.mkdtemp()
        repo_path = os.path.join(temp_dir, "repo")
    else:
        repo_path = os.path.join(target_dir, "repo")
        os.makedirs(target_dir, exist_ok=True)
    
    try:
        result = subprocess.run(
            ["git", "clone", repo_url, repo_path],
            check=True,
            capture_output=True,
            text=True,
            timeout=120  # Increased timeout for large repos
        )
        return repo_path
    except subprocess.CalledProcessError as e:
        error_msg = f"Git clone failed: {e.stderr}"
        raise RuntimeError(error_msg) from e
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git clone timed out after 60 seconds") from None


def get_repo_file_list(repo_url: str) -> List[str]:
    """Clone repo to a temp dir and return relative file paths (normalized with forward slashes).
    Used for cross-referencing PDF claims. Returns [] on clone failure.
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = clone_repo(repo_url, tmpdir)
            out: List[str] = []
            for root, _dirs, files in os.walk(repo_path):
                for f in files:
                    abs_path = os.path.join(root, f)
                    rel = os.path.relpath(abs_path, repo_path)
                    out.append(rel.replace("\\", "/"))
            return out
    except Exception:
        return []


def analyze_git_history(repo_path: str) -> Dict[str, Any]:
    """Analyze git commit history for progression evidence.
    
    Args:
        repo_path: Path to git repository
        
    Returns:
        Dictionary with has_progression, commit_summary, rationale, confidence
    """
    try:
        # Get commit history
        result = subprocess.run(
            ["git", "-C", repo_path, "log", "--oneline", "--reverse"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        commits = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        
        # Get timestamps
        timestamp_result = subprocess.run(
            ["git", "-C", repo_path, "log", "--format=%ai", "--reverse"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        timestamps = [line.strip() for line in timestamp_result.stdout.strip().split("\n") if line.strip()]
        
        has_progression = len(commits) > 3
        is_atomic = len(commits) > 1 and not any("bulk" in c.lower() or "init" in c.lower() and len(commits) == 1 for c in commits)
        
        rationale = (
            f"Found {len(commits)} commits. "
            f"{'Shows progression with atomic commits' if has_progression and is_atomic else 'Monolithic or insufficient commit history'}."
        )
        
        confidence = 0.9 if has_progression and is_atomic else 0.3
        
        return {
            "has_progression": has_progression and is_atomic,
            "commit_count": len(commits),
            "commit_summary": "\n".join(commits[:10]),  # First 10 commits
            "timestamps": timestamps[:10],
            "rationale": rationale,
            "confidence": confidence
        }
    except subprocess.CalledProcessError as e:
        return {
            "has_progression": False,
            "commit_count": 0,
            "commit_summary": f"Git analysis failed: {e.stderr}",
            "timestamps": [],
            "rationale": f"Git history analysis failed: {e.stderr}",
            "confidence": 0.1
        }
    except subprocess.TimeoutExpired:
        return {
            "has_progression": False,
            "commit_count": 0,
            "commit_summary": "Git analysis timed out",
            "timestamps": [],
            "rationale": "Git history analysis timed out",
            "confidence": 0.1
        }
    except Exception as e:
        return {
            "has_progression": False,
            "commit_count": 0,
            "commit_summary": f"Git analysis error: {str(e)}",
            "timestamps": [],
            "rationale": f"Git history analysis error: {str(e)}",
            "confidence": 0.1
        }
