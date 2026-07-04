import pytest

from app.ingest import chunk_text

def test_empty_text_returns_no_chunk():
    assert chunk_text("") == []
    assert chunk_text("  \n ") == []

def test_short_text_is_one_chunk():
    text = "Hash tables give O(1) average lookup."
    chunks = chunk_text(text, chunk_size=800, overlap=150)
    assert chunks == [text]

def test_long_text_produced_overlapping_chunks():
    text = "abcdefghij" * 200 #2000 characters
    chunks = chunk_text(text, chunk_size=800, overlap=150)
    assert len(chunks) == 3
    # the tail of chunk 1 must reappear at the head of chunk 2
    assert chunks[0][-150:] == chunks[1][:150]

def test_invalid_argumennts_raise():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=100, overlap=100)