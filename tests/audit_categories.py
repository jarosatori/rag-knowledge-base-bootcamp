"""
Data hygiene audit — phase 1.5.

Compares the knowledge-base source files against what's actually stored in Qdrant.

Reports:
  1. Source files: count, unique categories from frontmatter, files missing frontmatter,
     files missing 'category' field, files where path-based fallback would produce garbage.
  2. Qdrant DB: total points, unique categories with counts, "garbage" categories
     (filenames-as-category, etc.), points per category.
  3. Diff: source-only files, db-only document_ids, mismatched categories.
  4. Recommended canonical taxonomy.

Usage:
    python tests/audit_categories.py
    python tests/audit_categories.py --json     # also dump structured report
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

# Make src/ importable
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import COLLECTION_NAME  # noqa: E402
from retrieve import get_qdrant_client  # noqa: E402

# Source KB lives in main repo, not in the worktree
KB_DIRS = [
    _ROOT.parent.parent.parent / "knowledge-base",  # main repo knowledge-base
]

SUPPORTED_EXTS = {".md", ".txt"}


def find_source_files() -> list[Path]:
    files: list[Path] = []
    for base in KB_DIRS:
        if not base.exists():
            print(f"  ⚠️  KB dir not found: {base}")
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
                files.append(p)
    return sorted(files)


def parse_frontmatter(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1])
        return fm if isinstance(fm, dict) else None
    except Exception:
        return None


def audit_source(files: list[Path]) -> dict:
    total = len(files)
    no_frontmatter = []
    no_category = []
    categories = Counter()
    sensitivities = Counter()
    by_category_files = defaultdict(list)

    for f in files:
        fm = parse_frontmatter(f)
        if fm is None:
            no_frontmatter.append(str(f.name))
            continue
        cat = fm.get("category")
        sens = fm.get("sensitivity")
        if not cat:
            no_category.append(str(f.name))
        else:
            categories[cat] += 1
            by_category_files[cat].append(str(f.name))
        if sens:
            sensitivities[sens] += 1

    return {
        "total_files": total,
        "files_no_frontmatter": no_frontmatter,
        "files_no_category": no_category,
        "categories": dict(categories.most_common()),
        "sensitivities": dict(sensitivities.most_common()),
        "by_category_files": dict(by_category_files),
    }


def is_garbage_category(cat: str) -> bool:
    """Heuristic: garbage categories are filenames or have file extensions."""
    if not cat:
        return True
    if cat.endswith(".md") or cat.endswith(".txt"):
        return True
    if len(cat) > 40:  # legit categories are short slugs
        return True
    return False


def audit_qdrant() -> dict:
    client = get_qdrant_client()
    try:
        info = client.get_collection(COLLECTION_NAME)
        total_points = info.points_count
    except Exception as e:
        return {"error": f"Cannot reach Qdrant: {e}"}

    categories = Counter()
    sensitivities = Counter()
    sources = Counter()
    file_paths = Counter()

    # Scroll through all points
    next_offset = None
    scanned = 0
    while True:
        points, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=500,
            offset=next_offset,
            with_payload=True,
            with_vectors=False,
        )
        for p in points:
            payload = p.payload or {}
            cat = payload.get("category") or "(missing)"
            sens = payload.get("sensitivity") or "(missing)"
            src = payload.get("source") or "(missing)"
            fp = payload.get("file_path") or "(missing)"
            categories[cat] += 1
            sensitivities[sens] += 1
            sources[src] += 1
            file_paths[fp] += 1
            scanned += 1
        if next_offset is None:
            break

    garbage_cats = {c: n for c, n in categories.items() if is_garbage_category(c)}
    clean_cats = {c: n for c, n in categories.items() if not is_garbage_category(c)}

    return {
        "total_points": total_points,
        "scanned": scanned,
        "unique_categories": len(categories),
        "categories_clean": dict(sorted(clean_cats.items(), key=lambda x: -x[1])),
        "categories_garbage": dict(sorted(garbage_cats.items(), key=lambda x: -x[1])),
        "sensitivities": dict(sensitivities.most_common()),
        "unique_file_paths": len(file_paths),
    }


def diff_source_vs_db(source: dict, db: dict) -> dict:
    src_cats = set(source.get("categories", {}).keys())
    db_cats = set(db.get("categories_clean", {}).keys())
    return {
        "in_source_not_in_db": sorted(src_cats - db_cats),
        "in_db_not_in_source": sorted(db_cats - src_cats),
        "common": sorted(src_cats & db_cats),
    }


def print_report(source: dict, db: dict, diff: dict) -> None:
    print("\n" + "=" * 78)
    print("DATA HYGIENE AUDIT — Phase 1.5")
    print("=" * 78)

    print("\n── SOURCE FILES ──────────────────────────────────────────────────────")
    print(f"Total source files (.md/.txt):  {source['total_files']}")
    print(f"Files without frontmatter:       {len(source['files_no_frontmatter'])}")
    print(f"Files with frontmatter but no category: {len(source['files_no_category'])}")
    print(f"\nUnique categories in source ({len(source['categories'])}):")
    for cat, n in source["categories"].items():
        print(f"  {n:>4}  {cat}")
    print(f"\nSensitivities in source:")
    for s, n in source["sensitivities"].items():
        print(f"  {n:>4}  {s}")

    if source["files_no_frontmatter"]:
        print(f"\n⚠️  Files missing frontmatter (showing first 15):")
        for f in source["files_no_frontmatter"][:15]:
            print(f"     {f}")
        if len(source["files_no_frontmatter"]) > 15:
            print(f"     ... and {len(source['files_no_frontmatter']) - 15} more")

    if source["files_no_category"]:
        print(f"\n⚠️  Files with frontmatter but missing 'category' (first 15):")
        for f in source["files_no_category"][:15]:
            print(f"     {f}")
        if len(source["files_no_category"]) > 15:
            print(f"     ... and {len(source['files_no_category']) - 15} more")

    print("\n── QDRANT DB ─────────────────────────────────────────────────────────")
    if "error" in db:
        print(f"  ❌ {db['error']}")
        return
    print(f"Total points in collection:      {db['total_points']}")
    print(f"Scanned:                         {db['scanned']}")
    print(f"Unique categories:               {db['unique_categories']}")
    print(f"Unique file_paths:               {db['unique_file_paths']}")

    print(f"\nClean categories in DB ({len(db['categories_clean'])}):")
    for cat, n in db["categories_clean"].items():
        print(f"  {n:>5}  {cat}")

    if db["categories_garbage"]:
        print(f"\n🚨 GARBAGE categories in DB ({len(db['categories_garbage'])}):")
        for cat, n in list(db["categories_garbage"].items())[:30]:
            cat_short = cat[:60] + "…" if len(cat) > 60 else cat
            print(f"  {n:>5}  {cat_short}")
        if len(db["categories_garbage"]) > 30:
            print(f"  ... and {len(db['categories_garbage']) - 30} more")

    print(f"\nSensitivities in DB:")
    for s, n in db["sensitivities"].items():
        print(f"  {n:>5}  {s}")

    print("\n── DIFF: source vs DB categories ─────────────────────────────────────")
    print(f"Common categories ({len(diff['common'])}): {', '.join(diff['common']) or '(none)'}")
    print(f"\nIn source but not in DB ({len(diff['in_source_not_in_db'])}):")
    for c in diff["in_source_not_in_db"]:
        print(f"  - {c}")
    print(f"\nIn DB but not in source ({len(diff['in_db_not_in_source'])}):")
    for c in diff["in_db_not_in_source"]:
        print(f"  - {c}")

    print("\n" + "=" * 78)
    print("RECOMMENDATIONS")
    print("=" * 78)
    n_garbage = sum(db.get("categories_garbage", {}).values())
    pct_garbage = (n_garbage / max(db.get("scanned", 1), 1)) * 100
    print(f"  • {n_garbage} chunks ({pct_garbage:.1f}%) have garbage category — fix needed.")
    print(f"  • Source has {len(source['categories'])} unique categories.")
    print(f"  • DB has {len(db.get('categories_clean', {}))} clean + {len(db.get('categories_garbage', {}))} garbage.")
    print(f"  • Recommended action: fix file_reader.extract_metadata_from_path bug,")
    print(f"    align canonical taxonomy from source frontmatter, full re-ingest.")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Dump JSON report to tests/results/audit.json")
    args = parser.parse_args()

    print("Scanning source files...")
    files = find_source_files()
    source = audit_source(files)

    print(f"Scanning Qdrant collection '{COLLECTION_NAME}'...")
    db = audit_qdrant()

    diff = diff_source_vs_db(source, db) if "error" not in db else {"common": [], "in_source_not_in_db": [], "in_db_not_in_source": []}

    print_report(source, db, diff)

    if args.json:
        out_dir = _ROOT / "tests" / "results"
        out_dir.mkdir(exist_ok=True)
        # Trim huge fields before dumping
        source_dump = {**source}
        source_dump.pop("by_category_files", None)
        path = out_dir / "audit.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"source": source_dump, "db": db, "diff": diff}, f, indent=2, ensure_ascii=False)
        print(f"JSON report → {path}\n")


if __name__ == "__main__":
    main()
