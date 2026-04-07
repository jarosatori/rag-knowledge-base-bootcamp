"""
Chunking module — splits documents into semantically meaningful chunks.
"""

import tiktoken
from config import CHUNK_SIZE, CHUNK_OVERLAP


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    encoder = tiktoken.get_encoding(model)
    return len(encoder.encode(text))


def split_into_paragraphs(text: str) -> list[str]:
    """Split text by double newlines (paragraph boundaries)."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs


def chunk_document(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split document into chunks of approximately chunk_size tokens,
    respecting paragraph boundaries where possible.
    Overlap ensures context continuity between chunks.
    """
    paragraphs = split_into_paragraphs(text)

    chunks = []
    current_chunk_parts = []
    current_tokens = 0

    for paragraph in paragraphs:
        para_tokens = count_tokens(paragraph)

        # If single paragraph exceeds chunk_size, split it by sentences
        if para_tokens > chunk_size:
            if current_chunk_parts:
                chunks.append("\n\n".join(current_chunk_parts))
                current_chunk_parts = []
                current_tokens = 0

            sentence_chunks = _split_long_paragraph(paragraph, chunk_size, overlap)
            chunks.extend(sentence_chunks)
            continue

        # If adding this paragraph would exceed chunk_size, finalize current chunk
        if current_tokens + para_tokens > chunk_size and current_chunk_parts:
            chunks.append("\n\n".join(current_chunk_parts))

            # Keep last part(s) for overlap
            overlap_parts = []
            overlap_tokens = 0
            for part in reversed(current_chunk_parts):
                part_tokens = count_tokens(part)
                if overlap_tokens + part_tokens <= overlap:
                    overlap_parts.insert(0, part)
                    overlap_tokens += part_tokens
                else:
                    break

            current_chunk_parts = overlap_parts
            current_tokens = overlap_tokens

        current_chunk_parts.append(paragraph)
        current_tokens += para_tokens

    # Don't forget the last chunk
    if current_chunk_parts:
        chunks.append("\n\n".join(current_chunk_parts))

    return chunks


def _split_long_paragraph(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split a long paragraph by sentences when it exceeds chunk_size."""
    # Split by sentence boundaries
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_parts = []
    current_tokens = 0

    for sentence in sentences:
        sent_tokens = count_tokens(sentence)

        if current_tokens + sent_tokens > chunk_size and current_parts:
            chunks.append(" ".join(current_parts))

            # Overlap: keep last sentence(s)
            overlap_parts = []
            overlap_tokens = 0
            for part in reversed(current_parts):
                part_tokens = count_tokens(part)
                if overlap_tokens + part_tokens <= overlap:
                    overlap_parts.insert(0, part)
                    overlap_tokens += part_tokens
                else:
                    break

            current_parts = overlap_parts
            current_tokens = overlap_tokens

        current_parts.append(sentence)
        current_tokens += sent_tokens

    if current_parts:
        chunks.append(" ".join(current_parts))

    return chunks
