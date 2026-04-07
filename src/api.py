"""
FastAPI REST server for the Knowledge Base.

Endpoints:
  GET  /                     → Web UI for testing queries
  GET  /api/search?q=...     → Search the knowledge base
  GET  /api/stats            → Collection statistics

Run:
  python src/api.py
  → opens at http://localhost:8000
"""

import os
import sys
from fastapi import FastAPI, Query, Header, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from retrieve import retrieve_public, retrieve_internal, retrieve_private, get_full_document
from ingest import get_qdrant_client, COLLECTION_NAME
from config import API_KEY_ACCESS_MAP, ACCESS_LEVEL_FILTERS, CATEGORIES

app = FastAPI(title="Knowledge Base API", version="1.0")


def _resolve_api_key(authorization: str | None) -> str:
    """
    Resolve API key from Authorization header.
    Returns access level string: "public_only", "internal", or "full".
    Raises 401 if key is missing/invalid.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header. Use: Authorization: Bearer <api-key>")

    # Support "Bearer <key>" or just "<key>"
    key = authorization.replace("Bearer ", "").strip()

    access_level = API_KEY_ACCESS_MAP.get(key)
    if not access_level or not key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return access_level


@app.get("/", response_class=HTMLResponse)
def web_ui():
    """Simple web UI for testing queries."""
    return """
    <!DOCTYPE html>
    <html lang="sk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Knowledge Base</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #0a0a0a; color: #e0e0e0;
                min-height: 100vh; padding: 40px 20px;
            }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { font-size: 28px; margin-bottom: 8px; color: #fff; }
            .subtitle { color: #888; margin-bottom: 32px; font-size: 14px; }
            .search-box {
                display: flex; gap: 12px; margin-bottom: 32px;
            }
            input[type="text"] {
                flex: 1; padding: 14px 18px; border-radius: 12px;
                border: 1px solid #333; background: #1a1a1a;
                color: #fff; font-size: 16px; outline: none;
            }
            input[type="text"]:focus { border-color: #555; }
            input[type="text"]::placeholder { color: #666; }
            button {
                padding: 14px 28px; border-radius: 12px; border: none;
                background: #2563eb; color: white; font-size: 16px;
                cursor: pointer; font-weight: 600;
            }
            button:hover { background: #1d4ed8; }
            button:disabled { background: #333; cursor: wait; }
            .filters {
                display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap;
            }
            select {
                padding: 8px 12px; border-radius: 8px; border: 1px solid #333;
                background: #1a1a1a; color: #ccc; font-size: 13px;
            }
            .result {
                background: #141414; border: 1px solid #222;
                border-radius: 12px; padding: 20px; margin-bottom: 16px;
            }
            .result-header {
                display: flex; justify-content: space-between;
                margin-bottom: 12px; font-size: 13px; color: #888;
            }
            .score {
                background: #1e3a5f; color: #60a5fa; padding: 2px 10px;
                border-radius: 6px; font-weight: 600;
            }
            .tags { display: flex; gap: 6px; flex-wrap: wrap; }
            .tag {
                background: #1a2e1a; color: #6ee7b7; padding: 2px 8px;
                border-radius: 4px; font-size: 12px;
            }
            .result-text {
                line-height: 1.6; color: #ccc; font-size: 14px;
                white-space: pre-wrap;
            }
            .stats { color: #666; font-size: 13px; margin-bottom: 16px; }
            .empty { color: #666; text-align: center; padding: 40px; }
            .loading { color: #888; text-align: center; padding: 40px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Knowledge Base</h1>
            <p class="subtitle">Vektorova znalostna baza &bull; <span id="chunk-count">...</span> chunkov</p>

            <div class="search-box" style="margin-bottom: 12px;">
                <input type="password" id="apikey" placeholder="API Key..." style="flex:0.4;">
                <input type="text" id="query" placeholder="Poloz otazku..." autofocus
                       onkeydown="if(event.key==='Enter')search()">
                <button id="btn" onclick="search()">Hladat</button>
            </div>

            <div class="filters">
                <select id="topk">
                    <option value="3">Top 3</option>
                    <option value="5" selected>Top 5</option>
                    <option value="10">Top 10</option>
                </select>
            </div>

            <div id="results"></div>
        </div>

        <script>
            // Load stats on page load (requires API key)
            function getHeaders() {
                const key = document.getElementById('apikey').value.trim();
                return key ? { 'Authorization': 'Bearer ' + key } : {};
            }

            // Try loading stats after API key is entered
            document.getElementById('apikey').addEventListener('change', () => {
                fetch('/api/stats', { headers: getHeaders() }).then(r=>r.json()).then(d=>{
                    document.getElementById('chunk-count').textContent = d.total_chunks || '?';
                }).catch(() => {});
            });

            async function search() {
                const q = document.getElementById('query').value.trim();
                if (!q) return;

                const apikey = document.getElementById('apikey').value.trim();
                if (!apikey) { alert('Zadaj API Key'); return; }

                const topk = document.getElementById('topk').value;
                const btn = document.getElementById('btn');
                const results = document.getElementById('results');

                btn.disabled = true;
                btn.textContent = '...';
                results.innerHTML = '<div class="loading">Hladam...</div>';

                try {
                    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&top_k=${topk}`, { headers: getHeaders() });
                    const data = await res.json();

                    if (data.results.length === 0) {
                        results.innerHTML = '<div class="empty">Ziadne vysledky</div>';
                        return;
                    }

                    results.innerHTML = `<div class="stats">${data.results.length} vysledkov za ${data.search_time_ms}ms</div>` +
                        data.results.map((r, i) => `
                            <div class="result">
                                <div class="result-header">
                                    <div class="tags">
                                        <span class="tag">${r.category || '?'}</span>
                                        <span class="tag">${r.content_type || '?'}</span>
                                        <span class="tag">${r.sensitivity}</span>
                                    </div>
                                    <span class="score">${(r.score * 100).toFixed(1)}%</span>
                                </div>
                                <div class="result-text">${escapeHtml(r.text)}</div>
                            </div>
                        `).join('');
                } catch (err) {
                    results.innerHTML = `<div class="empty">Chyba: ${err.message}</div>`;
                } finally {
                    btn.disabled = false;
                    btn.textContent = 'Hladat';
                }
            }

            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
        </script>
    </body>
    </html>
    """


@app.get("/api/search")
def search(
    q: str = Query(..., min_length=1, max_length=2000, description="Search query"),
    top_k: int = Query(5, ge=1, le=50, description="Number of results (1-50)"),
    category: str | None = Query(None, description="Filter by category"),
    authorization: str | None = Header(None),
):
    """Search the knowledge base. Access level is determined by API key."""
    import time
    start = time.time()

    access_level = _resolve_api_key(authorization)

    # Validate category against whitelist
    if category and category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")

    # Map access level to retrieve function
    retrieve_fn = {
        "public_only": retrieve_public,
        "internal": retrieve_internal,
        "full": retrieve_private,
    }.get(access_level, retrieve_public)

    kwargs = {}
    if category:
        kwargs["category"] = category

    results = retrieve_fn(q, top_k=top_k, **kwargs)
    elapsed = round((time.time() - start) * 1000)

    return {
        "query": q,
        "access_level": access_level,
        "search_time_ms": elapsed,
        "results": [
            {
                "text": r["text"],
                "score": round(r["score"], 4),
                "category": r["metadata"].get("category"),
                "content_type": r["metadata"].get("content_type"),
                "sensitivity": r["metadata"].get("sensitivity"),
                "source": r["metadata"].get("source"),
                "tags": r["metadata"].get("tags", []),
            }
            for r in results
        ],
    }



@app.get("/api/document")
def document(
    file_path: str = Query(..., description="The 'file_path' metadata of the document"),
    authorization: str | None = Header(None),
):
    """
    Retrieve the FULL text of a single document, stitched from all its chunks.
    Access level is determined by API key.
    """
    access_level = _resolve_api_key(authorization)
    try:
        doc = get_full_document(file_path, access_level=access_level)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    return {
        "file_path": doc["file_path"],
        "total_chunks": doc["total_chunks"],
        "chunks_returned": doc["chunks_returned"],
        "category": doc["metadata"].get("category"),
        "content_type": doc["metadata"].get("content_type"),
        "sensitivity": doc["metadata"].get("sensitivity"),
        "source": doc["metadata"].get("source"),
        "tags": doc["metadata"].get("tags", []),
        "text": doc["text"],
    }


@app.get("/api/stats")
def stats(authorization: str | None = Header(None)):
    """Get collection statistics, including category and sensitivity breakdown."""
    _resolve_api_key(authorization)
    try:
        client = get_qdrant_client()
        info = client.get_collection(COLLECTION_NAME)

        # Scan all points to compute category/sensitivity histograms
        from collections import Counter
        categories: Counter = Counter()
        sensitivities: Counter = Counter()
        content_types: Counter = Counter()
        file_paths: set = set()

        next_offset = None
        while True:
            points, next_offset = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=1000,
                offset=next_offset,
                with_payload=True,
                with_vectors=False,
            )
            for p in points:
                payload = p.payload or {}
                categories[payload.get("category", "?")] += 1
                sensitivities[payload.get("sensitivity", "?")] += 1
                content_types[payload.get("content_type", "?")] += 1
                fp = payload.get("file_path")
                if fp:
                    file_paths.add(fp)
            if next_offset is None:
                break

        return {
            "collection": COLLECTION_NAME,
            "total_chunks": info.points_count,
            "total_documents": len(file_paths),
            "status": info.status.value if hasattr(info.status, 'value') else str(info.status),
            "categories": dict(categories.most_common()),
            "sensitivities": dict(sensitivities.most_common()),
            "content_types": dict(content_types.most_common()),
            "embedding_model": "text-embedding-3-large",
            "reranker": "cohere rerank-multilingual-v3.0",
        }
    except Exception as e:
        print(f"Stats error: {e}")
        return {"error": "Failed to fetch stats", "total_chunks": "?", "status": "error"}


if __name__ == "__main__":
    print("\n  Knowledge Base API")
    print("  http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
