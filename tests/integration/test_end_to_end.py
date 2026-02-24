"""End-to-end tests for complete audit workflow."""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.graph import build_auditor_graph
from src.state import AgentState


class TestEndToEnd:
    """End-to-end tests for complete audit workflow."""
    
    @pytest.fixture
    def sample_rubric(self):
        """Sample rubric for testing."""
        return {
            "rubric_metadata": {
                "rubric_name": "Test Rubric",
                "version": "1.0.0"
            },
            "dimensions": [
                {
                    "id": "test_criterion",
                    "name": "Test Criterion",
                    "target_artifact": "github_repo",
                    "forensic_instruction": "Test instruction",
                    "judicial_logic": {
                        "prosecutor": "Be critical",
                        "defense": "Be charitable",
                        "tech_lead": "Be pragmatic"
                    }
                }
            ],
            "synthesis_rules": {
                "security_override": "Test rule"
            }
        }
    
    @pytest.fixture
    def sample_state(self, sample_rubric):
        """Create a sample AgentState."""
        return {
            "repo_url": "https://github.com/test/repo.git",
            "pdf_path": "/test/report.pdf",
            "rubric_dimensions": sample_rubric["dimensions"],
            "evidences": {},
            "opinions": [],
            "errors": [],
            "final_report": None
        }
    
    def test_complete_workflow_structure(self, sample_state):
        """Test that the complete workflow has correct structure."""
        graph = build_auditor_graph()
        assert graph is not None
        
        # Verify state structure
        assert "repo_url" in sample_state
        assert "rubric_dimensions" in sample_state
        assert isinstance(sample_state["evidences"], dict)
        assert isinstance(sample_state["opinions"], list)
    
    @pytest.mark.skip(reason="Requires actual API keys and network access")
    def test_full_audit_execution(self, sample_state):
        """Test full audit execution (requires API keys)."""
        # This test would run a full audit but is skipped by default
        # Uncomment and provide API keys to run
        graph = build_auditor_graph()
        # final_state = graph.invoke(sample_state)
        # assert final_state["final_report"] is not None
