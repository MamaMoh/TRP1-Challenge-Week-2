# Feature Specification: Automaton Auditor - Digital Courtroom Swarm

**Feature ID**: 1-automaton-auditor  
**Created**: 2026-02-24  
**Status**: Draft  
**Owner**: Development Team

## Overview

The Automaton Auditor is a production-grade, hierarchical multi-agent system that autonomously evaluates code repositories and documentation through a "Digital Courtroom" architecture. It forensically analyzes GitHub repositories and PDF reports, applies dialectical judgment from three distinct personas (Prosecutor, Defense, Tech Lead), synthesizes verdicts using deterministic conflict resolution, and produces executive-grade audit reports. The system serves both as an automated grader for Week 2 submissions and as a blueprint for future PR security audits, compliance checking, and architectural gatekeeping in AI-native organizations where code generation outpaces human review capacity.

## User Scenarios & Testing

### Primary Scenario: Audit a Week 2 Submission
**As a** peer evaluator or automated grading system  
**I want to** submit a GitHub repository URL and PDF report for automated forensic analysis  
**So that** I receive a comprehensive, objective audit report with scores, evidence, and remediation guidance

**Acceptance Criteria**:
- [ ] System accepts repository URL and PDF file path as inputs
- [ ] System produces a Markdown audit report within reasonable time (under 10 minutes for typical repository)
- [ ] Report includes executive summary, criterion-by-criterion scores (1-5), evidence citations, and actionable remediation plan
- [ ] Report is saved to designated audit output directory
- [ ] All evidence claims are traceable to specific file paths or commit hashes

### Secondary Scenario: Participate in Adversarial Improvement Loop
**As a** developer improving my auditor system  
**I want to** receive peer audit reports on my implementation  
**So that** I can identify bugs, architectural flaws, and areas for improvement in both my Week 2 code and my auditor swarm itself

**Acceptance Criteria**:
- [ ] System can process audit reports received from peers
- [ ] Developer can use peer feedback to fix issues in Week 2 implementation
- [ ] Developer can refine auditor swarm to catch previously missed issues
- [ ] Improvement loop creates measurable enhancement in both code quality and auditor capability

### Secondary Scenario: Self-Audit for Quality Assurance
**As a** developer  
**I want to** run the auditor against my own Week 2 repository  
**So that** I can proactively identify issues before peer review

**Acceptance Criteria**:
- [ ] System can audit the developer's own repository
- [ ] Self-audit reports are saved separately from peer audits
- [ ] Self-audit follows same forensic rigor as peer audits

## Functional Requirements

### FR-1: Forensic Evidence Collection (Detective Layer)
**Description**: System must collect objective, verifiable evidence from GitHub repositories and PDF reports without subjective interpretation. Evidence collection must be parallelizable and produce structured, traceable results.

**Acceptance Criteria**:
- [ ] RepoInvestigator agent clones repositories in sandboxed temporary directories
- [ ] RepoInvestigator analyzes git commit history (count, progression pattern, timestamps)
- [ ] RepoInvestigator uses AST parsing (not regex) to verify code structure (StateGraph, reducers, Pydantic models)
- [ ] DocAnalyst agent parses PDF reports and extracts text content
- [ ] DocAnalyst verifies claims in PDF by cross-referencing with actual repository files (hallucination detection)
- [ ] All evidence includes confidence scores (0.0-1.0), file locations, and rationale
- [ ] Evidence collection runs in parallel for efficiency
- [ ] No raw os.system calls or unsanitized shell execution
- [ ] Failed detective agents retry up to 3 times before logging error to state.errors and continuing with partial evidence

### FR-2: Dialectical Judicial Evaluation (Judicial Layer)
**Description**: System must apply three distinct judge personas (Prosecutor, Defense, Tech Lead) to evaluate the same evidence independently, creating dialectical tension that leads to nuanced assessment.

**Acceptance Criteria**:
- [ ] Prosecutor persona applies critical lens: hunts for security flaws, structural violations, laziness
- [ ] Defense persona applies charitable lens: rewards effort, deep thinking, creative solutions, iteration history
- [ ] Tech Lead persona applies pragmatic lens: focuses on maintainability, working state, technical debt
- [ ] Each judge produces structured JudicialOpinion with score (1-5), argument, and cited evidence
- [ ] Judges operate in parallel on the same evidence set
- [ ] Judge personas have distinct, non-overlapping system prompts (minimum 90% difference)
- [ ] All judge outputs are validated Pydantic models (no freeform text)
- [ ] When insufficient evidence exists, judges still produce opinions with score 1 and argument explaining evidence insufficiency

### FR-3: Deterministic Conflict Resolution (Chief Justice Layer)
**Description**: System must synthesize conflicting judicial opinions using hardcoded deterministic rules, not LLM averaging, to produce final verdicts with explicit dissent documentation.

