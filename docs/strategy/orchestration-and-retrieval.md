# Orchestration And Retrieval Decision

Status: active on `codex/field-kit-winning-track`.

## Orchestration

EduAssist Field Kit currently uses a lightweight custom planner-executor-
composer loop, not LangGraph and not the specialist supervisor architecture from
the larger EduAssist platform.

Runtime flow:

```text
Streamlit UI
  -> DemoEngine
  -> Gemma planner, when enabled
  -> typed tool registry validation
  -> deterministic policy and tool executor
  -> Gemma grounded composer, when enabled
  -> action output and audit trace
```

The choice is deliberate for this hackathon fork:

- The demo needs to be easy for judges to run locally with Gemma 4 and minimal
  infrastructure.
- The tool surface is small enough that a graph framework would add dependency
  and explanation overhead without improving the demo outcome.
- Student-data access must stay deterministic and auditable; the model proposes
  tool calls, but Python validates names, arguments, and persona scope.
- The public repository should communicate the Gemma 4 value clearly: local
  planning, local composition, local document intake, and explicit tool traces.
- The original production-style platform can still compare LangGraph,
  specialist supervisors, and other orchestration paths later; this fork is the
  focused competition artifact.

This does not reject LangGraph. It postpones it until there is a larger graph
with retries, interrupts, memory, long-running tasks, or multiple specialist
agents. For the current product story, the winning architecture is the smallest
auditable loop that proves local Gemma plus deterministic tools.

## Retrieval

Retrieval was improved on this branch.

Previous behavior:

- public document search counted the intersection between query tokens and each
  document's title/body tokens;
- ranking had no explanation beyond the returned evidence.

Current behavior:

- local lexical retrieval is implemented in
  `src/eduassist_gemma_good/retrieval.py`;
- query tokens are expanded through auditable bilingual synonym groups;
- common English and Portuguese stopwords are removed;
- title matches receive higher weight than body matches;
- exact significant phrases add a small bonus;
- returned public document payloads include `rank`, `score`, and
  `matched_terms`;
- no embedding service, vector database, or cloud retriever is required.

This is intentionally not Qdrant/embedding RAG. The synthetic public corpus is
small, and the competition narrative values offline operation, inspectability,
and low setup friction. If the public document corpus grows, the next upgrade
would be a local hybrid retriever:

```text
BM25 / lexical score
  + local embedding rerank, optional
  + same Evidence contract
  + same access policy boundary
```

The protected student path is not retrieval-based. It remains a scoped
deterministic lookup guarded by persona authorization.
