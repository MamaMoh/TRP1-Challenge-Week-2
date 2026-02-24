# Research: Automaton Auditor Implementation

**Date**: 2026-02-24  
**Purpose**: Resolve technical unknowns and establish best practices for implementation

## Research Topics

### 1. LangGraph StateGraph Parallel Execution Patterns

**Decision**: Use `add_edge()` with multiple nodes from same source for fan-out, and synchronization node for fan-in.

**Rationale**: 
- LangGraph supports parallel execution by having multiple edges from a single node
- Fan-out: Multiple `add_edge()` calls from same source node to different target nodes
- Fan-in: All parallel nodes must complete before next layer (use conditional edges or explicit synchronization)
- State reducers (operator.ior, operator.add) ensure safe parallel writes

**Alternatives Considered**:
- Sequential execution: Rejected - fails challenge requirements and performance goals
- Threading/async: Rejected - LangGraph handles parallelism internally, manual threading would conflict

**Implementation Pattern**:
```python
# Fan-out: Detectives run in parallel
workflow.add_edge("entry", "repo_investigator")
workflow.add_edge("entry", "doc_analyst")
workflow.add_edge("entry", "vision_inspector")

# Fan-in: Synchronization before judges
workflow.add_edge("repo_investigator", "evidence_aggregator")
workflow.add_edge("doc_analyst", "evidence_aggregator")
workflow.add_edge("vision_inspector", "evidence_aggregator")

# Fan-out: Judges run in parallel
workflow.add_edge("evidence_aggregator", "prosecutor")
workflow.add_edge("evidence_aggregator", "defense")
workflow.add_edge("evidence_aggregator", "tech_lead")
```

### 2. Pydantic State Reducers for Parallel Safety

**Decision**: Use `Annotated[Dict, operator.ior]` for dictionary merges and `Annotated[List, operator.add]` for list appends.

**Rationale**:
- `operator.ior` (|=) merges dictionaries without overwriting keys
- `operator.add` concatenates lists without losing elements
- LangGraph automatically applies reducers when parallel nodes write to same state field
- TypedDict + Pydantic provides type safety and validation

**Alternatives Considered**:
- Manual merging in nodes: Rejected - error-prone, violates DRY principle
- Locking mechanisms: Rejected - unnecessary complexity, reducers are atomic

**Implementation Pattern**:
```python
from typing import Annotated
import operator

class AgentState(TypedDict):
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]
    opinions: Annotated[List[JudicialOpinion], operator.add]
    errors: Annotated[List[str], operator.add]
```

### 3. AST Parsing for Code Structure Verification

**Decision**: Use Python's built-in `ast` module to parse and verify LangGraph structure.

**Rationale**:
- `ast` module is standard library, no external dependencies
- Can verify StateGraph instantiation, add_edge calls, reducer usage
- More reliable than regex for structure verification
- Can extract actual code structure, not just string matching

**Alternatives Considered**:
- Regex matching: Rejected - brittle, fails on code formatting changes
- tree-sitter: Rejected - adds dependency, ast module sufficient for Python-only analysis
- Static analysis tools: Rejected - overkill, ast module provides needed functionality

**Implementation Pattern**:
```python
import ast

def verify_stategraph(file_path: str) -> bool:
    with open(file_path) as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if (isinstance(node.func, ast.Attribute) and 
                node.func.attr == "StateGraph"):
                return True
    return False
```

### 4. PDF Parsing with Docling

**Decision**: Use Docling library for structured PDF parsing and text extraction.

**Rationale**:
- Docling provides better structure extraction than PyPDF2
- Handles complex layouts and tables
- Can extract text with context preservation
- Active maintenance and good documentation

**Alternatives Considered**:
- PyPDF2: Rejected - poor structure extraction, struggles with complex layouts
- pdfplumber: Rejected - good for tables but less structured output
- OCR libraries: Rejected - not needed for standard PDFs, adds complexity

**Implementation Pattern**:
```python
from docling import DocumentConverter

def parse_pdf(pdf_path: str) -> str:
    converter = DocumentConverter()
    doc = converter.convert(pdf_path)
    return doc.document.export_to_markdown()
```

### 5. LangSmith Tracing Setup

**Decision**: Use environment variables (LANGCHAIN_TRACING_V2=true) for automatic tracing.

**Rationale**:
- LangSmith integrates automatically with LangChain/LangGraph
- No code changes needed, just environment configuration
- Provides full observability into agent reasoning
- Traces are exportable for review

**Alternatives Considered**:
- Custom logging: Rejected - doesn't capture LLM reasoning, less structured
- Manual instrumentation: Rejected - LangSmith automatic tracing is sufficient

**Implementation Pattern**:
```bash
# .env file
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_key
LANGCHAIN_PROJECT=automaton-auditor
```

### 6. Structured Outputs with LangChain

**Decision**: Use `.with_structured_output(PydanticModel)` for judge personas.

**Rationale**:
- Ensures all judge outputs are validated Pydantic models
- Prevents freeform text that can't be traced or validated
- Automatic retry on validation failures
- Type-safe integration with state management

**Alternatives Considered**:
- Manual JSON parsing: Rejected - error-prone, no validation
- bind_tools(): Rejected - more complex, structured_output is simpler for this use case
- Prompt engineering only: Rejected - doesn't guarantee structure, violates constitution

**Implementation Pattern**:
```python
from langchain_openai import ChatOpenAI
from src.state import JudicialOpinion

llm = ChatOpenAI(model="gpt-4o")
chain = prompt | llm.with_structured_output(JudicialOpinion)
opinion = chain.invoke({"evidence": evidence_text})
```

### 7. Sandboxed Git Operations

**Decision**: Use `tempfile.TemporaryDirectory()` for all git clone operations.

**Rationale**:
- Automatic cleanup after execution
- Isolated from working directory
- Prevents contamination of local environment
- Security best practice for untrusted repositories

**Alternatives Considered**:
- Fixed directory: Rejected - security risk, cleanup issues
- Docker containers: Rejected - overkill, adds complexity
- GitPython library: Rejected - still needs directory management, subprocess is sufficient

**Implementation Pattern**:
```python
import tempfile
import subprocess

def clone_repo(repo_url: str) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = os.path.join(tmpdir, "repo")
        subprocess.run(
            ["git", "clone", repo_url, repo_path],
            check=True,
            capture_output=True
        )
        return repo_path  # Note: path valid only within context
```

## Resolved Clarifications

All technical decisions have been made. No NEEDS CLARIFICATION markers remain.

## Next Steps

Proceed to Phase 1: Design & Contracts
- Create data-model.md with entity definitions
- Define interface contracts (CLI interface)
- Create quickstart.md for developer onboarding
