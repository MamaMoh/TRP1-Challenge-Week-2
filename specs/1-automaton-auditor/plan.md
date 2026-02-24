# Implementation Plan: Automaton Auditor - Digital Courtroom Swarm

**Branch**: `1-automaton-auditor` | **Date**: 2026-02-24 | **Spec**: [spec.md](./spec.md)

## Summary

The Automaton Auditor is a production-grade, hierarchical multi-agent LangGraph system that autonomously evaluates GitHub repositories and PDF reports through a "Digital Courtroom" architecture. The system implements three distinct layers: (1) Detective Layer for parallel forensic evidence collection using AST parsing and git analysis, (2) Judicial Layer with three dialectical personas (Prosecutor, Defense, Tech Lead) that independently evaluate evidence, and (3) Chief Justice Layer that synthesizes verdicts using deterministic conflict resolution rules. The system produces executive-grade Markdown audit reports with actionable remediation plans, serving as both an automated grader and a blueprint for future PR security audits and compliance checking.

## Technical Context

**Language/Version**: Python 3.10+ (required by LangGraph and modern type hints)  
**Primary Dependencies**: 
- LangGraph >=0.2.0 (StateGraph orchestration)
- LangChain >=0.3.0 (LLM integration, prompts)
- LangChain-OpenAI >=0.2.0 (GPT-4o for judge personas)
- Pydantic >=2.0.0 (typed model validation)
- Docling >=1.0.0 (PDF parsing)
- Python-dotenv >=1.0.0 (environment configuration)
- LangSmith >=0.1.0 (observability tracing)

**Storage**: File-based (Markdown reports, JSON rubric, temporary git clones)  
**Testing**: pytest (unit tests for tools, integration tests for graph orchestration, contract tests for state models)  
**Target Platform**: Cross-platform (Windows/Linux/macOS) - Python CLI tool  
**Project Type**: CLI tool (command-line interface for auditing repositories)  
**Performance Goals**: 
- Complete audit of typical repository (50-200 files) in under 10 minutes
- Parallel evidence collection should reduce time by 60%+ vs sequential
- AST parsing should complete in under 30 seconds for typical codebase

**Constraints**: 
- Must handle repositories up to 1000 files, 100MB
- All git operations must be sandboxed (tempfile.TemporaryDirectory)
- No raw os.system calls (security requirement)
- All LLM outputs must be structured (Pydantic validation)
- State reducers required for parallel safety

**Scale/Scope**: 
- Single repository audit per execution
- 3 detective agents (RepoInvestigator, DocAnalyst, optional VisionInspector)
- 3 judge personas (Prosecutor, Defense, Tech Lead)
- 1 synthesis node (Chief Justice)
- 4 rubric dimensions (forensic_accuracy_code, forensic_accuracy_docs, judicial_nuance, langgraph_architecture)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Check (Phase 0)

#### Gate 1: State Reducers ✅ PASS
**Status**: Required by spec (FR-7). Implementation will use operator.ior for evidences dict and operator.add for opinions/errors lists.

#### Gate 2: Structured Outputs ✅ PASS
**Status**: Required by spec (FR-2). All judge outputs will be Pydantic JudicialOpinion models with .with_structured_output().

#### Gate 3: Deterministic Synthesis ✅ PASS
**Status**: Required by spec (FR-3). Chief Justice will use hardcoded Python rules, not LLM prompts.

#### Gate 4: Forensic Separation ✅ PASS
**Status**: Required by spec (FR-1, FR-2). Detectives only collect facts, Judges only interpret evidence, Chief Justice only synthesizes.

#### Gate 5: Parallel Architecture ✅ PASS
**Status**: Required by spec (FR-8). Graph will implement fan-out for detectives/judges and fan-in for evidence aggregation.

**Pre-Design Status**: ✅ ALL GATES PASS - Proceeded to Phase 0 research

### Post-Design Check (Phase 1)

#### Gate 1: State Reducers ✅ PASS
**Status**: Confirmed in data-model.md. AgentState uses `Annotated[Dict[str, List[Evidence]], operator.ior]` and `Annotated[List[JudicialOpinion], operator.add]`. Reducer behavior documented.

#### Gate 2: Structured Outputs ✅ PASS
**Status**: Confirmed in research.md. Judges use `.with_structured_output(JudicialOpinion)`. Pydantic validation enforced.

#### Gate 3: Deterministic Synthesis ✅ PASS
**Status**: Confirmed in research.md and data-model.md. Chief Justice uses hardcoded Python rules (security override, fact supremacy, Tech Lead tie-breaker). No LLM prompts for synthesis.

#### Gate 4: Forensic Separation ✅ PASS
**Status**: Confirmed in data-model.md. Evidence model is factual (found: bool, location: str). JudicialOpinion is interpretive (score, argument). Clear separation maintained.

#### Gate 5: Parallel Architecture ✅ PASS
**Status**: Confirmed in research.md. Graph structure uses fan-out (multiple edges from same source) and fan-in (synchronization node). Parallel execution pattern documented.

**Post-Design Status**: ✅ ALL GATES PASS - Ready for implementation

## Project Structure

### Documentation (this feature)

```text
specs/1-automaton-auditor/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── state.py             # Pydantic models (Evidence, JudicialOpinion, AgentState)
├── graph.py             # LangGraph StateGraph definition
├── config.py            # Configuration and rubric loading
├── nodes/
│   ├── detectives.py    # RepoInvestigator, DocAnalyst, VisionInspector nodes
│   ├── judges.py        # Prosecutor, Defense, TechLead nodes
│   └── justice.py      # ChiefJustice synthesis node
├── tools/
│   ├── git_tools.py     # Sandboxed git clone and history analysis
│   ├── ast_parser.py    # AST-based code structure verification
│   └── pdf_parser.py    # PDF parsing with Docling
└── utils/
    └── context_builder.py  # Rubric loading and context preparation

rubric/
└── week2_rubric.json    # Machine-readable rubric (from challenge spec)

audit/
├── report_bypeer_received/    # Reports received from peers
├── report_onpeer_generated/   # Reports generated for peers
├── report_onself_generated/   # Self-audit reports
└── langsmith_logs/            # Exported LangSmith traces

main.py                 # CLI entry point
pyproject.toml          # uv-managed dependencies
.env.example           # Environment variable template
README.md              # Project documentation

tests/
├── unit/
│   ├── test_state.py          # State model tests
│   ├── test_tools.py          # Tool function tests
│   └── test_nodes.py          # Node function tests
├── integration/
│   ├── test_graph_orchestration.py  # Full graph execution tests
│   └── test_end_to_end.py           # Complete audit workflow tests
└── fixtures/
    ├── sample_repo/            # Test repository
    └── sample_report.pdf       # Test PDF report
```

**Structure Decision**: Single project structure (Option 1) with clear separation of concerns:
- `src/state.py`: Foundation layer (Pydantic models)
- `src/tools/`: Forensic tools (isolated, testable)
- `src/nodes/`: Agent nodes (detectives, judges, justice)
- `src/graph.py`: Orchestration layer (LangGraph StateGraph)
- `main.py`: CLI interface (simple entry point)

This structure follows the Digital Courtroom metaphor: tools collect evidence, nodes process it, graph orchestrates the flow.

## Complexity Tracking

> **No violations detected - all complexity is justified by requirements**

All architectural decisions align with constitution principles and spec requirements. The multi-agent structure is necessary for dialectical evaluation, parallel execution is required for performance, and state reducers are mandatory for data safety.
