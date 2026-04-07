import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (parent of src/)
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env", override=True)

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072

# Cohere — used by reranker (phase 3)
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
RERANKER_MODEL = "rerank-multilingual-v3.0"
RERANKER_ENABLED = bool(COHERE_API_KEY)
# Multiplier: how many candidates to fetch from vector search before reranking.
# Higher = better recall, slower & more expensive. 4× is the industry default.
RERANK_CANDIDATE_MULTIPLIER = 4

# Qdrant — supports both local (Docker) and cloud (Qdrant Cloud)
QDRANT_URL = os.getenv("QDRANT_URL", "")          # e.g. https://xxx.aws.cloud.qdrant.io
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")   # Qdrant Cloud API key
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost") # fallback for local Docker
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "knowledge_base"

# Chunking
CHUNK_SIZE = 400  # tokens
CHUNK_OVERLAP = 75  # tokens

# Metadata enums
CATEGORIES = [
    "leadership", "sales", "operations", "mindset",
    "framework", "marketing", "finance", "hiring", "culture"
]

CONTENT_TYPES = [
    "princíp", "príbeh", "framework", "how-to",
    "checklist", "case-study", "analýza"
]

SENSITIVITY_LEVELS = ["public", "internal", "private"]

AUDIENCES = ["founder", "manager", "employee", "general"]

# ── API Key Access Levels ────────────────────────────────────
# Each API key has a hardcoded access level that CANNOT be overridden by the client.
# access_level determines what sensitivity levels the key can access:
#   "public_only" → only sensitivity="public"
#   "internal"    → sensitivity="public" + "internal"
#   "full"        → all content including "private"

MENTOR_BOT_API_KEY = os.getenv("MENTOR_BOT_API_KEY", "")
INTERNAL_TOOLS_API_KEY = os.getenv("INTERNAL_TOOLS_API_KEY", "")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

API_KEY_ACCESS_MAP = {
    MENTOR_BOT_API_KEY: "public_only",
    INTERNAL_TOOLS_API_KEY: "internal",
    ADMIN_API_KEY: "full",
}

ACCESS_LEVEL_FILTERS = {
    "public_only": ["public"],
    "internal": ["public", "internal"],
    "full": ["public", "internal", "private"],
}
