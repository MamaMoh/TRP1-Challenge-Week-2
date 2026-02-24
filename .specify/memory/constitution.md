# Automaton Auditor Constitution

## Core Principles

### I. Production-Grade Architecture
Every component must be production-ready: proper error handling, observability, typed state management, and structured outputs. No toy implementations or proof-of-concepts. The system must handle edge cases gracefully and provide full traceability.

### II. Separation of Concerns (Digital Courtroom)
Strict separation between layers: Detectives collect facts only (no opinions), Judges interpret evidence only (no investigation), Chief Justice synthesizes only (no new evidence collection). This separation prevents hallucination and ensures objectivity.

### III. Parallel Execution Safety
All parallel agent execution must use state reducers (operator.ior for dictionaries, operator.add for lists) to prevent data loss. Typed state (Pydantic + TypedDict) is mandatory, not optional.

### IV. Deterministic Conflict Resolution
Chief Justice synthesis must use hardcoded deterministic rules, not LLM prompts. Security flaws always cap scores at 3. Facts override opinions. Tech Lead breaks ties. All conflict resolution logic must be traceable and auditable.

### V. Forensic Accuracy Over Speed
Evidence collection must use AST parsing (not regex) for code structure verification. Git history analysis must verify actual commit patterns, not just count commits. All evidence must include confidence scores, locations, and rationale.

### VI. Dialectical Tension Required
Judge personas must have distinct, non-overlapping system prompts (minimum 90% difference). Prosecutor hunts flaws, Defense rewards effort, Tech Lead evaluates pragmatically. Genuine disagreement is expected and valuable.

### VII. Observability Mandatory
Full LangSmith tracing required (LANGCHAIN_TRACING_V2=true). All agent interactions, evidence collection, and judicial deliberation must be traceable. Traces must capture the "reasoning loop" showing how judges argue.

## Technology Constraints

- **Language**: Python 3.10+ (required by LangGraph)
- **State Management**: LangGraph StateGraph with Pydantic models (non-negotiable)
- **LLM Integration**: LangChain with structured outputs (.with_structured_output or bind_tools)
- **PDF Parsing**: Docling or equivalent (not PyPDF2 for better structure extraction)
- **Code Analysis**: Python AST module (not regex for structure verification)
- **Git Operations**: Sandboxed temporary directories (tempfile.TemporaryDirectory)

## Quality Gates

### Gate 1: State Reducers
**REQUIRED**: All parallel writes must use reducers. Violation: ERROR - system will lose data in parallel execution.

### Gate 2: Structured Outputs
**REQUIRED**: All judge outputs must be Pydantic models. Violation: ERROR - freeform text cannot be validated or traced.

### Gate 3: Deterministic Synthesis
**REQUIRED**: Chief Justice must use hardcoded rules. Violation: ERROR - LLM-based synthesis is non-deterministic and non-auditable.

### Gate 4: Forensic Separation
**REQUIRED**: Detectives never opine, Judges never investigate. Violation: ERROR - breaks objectivity and enables hallucination.

### Gate 5: Parallel Architecture
**REQUIRED**: Detectives and Judges must execute in parallel (fan-out/fan-in). Violation: WARNING - linear execution fails challenge requirements.

## Development Workflow

1. **Foundation First**: State models and dependencies must be implemented before any agents
2. **Tools Before Agents**: Forensic tools (git, AST, PDF) must be implemented before detective nodes
3. **Detectives Before Judges**: Evidence collection must work before judicial evaluation
4. **Judges Before Synthesis**: All three judge personas must work before Chief Justice
5. **Test with Real Data**: Use actual Week 2 repositories for testing, not synthetic examples

## Governance

Constitution supersedes all other practices. Amendments require:
- Documentation of why change is needed
- Impact analysis on existing architecture
- Approval for complexity increases

All PRs must verify compliance with constitution gates. Complexity violations must be justified in Complexity Tracking section.

**Version**: 1.0.0 | **Ratified**: 2026-02-24 | **Last Amended**: 2026-02-24
