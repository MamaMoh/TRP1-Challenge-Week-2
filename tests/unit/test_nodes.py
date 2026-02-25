"""Unit tests for node functions."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.state import AgentState, Evidence, JudicialOpinion
from src.nodes.detectives import (
    repo_investigator_node,
    doc_analyst_node,
    evidence_aggregator_node
)
from src.nodes.judges import prosecutor_node, defense_node, tech_lead_node
from src.nodes.justice import chief_justice_node


class TestDetectiveNodes:
    """Tests for detective nodes."""
    
    @pytest.fixture
    def sample_state(self):
        """Create a sample AgentState for testing."""
        return {
            "repo_url": "https://github.com/test/repo.git",
            "pdf_path": "/test/report.pdf",
            "rubric_dimensions": [
                {
                    "id": "test_criterion",
                    "name": "Test Criterion",
                    "target_artifact": "github_repo",
                    "forensic_instruction": "Test instruction",
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
    
    def test_evidence_aggregator_node(self, sample_state):
        """Test evidence aggregator node."""
        result = evidence_aggregator_node(sample_state)
        # Should return state unchanged (just passes through)
        assert result == sample_state
    
    @patch('src.nodes.detectives.clone_repo')
    @patch('src.nodes.detectives.analyze_git_history')
    @patch('src.nodes.detectives.verify_state_models')
    @patch('src.nodes.detectives.analyze_graph_structure')
    def test_repo_investigator_node_success(self, mock_graph, mock_state, mock_git, mock_clone, sample_state):
        """Test repo investigator node with successful analysis."""
        # Mock successful clone and analysis
        mock_clone.return_value = "/tmp/repo"
        mock_git.return_value = {
            "has_progression": True,
            "commit_count": 5,
            "commit_summary": "Test commits",
            "timestamps": [],
            "rationale": "Good progression",
            "confidence": 0.9
        }
        mock_state.return_value = {
            "has_pydantic_state": True,
            "code_snippet": "class State: pass",
            "file_path": "src/state.py",
            "rationale": "Found Pydantic",
            "confidence": 0.9
        }
        mock_graph.return_value = {
            "has_parallel_execution": True,
            "graph_structure": "StateGraph()",
            "file_path": "src/graph.py",
            "rationale": "Found parallel execution",
            "confidence": 0.9
        }
        
        with patch('tempfile.TemporaryDirectory') as mock_tmp:
            mock_tmp.return_value.__enter__.return_value = "/tmp"
            result = repo_investigator_node(sample_state)
            
            assert "evidences" in result
            # Should have collected some evidence
            assert isinstance(result["evidences"], dict)
    
    @patch('src.nodes.detectives.parse_pdf')
    def test_doc_analyst_node_success(self, mock_parse, sample_state):
        """Test doc analyst node with successful PDF parsing."""
        mock_parse.return_value = "This document discusses Dialectical Synthesis and Metacognition."
        
        # Update state for PDF dimension
        sample_state["rubric_dimensions"] = [
            {
                "id": "theoretical_depth",
                "name": "Theoretical Depth",
                "target_artifact": "pdf_report",
                "forensic_instruction": "Search for keywords",
                "judicial_logic": {
                    "prosecutor": "Test",
                    "defense": "Test",
                    "tech_lead": "Test"
                }
            }
        ]
        
        result = doc_analyst_node(sample_state)
        assert "evidences" in result


class TestJudgeNodes:
    """Tests for judge nodes."""
    
    @pytest.fixture
    def sample_state_with_evidence(self):
        """Create a sample state with evidence."""
        return {
            "repo_url": "https://github.com/test/repo.git",
            "pdf_path": "/test/report.pdf",
            "rubric_dimensions": [
                {
                    "id": "test_criterion",
                    "name": "Test Criterion",
                    "target_artifact": "github_repo",
                    "forensic_instruction": "Test",
                    "judicial_logic": {
                        "prosecutor": "Be critical",
                        "defense": "Be charitable",
                        "tech_lead": "Be pragmatic"
                    }
                }
            ],
            "evidences": {
                "test_criterion": [
                    Evidence(
                        goal="Test",
                        found=True,
                        content="Test content",
                        location="test.py",
                        rationale="Test",
                        confidence=0.9
                    )
                ]
            },
            "opinions": [],
            "errors": [],
            "final_report": None
        }
    
    @patch('src.nodes.judges.ChatOpenAI')
    @patch('src.nodes.judges.get_rate_limiter')
    def test_prosecutor_node(self, mock_rate_limiter, mock_llm_class, sample_state_with_evidence):
        """Test prosecutor node."""
        # Mock rate limiter
        mock_limiter = Mock()
        mock_limiter.wait_if_needed.return_value = 0.0
        mock_rate_limiter.return_value = mock_limiter
        
        # Mock LLM
        mock_llm = Mock()
        mock_chain = Mock()
        mock_opinion = JudicialOpinion(
            judge="Prosecutor",
            criterion_id="test_criterion",
            score=2,
            argument="Critical analysis"
        )
        mock_chain.invoke.return_value = mock_opinion
        mock_llm.with_structured_output.return_value = mock_chain
        mock_llm_class.return_value = mock_llm
        
        with patch('src.nodes.judges.ChatPromptTemplate') as mock_prompt:
            mock_pipe_left = Mock()
            mock_pipe_left.__or__ = lambda self, other: other
            mock_prompt.from_messages.return_value = mock_pipe_left

            result = prosecutor_node(sample_state_with_evidence)
            assert "opinions" in result
            assert len(result["opinions"]) > 0


class TestJusticeNode:
    """Tests for Chief Justice node."""
    
    @pytest.fixture
    def sample_state_with_opinions(self):
        """Create a sample state with judge opinions."""
        return {
            "repo_url": "https://github.com/test/repo.git",
            "pdf_path": "/test/report.pdf",
            "rubric_dimensions": [
                {
                    "id": "test_criterion",
                    "name": "Test Criterion",
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
            "opinions": [
                JudicialOpinion(
                    judge="Prosecutor",
                    criterion_id="test_criterion",
                    score=2,
                    argument="Too critical"
                ),
                JudicialOpinion(
                    judge="Defense",
                    criterion_id="test_criterion",
                    score=4,
                    argument="Too lenient"
                ),
                JudicialOpinion(
                    judge="TechLead",
                    criterion_id="test_criterion",
                    score=3,
                    argument="Balanced"
                )
            ],
            "errors": [],
            "final_report": None
        }
    
    @patch('src.nodes.justice.load_rubric')
    def test_chief_justice_node(self, mock_load_rubric, sample_state_with_opinions):
        """Test Chief Justice synthesis node."""
        mock_load_rubric.return_value = {
            "synthesis_rules": {
                "security_override": "Test",
                "fact_supremacy": "Test"
            }
        }
        
        result = chief_justice_node(sample_state_with_opinions)
        assert "final_report" in result
        assert result["final_report"] is not None
        assert hasattr(result["final_report"], "overall_score")
        assert hasattr(result["final_report"], "criteria")
