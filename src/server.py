"""
Combined server — REST API + MCP SSE on a single port.

For Railway / cloud deployment:
  python src/server.py
  → REST API at /api/search, /api/stats, / (web UI)
  → MCP SSE at /kb/<token>/sse (for Claude Cowork)

Uses $PORT env var (Railway sets this automatically), default 8000.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import ASGIApp, Receive, Scope, Send

# Import the FastAPI app (REST API + Web UI)
from api import app as fastapi_app

# Import the MCP server instance
from mcp_server import mcp

# Secret token for MCP access — set in .env / Railway Variables
MCP_SECRET_TOKEN = os.getenv("MCP_SECRET_TOKEN", "")


class TrustProxyHostMiddleware:
    """Replace external Host header with localhost so MCP SSE app accepts it."""
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http", "websocket"):
            new_headers = []
            for k, v in scope.get("headers", []):
                if k == b"host":
                    new_headers.append((k, b"localhost:8000"))
                else:
                    new_headers.append((k, v))
            scope = dict(scope)
            scope["headers"] = new_headers
        await self.app(scope, receive, send)


# Get MCP SSE app and wrap with host-fix middleware
mcp_sse_app = TrustProxyHostMiddleware(mcp.sse_app())

# Build routes
# Token-protected MCP: /kb/<token>/sse  (nested mounts)
# No token (local dev): /mcp/sse
routes = []

if MCP_SECRET_TOKEN:
    routes.append(Mount("/kb", routes=[
        Mount(f"/{MCP_SECRET_TOKEN}", app=mcp_sse_app),
    ]))
else:
    routes.append(Mount("/mcp", app=mcp_sse_app))

routes.append(Mount("/", app=fastapi_app))

combined_app = Starlette(routes=routes)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"\n  Knowledge Base — Combined Server")
    print(f"  REST API:  http://0.0.0.0:{port}/")
    if MCP_SECRET_TOKEN:
        print(f"  MCP SSE:   http://0.0.0.0:{port}/kb/{MCP_SECRET_TOKEN}/sse")
    else:
        print(f"  MCP SSE:   http://0.0.0.0:{port}/mcp/sse  (⚠ NO TOKEN — open access)")
    print()
    uvicorn.run(combined_app, host="0.0.0.0", port=port)
