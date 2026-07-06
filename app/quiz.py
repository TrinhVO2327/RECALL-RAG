"""Quiz generation: turn document chunks into validated Q/A cards."""

import json

import anthropic
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.vectorstore import get_document_chunks

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


class QuizCard(BaseModel):
    """One flashcard. Pydantic rejects any LLM output that doesn't fit this shape."""

    question: str
    answer: str
    explanation: str


_SYSTEM_PROMPT = """You create study flashcards from source material.

Rules:
- Base every card ONLY on the provided excerpts.
- Questions must test understanding, not trivia — prefer "why" and "how" over "what".
- Respond with ONLY a valid JSON array, no markdown fences, no preamble.
- Each element must be exactly: {"question": "...", "answer": "...", "explanation": "..."}
- The explanation should say WHY the answer is correct, in one or two sentences."""    

def generate_quiz(document_id: str, num_cards: int = 5) -> list[QuizCard]:
    """Generate validated quiz cards from a document's chunks."""
    chunks = get_document_chunks(document_id, limit=8)
    if not chunks:
        raise ValueError(f"No chunks found for document {document_id}")

    material = "\n\n---\n\n".join(chunks)

    message = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Create {num_cards} flashcards from this material:\n\n{material}",
            }
        ],
    )

    raw = "".join(block.text for block in message.content if block.type == "text")
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
        return [QuizCard(**card) for card in parsed]
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"LLM returned malformed quiz data: {exc}") from exc