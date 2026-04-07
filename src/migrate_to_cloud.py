"""
Migrate data from local Qdrant (Docker) to Qdrant Cloud.

Usage:
  1. Set QDRANT_URL and QDRANT_API_KEY in .env
  2. Run: python src/migrate_to_cloud.py

This script:
  - Reads ALL points from local Qdrant (localhost:6333)
  - Creates collection on Qdrant Cloud if it doesn't exist
  - Uploads all points (with vectors + payloads) to cloud
  - No re-embedding needed — vectors are copied as-is
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config import (
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_HOST,
    QDRANT_PORT,
    COLLECTION_NAME,
    EMBEDDING_DIMENSIONS,
)


def migrate():
    if not QDRANT_URL or not QDRANT_API_KEY:
        print("ERROR: Set QDRANT_URL and QDRANT_API_KEY in .env first!")
        print("  Get these from https://cloud.qdrant.io after creating a free cluster.")
        sys.exit(1)

    # Connect to both
    local = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    cloud = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # Check local collection
    local_info = local.get_collection(COLLECTION_NAME)
    total = local_info.points_count
    print(f"Local Qdrant: {total} points in '{COLLECTION_NAME}'")

    if total == 0:
        print("Nothing to migrate!")
        return

    # Create collection on cloud if needed
    cloud_collections = [c.name for c in cloud.get_collections().collections]
    if COLLECTION_NAME not in cloud_collections:
        cloud.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSIONS,
                distance=Distance.COSINE,
            ),
        )
        print(f"Created collection '{COLLECTION_NAME}' on Qdrant Cloud")
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists on cloud")

    # Scroll through all points and upload in batches
    batch_size = 100
    offset = None
    uploaded = 0

    while True:
        results, next_offset = local.scroll(
            collection_name=COLLECTION_NAME,
            limit=batch_size,
            offset=offset,
            with_vectors=True,
            with_payload=True,
        )

        if not results:
            break

        points = [
            PointStruct(
                id=point.id,
                vector=point.vector,
                payload=point.payload,
            )
            for point in results
        ]

        cloud.upsert(collection_name=COLLECTION_NAME, points=points)
        uploaded += len(points)
        print(f"  Uploaded {uploaded}/{total} points...")

        if next_offset is None:
            break
        offset = next_offset

    # Verify
    cloud_info = cloud.get_collection(COLLECTION_NAME)
    print(f"\nMigration complete!")
    print(f"  Local:  {total} points")
    print(f"  Cloud:  {cloud_info.points_count} points")
    print(f"\nYour Qdrant Cloud URL: {QDRANT_URL}")


if __name__ == "__main__":
    migrate()
