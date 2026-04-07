"""
Retrieval module — searches the knowledge base with hardcoded access levels.

Security:
- Each API key has a HARDCODED access_level that cannot be overridden by the client.
- The client sends their API key, and the server determines what they can see.
- This prevents any client from requesting data above their access level.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

from config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_HOST,
    QDRANT_PORT,
    COLLECTION_NAME,
    API_KEY_ACCESS_MAP,
    ACCESS_LEVEL_FILTERS,
    RERANKER_ENABLED,
    RERANK_CANDIDATE_MULTIPLIER,
)
from embedder import embed_single
from reranker import rerank
from query_expansion import hyde_expand, multi_query_expand


def get_qdrant_client() -> QdrantClient:
    """Connect to Qdrant Cloud if URL is set, otherwise fallback to local Docker."""
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def resolve_access_level(api_key: str) -> str:
    """
    Look up the hardcoded access level for an API key.
    Returns the access level string, or raises if key is unknown.
    """
    # Filter out empty placeholder keys
    access_level = API_KEY_ACCESS_MAP.get(api_key)
    if not access_level or not api_key or api_key.startswith("sem-vloz"):
        raise PermissionError(f"Unknown or unconfigured API key.")
    return access_level


def _candidate_count(top_k: int, use_reranker: bool) -> int:
    """How many candidates to fetch from vector search before reranking."""
    if use_reranker and RERANKER_ENABLED:
        return max(top_k * RERANK_CANDIDATE_MULTIPLIER, top_k)
    return top_k


def retrieve(
    query: str,
    api_key: str,
    top_k: int = 5,
    category: str | None = None,
    audience: str | None = None,
    content_type: str | None = None,
    tags: list[str] | None = None,
    use_reranker: bool = True,
) -> list[dict]:
    """
    Search the knowledge base with access control.

    Args:
        query: The search question/text.
        api_key: The caller's API key — determines what sensitivity levels they can access.
        top_k: Number of results to return (default 5).
        category: Filter by category (e.g. "leadership", "sales").
        audience: Filter by audience (e.g. "founder", "manager").
        content_type: Filter by content type (e.g. "framework", "how-to").
        tags: Filter by tags (matches any of the provided tags).

    Returns:
        List of dicts with keys: text, metadata, score.
    """
    # Resolve access level from API key — HARDCODED, not client-controlled
    access_level = resolve_access_level(api_key)
    allowed_sensitivities = ACCESS_LEVEL_FILTERS[access_level]

    client = get_qdrant_client()

    # Build query embedding
    query_vector = embed_single(query)

    # Build filters — sensitivity filter is ALWAYS applied based on API key
    must_conditions = [
        FieldCondition(
            key="sensitivity",
            match=MatchAny(any=allowed_sensitivities),
        )
    ]

    # Exclude chunks still pending approval (they shouldn't appear in public results)
    # Only approved public chunks are visible
    if "public" in allowed_sensitivities and access_level != "full":
        must_conditions.append(
            FieldCondition(
                key="pending_public_approval",
                match=MatchValue(value=False),
            )
        )

    if category:
        must_conditions.append(
            FieldCondition(key="category", match=MatchValue(value=category))
        )

    if audience:
        must_conditions.append(
            FieldCondition(key="audience", match=MatchValue(value=audience))
        )

    if content_type:
        must_conditions.append(
            FieldCondition(key="content_type", match=MatchValue(value=content_type))
        )

    if tags:
        for tag in tags:
            must_conditions.append(
                FieldCondition(key="tags", match=MatchValue(value=tag))
            )

    query_filter = Filter(must=must_conditions)

    # Search — fetch extra candidates if reranker will trim them
    fetch_k = _candidate_count(top_k, use_reranker)
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=fetch_k,
        with_payload=True,
    )

    # Format results
    formatted = []
    for point in results.points:
        payload = point.payload
        text = payload.pop("text", "")
        formatted.append({
            "text": text,
            "score": point.score,
            "metadata": payload,
        })

    if use_reranker:
        formatted = rerank(query, formatted, top_n=top_k)
    else:
        formatted = formatted[:top_k]
    return formatted


# ── Convenience functions (for direct use in code, without API key routing) ──

def retrieve_public(query: str, top_k: int = 5, use_reranker: bool = True, **kwargs) -> list[dict]:
    """For Mentor Bot — only approved public content."""
    must_conditions = [
        FieldCondition(key="sensitivity", match=MatchValue(value="public")),
        FieldCondition(key="pending_public_approval", match=MatchValue(value=False)),
    ]
    _add_optional_filters(must_conditions, kwargs)
    return _vector_search_then_rerank(
        query, must_conditions, top_k, use_reranker,
        use_query_expansion=kwargs.get("use_query_expansion", False),
        expansion_mode=kwargs.get("expansion_mode", "hyde"),
    )


def retrieve_internal(query: str, top_k: int = 5, use_reranker: bool = True, **kwargs) -> list[dict]:
    """For internal tools — public + internal content."""
    must_conditions = [
        FieldCondition(key="sensitivity", match=MatchAny(any=["public", "internal"])),
    ]
    _add_optional_filters(must_conditions, kwargs)
    return _vector_search_then_rerank(
        query, must_conditions, top_k, use_reranker,
        use_query_expansion=kwargs.get("use_query_expansion", False),
        expansion_mode=kwargs.get("expansion_mode", "hyde"),
    )


def retrieve_private(query: str, top_k: int = 5, use_reranker: bool = True, **kwargs) -> list[dict]:
    """For personal use — all content including private."""
    must_conditions: list = []
    _add_optional_filters(must_conditions, kwargs)
    return _vector_search_then_rerank(
        query, must_conditions, top_k, use_reranker,
        use_query_expansion=kwargs.get("use_query_expansion", False),
        expansion_mode=kwargs.get("expansion_mode", "hyde"),
    )


def _vector_search_then_rerank(
    query: str,
    must_conditions: list,
    top_k: int,
    use_reranker: bool,
    use_query_expansion: bool = False,
    expansion_mode: str = "hyde",
) -> list[dict]:
    """
    Shared retrieval pipeline:
        (optional query expansion) → vector search → (optional rerank) → top_k.

    expansion_mode:
        "hyde"  — embed a hypothetical answer instead of the query
        "multi" — retrieve for N query variants and union the results
    """
    client = get_qdrant_client()
    fetch_k = _candidate_count(top_k, use_reranker)
    query_filter = Filter(must=must_conditions) if must_conditions else None

    # ── Query expansion (optional) ──
    if use_query_expansion and expansion_mode == "multi":
        queries = multi_query_expand(query)
    elif use_query_expansion and expansion_mode == "hyde":
        queries = [hyde_expand(query)]
    else:
        queries = [query]

    # ── Vector search for each query variant ──
    seen_ids: set = set()
    formatted: list[dict] = []
    for q in queries:
        query_vector = embed_single(q)
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=fetch_k,
            with_payload=True,
        )
        for point in results.points:
            if point.id in seen_ids:
                continue
            seen_ids.add(point.id)
            payload = dict(point.payload or {})
            text = payload.pop("text", "")
            formatted.append({
                "text": text,
                "score": point.score,
                "metadata": payload,
            })

    # ── Rerank (optional) against the ORIGINAL query, not the expansion ──
    if use_reranker:
        formatted = rerank(query, formatted, top_n=top_k)
    else:
        # Sort by vector score and take top_k
        formatted.sort(key=lambda r: r["score"], reverse=True)
        formatted = formatted[:top_k]
    return formatted


def _add_optional_filters(conditions: list, kwargs: dict):
    """Add optional category/audience/content_type/tags filters."""
    if kwargs.get("category"):
        conditions.append(FieldCondition(key="category", match=MatchValue(value=kwargs["category"])))
    if kwargs.get("audience"):
        conditions.append(FieldCondition(key="audience", match=MatchValue(value=kwargs["audience"])))
    if kwargs.get("content_type"):
        conditions.append(FieldCondition(key="content_type", match=MatchValue(value=kwargs["content_type"])))
    if kwargs.get("tags"):
        for tag in kwargs["tags"]:
            conditions.append(FieldCondition(key="tags", match=MatchValue(value=tag)))


# ── Document-level retrieval (phase 2) ───────────────────────

def get_full_document(
    file_path: str,
    api_key: str | None = None,
    access_level: str | None = None,
) -> dict:
    """
    Retrieve every chunk belonging to a single source document and stitch them
    back together in chunk_index order.

    Args:
        file_path: The 'file_path' metadata value (relative path under knowledge-base/).
                   This is the document_id in our schema.
        api_key:   Optional API key — if provided, sensitivity filtering is enforced.
        access_level: Alternative to api_key — explicit access level string
                      ("public_only" | "internal" | "full"). Used internally.

    Returns:
        {
            "file_path": str,
            "total_chunks": int,
            "chunks_returned": int,
            "metadata": dict,        # metadata of chunk_index 0 (representative)
            "text": str,             # full stitched text
            "chunks": [ {chunk_index, text, metadata}, ... ]
        }

    Raises:
        PermissionError if api_key is unknown.
        ValueError if no chunks found for file_path.
    """
    # Resolve access level
    if api_key is not None:
        access_level = resolve_access_level(api_key)
    if access_level is None:
        access_level = "internal"  # default for direct callers
    allowed_sensitivities = ACCESS_LEVEL_FILTERS[access_level]

    client = get_qdrant_client()

    must_conditions = [
        FieldCondition(key="file_path", match=MatchValue(value=file_path)),
        FieldCondition(key="sensitivity", match=MatchAny(any=allowed_sensitivities)),
    ]

    # Public-only callers should not see pending content
    if "public" in allowed_sensitivities and access_level != "full":
        must_conditions.append(
            FieldCondition(key="pending_public_approval", match=MatchValue(value=False))
        )

    query_filter = Filter(must=must_conditions)

    # Scroll all matching chunks (no vector search needed)
    chunks: list[dict] = []
    next_offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=query_filter,
            limit=500,
            offset=next_offset,
            with_payload=True,
            with_vectors=False,
        )
        for p in points:
            payload = dict(p.payload or {})
            text = payload.pop("text", "")
            chunks.append({
                "chunk_index": payload.get("chunk_index", 0),
                "text": text,
                "metadata": payload,
            })
        if next_offset is None:
            break

    if not chunks:
        raise ValueError(f"No chunks found for file_path: {file_path}")

    chunks.sort(key=lambda c: c["chunk_index"])
    full_text = "\n\n".join(c["text"] for c in chunks)
    representative_meta = chunks[0]["metadata"]

    return {
        "file_path": file_path,
        "total_chunks": representative_meta.get("total_chunks", len(chunks)),
        "chunks_returned": len(chunks),
        "metadata": representative_meta,
        "text": full_text,
        "chunks": chunks,
    }


# ── Internal helpers ─────────────────────────────────────────

def _format_results(results) -> list[dict]:
    """Format Qdrant results into clean dicts."""
    formatted = []
    for point in results.points:
        payload = point.payload
        text = payload.pop("text", "")
        formatted.append({
            "text": text,
            "score": point.score,
            "metadata": payload,
        })
    return formatted


if __name__ == "__main__":
    import sys
    query_text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Ako efektívne delegovať úlohy?"

    print(f"Query: {query_text}\n")
    print("=" * 60)
    print("Testing retrieve_internal (public + internal):\n")

    results = retrieve_internal(query_text)

    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} (score: {result['score']:.4f}) ---")
        print(f"Sensitivity: {result['metadata'].get('sensitivity', 'N/A')}")
        print(f"Category: {result['metadata'].get('category', 'N/A')}")
        print(f"Type: {result['metadata'].get('content_type', 'N/A')}")
        print(f"Source: {result['metadata'].get('source', 'N/A')}")
        print(f"Text: {result['text'][:200]}...")
