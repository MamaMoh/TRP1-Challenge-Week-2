# Automaton Auditor — Demo Script (Five-Meeting Format)

**Purpose:** Structured demo script for presenting the project across five meeting segments.  
**Themes:** End-to-End Pipeline Execution • Layered Architecture Visibility • Concept Translation & Strategic Justification • Professional Delivery & Pacing

---

## 5-Minute Version (Single Slot)

Use this when you have **only 5 minutes** to explain and demo. Stick to the timings; skip the optional line if you’re behind.

| Time | Segment | What to do |
|------|---------|------------|
| **0:00–1:00** | **Intro** | Say what it is, why it matters, input/output. |
| **1:00–2:00** | **Pipeline demo** | Run CLI or show pre-generated report. |
| **2:00–3:30** | **Architecture** | Show the three layers and graph flow. |
| **3:30–4:30** | **Design rationale** | Digital Courtroom, Chief Justice, one trade-off. |
| **4:30–5:00** | **Close** | One-line outcome, repo/report, “Questions?” |

### Script (5 min)

**0:00–1:00 — Intro**  
*"Automaton Auditor is a multi-agent system that evaluates GitHub repos and PDF reports against a rubric—governance at scale. Input: repo URL and PDF. Output: a structured audit report with per-criterion scores, three judge perspectives—Prosecutor, Defense, Tech Lead—and a deterministic Chief Justice that applies security and fact-based rules. Built with LangGraph."*

**1:00–2:00 — Pipeline demo**  
- **Option A (if you can run live):**  
  `python main.py --repo https://github.com/MamaMoh/TRP1-Challenge-Week-2 --pdf <path-to-pdf> --output audit/demo_run`  
  *"Three detectives run in parallel, then three judges, then Chief Justice. Report is written to the audit folder."*
- **Option B (no time for a full run):**  
  Open `audit/report_onself_generated/audit_report.json` (or the Markdown report).  
  *"This is a real run on our own repo: executive summary, scores per criterion, judge opinions, and remediation. The pipeline goes CLI → detectives → judges → Chief Justice → this file."*

**2:00–3:30 — Architecture**  
*"Three layers. Layer 1: three detectives in parallel—RepoInvestigator, DocAnalyst, VisionInspector—they gather evidence into shared state. Layer 2: Prosecutor, Defense, Tech Lead score each rubric dimension; opinions are merged. Layer 3: Chief Justice is pure Python—no LLM—it applies security override, fact supremacy, and variance rules to produce the final score."*  
*(Optional: show the flow once.)*  
`start → [3 detectives] → evidence_aggregator → [3 judges] → chief_justice → END`

**3:30–4:30 — Design rationale**  
*"We call it a Digital Courtroom: detectives collect evidence, judges argue from fixed personas, Chief Justice decides with deterministic rules so results are repeatable and auditable. We ran it on ourselves: 4.0/5; strengths in git forensics, state, graph, and Chief Justice; gaps in safe-tool evidence and diagram analysis—all in the remediation plan."*

**4:30–5:00 — Close**  
*"Repo and full report are in the docs. Happy to take one or two questions."*

### 5-min checklist

- [ ] Decide: live run (Option A) or show existing report (Option B).
- [ ] Have `audit/report_onself_generated/` (or `audit/demo_run/`) and one report file open.
- [ ] If live run: use a real PDF path; run from project root with deps ready.

---

## Meeting 1 — Opening & Professional Framing  
**Duration:** ~3–5 min | **Focus:** Professional delivery, context, and stakes

### Script

- **Opening:**  
  *"We're going to walk through Automaton Auditor: a multi-agent evaluation system built for governance at scale. Instead of producing artifacts, it evaluates GitHub repos and PDF reports against a structured rubric using a 'Digital Courtroom' design."*

- **Stakes:**  
  *"In an AI-native enterprise, autonomous agents can generate code faster than humans can review. The bottleneck shifts from production to evaluation. This system addresses that by automating forensic analysis and nuanced judgment with distinct perspectives—Prosecutor, Defense, Tech Lead—and a deterministic Chief Justice."*

- **Deliverables (one sentence):**  
  *"Inputs: repo URL and PDF. Output: structured audit report—Markdown and JSON—with per-criterion scores, judge opinions, dissent summaries, and a remediation plan."*

- **Pacing:** Keep intro tight. No deep technical dive yet. Offer to go deeper in the next segment.

### Checklist

- [ ] State repo and report location (e.g. `docs/FDE_Week2_Final_Report.md`)
- [ ] Confirm audience knows this is LangGraph-based and rubric-driven

---

## Meeting 2 — End-to-End Pipeline Execution  
**Duration:** ~5–7 min | **Focus:** One full run, CLI to output

### Script

- **Intent:**  
  *"I'll run the pipeline once so you see the full flow: from CLI to final report."*

- **Command (run live or pre-recorded):**
  ```bash
  python main.py --repo https://github.com/MamaMoh/TRP1-Challenge-Week-2 --pdf docs/FDE_Week2_Final_Report.md --output audit/demo_run --verbose
  ```
  *(If PDF path is used for a Markdown report, ensure the project supports it or use an actual PDF path from the repo.)*

- **Narrate as it runs:**
  1. *"Setup: PDF resolved, rubric loaded from `rubric/week2_rubric.json`."*
  2. *"Layer 1: Three detectives run in parallel—RepoInvestigator, DocAnalyst, VisionInspector—gathering evidence into shared state."*
  3. *"Evidence aggregation and conditional routing: if there are errors or no evidence, we still run judges but with a degradation message."*
  4. *"Layer 2: Prosecutor, Defense, and Tech Lead score each rubric dimension in parallel; their opinions are merged."*
  5. *"Layer 3: Chief Justice runs—no LLM—applying security override, fact supremacy, and variance rules to produce the final score and report."*
  6. *"Output: Markdown and JSON written to the chosen audit directory."*

- **Show output:**  
  Open `audit/demo_run/audit_report.json` (or equivalent) and scroll to: executive summary, one criterion’s scores and opinions, and the remediation section.

### Checklist

- [ ] Run from project root; `.env` / dependencies ready
- [ ] Have a real PDF path or document that the CLI accepts (e.g. local PDF or URL)
- [ ] If live run is slow, use `--trace` only if needed and keep narration concise

---

## Meeting 3 — Layered Architecture Visibility  
**Duration:** ~5–7 min | **Focus:** Graph, layers, state, and visibility

### Script

- **Intent:**  
  *"I'll show how the system is structured so the pipeline is visible and auditable."*

- **Three layers (use diagram or `docs/FDE_Week2_Final_Report.md` §3.1, §6):**
  1. **Detective layer (parallel):**  
     *"RepoInvestigator handles clone, AST, git history, safe tools, structured output. DocAnalyst does PDF parsing and cross-reference. VisionInspector looks for architecture diagrams. All write into shared state with a merge reducer."*
  2. **Judicial layer (parallel):**  
     *"Prosecutor, Defense, Tech Lead each score every rubric dimension via `with_structured_output(JudicialOpinion)`. Opinions are appended to state; no LLM in the final step."*
  3. **Chief Justice (deterministic):**  
     *"Pure Python. Groups opinions by dimension, applies security override, fact supremacy, functionality weight, and variance/dissent rules. Produces CriterionResult and AuditReport."*

- **Graph visibility:**  
  - Either draw on whiteboard or show the ASCII flow from the report:
    ```
    start → [ RepoInvestigator | DocAnalyst | VisionInspector ] → evidence_aggregator
          → route_after_aggregator → to_judges OR handle_failure_or_missing
          → [ Prosecutor | Defense | Tech Lead ] → chief_justice → END
    ```
  - *"Fan-out and fan-in are explicit in the StateGraph; conditional routing after the aggregator handles errors and missing evidence."*

- **State:**  
  *"State is typed: AgentState (TypedDict), Evidence and JudicialOpinion (Pydantic). Reducers: evidences merged with `operator.ior`, opinions and errors appended with `operator.add`. That way we can trace what each node added."*

### Checklist

- [ ] Point to `src/graph.py` for node/edge wiring if anyone wants to look
- [ ] Optionally show one reducer in `src/state.py` for “reducer semantics”

---

## Meeting 4 — Concept Translation & Strategic Justification  
**Duration:** ~5–7 min | **Focus:** Why this design; rubric alignment; trade-offs

### Script

- **Digital Courtroom:**  
  *"We frame it as a Digital Courtroom: detectives gather evidence as structured objects; judges interpret via fixed personas; the Chief Justice synthesizes with deterministic rules, not an LLM. That gives repeatability and auditability."*

