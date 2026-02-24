# Tasks: Automaton Auditor - Digital Courtroom Swarm

**Input**: Design documents from `/specs/1-automaton-auditor/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure per plan.md (src/, src/nodes/, src/tools/, src/utils/, tests/, rubric/, audit/)
- [x] T002 Update pyproject.toml with all dependencies (LangGraph, LangChain, Pydantic, Docling, etc.)
- [x] T003 [P] Create .env.example with required environment variables (OPENAI_API_KEY, LANGCHAIN_TRACING_V2, etc.)
- [x] T004 [P] Create README.md with project overview and setup instructions
- [x] T005 [P] Configure pytest in pyproject.toml for testing framework

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create Evidence Pydantic model in src/state.py with id (UUID), goal, found, content, location, rationale, confidence fields
- [x] T007 Create JudicialOpinion Pydantic model in src/state.py with judge, criterion_id, score, argument, cited_evidence fields
- [x] T008 Create AgentState TypedDict in src/state.py with repo_url, pdf_path, rubric_dimensions, evidences (operator.ior), opinions (operator.add), errors (operator.add), final_report
- [x] T009 Create rubric/week2_rubric.json with machine-readable rubric structure (rubric_metadata, dimensions array, synthesis_rules)
- [x] T010 Create src/config.py with rubric loading function and environment variable management
- [x] T011 Create src/utils/context_builder.py with function to load rubric and prepare context for agents

**Checkpoint**: Foundation ready - state models, rubric, and configuration infrastructure complete. User story implementation can now begin.

---

## Phase 3: User Story 1 - Audit a Week 2 Submission (Priority: P1) 🎯 MVP

**Goal**: System accepts repository URL and PDF report, performs forensic analysis through three-layer Digital Courtroom architecture, and produces executive-grade Markdown audit report with scores, evidence citations, and remediation guidance.

**Independent Test**: Run `python main.py --repo <test_repo_url> --pdf <test_pdf_path>` and verify complete audit report is generated in under 10 minutes with all required sections (executive summary, criterion scores, evidence citations, remediation plan).

### Implementation for User Story 1

#### Detective Layer (Forensic Evidence Collection)

- [x] T012 [P] [US1] Implement clone_repo function in src/tools/git_tools.py with sandboxed tempfile.TemporaryDirectory
- [x] T013 [P] [US1] Implement analyze_git_history function in src/tools/git_tools.py to extract commit count, progression pattern, timestamps
- [x] T014 [P] [US1] Implement verify_state_models function in src/tools/ast_parser.py using Python AST to verify Pydantic BaseModel/TypedDict usage
- [x] T015 [P] [US1] Implement analyze_graph_structure function in src/tools/ast_parser.py using AST to verify StateGraph instantiation and parallel execution (add_edge fan-out)
- [x] T016 [P] [US1] Implement parse_pdf function in src/tools/pdf_parser.py using Docling to extract text content
- [x] T017 [US1] Implement repo_investigator_node function in src/nodes/detectives.py that clones repo, runs git/AST analysis, creates Evidence objects with UUIDs, handles retries (up to 3 times)
- [x] T018 [US1] Implement doc_analyst_node function in src/nodes/detectives.py that parses PDF, extracts keywords, cross-references claims with repo files, creates Evidence objects with UUIDs, handles retries
- [x] T019 [US1] Implement vision_inspector_node function in src/nodes/detectives.py (optional - multimodal diagram analysis)
- [x] T020 [US1] Implement evidence_aggregator_node function in src/nodes/detectives.py to synchronize evidence collection before judicial layer

#### Judicial Layer (Dialectical Evaluation)

- [x] T021 [P] [US1] Implement prosecutor_node function in src/nodes/judges.py with critical lens system prompt (hunts security flaws, structural violations), uses .with_structured_output(JudicialOpinion), handles insufficient evidence (score 1)
- [x] T022 [P] [US1] Implement defense_node function in src/nodes/judges.py with charitable lens system prompt (rewards effort, deep thinking), uses .with_structured_output(JudicialOpinion), handles insufficient evidence (score 1)
- [x] T023 [P] [US1] Implement tech_lead_node function in src/nodes/judges.py with pragmatic lens system prompt (maintainability, working state), uses .with_structured_output(JudicialOpinion), handles insufficient evidence (score 1)
- [x] T024 [US1] Ensure all judge personas have distinct system prompts (minimum 90% difference) in src/nodes/judges.py

#### Chief Justice Layer (Synthesis)

- [x] T025 [US1] Implement chief_justice_node function in src/nodes/justice.py with hardcoded deterministic rules (security flaws cap at 3, facts override opinions, Tech Lead breaks ties, dissent documentation when scores differ >2 points)
- [x] T026 [US1] Implement report generation in chief_justice_node to create Markdown report with executive summary, criterion breakdown, dissent summaries, remediation plan with file paths

#### Graph Orchestration

- [x] T027 [US1] Create build_auditor_graph function in src/graph.py using LangGraph StateGraph
- [x] T028 [US1] Wire detective nodes in parallel (fan-out) in src/graph.py: entry → repo_investigator, doc_analyst, vision_inspector
- [x] T029 [US1] Wire evidence aggregation (fan-in) in src/graph.py: detectives → evidence_aggregator
- [x] T030 [US1] Wire judge nodes in parallel (fan-out) in src/graph.py: evidence_aggregator → prosecutor, defense, tech_lead
- [x] T031 [US1] Wire Chief Justice synthesis in src/graph.py: judges → chief_justice → END
- [x] T032 [US1] Add conditional edges for error handling in src/graph.py

#### CLI Interface

- [x] T033 [US1] Implement main.py CLI entry point with argparse for --repo, --pdf, --output, --rubric, --verbose, --trace arguments
- [x] T034 [US1] Implement input validation in main.py (repo URL format, PDF file existence, rubric JSON validation with fail-fast on invalid rubric)
- [x] T035 [US1] Implement audit execution flow in main.py: load rubric, initialize state, run graph, save report to output directory
- [x] T036 [US1] Implement error handling in main.py for synthesis failures (fail entire audit, save partial state/traces for debugging)

#### Observability

- [x] T037 [US1] Configure LangSmith tracing in main.py (LANGCHAIN_TRACING_V2=true, export traces to audit/langsmith_logs/)

**Checkpoint**: At this point, User Story 1 should be fully functional. Run end-to-end test: `python main.py --repo <test_repo> --pdf <test_pdf>` and verify complete audit report generation.

---

## Phase 4: User Story 2 - Participate in Adversarial Improvement Loop (Priority: P2)

**Goal**: Developer can receive peer audit reports, use feedback to fix issues in Week 2 implementation, and refine auditor swarm to catch previously missed issues, creating measurable enhancement in both code quality and auditor capability.

**Independent Test**: Receive peer audit report, identify issues, fix Week 2 code, refine auditor (e.g., add new evidence collection), re-run audit and verify improved detection.

### Implementation for User Story 2

- [x] T038 [US2] Create audit/report_bypeer_received/ directory structure for storing received peer reports
- [x] T039 [US2] Implement report parser utility in src/utils/report_parser.py to extract issues and remediation suggestions from peer audit reports
- [x] T040 [US2] Create documentation in README.md explaining adversarial improvement loop workflow
- [x] T041 [US2] Add --compare flag to main.py to compare current audit with peer audit report and highlight differences

**Checkpoint**: At this point, User Story 2 should enable developers to process peer feedback and improve both their Week 2 code and auditor capabilities.

---

## Phase 5: User Story 3 - Self-Audit for Quality Assurance (Priority: P3)

**Goal**: Developer can run the auditor against their own Week 2 repository to proactively identify issues before peer review, with self-audit reports saved separately and following same forensic rigor as peer audits.

**Independent Test**: Run `python main.py --repo <own_repo> --pdf <own_pdf> --output audit/report_onself_generated/` and verify self-audit report is generated with same structure and rigor as peer audits.

### Implementation for User Story 3

- [x] T042 [US3] Ensure --output flag in main.py supports audit/report_onself_generated/ directory
- [x] T043 [US3] Verify self-audit uses same forensic protocols and judicial evaluation as peer audits (no special handling needed - already implemented in US1)
- [x] T044 [US3] Add documentation in README.md explaining self-audit workflow and benefits

**Checkpoint**: At this point, User Story 3 should enable developers to self-audit their repositories with the same rigor as peer audits.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T045 [P] Add comprehensive error messages throughout codebase with clear context
- [x] T046 [P] Add logging statements for all major operations (evidence collection, judge reasoning, synthesis)
- [x] T047 [P] Optimize AST parsing performance for large codebases (caching, incremental parsing)
- [x] T048 [P] Add timeout handling for git clone operations and LLM API calls
- [x] T049 [P] Implement rate limiting protection for OpenAI API calls
- [x] T050 [P] Add unit tests for state models in tests/unit/test_state.py (Evidence, JudicialOpinion validation)
- [x] T051 [P] Add unit tests for tools in tests/unit/test_tools.py (git_tools, ast_parser, pdf_parser)
- [x] T052 [P] Add unit tests for nodes in tests/unit/test_nodes.py (detectives, judges, justice)
- [x] T053 Add integration tests for graph orchestration in tests/integration/test_graph_orchestration.py
- [x] T054 Add end-to-end tests in tests/integration/test_end_to_end.py using fixtures/sample_repo/ and fixtures/sample_report.pdf
- [x] T055 Update README.md with complete usage examples and troubleshooting guide
- [x] T056 Validate quickstart.md workflow end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1) is MVP and must be complete first
  - User Stories 2 and 3 can proceed after US1 or in parallel if team capacity allows
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. This is the MVP.
- **User Story 2 (P2)**: Can start after User Story 1 - Builds on audit report format and structure
- **User Story 3 (P3)**: Can start after User Story 1 - Uses same core functionality, just different output directory

### Within Each User Story

- Tools before detective nodes (T012-T016 before T017-T020)
- Detective nodes before evidence aggregation (T017-T019 before T020)
- Evidence aggregation before judge nodes (T020 before T021-T024)
- Judge nodes before Chief Justice (T021-T024 before T025-T026)
- Graph orchestration after all nodes (T027-T032 after nodes complete)
- CLI interface after graph (T033-T036 after graph complete)
- Observability can be added in parallel (T037)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005)
- All Foundational tasks marked [P] can run in parallel within Phase 2 (none marked [P] - sequential due to dependencies)
- Detective tools (T012-T016) can be implemented in parallel
- Detective nodes (T017-T019) can be implemented in parallel after tools complete
- Judge nodes (T021-T023) can be implemented in parallel
- Polish tasks marked [P] can run in parallel (T045-T052)

---

## Parallel Example: User Story 1

```bash
# Launch all detective tools in parallel:
Task: "Implement clone_repo function in src/tools/git_tools.py"
Task: "Implement analyze_git_history function in src/tools/git_tools.py"
Task: "Implement verify_state_models function in src/tools/ast_parser.py"
Task: "Implement analyze_graph_structure function in src/tools/ast_parser.py"
Task: "Implement parse_pdf function in src/tools/pdf_parser.py"

# Launch all judge nodes in parallel (after evidence aggregation):
Task: "Implement prosecutor_node function in src/nodes/judges.py"
Task: "Implement defense_node function in src/nodes/judges.py"
Task: "Implement tech_lead_node function in src/nodes/judges.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (MVP - complete audit workflow)
4. **STOP and VALIDATE**: Test User Story 1 independently with real Week 2 repository
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Adversarial loop)
4. Add User Story 3 → Test independently → Deploy/Demo (Self-audit)
5. Add Polish phase → Production-ready system

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: Detective tools (T012-T016) → Detective nodes (T017-T020)
   - Developer B: Judge nodes (T021-T024) → Chief Justice (T025-T026)
   - Developer C: Graph orchestration (T027-T032) → CLI (T033-T036)
3. Stories 2 and 3 can be worked on in parallel after US1 completes

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All detective tools must use sandboxed operations (tempfile.TemporaryDirectory)
- All judge outputs must use .with_structured_output() for Pydantic validation
- Chief Justice must use hardcoded rules, not LLM prompts
- Evidence objects must have UUIDs for citation tracking
