# Automaton Auditor

Deep LangGraph Swarms for Autonomous Governance — Week 2 Challenge

## Overview

The Automaton Auditor is a production-grade, hierarchical multi-agent system that evaluates GitHub repositories and PDF reports through a **Digital Courtroom** architecture: detectives collect forensic evidence in parallel, three judge personas (Prosecutor, Defense, Tech Lead) render dialectical opinions, and a Chief Justice node synthesizes a final verdict with deterministic conflict resolution. Output is an executive-grade audit report (Markdown + JSON).

## Project structure

```
├── src/
│   ├── state.py          # Pydantic models & AgentState (reducers)
│   ├── graph.py          # LangGraph StateGraph (detectives → judges → chief justice)
│   ├── config.py         # Rubric loading, env config, list rubrics
│   ├── paths.py          # Central paths (rubric, audit dirs, reports)
│   ├── nodes/            # detectives, judges, justice
│   ├── tools/            # git, AST, PDF (incl. URL download)
│   └── utils/            # report serialization, context builder, logger
├── rubric/               # Machine-readable rubric JSON (e.g. week2_rubric.json)
├── audit/                # Generated reports (report_onself_generated/, etc.)
├── tests/
└── main.py               # CLI entry point
```

## Setup

1. **Install dependencies**

   ```bash
   uv sync
   ```

2. **Environment**

   Copy `.env.example` to `.env` and set at least one of:

   - `OPENAI_API_KEY` — OpenAI (default)
   - `OPENROUTER_API_KEY` — OpenRouter (optional; set `LLM_MODEL` for Claude/Gemini etc.)

   The app loads `.env` first; if no API key is found, it falls back to `.env.example`.

3. **Run an audit**

   ```bash
   uv run python main.py --repo <repo_url> --pdf <path_or_url>
   ```

## Usage

| Action | Command |
|--------|--------|
| **Audit (local PDF)** | `python main.py -r https://github.com/user/repo.git -p ./report.pdf` |
| **Audit (PDF URL)** | `python main.py -r https://github.com/user/repo.git -p "https://drive.google.com/..."` |
| **List rubrics** | `python main.py --list-rubrics` |
| **Custom rubric** | `python main.py -r <repo> -p <pdf> --rubric rubric/week2_rubric.json` |
| **Custom output dir** | `python main.py -r <repo> -p <pdf> --output audit/report_onpeer_generated/` |
| **Compare with peer report** | `python main.py -r <repo> -p <pdf> --compare path/to/peer_audit_report.md` |
| **Verbose + tracing** | `python main.py -r <repo> -p <pdf> --verbose --trace` |

- **PDF**: Accepts a local path or an HTTP(S) URL. Google Drive share links are converted to direct-download URLs automatically.
- **Rubric**: Default is `rubric/week2_rubric.json`. Use `--list-rubrics` to see available files.

## Testing on peer vs by peer

| Scenario | What you do | Where output goes |
|----------|-------------|-------------------|
| **On peer** | You audit a peer’s repo and PDF (you run the auditor on their repo + report). | `--output audit/report_onpeer_generated/` so the report is saved there. |
| **By peer** | A peer has audited your repo and sent you their `audit_report.md`. You want to compare it with your own run. | Put their report in `audit/report_bypeer_received/` (e.g. `peer_audit_report.md`). Run your audit, then pass `--compare audit/report_bypeer_received/peer_audit_report.md` to see score differences and per-criterion diffs. |

**Example — audit a peer’s submission (on peer):**

```bash
python main.py -r https://github.com/peer/their-week2-repo.git -p "https://drive.google.com/..." -o audit/report_onpeer_generated/
```

**Example — compare with a report you received (by peer):**

```bash
# 1. Run your own audit (same repo + PDF)
python main.py -r https://github.com/you/your-repo.git -p ./reports/your_report.pdf -o audit/report_onself_generated/

# 2. Compare with the peer’s report you received
python main.py -r https://github.com/you/your-repo.git -p ./reports/your_report.pdf --compare audit/report_bypeer_received/peer_audit_report.md
```

The second run re-runs the full audit and then prints a comparison (overall score difference, criterion-by-criterion diffs, and issues the peer’s report flagged). To only compare without re-running, use the report parser in code: `from src.utils.report_parser import compare_reports; compare_reports("audit/report_onself_generated/audit_report.md", "audit/report_bypeer_received/peer_audit_report.md")`.

## Architecture

- **Layer 1 — Detectives**: RepoInvestigator (git + AST), DocAnalyst (PDF + cross-ref), VisionInspector (diagrams; optional). Run in parallel; evidence merged via state reducer.
- **Layer 2 — Judges**: Prosecutor, Defense, Tech Lead. Each scores every rubric dimension from their persona; opinions stored as dicts to avoid serialization issues.
- **Layer 3 — Chief Justice**: Hardcoded rules (security override, fact supremacy, functionality weight, dissent when variance > 2). Produces `AuditReport` and remediation plan.

**StateGraph flow (parallel fan-out / fan-in):**

```mermaid
flowchart LR
    subgraph Detectives["Layer 1: Detectives"]
        START([start])
        RI[RepoInvestigator]
        DA[DocAnalyst]
        VI[VisionInspector]
        START --> RI
        START --> DA
        START --> VI
    end
    subgraph Sync["Sync"]
        EA[Evidence Aggregator]
    end
    subgraph Judges["Layer 2: Judges"]
        P[Prosecutor]
        D[Defense]
        TL[Tech Lead]
    end
    CJ[Chief Justice]
    END([END])
    RI --> EA
    DA --> EA
    VI --> EA
    EA --> P
    EA --> D
    EA --> TL
    P --> CJ
    D --> CJ
    TL --> CJ
    CJ --> END
```

A detailed diagram is in `docs/architecture.md`. Report shows the **original PDF URL** (e.g. Google Drive link), not the temporary download path.

## Output

- **Markdown**: `audit_report.md` — metadata table, score overview, criterion breakdown with judge opinions and remediation.
- **JSON**: `audit_report.json` — same content for tooling.

## Testing

```bash
uv sync --dev
pytest
pytest --cov=src --cov-report=html
pytest tests/unit/
pytest tests/integration/
```

## Troubleshooting

| Issue | What to do |
|-------|------------|
| Rubric not found | Ensure `rubric/week2_rubric.json` exists; use `--rubric` or `--list-rubrics`. |
| No API key | Set `OPENAI_API_KEY` or `OPENROUTER_API_KEY` in `.env` (or `.env.example`). |
| Git clone failed | Check repo URL, network, and that the repo is public or credentials are set. |
| PDF download failed | For Google Drive, use a link shared with “Anyone with the link”. |
| Synthesis failed | Inspect `debug_state.json` in the output dir; use `--trace` and LangSmith. |
| Rate limits | Rate limiter is enabled; wait and retry or adjust `src/utils/rate_limiter.py`. |

## License

Week 2 Challenge — TRP1 Intensive Training
