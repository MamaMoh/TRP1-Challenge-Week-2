# Quickstart Guide: Automaton Auditor

**Date**: 2026-02-24  
**Purpose**: Get developers up and running with the Automaton Auditor in 5 minutes

## Prerequisites

- Python 3.10 or higher
- `uv` package manager installed
- Git command-line tools installed
- OpenAI API key (for LLM operations)
- LangSmith API key (optional, for tracing)

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/MamaMoh/TRP1-Challenge-Week-2.git
cd TRP1-Challenge-Week-2
```

### 2. Install Dependencies

```bash
uv sync
```

This installs all required packages:
- LangGraph, LangChain, LangChain-OpenAI
- Pydantic, typing-extensions
- Docling (PDF parsing)
- Python-dotenv

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
OPENAI_API_KEY=sk-your-key-here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key-here
LANGCHAIN_PROJECT=automaton-auditor
```

### 4. Run Tests (Optional but Recommended)

```bash
# Install dev dependencies
uv sync --dev

# Run test suite
pytest

# Run with verbose output
pytest -v
```

### 5. Verify Installation

```bash
uv run python -c "from src.state import Evidence, JudicialOpinion; print('✓ Installation successful')"
```

## Basic Usage

### Run Your First Audit

```bash
uv run python main.py \
  --repo https://github.com/user/week2-repo.git \
  --pdf ./path/to/report.pdf
```

The audit report will be saved to `audit/report_onself_generated/audit_report.md`

### Run with Verbose Output

```bash
uv run python main.py \
  --repo https://github.com/user/week2-repo.git \
  --pdf ./path/to/report.pdf \
  --verbose
```

This shows progress messages and evidence collection status.

### Run with Tracing

```bash
uv run python main.py \
  --repo https://github.com/user/week2-repo.git \
  --pdf ./path/to/report.pdf \
  --trace
```

This enables LangSmith tracing for debugging agent reasoning.

## Project Structure Overview

```
TRP1-Challenge-Week-2/
├── src/
│   ├── state.py          # Pydantic models (Evidence, JudicialOpinion, AgentState)
│   ├── graph.py          # LangGraph StateGraph definition
│   ├── nodes/            # Agent nodes (detectives, judges, justice)
│   ├── tools/            # Forensic tools (git, AST, PDF)
│   └── utils/            # Utility functions
├── rubric/
│   └── week2_rubric.json # Machine-readable rubric
├── audit/                # Generated reports
└── main.py               # CLI entry point
```

## Development Workflow

### 1. Make Changes

Edit files in `src/` directory. The system uses hot-reload for development.

### 2. Test Your Changes

```bash
# Run unit tests
uv run pytest tests/unit/

# Run integration tests
uv run pytest tests/integration/

# Run full test suite
uv run pytest
```

### 3. Test with Real Data

```bash
# Test against your own repository
uv run python main.py \
  --repo https://github.com/your-username/your-repo.git \
  --pdf ./your-report.pdf \
  --output audit/report_onself_generated/
```

### 4. Review Results

Check the generated report:
```bash
cat audit/report_onself_generated/audit_report.md
```

## Common Tasks

### Adding a New Detective Agent

1. Create node function in `src/nodes/detectives.py`
2. Add node to graph in `src/graph.py`
3. Wire edges for parallel execution
4. Test with `pytest tests/unit/test_detectives.py`

### Adding a New Judge Persona

1. Create node function in `src/nodes/judges.py`
2. Add distinct system prompt (90%+ different from others)
3. Ensure structured output (Pydantic model)
4. Add to graph parallel execution
5. Test with `pytest tests/unit/test_judges.py`

### Modifying Rubric

1. Edit `rubric/week2_rubric.json`
2. No code changes needed (rubric loaded at runtime)
3. Test with `--rubric` flag to use custom rubric

### Debugging Agent Reasoning

1. Enable tracing: `--trace` flag or `LANGCHAIN_TRACING_V2=true`
2. Check LangSmith dashboard for trace URL
3. Review agent prompts, responses, and state transitions
4. Use verbose mode: `--verbose` for stdout logging

## Troubleshooting

### "Missing OPENAI_API_KEY"

**Solution**: Add your API key to `.env` file:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### "Failed to clone repository"

**Solution**: 
- Check repository URL is valid and public
- Verify network connectivity
- Check git is installed: `git --version`

### "PDF file not found"

**Solution**: 
- Use absolute path: `--pdf /full/path/to/file.pdf`
- Or relative path from project root: `--pdf ./path/to/file.pdf`
- Verify file exists: `ls -la path/to/file.pdf`

### "State reducer error"

**Solution**: 
- Ensure all parallel nodes use reducers (operator.ior, operator.add)
- Check state model definitions in `src/state.py`
- Verify graph edges are correctly wired

### "Judge output not structured"

**Solution**: 
- Ensure `.with_structured_output(JudicialOpinion)` is used
- Check Pydantic model validation
- Verify prompt returns valid JSON

## Next Steps

- Read [data-model.md](./data-model.md) for entity definitions
- Review [contracts/cli-interface.md](./contracts/cli-interface.md) for CLI details
- Check [research.md](./research.md) for implementation decisions
- See [spec.md](./spec.md) for full requirements

## Getting Help

- Check logs in `audit/langsmith_logs/` for detailed traces
- Use `--verbose` flag for progress information
- Review error messages for specific failure points
- Check constitution compliance in `.specify/memory/constitution.md`
