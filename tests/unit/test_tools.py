"""Unit tests for forensic tools."""
import os
import tempfile
import pytest
from pathlib import Path

from src.tools.git_tools import clone_repo, analyze_git_history
from src.tools.ast_parser import (
    verify_state_models,
    analyze_graph_structure,
    verify_safe_tool_engineering,
    verify_structured_output
)
from src.tools.pdf_parser import parse_pdf, extract_keywords, verify_file_claims


class TestGitTools:
    """Tests for git tools."""
    
    def test_analyze_git_history_nonexistent_repo(self):
        """Test git history analysis on non-existent repo."""
        result = analyze_git_history("/nonexistent/path")
        assert result["has_progression"] is False
        assert result["commit_count"] == 0
        assert result["confidence"] < 0.5
    
    def test_analyze_git_history_empty_repo(self, tmp_path):
        """Test git history analysis on empty directory."""
        result = analyze_git_history(str(tmp_path))
        assert result["has_progression"] is False
        assert "commit_count" in result


class TestASTParser:
    """Tests for AST parser tools."""
    
    def test_verify_state_models_nonexistent_path(self):
        """Test state model verification on non-existent path."""
        result = verify_state_models("/nonexistent/path")
        assert result["has_pydantic_state"] is False
        assert result["confidence"] < 1.0
    
    def test_analyze_graph_structure_nonexistent_path(self):
        """Test graph structure analysis on non-existent path."""
        result = analyze_graph_structure("/nonexistent/path")
        assert result["has_parallel_execution"] is False
        assert "rationale" in result
    
    def test_verify_safe_tool_engineering_nonexistent_path(self):
        """Test safe tool engineering verification on non-existent path."""
        result = verify_safe_tool_engineering("/nonexistent/path")
        assert result["is_safe"] is False
        assert "uses_sandboxing" in result
    
    def test_verify_structured_output_nonexistent_path(self):
        """Test structured output verification on non-existent path."""
        result = verify_structured_output("/nonexistent/path")
        assert result["has_structured_output"] is False
        assert "uses_pydantic" in result
    
    def test_verify_state_models_with_valid_pydantic(self, tmp_path):
        """Test state model verification with valid Pydantic code."""
        state_file = tmp_path / "state.py"
        state_file.write_text("""
from pydantic import BaseModel

class Evidence(BaseModel):
    goal: str
    found: bool
""")
        
        # Create src directory structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "state.py").write_text(state_file.read_text())
        
        result = verify_state_models(str(tmp_path))
        # Should find the Pydantic model
        assert "has_pydantic_state" in result


class TestPDFParser:
    """Tests for PDF parser tools."""
    
    def test_extract_keywords(self):
        """Test keyword extraction from text."""
        content = "This document discusses Dialectical Synthesis and Metacognition in detail."
        keywords = ["Dialectical Synthesis", "Metacognition", "Fan-Out"]
        results = extract_keywords(content, keywords)
        
        assert "Dialectical Synthesis" in results
        assert "Metacognition" in results
        assert len(results["Dialectical Synthesis"]) > 0
        assert len(results["Metacognition"]) > 0
        assert len(results["Fan-Out"]) == 0  # Not in content
    
    def test_verify_file_claims(self):
        """Test file claim verification."""
        pdf_content = "We implemented the logic in src/tools/ast_parser.py and src/nodes/judges.py"
        repo_files = ["src/tools/ast_parser.py", "src/nodes/judges.py", "src/state.py"]
        
        results = verify_file_claims(pdf_content, repo_files)
        # Should find some file paths
        assert len(results) > 0
    
    def test_parse_pdf_nonexistent(self):
        """Test PDF parsing on non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_pdf("/nonexistent/file.pdf")
