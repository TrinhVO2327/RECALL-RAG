"""RAG: retrieve relevant chunks, then generate a grounded, cited answer."""

import anthropic

from app.config import settings
from app.vectorstore import search

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_SYSTEM_PROMPT = """You are a study assistant. Answer the student's question using ONLY the provided source excerpts.

Rules:
- Base your answer strictly on the excerpts. If they don't contain the answer, say so plainly — do not use outside knowledge.
- Cite which sources you used by their number, like [1] or [2], inline where relevant.
- Be concise and clear: this is for studying."""

def answer_question(question: str, top_k: int=4) -> dict:
    """Retrieve the most relevant chunks and generate a cited answer."""
    hits = search(question, top_k=top_k)

    if not hits:
        return {"answer": "No documents have been uploaded yet.", "sources": []}
    
    context = "\n\n".join(
        f"[{i+1}] (from {h['filename']}, chunk {h['chunk_index']}): {h['chunk']}"
        for i, h in enumerate(hits)
    )

    message = _client.messages.create(
        model="claude-opus-4-7",
        max_tokens=600,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Source excerpts:\n\n{context}\n\nQuestion: {question}",
            }
        ],
    )

    answer_text = "".join(block.text for block in message.content if block.type == "text")

    sources = [
            {"number": i + 1, "filename": h["filename"], "chunk_index": h["chunk_index"]}
            for i, h in enumerate(hits)
        ]

    return {"answer": answer_text, "sources": sources}  