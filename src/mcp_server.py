"""
MCP Server for Knowledge Base.

Exposes the knowledge base as tools that Claude can use:
  - search_knowledge_base: Search for relevant content
  - get_kb_stats: Get collection statistics

Run locally (stdio, for Claude Code):
  python src/mcp_server.py

Run as remote server (SSE, for Claude Cowork):
  python src/mcp_server.py --remote
  → runs on http://localhost:8100/sse
"""

import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from mcp.server.fastmcp import FastMCP

from retrieve import retrieve_public, retrieve_internal, retrieve_private, get_full_document as _get_full_document
from ingest import get_qdrant_client, COLLECTION_NAME
from config import CATEGORIES

mcp = FastMCP(
    "Knowledge Base",
    instructions="""Toto je vektorová znalostná báza obsahujúca know-how o biznise, leadershippe,
    financiách, stratégii, mindset a ďalších témach. Použi nástroj search_knowledge_base
    keď potrebuješ nájsť relevantné informácie k otázke používateľa.
    Vždy odpovedaj na základe nájdených výsledkov, nie z vlastných znalostí.""",
)


@mcp.tool()
def search_knowledge_base(
    query: str,
    access_level: str = "internal",
    top_k: int = 5,
    category: str | None = None,
) -> str:
    """
    Search the knowledge base for relevant content.

    Args:
        query: The search question in Slovak or English.
        access_level: Access level - "public" (mentor bot), "internal" (team), "private" (admin). Default: "internal".
        top_k: Number of results to return (1-10). Default: 5.
        category: Optional category filter (e.g. "leadership", "sales", "operations", "mindset", "finance", "marketing", "hiring", "culture").
    """
    # Validate access_level — private requires API key auth, not available via MCP
    if access_level not in ("public", "internal"):
        access_level = "internal"

    # Validate top_k bounds
    top_k = max(1, min(top_k, 10))

    # Validate category against whitelist
    if category and category not in CATEGORIES:
        return f"Neplatná kategória. Povolené: {', '.join(CATEGORIES)}"

    retrieve_fn = {
        "public": retrieve_public,
        "internal": retrieve_internal,
    }.get(access_level, retrieve_internal)

    kwargs = {}
    if category:
        kwargs["category"] = category

    results = retrieve_fn(query, top_k=top_k, **kwargs)

    if not results:
        return "Žiadne relevantné výsledky pre túto otázku."

    output = []
    for i, r in enumerate(results, 1):
        meta = r["metadata"]
        output.append(
            f"--- Výsledok {i} (relevancia: {r['score']:.1%}) ---\n"
            f"Kategória: {meta.get('category', '?')} | Typ: {meta.get('content_type', '?')} | "
            f"Zdroj: {meta.get('source', '?')}\n"
            f"Tagy: {', '.join(meta.get('tags', []))}\n\n"
            f"{r['text']}\n"
        )

    return "\n".join(output)


@mcp.tool()
def get_full_document(file_path: str, access_level: str = "internal") -> str:
    """
    Retrieve the FULL text of a single source document, stitched from all its chunks
    in original order. Use this when the user asks for a complete article, transcript,
    case study, or framework — not a snippet.

    Args:
        file_path: The 'file_path' metadata of the document (relative path under
                   knowledge-base/), as returned by search_knowledge_base in result metadata.
        access_level: "public" or "internal". Default: "internal".
    """
    if access_level not in ("public", "internal"):
        access_level = "internal"
    level_map = {"public": "public_only", "internal": "internal"}
    try:
        doc = _get_full_document(file_path, access_level=level_map[access_level])
    except ValueError as e:
        return f"Dokument nenájdený: {e}"
    except PermissionError as e:
        return f"Prístup zamietnutý: {e}"

    meta = doc["metadata"]
    header = (
        f"=== {file_path} ===\n"
        f"Kategória: {meta.get('category', '?')} | Typ: {meta.get('content_type', '?')} | "
        f"Zdroj: {meta.get('source', '?')}\n"
        f"Chunkov: {doc['chunks_returned']}/{doc['total_chunks']} | "
        f"Tagy: {', '.join(meta.get('tags', []))}\n"
        f"{'=' * 60}\n\n"
    )
    return header + doc["text"]


@mcp.tool()
def get_kb_stats() -> str:
    """Get knowledge base statistics — total chunks, status."""
    try:
        client = get_qdrant_client()
        info = client.get_collection(COLLECTION_NAME)
        return json.dumps({
            "collection": COLLECTION_NAME,
            "total_chunks": info.points_count,
            "status": info.status.value if hasattr(info.status, 'value') else str(info.status),
        }, indent=2)
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    if "--remote" in sys.argv:
        # Remote mode: SSE transport for Claude Cowork
        import uvicorn
        from starlette.middleware import Middleware
        from starlette.middleware.cors import CORSMiddleware

        app = mcp.sse_app()

        # Middleware to fix Host header for ngrok tunneling
        from starlette.types import ASGIApp, Receive, Scope, Send

        class TrustProxyHostMiddleware:
            """Replace external Host header with localhost so SSE app accepts it."""
            def __init__(self, app: ASGIApp):
                self.app = app

            async def __call__(self, scope: Scope, receive: Receive, send: Send):
                if scope["type"] in ("http", "websocket"):
                    headers = dict(scope.get("headers", []))
                    # Replace host header with localhost
                    new_headers = []
                    for k, v in scope.get("headers", []):
                        if k == b"host":
                            new_headers.append((k, b"localhost:8100"))
                        else:
                            new_headers.append((k, v))
                    scope = dict(scope)
                    scope["headers"] = new_headers
                await self.app(scope, receive, send)

        # Wrap with CORS and host-fix middleware
        from starlette.applications import Starlette
        from starlette.routing import Mount

        wrapped = TrustProxyHostMiddleware(app)

        print("\n  MCP Server (SSE remote)")
        print("  http://0.0.0.0:8100/sse\n")
        uvicorn.run(wrapped, host="0.0.0.0", port=8100)
    else:
        # Local mode: stdio transport for Claude Code
        mcp.run()
