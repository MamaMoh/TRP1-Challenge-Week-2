# Automaton Auditor

Deep LangGraph Swarms for Autonomous Governance - Week 2 Challenge

## Overview

The Automaton Auditor is a production-grade, hierarchical multi-agent LangGraph system that autonomously evaluates GitHub repositories and PDF reports through a "Digital Courtroom" architecture. It forensically analyzes code, applies dialectical judgment from three distinct personas (Prosecutor, Defense, Tech Lead), and produces executive-grade audit reports.

## Project Structure

```
TRP1-Challenge-Week-2/
├── src/
│   ├── state.py        # Pydantic models (Evidence, JudicialOpinion, AgentState)
│   ├── graph.py        # LangGraph StateGraph definition
│   ├── config.py       # Configuration and rubric loading
│   ├── nodes/          # Detective, Judge, and Chief Justice nodes
│   ├── tools/          # Forensic tools (git, AST, PDF parsers)
│   └── utils/          # Utility functions
├── rubric/             # Machine-readable rubric JSON
├── audit/              # Generated audit reports
├── tests/              # Unit, integration, and fixture tests
└── main.py             # CLI entry point
```

## Setup

1. **Install dependencies:**
```bash
uv sync
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run the auditor:**
```bash
uv run python main.py --repo <repo_url> --pdf <pdf_path>
```

## Architecture

The system implements a three-layer "Digital Courtroom" architecture:

- **Layer 1: Detective Layer** - Parallel forensic evidence collection (RepoInvestigator, DocAnalyst, VisionInspector)
- **Layer 2: Judicial Layer** - Dialectical opinion generation (Prosecutor, Defense, Tech Lead personas)
- **Layer 3: Chief Justice** - Deterministic conflict resolution and report synthesis

## Features

- **Forensic Accuracy**: AST-based code analysis, git history verification, PDF cross-referencing
- **Dialectical Evaluation**: Three distinct judge personas with conflicting perspectives
- **Deterministic Synthesis**: Hardcoded rules for conflict resolution (not LLM averaging)
- **Production-Grade**: State reducers for parallel safety, structured outputs, full observability

## Usage Examples

### Basic Audit
```bash
python main.py --repo https://github.com/user/repo.git --pdf report.pdf
```

### Self-Audit
```bash
python main.py --repo https://github.com/yourusername/your-repo.git \
               --pdf your_report.pdf \
               --output audit/report_onself_generated/
```

### Compare with Peer Report
```bash
python main.py --repo https://github.com/user/repo.git \
               --pdf report.pdf \
               --compare audit/report_bypeer_received/peer_audit_report.md
```

### Verbose Mode with Tracing
```bash
python main.py --repo https://github.com/user/repo.git \
               --pdf report.pdf \
               --verbose --trace
```

## Workflows

### Self-Audit Workflow

Before submitting your Week 2 repository for peer review, run a self-audit to identify issues proactively:

1. **Generate Self-Audit Report:**
   ```bash
   python main.py --repo <your_repo_url> --pdf <your_pdf_report> \
                  --output audit/report_onself_generated/
   ```

2. **Review the Report:**
   - Check the executive summary for overall score
   - Review criterion-by-criterion breakdown
   - Focus on criteria scoring below 3/5

3. **Apply Remediation:**
   - Follow the remediation plan in the report
   - Fix identified issues in your code
   - Update your PDF report if claims don't match implementation

4. **Re-run Self-Audit:**
   - Verify improvements are detected
   - Iterate until all critical issues are resolved

**Benefits:**
- Catch issues before peer review
- Improve your score proactively
- Ensure your repository meets all rubric requirements
- Same forensic rigor as peer audits

### Adversarial Improvement Loop (MinMax Optimization)

The adversarial improvement loop is the core meta-game of Week 2: your auditor improves by finding issues in peer code, and peer auditors improve your code by finding issues you missed.

1. **Receive Peer Audit:**
   - Peer runs their auditor on your repository
   - You receive report in `audit/report_bypeer_received/`
   - Review issues identified by peer's auditor

2. **Fix Your Week 2 Code:**
   - Address issues found by peer auditor
   - Fix bugs, improve architecture, add missing features
   - Update your repository

3. **Improve Your Auditor:**
   - Analyze what peer auditor caught that yours missed
   - Enhance your detective nodes to catch similar issues
   - Refine judge prompts for better evaluation
   - Add new evidence collection protocols

4. **Compare Audits:**
   ```bash
   python main.py --repo <repo> --pdf <pdf> \
                  --compare audit/report_bypeer_received/peer_report.md
   ```
   - See score differences
   - Identify where your auditor is too lenient/strict
   - Understand peer's evaluation criteria

5. **Iterate:**
   - Re-run your improved auditor on peers' repos
   - Receive new feedback
   - Continue the improvement cycle

**Goal:** Create a co-evolutionary pressure where:
- Stronger auditors find deeper flaws
- Better code forces auditors to evolve further
- Both code quality and auditor capability improve

## Development

See [quickstart.md](specs/1-automaton-auditor/quickstart.md) for detailed development workflow.

## Testing

Run the test suite:

```bash
# Install dev dependencies
uv sync --dev

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_state.py

# Run integration tests
pytest tests/integration/
```

## Troubleshooting

### Common Issues

**Error: "Rubric file not found"**
- Ensure `rubric/week2_rubric.json` exists
- Check file path is correct
- Verify JSON syntax is valid

**Error: "Required environment variable not set: OPENAI_API_KEY"**
- Copy `.env.example` to `.env`
- Add your OpenAI API key to `.env`
- Restart your terminal/IDE after setting environment variables

**Error: "Git clone failed"**
- Verify repository URL is accessible
- Check network connection
- Ensure repository is public or credentials are configured
- Try cloning manually: `git clone <repo_url>`

**Error: "PDF parsing failed"**
- Verify PDF file exists and is readable
- Ensure PDF is not corrupted
- Check if PDF requires OCR (not supported - use standard PDFs)
- Try opening the PDF in a PDF viewer to verify it's valid

**Warning: "Synthesis failed - no report generated"**
- Check LangSmith traces for detailed error information
- Review partial state saved in `debug_state.json`
- Verify all judge nodes completed successfully
- Check for rate limiting issues (see rate limiter logs)

**Error: "Rate limit exceeded"**
- The system includes rate limiting (60 calls/minute default)
- Wait a few minutes and retry
- Check LangSmith dashboard for API usage
- Consider adjusting rate limits in `src/utils/rate_limiter.py`

**Performance Issues**
- AST parsing is cached for performance
- Large repositories may take longer to analyze
- Use `--verbose` flag to see progress
- Check system resources (memory, CPU)

## License

Week 2 Challenge - TRP1 Intensive Training
