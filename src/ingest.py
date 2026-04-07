"""
Ingestion pipeline — reads files, chunks them, embeds, and uploads to Qdrant.

Supports incremental ingestion:
- Tracks file hashes in .ingested_files.json
- Only processes new or modified files
- Removes chunks from deleted/renamed files
- Use --full flag to force full re-ingestion

Security rules:
- Default sensitivity for ALL new content = "internal"
- If frontmatter says "public", it gets stored as "internal" with pending_public_approval=True
- Sensitivity scanner runs on every chunk to detect PII/sensitive data
- All sensitivity changes are audit-logged
"""

import os
import sys
import json
import hashlib
import uuid
from pathlib import Path
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)

from config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_HOST,
    QDRANT_PORT,
    COLLECTION_NAME,
    EMBEDDING_DIMENSIONS,
)
from file_reader import read_file, extract_metadata_from_path, extract_yaml_frontmatter
from chunker import chunk_document
from embedder import embed_texts
from sensitivity_scanner import scan_chunk
from audit_log import log_sensitivity_change


SUPPORTED_EXTENSIONS = {".md", ".txt", ".docx", ".pdf"}
TRACKER_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".ingested_files.json")


def get_qdrant_client() -> QdrantClient:
    """Connect to Qdrant Cloud if URL is set, otherwise fallback to local Docker."""
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


PAYLOAD_INDEXES = {
    "sensitivity": PayloadSchemaType.KEYWORD,
    "category": PayloadSchemaType.KEYWORD,
    "audience": PayloadSchemaType.KEYWORD,
    "content_type": PayloadSchemaType.KEYWORD,
    "tags": PayloadSchemaType.KEYWORD,
    "pending_public_approval": PayloadSchemaType.BOOL,
    "file_path": PayloadSchemaType.KEYWORD,  # phase 2: needed for get_full_document
}


def ensure_collection(client: QdrantClient):
    """Create collection if it doesn't exist, and ensure all payload indexes exist."""
    collections = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSIONS,
                distance=Distance.COSINE,
            ),
        )
        print(f"Created collection: {COLLECTION_NAME}")
    else:
        print(f"Collection already exists: {COLLECTION_NAME}")

    # Ensure payload indexes exist (idempotent — safe to re-run)
    for field, schema in PAYLOAD_INDEXES.items():
        try:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=schema,
            )
            print(f"  Created payload index: {field}")
        except Exception:
            pass  # Index already exists


def find_files(base_dir: str) -> list[str]:
    """Recursively find all supported files in the knowledge base directory."""
    files = []
    for root, _, filenames in os.walk(base_dir):
        for filename in filenames:
            if Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS:
                files.append(os.path.join(root, filename))
    return sorted(files)


# ── File tracking for incremental ingestion ──────────────────

def _file_hash(file_path: str) -> str:
    """Compute MD5 hash of a file's content."""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_tracker() -> dict:
    """Load the tracker file. Returns {relative_path: {"hash": ..., "chunk_ids": [...]}}"""
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_tracker(tracker: dict):
    """Save the tracker file."""
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(tracker, f, ensure_ascii=False, indent=2)


def _get_changed_files(all_files: list[str], base_dir: str, tracker: dict) -> tuple[list[str], list[str], list[str]]:
    """
    Compare current files against tracker.
    Returns: (new_files, modified_files, deleted_rel_paths)
    """
    current_rel_paths = {}
    for f in all_files:
        rel = os.path.relpath(f, base_dir)
        current_rel_paths[rel] = f

    new_files = []
    modified_files = []
    deleted_rel_paths = []

    # Find new and modified
    for rel, full_path in current_rel_paths.items():
        current_hash = _file_hash(full_path)
        if rel not in tracker:
            new_files.append(full_path)
        elif tracker[rel]["hash"] != current_hash:
            modified_files.append(full_path)

    # Find deleted
    for rel in tracker:
        if rel not in current_rel_paths:
            deleted_rel_paths.append(rel)

    return new_files, modified_files, deleted_rel_paths