- **Key design choices and rationale:**
  - **StateGraph over a linear script:**  
    *"We need explicit parallelism, fan-out/fan-in, and conditional edges for the rubric. Trade-off: more moving parts, but the flow is visible and testable."*
  - **Three judges + Chief Justice:**  
    *"Prosecutor minimizes benefit of the doubt; Defense credits intent; Tech Lead is the pragmatic tie-breaker. Chief Justice applies rules—e.g. security cap, fact supremacy—so the final score is traceable."*
  - **Conditional after aggregator:**  
    *"On errors or empty evidence we still run judges and Chief Justice so the report can state 'degraded audit' instead of failing silently."*
  - **Sandboxing:**  
    *"Clone in a temp directory, subprocess with list args (no shell), URL validation, timeout. We don’t execute cloned code."*

- **Rubric alignment:**  
  *"The implementation maps to the challenge rubric: forensic analysis via tools and structured Evidence; nuanced judgment via Prosecutor/Defense/Tech Lead; constructive feedback via per-criterion remediation in the report."*

- **Self-audit result (one line):**  
  *"We ran the system on its own repo and report. Overall 4.0/5. Strengths: git forensics, state, graph, structured output, Chief Justice. Gaps: safe-tool evidence depth, judicial nuance implementation, and architectural diagram coverage—all documented in the remediation plan."*

### Checklist

- [ ] Have §9 (Evaluation Criteria Alignment) and §10 (Remediation) of the report ready if someone asks for trade-offs or next steps

---

## Meeting 5 — Wrap-Up, Q&A & Next Steps  
**Duration:** ~3–5 min | **Focus:** Professional close, pacing, and follow-up

### Script

- **Summary:**  
  *"In five segments we covered: the problem and deliverables, a full pipeline run, the three-layer architecture and graph visibility, and the design rationale and rubric alignment. The repo is [GitHub URL]; the main report is in `docs/FDE_Week2_Final_Report.md`."*

- **Next steps (from remediation plan):**  
  *"Immediate next steps: add a clear architecture diagram (e.g. Mermaid) for VisionInspector, enrich Safe Tool evidence in the report, and implement judge timeout and missing-opinion handling in the Chief Justice."*

- **Q&A:**  
  - If asked about MinMax: *"Prosecutor vs Defense variance triggers dissent summaries; Chief Justice uses security override and Tech Lead tie-breaker so the outcome is explainable."*
  - If asked about running on another repo: *"Same CLI: pass `--repo` and `--pdf`; optional `--compare` to compare with another audit report."*

- **Close:**  
  *"Happy to go deeper on any layer or the rubric in a follow-up. Thanks."*

### Checklist

- [ ] Share link to repo and report path again
- [ ] Note any commitments (e.g. “I’ll send the Mermaid diagram by X”)

---

## Quick Reference: Commands & Paths

| Item | Value |
|------|--------|
| CLI entry | `python main.py` |
| Full run (example) | `python main.py --repo <url> --pdf <path_or_url> [--output audit/demo_run] [--verbose]` |
| List rubrics | `python main.py --list-rubrics` |
| Compare with peer | `python main.py --repo <url> --pdf <path> --compare audit/report_onpeer_generated/audit_report.json` |
| Report (self-audit) | `docs/FDE_Week2_Final_Report.md` |
| Audit output (example) | `audit/report_onself_generated/` or `audit/demo_run/` |
| Graph wiring | `src/graph.py` |
| State & reducers | `src/state.py` |

---

## Theme Mapping

| Theme | Primary meeting(s) | How it’s covered |
|-------|--------------------|------------------|
| **End-to-End Pipeline Execution** | Meeting 2 | Live (or recorded) run; narration from CLI to report; show JSON/MD output. |
| **Layered Architecture Visibility** | Meeting 3 | Three layers; StateGraph; fan-out/fan-in; conditional edges; state types and reducers. |
| **Concept Translation & Strategic Justification** | Meeting 4 | Digital Courtroom; design choices; rubric alignment; self-audit and remediation. |
| **Professional Delivery & Pacing** | Meetings 1 & 5 | Short intro and close; clear segments; checklist and time guidance; Q&A and next steps. |

---

*Script version: 1.0. Adjust timings and examples (e.g. PDF path) to match your environment.*
