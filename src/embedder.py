"""
Embedding module — generates vector embeddings via OpenAI API.
"""

from openai import OpenAI
from config import OPENAI_API_KEY, EMBEDDING_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts using OpenAI embedding model.
    Batches by 100 texts at a time to stay under the 300k token limit.
    """
    all_embeddings = []
    batch_size = 100  # Safe batch size to stay under token limits

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"    Embedding batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1} ({len(batch)} chunks)...")
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


def embed_single(text: str) -> list[float]:
    """Embed a single text string."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding
