"""
Reranker module — uses Cohere Rerank API to re-score candidate chunks against
the query. Vector similarity gets you "topically related"; the reranker gets you
"actually answers the question". Typical Recall@5 lift: +15-30%.

Used as a second-stage filter inside retrieve.py: vector search returns N×K
candidates, the reranker scores them, top K are returned.

Set COHERE_API_KEY in .env to enable. If unset, rerank() is a no-op pass-through.
"""

from __future__ import annotations

from config import COHERE_API_KEY, RERANKER_MODEL, RERANKER_ENABLED


_client = None


def _get_client():
    """Lazy-init the Cohere client (so unit tests / no-key envs don't crash on import)."""
    global _client
    if _client is None:
        if not COHERE_API_KEY:
            return None
        import cohere
        _client = cohere.ClientV2(api_key=COHERE_API_KEY)
    return _client


def rerank(query: str, results: list[dict], top_n: int) -> list[dict]:
    """
    Re-score candidate results using Cohere Rerank.

    Args:
        query: The original user query.
        results: List of dicts with at least a "text" key (and "metadata", "score").
                 Order is preserved through reranking.
        top_n: How many top results to return after reranking.

    Returns:
        Top N results, sorted by reranker relevance_score (descending).
        Each result gets two new fields:
            - "vector_score": the original vector similarity score
            - "rerank_score": the reranker's relevance score (0..1)
        The "score" field is overwritten with the rerank score so downstream
        code can keep using "score" without changes.

    No-op behavior: if reranker is disabled (no API key) or the call fails,
    returns the first top_n results unchanged.
    """
    if not RERANKER_ENABLED or not results:
        return results[:top_n]

    client = _get_client()
    if client is None:
        return results[:top_n]

    documents = [r.get("text", "") for r in results]

    try:
        response = client.rerank(
            model=RERANKER_MODEL,
            query=query,
            documents=documents,
            top_n=min(top_n, len(documents)),
        )
    except Exception as e:
        # Fail gracefully — never break retrieval just because reranker had a bad day
        print(f"  ⚠ Reranker failed, falling back to vector order: {e}")
        return results[:top_n]

    reranked: list[dict] = []
    for item in response.results:
        idx = item.index
        original = results[idx]
        new_item = {**original}
        new_item["vector_score"] = original.get("score")
        new_item["rerank_score"] = float(item.relevance_score)
        new_item["score"] = float(item.relevance_score)  # overwrite for downstream consistency
        reranked.append(new_item)

    return reranked