**Acceptance Criteria**:
- [ ] Chief Justice applies hardcoded rules: security flaws cap score at 3, facts override opinions, Tech Lead breaks ties
- [ ] When Prosecutor and Defense differ by more than 2 points, dissent is explicitly documented
- [ ] Final scores per criterion are calculated deterministically (not via LLM prompt)
- [ ] Synthesis explains why one perspective was overruled when conflicts occur
- [ ] All conflict resolution logic is traceable and auditable
- [ ] If synthesis fails (state corruption, missing opinions, logic error), audit fails with error, partial state and traces saved for debugging

### FR-4: Executive-Grade Report Generation
**Description**: System must produce professional Markdown reports that stand up to scrutiny, with clear structure, actionable remediation, and professional formatting.

**Acceptance Criteria**:
- [ ] Report includes executive summary with overall assessment
- [ ] Report includes criterion-by-criterion breakdown with final scores
- [ ] Report includes dissent summaries explaining judicial conflicts
- [ ] Report includes specific remediation plan with file paths and suggested fixes
- [ ] Report formatting is clean, professional, and suitable for executive review
- [ ] All claims in report are backed by cited evidence

### FR-5: Machine-Readable Rubric Integration
**Description**: System must load and apply a machine-readable JSON rubric that defines forensic protocols, judicial logic, and synthesis rules.

**Acceptance Criteria**:
- [ ] System loads rubric from JSON file at runtime
- [ ] Rubric defines target artifacts (github_repo, pdf_report) for each dimension
- [ ] Rubric provides forensic instructions for detective agents
- [ ] Rubric provides judicial logic for each judge persona per criterion
- [ ] Rubric defines synthesis rules for conflict resolution
- [ ] Rubric can be updated without code changes
- [ ] Invalid rubric (malformed JSON, missing fields, schema mismatch) causes immediate failure with clear error message before audit starts

### FR-6: Observability and Tracing
**Description**: System must provide full observability into agent reasoning, evidence collection, and judicial deliberation for debugging and improvement.

**Acceptance Criteria**:
- [ ] All agent interactions are traced via LangSmith (LANGCHAIN_TRACING_V2=true)
- [ ] Traces show evidence collection process, judge reasoning, and conflict resolution
- [ ] Traces are exportable or linkable for review
- [ ] Traces capture the "reasoning loop" showing how judges argue

### FR-7: State Management with Parallel Safety
**Description**: System must use typed state with reducers to safely handle parallel agent execution without data loss or overwrites.

**Acceptance Criteria**:
- [ ] State uses Pydantic models for Evidence and JudicialOpinion
- [ ] State uses TypedDict for AgentState
- [ ] State uses operator.ior reducer for dictionary merges (evidences)
- [ ] State uses operator.add reducer for list appends (opinions, errors)
- [ ] Parallel agents can write simultaneously without overwriting each other's data

### FR-8: LangGraph Orchestration
**Description**: System must use LangGraph StateGraph with proper parallel execution (fan-out/fan-in) and conditional edges.

**Acceptance Criteria**:
- [ ] Graph uses StateGraph from LangGraph
- [ ] Detectives execute in parallel (fan-out)
- [ ] Evidence aggregation synchronizes before judicial layer (fan-in)
- [ ] Judges execute in parallel (fan-out)
- [ ] Chief Justice synthesizes after all judges complete
- [ ] Graph handles error cases with conditional edges

## Success Criteria

[Measurable, technology-agnostic outcomes]

- [ ] System can audit a typical Week 2 repository (50-200 files) and produce complete report in under 10 minutes
- [ ] Audit reports achieve 95%+ accuracy in detecting actual code structure (AST verification vs. manual inspection)
- [ ] System correctly identifies security vulnerabilities (unsanitized shell execution, missing sandboxing) in 100% of test cases
- [ ] Judicial opinions show measurable dialectical tension: Prosecutor and Defense scores differ by average of 1.5+ points when legitimate trade-offs exist
- [ ] Remediation plans are actionable: 80%+ of suggested fixes can be implemented without additional clarification
- [ ] System successfully participates in adversarial loop: peer audits identify real issues that lead to code improvements
- [ ] Self-audit capability enables developers to catch 70%+ of issues before peer review

## Key Entities

### Evidence
- **id**: Unique identifier (UUID) assigned when Evidence is created, used for citation in JudicialOpinion
- **goal**: The forensic objective being investigated (e.g., "Find StateGraph definition")
- **found**: Boolean indicating whether artifact exists (fact, not opinion)
- **content**: Extracted code snippet or text (optional)
- **location**: File path or commit hash for traceability
- **rationale**: Explanation of confidence in this evidence
- **confidence**: Numeric score 0.0-1.0 indicating certainty

### JudicialOpinion
- **judge**: Persona identifier (Prosecutor, Defense, TechLead)
- **criterion_id**: Links to specific rubric dimension
- **score**: Numeric rating 1-5
- **argument**: Reasoning for this score
- **cited_evidence**: List of Evidence UUIDs referenced (must exist in state.evidences)

### AgentState
- **repo_url**: Target repository to audit
- **pdf_path**: PDF report to analyze
- **rubric_dimensions**: Loaded rubric configuration
- **evidences**: Dictionary mapping criterion_id to list of Evidence objects
- **opinions**: List of JudicialOpinion objects from all judges
- **errors**: List of error messages encountered
- **final_report**: Generated Markdown audit report

### Rubric Dimension
- **id**: Unique identifier for evaluation criterion
- **name**: Human-readable criterion name
- **target_artifact**: What to analyze (github_repo, pdf_report)
- **forensic_instruction**: Protocol for detective agents
- **judicial_logic**: Per-persona evaluation guidelines
- **synthesis_rules**: Conflict resolution rules

## Constraints

- System must work with public GitHub repositories (no private repo authentication required initially)
- PDF reports must be parseable (standard PDF format, not scanned images without OCR)
- System must run in standard Python environment (Python 3.10+)
- All git operations must be sandboxed (temporary directories, cleaned up after execution)
- System must handle repositories that fail to clone or parse gracefully (error collection, not crashes)
- State management must prevent data loss during parallel execution (reducers required)
- All LLM outputs must be structured (Pydantic validation, no freeform text from judges)

## Assumptions

- OpenAI API access is available for LLM operations (GPT-4o or similar)
- LangSmith tracing is available but optional (system works without it, just less observable)
- Repositories are reasonably sized (under 1000 files, under 100MB)
- PDF reports are in English and follow standard technical documentation format
- Developers have basic familiarity with git and can interpret audit reports
- Rubric JSON follows the provided schema structure
- Network connectivity is available for git clone operations
- System runs in environment with sufficient disk space for temporary repository clones

## Dependencies

- LangGraph framework for state graph orchestration
- LangChain for LLM integration and prompt management
- Pydantic for typed model validation
- Python AST module for code structure analysis
- PDF parsing library (docling or equivalent)
- Git command-line tools for repository operations
- OpenAI API (or compatible LLM provider) for judge personas
- LangSmith for observability (optional but recommended)

## Out of Scope

- Real-time auditing of live repositories (system audits static snapshots)
- Multi-language code analysis (focus on Python for Week 2 challenge)
- Image-based diagram analysis (VisionInspector is optional)
- Authentication for private repositories (initial version handles public repos only)
- Continuous monitoring or scheduled audits (one-time execution per run)
- Integration with CI/CD pipelines (standalone tool, not CI plugin)
- Custom rubric creation UI (rubric is JSON file, edited manually)
- Historical trend analysis across multiple audit runs
- Collaborative features (no multi-user dashboard or sharing)

## Clarifications

### Session 2026-02-24

- Q: How should Evidence objects be uniquely identified for citation in JudicialOpinion.cited_evidence? → A: Auto-generated UUIDs assigned when Evidence is created
- Q: What should happen when a detective agent fails to collect evidence? → A: Retry failed detective up to 3 times before continuing with partial evidence
- Q: What should happen if the rubric JSON file is invalid? → A: Fail immediately with clear error message, exit before audit starts
- Q: What should happen when a judge cannot find sufficient evidence to form a confident opinion? → A: Still produce opinion with score 1 (lowest) and argument explaining evidence insufficiency
- Q: What should happen if the Chief Justice synthesis node fails to generate a valid report? → A: Fail entire audit, exit with error, save partial state/traces for debugging

## Notes

**Architecture Philosophy**: The "Digital Courtroom" metaphor is intentional - it enforces separation of concerns: detectives collect facts, judges interpret, chief justice synthesizes. This prevents single-agent bias and creates genuine dialectical tension.

**MinMax Optimization Loop**: The adversarial improvement cycle is critical. Peer audits should find real issues, forcing code improvements, which then require auditor improvements to catch deeper issues. This creates a co-evolutionary pressure toward excellence.

**Production-Grade Emphasis**: This is not a toy. It must handle errors gracefully, provide observability, use proper state management, and produce professional outputs. The architecture should be maintainable and extensible.

**Forensic vs. Judicial Separation**: Detectives must never opine - they only report facts. Judges must never investigate - they only interpret evidence. This separation ensures objectivity and prevents hallucination.

**Deterministic Synthesis**: The Chief Justice must use hardcoded rules, not LLM prompts, to ensure consistency and auditability. Security flaws should always cap scores regardless of other factors.
