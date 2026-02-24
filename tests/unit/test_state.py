"""Unit tests for state models."""
import pytest
from pydantic import ValidationError

from src.state import Evidence, JudicialOpinion, CriterionResult, AuditReport


class TestEvidence:
    """Tests for Evidence model."""
    
    def test_evidence_creation(self):
        """Test creating a valid Evidence object."""
        evidence = Evidence(
            goal="Test goal",
            found=True,
            content="Test content",
            location="test/file.py",
            rationale="Test rationale",
            confidence=0.9
        )
        assert evidence.goal == "Test goal"
        assert evidence.found is True
        assert evidence.confidence == 0.9
        assert evidence.id is not None  # UUID should be auto-generated
    
    def test_evidence_confidence_bounds(self):
        """Test confidence score validation (0.0-1.0)."""
        # Valid confidence
        evidence = Evidence(
            goal="Test",
            found=True,
            location="test.py",
            rationale="Test",
            confidence=0.5
        )
        assert evidence.confidence == 0.5
        
        # Too high
        with pytest.raises(ValidationError):
            Evidence(
                goal="Test",
                found=True,
                location="test.py",
                rationale="Test",
                confidence=1.5
            )
        
        # Too low
        with pytest.raises(ValidationError):
            Evidence(
                goal="Test",
                found=True,
                location="test.py",
                rationale="Test",
                confidence=-0.1
            )
    
    def test_evidence_optional_content(self):
        """Test that content is optional."""
        evidence = Evidence(
            goal="Test",
            found=False,
            location="test.py",
            rationale="Test",
            confidence=0.5
        )
        assert evidence.content is None


class TestJudicialOpinion:
    """Tests for JudicialOpinion model."""
    
    def test_judicial_opinion_creation(self):
        """Test creating a valid JudicialOpinion."""
        opinion = JudicialOpinion(
            judge="Prosecutor",
            criterion_id="test_criterion",
            score=3,
            argument="Test argument",
            cited_evidence=["evidence_1", "evidence_2"]
        )
        assert opinion.judge == "Prosecutor"
        assert opinion.score == 3
        assert len(opinion.cited_evidence) == 2
    
    def test_judicial_opinion_score_bounds(self):
        """Test score validation (1-5)."""
        # Valid scores
        for score in [1, 3, 5]:
            opinion = JudicialOpinion(
                judge="Prosecutor",
                criterion_id="test",
                score=score,
                argument="Test"
            )
            assert opinion.score == score
        
        # Too high
        with pytest.raises(ValidationError):
            JudicialOpinion(
                judge="Prosecutor",
                criterion_id="test",
                score=6,
                argument="Test"
            )
        
        # Too low
        with pytest.raises(ValidationError):
            JudicialOpinion(
                judge="Prosecutor",
                criterion_id="test",
                score=0,
                argument="Test"
            )
    
    def test_judicial_opinion_judge_enum(self):
        """Test that judge must be one of the valid values."""
        valid_judges = ["Prosecutor", "Defense", "TechLead"]
        for judge in valid_judges:
            opinion = JudicialOpinion(
                judge=judge,
                criterion_id="test",
                score=3,
                argument="Test"
            )
            assert opinion.judge == judge
        
        # Invalid judge
        with pytest.raises(ValidationError):
            JudicialOpinion(
                judge="InvalidJudge",
                criterion_id="test",
                score=3,
                argument="Test"
            )
    
    def test_judicial_opinion_empty_cited_evidence(self):
        """Test that cited_evidence can be empty."""
        opinion = JudicialOpinion(
            judge="Prosecutor",
            criterion_id="test",
            score=3,
            argument="Test",
            cited_evidence=[]
        )
        assert opinion.cited_evidence == []


class TestCriterionResult:
    """Tests for CriterionResult model."""
    
    def test_criterion_result_creation(self):
        """Test creating a valid CriterionResult."""
        opinions = [
            JudicialOpinion(
                judge="Prosecutor",
                criterion_id="test",
                score=2,
                argument="Test"
            ),
            JudicialOpinion(
                judge="Defense",
                criterion_id="test",
                score=4,
                argument="Test"
            ),
            JudicialOpinion(
                judge="TechLead",
                criterion_id="test",
                score=3,
                argument="Test"
            )
        ]
        
        result = CriterionResult(
            dimension_id="test",
            dimension_name="Test Dimension",
            final_score=3,
            judge_opinions=opinions,
            remediation="Fix this"
        )
        assert result.dimension_id == "test"
        assert result.final_score == 3
        assert len(result.judge_opinions) == 3
        assert result.dissent_summary is None
    
    def test_criterion_result_with_dissent(self):
        """Test CriterionResult with dissent summary."""
        result = CriterionResult(
            dimension_id="test",
            dimension_name="Test",
            final_score=3,
            judge_opinions=[],
            dissent_summary="Prosecutor and Defense disagreed",
            remediation="Fix"
        )
        assert result.dissent_summary == "Prosecutor and Defense disagreed"


class TestAuditReport:
    """Tests for AuditReport model."""
    
    def test_audit_report_creation(self):
        """Test creating a valid AuditReport."""
        report = AuditReport(
            repo_url="https://github.com/test/repo.git",
            executive_summary="Test summary",
            overall_score=3.5,
            criteria=[],
            remediation_plan="Test plan"
        )
        assert report.repo_url == "https://github.com/test/repo.git"
        assert report.overall_score == 3.5
    
    def test_audit_report_score_bounds(self):
        """Test overall_score validation (1.0-5.0)."""
        # Valid scores
        for score in [1.0, 3.0, 5.0]:
            report = AuditReport(
                repo_url="https://github.com/test/repo.git",
                executive_summary="Test",
                overall_score=score,
                criteria=[],
                remediation_plan="Test"
            )
            assert report.overall_score == score
        
        # Too high
        with pytest.raises(ValidationError):
            AuditReport(
                repo_url="https://github.com/test/repo.git",
                executive_summary="Test",
                overall_score=6.0,
                criteria=[],
                remediation_plan="Test"
            )
        
        # Too low
        with pytest.raises(ValidationError):
            AuditReport(
                repo_url="https://github.com/test/repo.git",
                executive_summary="Test",
                overall_score=0.5,
                criteria=[],
                remediation_plan="Test"
            )
