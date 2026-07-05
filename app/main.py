from fastapi import FastAPI, HTTPException, UploadFile

from app.ingest import chunk_text, extract_text_from_pdf

import uuid

from app.vectorstore import add_chunks, search

from app.rag import answer_question




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
        "chunk_count": len(chunks),
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
    