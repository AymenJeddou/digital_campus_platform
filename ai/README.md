# FSB Nexus — AI / RAG Module

The intelligence layer of the FSB Nexus digital campus platform. It provides an
**Agentic Retrieval-Augmented Generation (RAG)** pipeline that answers student
questions **only** from verified FSB documents and **cites the source document
and page on every answer** — in French, for the Faculty of Sciences of Bizerte.

Generation runs through a **provider-agnostic LLM client**: **Mistral**
(`mistral-medium-latest`) by default, with **Google Gemini** as a fallback —
switchable with a single environment variable, no code change.

---

## Folder structure

```
ai/
├── llm/
│   └── client.py             # Provider-agnostic get_llm() -> generate(prompt)->str (Mistral | Gemini)
├── agents/
│   ├── base_agent.py         # Shared agent: formats chunks, builds prompt, calls the LLM
│   ├── orientation_agent.py  # Programs, admission, campus life, post-Bac
│   ├── academic_agent.py     # Courses, prerequisites, study plans, calendar
│   ├── administrative_agent.py # Registration, scholarships, deadlines
│   └── learning_agent.py     # Course material explanations, learning plans
├── rag/
│   ├── pipeline.py           # RAGPipeline: main entry point (retrieve -> generate -> cite)
│   ├── generator.py          # RAGGenerator: validates agent_type + routes to the agent
│   ├── citation_formatter.py # Day 4: parse [doc, p.X] -> structured citations
│   ├── retrieval_grader.py   # Day 5: filter weak chunks by score threshold
│   └── groundedness_grader.py# Day 6 (stub): verify the answer is supported
├── prompts/
│   └── system_prompts.py     # The 4 French agent prompts + get_prompt() + AGENT_TYPES
├── tests/                    # pytest suite (no API key needed — LLM is mocked)
├── .env.example              # Provider + key placeholders (copy to .env)
└── requirements.txt          # mistralai, google-generativeai, python-dotenv, pytest
```

Retrieval itself lives outside this module, in Iheb's semantic search layer at
`src/search/retriever.py` (imported as `from src.search.retriever import retrieve`).

---

## Setup

```bash
# from the repository root
cp ai/.env.example ai/.env      # then edit ai/.env and add your real key
pip install -r ai/requirements.txt
```

Keys are read from `ai/.env` via `python-dotenv`. They are **never** hardcoded,
and `.env` is git-ignored — only `.env.example` is tracked.

### Configuration (`ai/.env`)

