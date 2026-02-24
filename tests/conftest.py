"""Pytest configuration and shared fixtures."""
import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def tmp_repo_dir():
    """Create a temporary directory for test repositories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return """
    This is a test PDF report.
    It discusses Dialectical Synthesis and Metacognition.
    The architecture uses Fan-In and Fan-Out patterns.
    State Synchronization is critical for parallel execution.
    """
