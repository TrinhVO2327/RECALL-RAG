from fastapi import FastAPI

app = FastAPI(
    title ="RecallRAG",
    description="AI-powered study assistant with RAG and spaced repetition.",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "RecallRAG is alive"}

