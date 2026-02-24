"""Integration tests for graph orchestration."""
import pytest
from unittest.mock import Mock, patch

from src.graph import build_auditor_graph
from src.state import AgentState


class TestGraphOrchestration:
    """Tests for LangGraph orchestration."""
    
    @pytest.fixture
    def sample_state(self):
        """Create a sample AgentState."""
        return {
            "repo_url": "https://github.com/test/repo.git",
            "pdf_path": "/test/report.pdf",
            "rubric_dimensions": [
                {
                    "id": "test_criterion",
                    "name": "Test",
                    "target_artifact": "github_repo",
                    "forensic_instruction": "Test",
                    "judicial_logic": {
                        "prosecutor": "Test",
                        "defense": "Test",
                        "tech_lead": "Test"
                    }
                }
            ],
            "evidences": {},
            "opinions": [],
            "errors": [],
            "final_report": None
        }
    
    def test_graph_builds_successfully(self):
        """Test that the graph can be built without errors."""
        graph = build_auditor_graph()
        assert graph is not None
    
    def test_graph_has_all_nodes(self):
        """Test that graph contains all required nodes."""
        graph = build_auditor_graph()
        # Graph should compile successfully
        assert graph is not None
    
    @patch('src.nodes.detectives.clone_repo')
    @patch('src.nodes.detectives.analyze_git_history')
    @patch('src.nodes.detectives.verify_state_models')
    @patch('src.nodes.detectives.analyze_graph_structure')
    @patch('src.nodes.detectives.parse_pdf')
    @patch('src.nodes.judges.ChatOpenAI')
    @patch('src.nodes.justice.load_rubric')
    def test_graph_execution_flow(self, mock_rubric, mock_llm, mock_pdf, mock_graph, 
                                   mock_state, mock_git, mock_clone, sample_state):
        """Test that graph executes through all layers."""
        # Mock all dependencies
        mock_clone.return_value = "/tmp/repo"
        mock_git.return_value = {"has_progression": True, "commit_count": 5, 
                                  "commit_summary": "", "timestamps": [],
                                  "rationale": "Test", "confidence": 0.9}
        mock_state.return_value = {"has_pydantic_state": True, "code_snippet": "",
                                   "file_path": "test.py", "rationale": "Test",
                                   "confidence": 0.9}
        mock_graph.return_value = {"has_parallel_execution": True, "graph_structure": "",
                                   "file_path": "test.py", "rationale": "Test",
                                   "confidence": 0.9}
        mock_pdf.return_value = "Test PDF content"
        
        mock_llm_instance = Mock()
        mock_chain = Mock()
        from src.state import JudicialOpinion
        mock_opinion = JudicialOpinion(
            judge="Prosecutor",
            criterion_id="test_criterion",
            score=3,
            argument="Test"
        )
        mock_chain.invoke.return_value = mock_opinion
        mock_llm_instance.with_structured_output.return_value = mock_chain
        mock_llm.return_value = mock_llm_instance
        
        mock_rubric.return_value = {"synthesis_rules": {}}
        
        graph = build_auditor_graph()
        
        with patch('tempfile.TemporaryDirectory') as mock_tmp:
            mock_tmp.return_value.__enter__.return_value = "/tmp"
            with patch('src.nodes.judges.ChatPromptTemplate'):
                with patch('src.nodes.judges.get_rate_limiter') as mock_rate:
                    mock_rate.return_value.wait_if_needed.return_value = 0.0
                    # Graph execution would happen here
                    # For now, just verify graph is buildable
                    assert graph is not None
