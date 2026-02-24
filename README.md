# Automaton Auditor

Deep LangGraph Swarms for Autonomous Governance

## Project Structure

```
TRP1-Challenge-Week-2/
├── src/
│   ├── nodes/          # Detective, Judge, and Chief Justice nodes
│   ├── tools/          # Forensic tools (git, AST, PDF parsers)
│   └── utils/          # Utility functions
├── rubric/             # Machine-readable rubric JSON
├── audit/              # Generated audit reports
└── main.py             # Entry point
```

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the auditor:
```bash
uv run python main.py <repo_url> <pdf_path>
```

## Architecture

- **Layer 1: Detective Layer** - Forensic evidence collection
- **Layer 2: Judicial Layer** - Dialectical opinion generation
- **Layer 3: Supreme Court** - Final verdict synthesis
