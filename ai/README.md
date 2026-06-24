# FSB Nexus — AI / RAG Module

The intelligence layer of the FSB Nexus digital campus platform. It provides an
Agentic Retrieval-Augmented Generation (RAG) pipeline that answers student
questions **only** from verified FSB documents and **cites the source document
and page on every answer** — in French, for the Faculty of Sciences of Bizerte.

Generation runs on Google **Gemini** (`gemini-2.0-flash`); embeddings (added in a
later step) use `text-embedding-004`.

## Folder structure

```
ai/
├── agents/
│   ├── base_agent.py          # Shared Gemini client + run() flow
│   ├── orientation_agent.py   # Programs, admission, campus life, post-Bac
│   ├── academic_agent.py      # Courses, prerequisites, study plans, calendar
│   ├── administrative_agent.py# Registration, scholarships, deadlines
│   └── learning_agent.py      # Course material explanations, learning plans
├── rag/
│   ├── generator.py           # RAGGenerator: validates + routes to an agent
│   ├── retrieval_grader.py    # Filters irrelevant chunks (Day 5)
│   ├── groundedness_grader.py # Verifies answer is grounded (Day 6)
│   └── citation_formatter.py  # Structures inline citations (Day 4)
├── prompts/
│   └── system_prompts.py      # The 4 agent system prompts + get_prompt()
├── tests/
│   └── test_prompts.py        # Prompt-formatting + routing tests (no API key)
├── .env.example               # Placeholder env vars (copy to .env)
├── requirements.txt           # google-generativeai, python-dotenv, pytest
└── README.md
```

## Setup

```bash
# from the ai/ folder
cp .env.example .env          # then edit .env and add your real Gemini key
pip install -r requirements.txt
```

`GEMINI_API_KEY` is read from the environment (via `python-dotenv`). The key is
**never** hardcoded, and `.env` is git-ignored — only `.env.example` is tracked.

## Pipeline

The RAG pipeline is the main entry point for generation:

```python
from ai.rag.pipeline import RAGPipeline

pipeline = RAGPipeline(agent_type="orientation")
result = pipeline.run(
    question="Quelles licences sont disponibles à la FSB?",
    chunks=[...],  # list of chunk dicts from the retriever
    student_profile={"student_status": "prospective", "academic_year": None}
)
print(result["answer"])
print(result["citations"])  # available after Day 4
```

Current pipeline steps:
- [x] Day 2: Generation (Gemini 2.0 Flash)
- [ ] Day 4: Citation formatting
- [ ] Day 5: Retrieval grader
- [ ] Day 6: Groundedness grader

## Running the tests

From the repository root:

```bash
pytest ai/tests/
```

The tests validate prompt formatting and agent routing only, so they pass
**without** a real API key.

## The 4 agents

- **Orientation Agent** — programs, admission requirements, campus life and
  post-Bac guidance; primary agent for prospective / newcomer students.
- **Academic Agent** — courses, prerequisites, study plans and the academic
  calendar; filters results by the student's `academic_year` by default.
- **Administrative Agent** — registration procedures, scholarships and
  administrative deadlines; newcomer-specific procedures only for prospective
  students.
- **Learning Agent** — course material explanations and learning plans, scoped
  to the student's current `academic_year`.

`student_status` and `academic_year` are injected as system context — never
taken from raw user input.

## Expected chunk format

The retriever (Knowledge Base role, Issue #3) hands off chunks in this shape:

```json
[
  {
    "chunk_id": "abc123",
    "text": "...",
    "source": "FSB Academic Handbook",
    "page": 12,
    "category": "course",
    "score": 0.91
  }
]
```

`RAGGenerator.generate(question, chunks, student_status, student_academic_year)`
consumes this list and returns `{"answer": "...", "raw_response": "..."}`.
A `FAKE_CHUNKS` constant in `rag/generator.py` mirrors this format for local
testing before the retriever is connected (Day 2).
