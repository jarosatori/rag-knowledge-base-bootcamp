"""
Approve-public CLI — review and approve chunks pending public release.

Usage:
    python src/approve_public.py

Shows all chunks with pending_public_approval=True, displays their content
and sensitivity warnings, and lets you approve, reject, or skip each one.
"""

import sys
import os

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME
from audit_log import log_sensitivity_change


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def get_pending_chunks(client: QdrantClient) -> list:
    """Get all chunks with pending_public_approval=True."""
    results = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="pending_public_approval",
                    match=MatchValue(value=True),
                ),
            ]
        ),
        limit=1000,
        with_payload=True,
        with_vectors=False,
    )
    return results[0]  # (points, next_offset)


def display_chunk(point, index: int, total: int):
    """Display a chunk for review."""
    payload = point.payload
    print(f"\n{'=' * 60}")
    print(f"  CHUNK {index}/{total}")
    print(f"{'=' * 60}")
    print(f"  ID:       {point.id}")
    print(f"  File:     {payload.get('file_path', 'N/A')}")
    print(f"  Category: {payload.get('category', 'N/A')}")
    print(f"  Type:     {payload.get('content_type', 'N/A')}")
    print(f"  Audience: {payload.get('audience', 'N/A')}")

    # Show sensitivity warnings prominently
    warnings = payload.get("sensitivity_warnings", [])
    if warnings:
        print(f"\n  ⚠️  WARNINGS: {', '.join(warnings)}")
    else:
        print(f"\n  ✅ No sensitivity warnings detected")

    # Show first 300 chars of content
    text = payload.get("text", "")
    preview = text[:300]
    if len(text) > 300:
        preview += "..."
    print(f"\n  Content preview:")
    print(f"  {'─' * 50}")
    for line in preview.split("\n"):
        print(f"  {line}")
    print(f"  {'─' * 50}")


def approve_chunk(client: QdrantClient, point):
    """Move chunk to public sensitivity."""
    client.set_payload(
        collection_name=COLLECTION_NAME,
        payload={
            "sensitivity": "public",
            "pending_public_approval": False,
            "approved_at": __import__("datetime").datetime.now().isoformat(),
        },
        points=[point.id],
    )

    log_sensitivity_change(
        chunk_id=str(point.id),
        changed_by="approve-cli",
        old_sensitivity="internal",
        new_sensitivity="public",
        reason="Manually approved via CLI",
        file_path=point.payload.get("file_path", ""),
    )


def reject_chunk(client: QdrantClient, point):
    """Keep chunk as internal and remove pending flag."""
    client.set_payload(
        collection_name=COLLECTION_NAME,
        payload={
            "sensitivity": "internal",
            "pending_public_approval": False,
            "rejected_at": __import__("datetime").datetime.now().isoformat(),
        },
        points=[point.id],
    )

    log_sensitivity_change(
        chunk_id=str(point.id),
        changed_by="approve-cli",
        old_sensitivity="internal (pending)",
        new_sensitivity="internal (rejected)",
        reason="Manually rejected via CLI",
        file_path=point.payload.get("file_path", ""),
    )


def run_approval():
    """Main approval workflow."""
    print("=" * 60)
    print("  APPROVE PUBLIC — Sensitivity Review")
    print("=" * 60)

    client = get_qdrant_client()
    pending = get_pending_chunks(client)

    if not pending:
        print("\n  No chunks pending public approval. All clean!")
        return

    print(f"\n  Found {len(pending)} chunks pending approval.\n")

    approved = 0
    rejected = 0
    skipped = 0

    for i, point in enumerate(pending, 1):
        display_chunk(point, i, len(pending))

        while True:
            print(f"\n  [a] Approve (→ public)  [r] Reject (→ stay internal)  [s] Skip  [q] Quit")
            choice = input("  Your choice: ").strip().lower()

            if choice == "a":
                approve_chunk(client, point)
                print("  ✅ Approved → public")
                approved += 1
                break
            elif choice == "r":
                reject_chunk(client, point)
                print("  ❌ Rejected → stays internal")
                rejected += 1
                break
            elif choice == "s":
                print("  ⏭ Skipped")
                skipped += 1
                break
            elif choice == "q":
                print("\n  Quitting approval workflow.")
                print(f"\n  Summary: {approved} approved, {rejected} rejected, {skipped} skipped")
                return
            else:
                print("  Invalid choice. Use a/r/s/q.")

    print(f"\n{'=' * 60}")
    print(f"  DONE: {approved} approved, {rejected} rejected, {skipped} skipped")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_approval()
