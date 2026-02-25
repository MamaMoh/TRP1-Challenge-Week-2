# Automaton Auditor — Architecture Diagram

StateGraph flow: parallel fan-out for Detectives and Judges, with Evidence Aggregator as synchronization (fan-in) before the judicial layer.

```mermaid
flowchart TB
    START([start]) --> RI[RepoInvestigator]
    START --> DA[DocAnalyst]
    START --> VI[VisionInspector]
    RI --> EA[Evidence Aggregator]
    DA --> EA
    VI --> EA
    EA --> P[Prosecutor]
    EA --> D[Defense]
    EA --> TL[Tech Lead]
    P --> CJ[Chief Justice]
    D --> CJ
    TL --> CJ
    CJ --> END([END])
```

- **Fan-out**: `start` → three Detectives in parallel; `Evidence Aggregator` → three Judges in parallel.
- **Fan-in**: All Detectives → Evidence Aggregator; all Judges → Chief Justice.
- Conditional edges (not shown): after Evidence Aggregator, route to `to_judges` or `handle_failure_or_missing` based on errors / evidence presence.