def _remove_chunks_for_file(client: QdrantClient, rel_path: str, tracker: dict):
    """Remove all chunks associated with a file from Qdrant."""
    if rel_path in tracker and tracker[rel_path].get("chunk_ids"):
        chunk_ids = tracker[rel_path]["chunk_ids"]
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=chunk_ids,
        )
        print(f"  Removed {len(chunk_ids)} old chunks for: {rel_path}")


# ── Sensitivity rules ────────────────────────────────────────

def _apply_sensitivity_rules(metadata: dict, chunk_text: str, chunk_id: str) -> dict:
    """
    Apply sensitivity rules:
    1. Default = "internal"
    2. If frontmatter requested "public" → store as "internal" + pending_public_approval
    3. Run sensitivity scan on chunk text
    4. Log any overrides
    """
    requested_sensitivity = metadata.get("sensitivity", "internal")

    if requested_sensitivity == "private":
        metadata["sensitivity"] = "private"
        metadata["pending_public_approval"] = False
    elif requested_sensitivity == "public":
        metadata["sensitivity"] = "internal"
        metadata["pending_public_approval"] = True
        metadata["requested_sensitivity"] = "public"

        log_sensitivity_change(
            chunk_id=chunk_id,
            changed_by="ingestion",
            old_sensitivity="public (requested)",
            new_sensitivity="internal (pending approval)",
            reason="Auto-downgrade: all new content defaults to internal",
            file_path=metadata.get("file_path", ""),
        )
    else:
        metadata["sensitivity"] = "internal"
        metadata["pending_public_approval"] = False

    warnings = scan_chunk(chunk_text)
    if warnings:
        metadata["sensitivity_warnings"] = warnings
        print(f"    ⚠ Sensitivity warnings: {warnings}")

    return metadata


# ── File processing ──────────────────────────────────────────

def ingest_file(file_path: str, base_dir: str) -> list[dict]:
    """
    Process a single file: read, extract metadata, chunk, return chunk dicts.
    """
    print(f"  Reading: {file_path}")

    text = read_file(file_path)
    if not text.strip():
        print(f"  Skipping empty file: {file_path}")
        return []

    path_metadata = extract_metadata_from_path(file_path, base_dir)

    frontmatter, content = extract_yaml_frontmatter(text)
    if frontmatter:
        for key in ["category", "content_type", "sensitivity", "audience", "tags", "source", "date"]:
            if key in frontmatter:
                path_metadata[key] = frontmatter[key]
        text = content

    # ── Phase 1.5 hygiene: validate + normalize before chunking ──
    # 1. Normalize sensitivity to lowercase (PUBLIC → public, INTERNAL → internal)
    if "sensitivity" in path_metadata and isinstance(path_metadata["sensitivity"], str):
        path_metadata["sensitivity"] = path_metadata["sensitivity"].strip().lower()

    # 2. Strict mode: a file MUST have a category, either from path or frontmatter.
    #    If missing, skip the file loudly instead of silently bucketing it as "general".
    category = path_metadata.get("category")
    if not category or not isinstance(category, str) or not category.strip():
        print(f"  ⛔ SKIP (missing category): {file_path}")
        print(f"     → Add 'category: <name>' to frontmatter or move under knowledge-base/<sensitivity>/<category>/")
        return []

    # 3. Default fallbacks for non-critical fields
    path_metadata.setdefault("sensitivity", "internal")
    path_metadata.setdefault("content_type", "general")
    path_metadata.setdefault("audience", "general")
    path_metadata.setdefault("tags", [])

    chunks = chunk_document(text)
    print(f"  Created {len(chunks)} chunks")

    records = []
    for i, chunk_text in enumerate(chunks):
        chunk_id = str(uuid.uuid4())

        metadata = {
            **path_metadata,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "file_path": os.path.relpath(file_path, base_dir),
            "ingested_at": datetime.now().isoformat(),
        }

        metadata = _apply_sensitivity_rules(metadata, chunk_text, chunk_id)

        record = {
            "id": chunk_id,
            "text": chunk_text,
            "metadata": metadata,
        }
        records.append(record)

    return records


