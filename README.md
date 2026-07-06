# RecallRAG 🧠

An AI-powered study assistant backend. Upload your study material (PDFs), ask
questions answered **from your own documents** with citations, auto-generate
quiz cards, and review them on an adaptive **SM-2 spaced-repetition** schedule.

Built with FastAPI, sentence-transformers, ChromaDB, SQLAlchemy, and the
Anthropic API.

## How it works
┌─────────────┐
PDF upload ──────►│   Ingest    │  extract text (pdfplumber)
│             │  split into overlapping chunks
└──────┬──────┘
▼
┌─────────────┐
│  Embeddings │  sentence-transformers (MiniLM)
│   + Chroma  │  vectors persisted to disk
└──────┬──────┘
┌────────────┴────────────┐
▼                         ▼
┌─────────────┐          ┌──────────────┐
│  /ask (RAG) │          │ /generate-   │
│  retrieve → │          │ quiz  (LLM → │
│  grounded,  │          │ Pydantic-    │
│  cited      │          │ validated    │
│  answer     │          │ cards)       │
└─────────────┘          └──────┬───────┘
▼
┌──────────────┐
│ SM-2 review  │
│ scheduler +  │
│ SQLite       │
└──────────────┘

## Features

- **Document ingestion** — PDF/text upload, chunked with overlap for retrieval
- **Semantic search** — meaning-based, not keyword-based (`/search`)
- **RAG Q&A** — answers grounded ONLY in uploaded material, with numbered
  citations; refuses questions the sources can't answer (`/ask`)
- **Quiz generation** — LLM-generated "why/how" flashcards, validated against
  a Pydantic contract so malformed output fails loudly (`/generate-quiz`)
- **Spaced repetition** — SM-2 algorithm: intervals adapt per-card to your
  recall grades; review history persisted in SQLite (`/due`, `/review/{id}`)

## Quickstart

```bash
git clone https://github.com/TrinhVO2327/RECALL-RAG.git
cd RECALL-RAG
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive API.

## Running tests

```bash
pytest -v
```

Covers the chunking edge cases and every behavioral guarantee of the SM-2
scheduler (interval progression, failure resets, ease floor).

## Design decisions

- **Chunk overlap (800/150 chars)** so ideas spanning a boundary aren't
  orphaned from their context.
- **Grounding prompt** forces the LLM to answer only from retrieved excerpts
  and admit when sources don't cover the question — hallucination control.
- **Pydantic as an LLM output contract**: the model is *asked* for JSON, but
  the response is *verified*; garbage triggers a clean 422, never silent
  corruption.
- **Pure-function scheduler**: SM-2 lives in a dependency-free module
  returning new state — trivially unit-testable, reusable outside the web app.
- **Layering**: `scheduler.py` computes, `models.py` persists, `main.py`
  orchestrates. No module knows about HTTP except the API layer.

## Roadmap

- Random-sample chunks across the whole document for quiz coverage
- User accounts + PostgreSQL (swap the SQLAlchemy engine URL)
- Evaluation harness for retrieval quality
- React frontend
