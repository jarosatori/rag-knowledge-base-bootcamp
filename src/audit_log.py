"""
Audit log — append-only JSON log for sensitivity changes.
Logs who changed what, when, and from what to what.
"""

import json
import os
from datetime import datetime

AUDIT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "audit_log.jsonl"
)


def log_sensitivity_change(
    chunk_id: str,
    changed_by: str,
    old_sensitivity: str,
    new_sensitivity: str,
    reason: str = "",
    file_path: str = "",
):
    """
    Append a sensitivity change record to the audit log.

    Args:
        chunk_id: The Qdrant point ID of the chunk.
        changed_by: Who made the change (API key name, "ingestion", "approve-cli").
        old_sensitivity: Previous sensitivity level.
        new_sensitivity: New sensitivity level.
        reason: Optional reason for the change.
        file_path: Source file path of the chunk.
    """
    record = {
        "timestamp": datetime.now().isoformat(),
        "chunk_id": chunk_id,
        "changed_by": changed_by,
        "old_sensitivity": old_sensitivity,
        "new_sensitivity": new_sensitivity,
        "reason": reason,
        "file_path": file_path,
    }

    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_audit_log(limit: int = 50) -> list[dict]:
    """Read the last N entries from the audit log."""
    if not os.path.exists(AUDIT_LOG_PATH):
        return []

    records = []
    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    return records[-limit:]