| Variable | Purpose | Default |
|---|---|---|
| `LLM_PROVIDER` | `mistral` or `gemini` | `gemini` |
| `MISTRAL_API_KEY` | Mistral key ([console](https://console.mistral.ai/api-keys)) | — |
| `MISTRAL_MODEL` | Generation model | `mistral-medium-latest` |
| `GEMINI_API_KEY` | Gemini key (fallback) | — |
| `GEMINI_MODEL` | Generation model | `gemini-2.5-flash` |

To switch providers, change `LLM_PROVIDER` (and make sure that provider's key is
set). Nothing else changes.

---

## How it works — step by step

A question becomes a cited answer through the following stages. The orchestrator
is `RAGPipeline.run()` in `rag/pipeline.py`.

### Step 0 — Build the pipeline for an agent
```python
pipeline = RAGPipeline(agent_type="orientation")
```
`RAGPipeline.__init__` creates a `RAGGenerator`, which **validates** the
`agent_type` against `AGENT_TYPES` (raises `ValueError` if unknown) and
instantiates the matching agent class. The agent's `__init__` builds the LLM
client via `get_llm()` — failing fast with a clear error if the provider's API
key is missing.

### Step 1 — Retrieve relevant chunks
```python
result = pipeline.run(question, student_profile=..., top_k=5, category_filter=["orientation"])
```
If no `chunks` are passed, the pipeline calls Iheb's
`retrieve(query, top_k, category_filter)` (semantic search over the knowledge
base). It returns the **top-K** chunks, each following the FSBridge V2 schema
(`chunk_id, text, title, source, page, category, score`). The agent never sees
the whole knowledge base — only these few chunks.
*The backend can also pass `chunks=` explicitly to bypass retrieval.*

### Step 2 — Format the chunks into context
`base_agent._format_chunks()` renders each chunk as a labelled block:
```
[Guide d'Orientation FSB, p.3]
<chunk text>
---
[Guide Académique FSB, p.12]
<chunk text>
```
The label uses the human-readable **`title`** (falling back to `source`). This
label is exactly what the model is told to cite, so citations come out clean.

### Step 3 — Build the agent prompt
`get_prompt()` injects four things into the selected agent's French system
prompt: the `student_status`, the `academic_year`, the formatted `context`, and
the `question`. The prompt enforces the safety rules: **answer only from the
context**, **cite `[document, p.X]` on every claim**, and **refuse** with a fixed
sentence (`Je ne trouve pas d'information fiable...`) if the context is
insufficient. `student_status` / `academic_year` are injected as system context —
never taken from raw user input.

### Step 4 — Call the LLM
`base_agent.run()` sends the prompt through `get_llm().generate(prompt)`. The
provider-agnostic client routes to Mistral or Gemini per `LLM_PROVIDER` and
returns the answer text. The agent wraps it as
`{"answer", "agent", "chunks_used", "raw_response"}`.

### Step 5 — Structure the citations (Day 4)
`citation_formatter.format_citations(answer, chunks)` parses the inline
`[document, p.X]` markers into a deduplicated list, and the pipeline adds it to
the result:
```json
{ "answer": "...", "agent": "orientation", "chunks_used": 2,
  "citations": [ { "document": "Guide d'Orientation FSB", "page": 3 } ] }
```
- A **refusal** answer yields `citations: []` (never cite "I can't find this").
- A real answer with **no** marker gets the top chunk attached as a fallback.

### Steps 5b / 5c — Graders (upcoming)
- **Day 5 — retrieval grader** (`retrieval_grader.py`): drop weak chunks by
  `score` *before* generation, and return the refusal sentence if none pass.
- **Day 6 — groundedness grader** (`groundedness_grader.py`): after generation,
  verify the answer is actually supported by the chunks; block it otherwise.

```
question
   │
   ▼  Step 1   retrieve(top_k, category_filter)        → chunks
   ▼  Step 5b  retrieval grader (Day 5)                → relevant chunks
   ▼  Step 2   _format_chunks                          → context
   ▼  Step 3   get_prompt(student_profile, context)    → prompt
   ▼  Step 4   get_llm().generate(prompt)              → answer
   ▼  Step 5c  groundedness grader (Day 6)             → validated answer
   ▼  Step 5   format_citations                        → {answer, citations}
answer + sources
```

---

## Usage

```python
from ai.rag.pipeline import RAGPipeline

pipeline = RAGPipeline(agent_type="orientation")
result = pipeline.run(
    question="Quelles licences sont disponibles à la FSB?",
    student_profile={"student_status": "prospective", "academic_year": None},
    top_k=5,
    category_filter=["orientation"],   # optional; opaque, passed straight through
)
print(result["answer"])
print(result["citations"])   # [{"document": "...", "page": 3}, ...]
```

---

## The 4 agents

- **Orientation** — programs, admission requirements, campus life and post-Bac
  guidance; primary agent for prospective / newcomer students.
- **Academic** — courses, prerequisites, study plans and the academic calendar;
  prioritises the student's `academic_year`.
- **Administrative** — registration procedures, scholarships and deadlines;
  newcomer-specific procedures only for prospective students.
- **Learning** — course material explanations and learning plans, scoped to the
  student's current `academic_year`.

The pipeline does **not** derive `category_filter` from `agent_type` — categories
are treated as opaque strings (per Iheb's handoff, the taxonomy will change). The
caller (or backend) supplies `category_filter` explicitly.

---

## Chunk schema (FSBridge V2)

`retrieve()` returns a list of:

```json
{
  "chunk_id": "a9e3a20794b8",
  "text": "...",
  "title": "Guide d'Orientation FSB",
  "source": "guide2025_cleaned.md",
  "page": 3,
  "category": "orientation",
  "score": 0.91
}
```

- `title` — human-readable name (used in citations).
- `source` — original filename (citation fallback).
- `page` — **0-based section index** within the document (not a printed page).
- `score` — cosine similarity in `[0, 1]` (used by the Day 5 grader).

`FAKE_CHUNKS` in `rag/generator.py` mirrors this schema for local testing before
the real retriever is connected.

---

## Build log (day by day)

- **Day 1** — module scaffold; 4 French agent system prompts; `get_prompt()`;
  `RAGGenerator` routing; prompt tests.
- **Day 2** — generation pipeline: `_format_chunks`, real LLM call, `RAGPipeline`,
  `student_profile` support, structured error handling.
- **Day 3** — wired the pipeline to Iheb's `retrieve()` (FSBridge V2 mock for now,
  real pgvector body on his Day 6); added the `title` field; cite by title.
- **Day 4** — citation formatting: inline `[doc, p.X]` → structured `citations`,
  with refusal/no-citation handling.
- **(infra)** — provider-agnostic LLM client; default switched to **Mistral**,
  Gemini retained as fallback.
- **Day 5** — retrieval grader: drop chunks below `RETRIEVAL_SCORE_THRESHOLD`
  (default `0.5`) before generation; refuse if none pass.
- **Day 6** — groundedness grader (upcoming).

---

## Running the tests

From the repository root:

```bash
pytest ai/tests/
```

The suite **mocks the LLM**, so it passes **without** any real API key (Mistral
or Gemini) — it validates prompt formatting, agent routing, retrieval wiring,
provider selection, and citation parsing.
