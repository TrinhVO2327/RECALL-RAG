"""Vector store: embed chunks and search them by meaning."""

import chromadb
from sentence_transformers import SentenceTransformer

#Loaded once at import time - the model is ~80MB and downloads on first use
_model = SentenceTransformer("all-MiniLM-L6-v2")

# Chroma persists vectors to disk in this folder (already in .gitignore).
_client = chromadb.PersistentClient(path="chroma_data")
_collection = _client.get_or_create_collection(name = "study_chunks")

def add_chunks(document_id: str, filename: str, chunks: list[str]) -> int :
    """Embed chunks and store them with metadata, return how many were added."""
    if not chunks:
        return 0
    
    embeddings = _model.encode(chunks).tolist()
    ids = [f"{document_id}-{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "filename": filename, "chunk_index": i}
        for i in range(len(chunks))
    ]

    _collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=chunks)
    return len(chunks)

def search(query: str, top_k: int=4) -> list[dict]:
    """Return the top_k chunks most similar in meaning to the query."""
    query_embedding = _model.encode([query]).tolist()
    results = _collection.query(query_embeddings=query_embedding, n_results=top_k)

    hits: list[dict] = []
    for i in range(len(results["ids"][0])):
        hits.append(
            {
                "chunk": results["documents"][0][i],
                "filename": results["metadatas"][0][i]["filename"],
                "chunk_index": results["metadatas"][0][i]["chunk_index"],
                "distance": results["distances"][0][i],
            }
        )
    return hits