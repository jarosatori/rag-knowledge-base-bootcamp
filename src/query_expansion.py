"""
Query expansion — phase 5.

Two strategies, both opt-in:

1. HyDE (Hypothetical Document Embeddings):
   Ask Claude Haiku to imagine the ideal answer to the query, then embed that
   imagined answer instead of the raw query. Typically lifts recall when user
   queries are short/vague and target chunks are longer/more specific.

2. Multi-query:
   Ask Claude Haiku to rewrite the query into N semantically diverse variants.
   Retrieve for each, union + dedupe, let the reranker sort it out.

Both cost 1 extra LLM call (Haiku ≈ $0.001 per expansion). Off by default.
Enable via retrieve(use_query_expansion=True, expansion_mode="hyde"|"multi").
"""

from __future__ import annotations

import os

_anthropic_client = None
_ANTHROPIC_AVAILABLE = False

try:
    import anthropic  # type: ignore
    _ANTHROPIC_AVAILABLE = True
except Exception:
    pass


def _get_client():
    global _anthropic_client
    if _anthropic_client is None and _ANTHROPIC_AVAILABLE:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return None
        _anthropic_client = anthropic.Anthropic(api_key=key)
    return _anthropic_client


HYDE_PROMPT = """Si expert na biznis a podnikanie. Predstav si ideálnu, detailnú odpoveď na otázku nižšie — tak ako by ju napísal skúsený mentor.

Otázka: {query}

Napíš 3-5 viet ako hypotetickú odpoveď. Žiadny úvod, žiadny záver, len samotný obsah odpovede v slovenčine.
Odpoveď:"""

MULTI_QUERY_PROMPT = """Prepíš túto otázku do 3 sémanticky odlišných variantov, ktoré by pomohli nájsť rôzne uhly pohľadu v znalostnej báze. Každý variant na samostatný riadok. Žiadne čísla, žiadne odrážky, len 3 riadky.

Otázka: {query}

Varianty:"""


def hyde_expand(query: str) -> str:
    """Return a hypothetical answer to `query` to use as embedding input.
    Falls back to the original query if anthropic isn't available or fails."""
    client = _get_client()
    if client is None:
        return query
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": HYDE_PROMPT.format(query=query)}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text")).strip()
        return text or query
    except Exception as e:
        print(f"  ⚠ HyDE expansion failed, using raw query: {e}")
        return query


def multi_query_expand(query: str) -> list[str]:
    """Return [original + 3 variants]. Falls back to [original] on failure."""
    client = _get_client()
    if client is None:
        return [query]
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            messages=[{"role": "user", "content": MULTI_QUERY_PROMPT.format(query=query)}],
        )
        text = "".join(b.text for b in msg.content if hasattr(b, "text")).strip()
        variants = [line.strip("-•* ").strip() for line in text.splitlines() if line.strip()]
        variants = [v for v in variants if v and v != query][:3]
        return [query] + variants
    except Exception as e:
        print(f"  ⚠ Multi-query expansion failed, using raw query: {e}")
        return [query]
