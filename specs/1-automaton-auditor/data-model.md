# Data Model: Automaton Auditor

**Date**: 2026-02-24  
**Purpose**: Define core entities, their fields, relationships, and validation rules

## Core Entities

### Evidence

**Purpose**: Represents objective forensic evidence collected by detective agents. Must be factual, not opinionated.

**Fields**:
- `goal: str` - The forensic objective being investigated (e.g., "Find StateGraph definition")
  - Required: Yes
  - Validation: Non-empty string
  - Example: "Verify Pydantic state models exist"
  
- `found: bool` - Whether the artifact exists (fact, not opinion)
  - Required: Yes
  - Validation: Boolean (True/False)
  - Example: True
  
- `content: Optional[str]` - Extracted code snippet or text
  - Required: No
  - Validation: String or None
  - Example: "from langgraph.graph import StateGraph"
  
- `location: str` - File path or commit hash for traceability
  - Required: Yes
  - Validation: Non-empty string, must be valid path or commit hash
  - Example: "src/graph.py" or "a1b2c3d4"
  
- `rationale: str` - Explanation of confidence in this evidence
  - Required: Yes
  - Validation: Non-empty string
  - Example: "AST parsing confirmed StateGraph import at line 15"
  
- `confidence: float` - Numeric score 0.0-1.0 indicating certainty
  - Required: Yes
  - Validation: Float between 0.0 and 1.0 (inclusive)
  - Example: 0.9

**Validation Rules**:
- All required fields must be present
- `confidence` must be in range [0.0, 1.0]
- `location` must be traceable (file path or commit hash format)
- `content` is optional but recommended when `found=True`

**State Transitions**: None (immutable once created)

### JudicialOpinion

**Purpose**: Represents an opinion rendered by a judge persona evaluating evidence for a specific rubric criterion.

**Fields**:
- `judge: Literal["Prosecutor", "Defense", "TechLead"]` - Persona identifier
  - Required: Yes
  - Validation: Must be exactly one of the three literal values
  - Example: "Prosecutor"
  
- `criterion_id: str` - Links to specific rubric dimension
  - Required: Yes
  - Validation: Non-empty string matching rubric dimension ID
  - Example: "langgraph_architecture"
  
- `score: int` - Numeric rating 1-5
  - Required: Yes
  - Validation: Integer between 1 and 5 (inclusive)
  - Example: 3
  
- `argument: str` - Reasoning for this score
  - Required: Yes
  - Validation: Non-empty string, minimum 50 characters
  - Example: "Graph is linear, not parallel. Fails architectural requirement for fan-out execution."
  
- `cited_evidence: List[str]` - List of evidence IDs referenced
  - Required: Yes (can be empty list)
  - Validation: List of non-empty strings
  - Example: ["evidence_1", "evidence_3"]

**Validation Rules**:
- `judge` must be one of the three persona types
- `score` must be in range [1, 5]
- `argument` must be substantial (minimum 50 characters to prevent shallow reasoning)
- `cited_evidence` must reference actual evidence IDs from state
- `criterion_id` must match a rubric dimension ID

**State Transitions**: None (immutable once created)

### AgentState

**Purpose**: Main state container for the LangGraph workflow. Uses reducers for parallel safety.

**Fields**:
- `repo_url: str` - Target repository to audit
  - Required: Yes
  - Validation: Valid GitHub URL format
  - Example: "https://github.com/user/repo.git"
  
- `pdf_path: str` - PDF report to analyze
  - Required: Yes
  - Validation: Valid file path, file must exist
  - Example: "/path/to/report.pdf"
  
- `rubric_dimensions: List[Dict]` - Loaded rubric configuration
  - Required: Yes
  - Validation: List of dictionaries matching rubric schema
  - Example: [{"id": "langgraph_architecture", "name": "...", ...}]
  
- `evidences: Annotated[Dict[str, List[Evidence]], operator.ior]` - Evidence by criterion
  - Required: Yes (can be empty dict)
  - Validation: Dictionary mapping criterion_id to list of Evidence objects
  - Reducer: `operator.ior` (dictionary merge) for parallel safety
  - Example: {"langgraph_architecture": [Evidence(...), ...]}
  
- `opinions: Annotated[List[JudicialOpinion], operator.add]` - All judicial opinions
  - Required: Yes (can be empty list)
  - Validation: List of JudicialOpinion objects
  - Reducer: `operator.add` (list append) for parallel safety
  - Example: [JudicialOpinion(...), ...]
  
- `errors: Annotated[List[str], operator.add]` - Error messages
  - Required: Yes (can be empty list)
  - Validation: List of non-empty error message strings
  - Reducer: `operator.add` (list append) for parallel safety
  - Example: ["Git clone failed: timeout"]
  
- `final_report: str` - Generated Markdown audit report
  - Required: No (empty string initially)
  - Validation: Valid Markdown string
  - Example: "# Automaton Auditor Report\n\n..."

**Validation Rules**:
- `repo_url` must be a valid GitHub URL (starts with https://github.com/)
- `pdf_path` must exist and be readable
- `rubric_dimensions` must be valid JSON matching rubric schema
- `evidences` keys must match `criterion_id` values from rubric
- `opinions` must have unique combinations of (judge, criterion_id)
- `errors` should be collected, not cause crashes

**State Transitions**:
1. **Initial**: `evidences={}`, `opinions=[]`, `errors=[]`, `final_report=""`
2. **After Detectives**: `evidences` populated with Evidence objects
3. **After Judges**: `opinions` populated with JudicialOpinion objects
4. **After Chief Justice**: `final_report` contains Markdown report

**Reducer Behavior**:
- `operator.ior` for `evidences`: When multiple detectives write, dictionaries merge (keys preserved)
- `operator.add` for `opinions`: When multiple judges write, lists concatenate (all opinions preserved)
- `operator.add` for `errors`: When multiple nodes error, lists concatenate (all errors preserved)

### Rubric Dimension

**Purpose**: Represents a single evaluation criterion from the machine-readable rubric JSON.

**Fields** (from JSON schema):
- `id: str` - Unique identifier for evaluation criterion
  - Required: Yes
  - Validation: Non-empty string, unique within rubric
  - Example: "forensic_accuracy_code"
  
- `name: str` - Human-readable criterion name
  - Required: Yes
  - Validation: Non-empty string
  - Example: "Forensic Accuracy (Codebase)"
  
- `target_artifact: Literal["github_repo", "pdf_report"]` - What to analyze
  - Required: Yes
  - Validation: Must be "github_repo" or "pdf_report"
  - Example: "github_repo"
  
- `forensic_instruction: str` - Protocol for detective agents
  - Required: Yes
  - Validation: Non-empty string
  - Example: "Trace the repository for production-grade engineering..."
  
- `judicial_logic: Dict[str, str]` - Per-persona evaluation guidelines
  - Required: Yes
  - Validation: Dictionary with keys "prosecutor", "defense", "tech_lead"
  - Example: {"prosecutor": "If tool execution relies on raw 'os.system'...", ...}
  
- `synthesis_rules: Dict[str, str]` - Conflict resolution rules (optional, at rubric level)
  - Required: No
  - Validation: Dictionary of rule name to rule description
  - Example: {"security_override": "Confirmed security flaws cap total score at 3."}

**Validation Rules**:
- `id` must be unique across all dimensions
- `target_artifact` must match detective agent capabilities
- `judicial_logic` must have all three persona keys
- `forensic_instruction` must be actionable for detective agents

**State Transitions**: None (loaded once at startup, immutable)

## Relationships

### Evidence → Rubric Dimension
- **Type**: Many-to-One
- **Relationship**: Each Evidence is collected for a specific `criterion_id` (rubric dimension)
- **Implementation**: `evidences` dictionary keys are `criterion_id` values

### JudicialOpinion → Rubric Dimension
- **Type**: Many-to-One
- **Relationship**: Each JudicialOpinion evaluates a specific `criterion_id`
- **Implementation**: `criterion_id` field references rubric dimension ID

### JudicialOpinion → Evidence
- **Type**: Many-to-Many
- **Relationship**: Each JudicialOpinion can cite multiple Evidence objects
- **Implementation**: `cited_evidence` list contains evidence IDs

### AgentState → All Entities
- **Type**: Container
- **Relationship**: AgentState contains all Evidence, JudicialOpinion, and Rubric Dimension data
- **Implementation**: State fields hold collections of entities

## Validation Summary

**Evidence**:
- ✅ All required fields present
- ✅ `confidence` in [0.0, 1.0]
- ✅ `location` is traceable

**JudicialOpinion**:
- ✅ `judge` is valid persona
- ✅ `score` in [1, 5]
- ✅ `argument` is substantial (≥50 chars)
- ✅ `cited_evidence` references exist

**AgentState**:
- ✅ `repo_url` is valid GitHub URL
- ✅ `pdf_path` exists
- ✅ `rubric_dimensions` matches schema
- ✅ Reducers prevent data loss in parallel execution

## State Flow

```
Initial State
  ↓
[Detectives collect evidence in parallel]
  ↓
State: evidences populated
  ↓
[Evidence Aggregator synchronizes]
  ↓
State: evidences ready for judges
  ↓
[Judges evaluate in parallel]
  ↓
State: opinions populated
  ↓
[Chief Justice synthesizes]
  ↓
Final State: final_report generated
```
