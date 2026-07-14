from fastapi import FastAPI, HTTPException, UploadFile

from app.ingest import chunk_text, extract_text_from_pdf

import uuid

from app.vectorstore import add_chunks, search

from app.rag import answer_question

from app.quiz import generate_quiz, explain_differently 

from datetime import date, timedelta

from app.database import Base, engine, get_session
from app.models import Card, Review
from app.scheduler import ReviewState, review as apply_review



Base.metadata.create_all(engine)  # creates recall.db + tables on startup

app = FastAPI(
    title ="RecallRAG",
    description="AI-powered study assistant with RAG and spaced repetition.",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "RecallRAG is alive"}

@app.post("/upload")
async def upload_document(file: UploadFile):
    """Accept a PDF or .txt file, extract its text, and chunk it."""
    file_bytes = await file.read()
    
    if file.content_type == "application/pdf":
        text = extract_text_from_pdf(file_bytes)
    elif file.content_type in ("text/plain", "text/markdown"):
        text = file_bytes.decode("utf-8", errors="replace")
    else:
        raise HTTPException(
            status_code = 415,
            detail=f"Unsupported file type: {file.content_type}. USe PDF or plain text.",
        )
    
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted (is this a scanned/ image-only PDF?).",
        )
    
    chunks = chunk_text(text)
    document_id = str(uuid.uuid4())
    stored = add_chunks(document_id, file.filename or "unknown", chunks)

    return {
        "document_id": document_id,
        "filename": file.filename,
        "characters": len(text),
        "chunk_stored": stored,
        "preview":  chunks[0][:300] if chunks else "",
    }

@app.get("/search")
def search_chunks(q: str, top_k: int = 4):
    """Find the chunks most relevant in meaning to the query."""
    if not q.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty.")
    return {"query": q,"results": search(q, top_k)}

@app.get("/ask")
def ask_question(q: str, top_k: int = 4):
    """Answer a question grounded in the uploaded documents, with citations."""
    if not q.strip():
        raise HTTPException(status_code=422, detail="Question must not be empty")
    return answer_question(q, top_k)

@app.post("/generate-quiz")
def create_quiz(document_id: str, num_cards: int = 5):
    """Generate quiz cards from an uploaded document."""
    try:
        cards = generate_quiz(document_id, num_cards)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    
    with get_session() as session:
        db_cards = [
            Card(document_id=document_id, question=c.question,
                 answer=c.answer, explanation=c.explanation)
            for c in cards
        ]
        session.add_all(db_cards)
        session.commit()
        saved = [{"id": c.id, "question": c.question} for c in db_cards]

    return {"document_id": document_id, "cards_saved": len(saved), "cards": saved}

@app.get("/due")
def due_cards():
    """Cards whose review date has arrived."""
    with get_session() as session:
        cards = session.query(Card).filter(Card.due_date <= date.today()).all()
        return {
            "due_count": len(cards),
            "cards": [
                {"id": c.id, "question": c.question, "answer": c.answer,
                 "explanation": c.explanation}
                for c in cards
            ],
        }
    

@app.post("/review/{card_id}")
def review_card(card_id: int, grade: int):
    """Submit a 0-5 self-grade; SM-2 reschedules the card."""
    if not 0 <= grade <= 5:
        raise HTTPException(status_code=422, detail="grade must be 0-5")

    with get_session() as session:
        card = session.get(Card, card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="card not found")

        state = ReviewState(card.repetitions, card.interval_days, card.ease_factor)
        new_state = apply_review(state, grade)

        card.repetitions = new_state.repetitions
        card.interval_days = new_state.interval_days
        card.ease_factor = new_state.ease_factor
        card.due_date = date.today() + timedelta(days=new_state.interval_days)
        session.add(Review(card_id=card.id, grade=grade))
        session.commit()

        return {
            "card_id": card.id,
            "next_review_in_days": new_state.interval_days,
            "due_date": card.due_date.isoformat(),
            "ease_factor": round(new_state.ease_factor, 2),
        }
    

@app.post("/explain/{card_id}")
def explain_card(card_id: int):
    """Alternative explanation for a card the user failed to recall."""
    with get_session() as session:
        card = session.get(Card, card_id)
        if card is None:
            raise HTTPException(status_code=404, detail="card not found")
        alt = explain_differently(card.question, card.answer, card.explanation)
        return {"card_id": card.id, "alternative_explanation": alt}
    
    
    