def upload_to_qdrant(client: QdrantClient, records: list[dict]):
    """Embed all chunks and upload to Qdrant."""
    if not records:
        return

    texts = [r["text"] for r in records]
    print(f"  Embedding {len(texts)} chunks...")
    embeddings = embed_texts(texts)

    points = []
    for record, embedding in zip(records, embeddings):
        point = PointStruct(
            id=record["id"],
            vector=embedding,
            payload={
                "text": record["text"],
                **record["metadata"],
            },
        )
        points.append(point)

    batch_size = 32
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        if i + batch_size < len(points):
            print(f"    Uploaded {min(i + batch_size, len(points))}/{len(points)} points...")

    print(f"  Uploaded {len(points)} points to Qdrant")


# ── Main pipeline ────────────────────────────────────────────

def run_ingestion(knowledge_base_dir: str, full: bool = False):
    """
    Main ingestion pipeline.

    Args:
        knowledge_base_dir: Path to the knowledge-base directory.
        full: If True, force full re-ingestion (ignore tracker).
    """
    print("=" * 60)
    print("KNOWLEDGE BASE INGESTION PIPELINE")
    if full:
        print("  MODE: Full re-ingestion")
    else:
        print("  MODE: Incremental (only new/changed files)")
    print("=" * 60)

    client = get_qdrant_client()
    ensure_collection(client)

    all_files = find_files(knowledge_base_dir)
    print(f"\nFound {len(all_files)} total files in knowledge-base/")

    tracker = _load_tracker()

    if full:
        # Full mode: process everything, clear tracker
        files_to_process = all_files
        tracker = {}
        print(f"Processing ALL {len(files_to_process)} files\n")
    else:
        # Incremental mode
        new_files, modified_files, deleted_paths = _get_changed_files(
            all_files, knowledge_base_dir, tracker
        )

        print(f"  New files:      {len(new_files)}")
        print(f"  Modified files: {len(modified_files)}")
        print(f"  Deleted files:  {len(deleted_paths)}")

        # Remove chunks for deleted and modified files
        for rel_path in deleted_paths:
            _remove_chunks_for_file(client, rel_path, tracker)
            del tracker[rel_path]

        for file_path in modified_files:
            rel_path = os.path.relpath(file_path, knowledge_base_dir)
            _remove_chunks_for_file(client, rel_path, tracker)

        files_to_process = new_files + modified_files

        if not files_to_process:
            print("\n  Nothing to do — all files are up to date!")
            _save_tracker(tracker)
            print("=" * 60)
            return

        print(f"\nProcessing {len(files_to_process)} files\n")

    # Process files
    all_records = []
    pending_count = 0
    warning_count = 0

    for file_path in files_to_process:
        records = ingest_file(file_path, knowledge_base_dir)
        for r in records:
            if r["metadata"].get("pending_public_approval"):
                pending_count += 1
            if r["metadata"].get("sensitivity_warnings"):
                warning_count += 1
        all_records.extend(records)

        # Update tracker
        rel_path = os.path.relpath(file_path, knowledge_base_dir)
        tracker[rel_path] = {
            "hash": _file_hash(file_path),
            "chunk_ids": [r["id"] for r in records],
            "ingested_at": datetime.now().isoformat(),
        }

    print(f"\nTotal chunks to embed: {len(all_records)}")
    if pending_count:
        print(f"  Pending public approval: {pending_count}")
    if warning_count:
        print(f"  Chunks with sensitivity warnings: {warning_count}")

    # Embed and upload
    upload_to_qdrant(client, all_records)

    # Save tracker
    _save_tracker(tracker)

    print(f"\nIngestion complete! {len(all_records)} new chunks added to Qdrant.")
    if pending_count:
        print(f"\n  Run 'python src/approve_public.py' to review pending public chunks.")
    print("=" * 60)


if __name__ == "__main__":
    full_mode = "--full" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--full"]

    kb_dir = args[0] if args else os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "knowledge-base"
    )
    run_ingestion(kb_dir, full=full_mode)
