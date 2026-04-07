"""
Phase 1.5 — Taxonomy consolidation tool.

Walks every .md/.txt file in the knowledge-base/, parses the YAML frontmatter,
and rewrites the 'category' field according to a canonical mapping (48 → 13).

Also normalizes 'sensitivity' to lowercase.

Modes:
  --dry-run   (default) Just print what WOULD change. No files are modified.
  --apply              Actually rewrite files. Backups go to tools/backups/<timestamp>/

Usage:
  python tools/consolidate_taxonomy.py
  python tools/consolidate_taxonomy.py --apply
  python tools/consolidate_taxonomy.py --dry-run --verbose
"""

from __future__ import annotations

import argparse
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import yaml

# ─────────────────────────────────────────────────────────────────────────────
# CANONICAL TAXONOMY (13 categories)
# ─────────────────────────────────────────────────────────────────────────────
# Mapping: every legacy category (case-insensitive, normalized) → canonical name.
# Anything not in this map is left UNCHANGED but reported in "unknown" bucket.

TAXONOMY_MAP = {
    # ── leadership ──
    "leadership": "leadership",
    "hr-leadership": "leadership",
    "founder psychology & identity": "leadership",
    "founder-psychology-identity": "leadership",

    # ── business-strategy ──
    "biznis-strategy": "business-strategy",
    "business-strategy": "business-strategy",
    "business-fundamentals": "business-strategy",
    "business-analysis": "business-strategy",
    "business model design": "business-strategy",
    "business-model-design": "business-strategy",
    "strategy": "business-strategy",
    "entrepreneurship": "business-strategy",

    # ── sales ──
    "sales": "sales",

    # ── marketing ──
    "marketing": "marketing",
    "marketing-strategy": "marketing",
    "brand & marketing": "marketing",
    "brand-marketing": "marketing",
    "content-creation": "marketing",
    "brand-story": "marketing",

    # ── operations ──
    "operations": "operations",
    "business-operations": "operations",
    "productivity": "operations",
    "growth-automation": "operations",
    "growth & scaling": "operations",
    "growth-scaling": "operations",

    # ── finance ──
    "finance": "finance",
    "financial-management": "finance",
    "capital-strategy": "finance",
    "capital strategy & financing": "finance",
    "capital-strategy-financing": "finance",
    "investment-strategy": "finance",

    # ── mindset ──
    "mindset": "mindset",
    "personal-growth": "mindset",
    "personal-development": "mindset",
    "mental-models": "mindset",
    "mental-resilience": "mindset",

    # ── hiring ──
    "hiring": "hiring",
    "culture": "hiring",  # culture is closely tied to hiring/people in Jaro's KB

    # ── product ──
    "product": "product",
    "product-development": "product",
    "product-strategy": "product",

    # ── technology ──
    "technology": "technology",
    "data-strategy": "technology",

    # ── case-study ──
    "case-study": "case-study",
    "business-lessons": "case-study",
    "business-opportunity": "case-study",
    "market-analysis": "case-study",

    # ── education ──
    "education": "education",
    "learning": "education",
    "mentoring": "education",
    "founder-education": "education",

    # ── risk ──
    "risk management & decision making": "risk",
    "risk-management-decision-making": "risk",
    "risk-management": "risk",
}

CANONICAL_CATEGORIES = sorted(set(TAXONOMY_MAP.values()))


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = _ROOT.parent.parent.parent / "knowledge-base"
BACKUP_DIR = _ROOT / "tools" / "backups"


def normalize_key(s: str) -> str:
    return (s or "").strip().lower()


def map_category(legacy: str | None) -> tuple[str | None, bool]:
    """
    Returns (canonical_or_None, is_known).
      - If legacy is None/empty → (None, False)
      - If legacy is in map → (canonical, True)
      - Otherwise → (legacy, False)  (unchanged but flagged)
    """
    if not legacy:
        return None, False
    key = normalize_key(legacy)
    if key in TAXONOMY_MAP:
        return TAXONOMY_MAP[key], True
    return legacy, False


def parse_frontmatter(text: str) -> tuple[dict | None, str | None, str | None]:
    """Returns (frontmatter_dict, raw_frontmatter_block, body) or (None, None, None)."""
    if not text.startswith("---"):
        return None, None, None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, None, None
    raw = parts[1]
    body = parts[2]
    try:
        fm = yaml.safe_load(raw)
        if not isinstance(fm, dict):
            return None, None, None
        return fm, raw, body
    except Exception:
        return None, None, None


def rewrite_frontmatter_block(raw_block: str, new_category: str | None, new_sensitivity: str | None) -> str:
    """
    Rewrite the raw frontmatter text in-place, only touching 'category' and 'sensitivity'.
    Preserves field order, comments, and YAML formatting elsewhere.
    """
    lines = raw_block.splitlines()
    out_lines = []
    cat_replaced = False
    sens_replaced = False

    for line in lines:
        stripped = line.lstrip()
        # Replace category line
        if new_category and stripped.startswith("category:") and not cat_replaced:
            indent = line[: len(line) - len(stripped)]
            out_lines.append(f'{indent}category: {new_category}')
            cat_replaced = True
            continue
        # Replace sensitivity line
        if new_sensitivity and stripped.startswith("sensitivity:") and not sens_replaced:
            indent = line[: len(line) - len(stripped)]
            out_lines.append(f'{indent}sensitivity: {new_sensitivity}')
            sens_replaced = True
            continue
        out_lines.append(line)

    return "\n".join(out_lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def process_file(path: Path) -> dict:
    """Returns a dict describing the planned change for this file."""
    result: dict = {
        "path": path,
        "rel": str(path.relative_to(KB_DIR)) if path.is_relative_to(KB_DIR) else str(path),
        "status": "unchanged",
        "old_category": None,
        "new_category": None,
        "old_sensitivity": None,
        "new_sensitivity": None,
        "reason": "",
    }

    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        result["status"] = "error"
        result["reason"] = f"read failed: {e}"
        return result

    fm, raw_block, body = parse_frontmatter(text)
    if fm is None:
        result["status"] = "no-frontmatter"
        result["reason"] = "needs manual frontmatter (or deletion)"
        return result

    old_cat = fm.get("category")
    old_sens = fm.get("sensitivity")
    result["old_category"] = old_cat
    result["old_sensitivity"] = old_sens

    new_cat, known = map_category(old_cat)
    new_sens = old_sens.lower() if isinstance(old_sens, str) else old_sens

    cat_changed = new_cat != old_cat and known
    sens_changed = new_sens != old_sens and isinstance(old_sens, str)

    result["new_category"] = new_cat
    result["new_sensitivity"] = new_sens

    if not old_cat:
        result["status"] = "missing-category"
        result["reason"] = "no category in frontmatter"
        return result

    if not known:
        result["status"] = "unknown-category"
        result["reason"] = f"'{old_cat}' not in taxonomy map"
        return result

    if cat_changed or sens_changed:
        result["status"] = "will-change"
        new_block = rewrite_frontmatter_block(raw_block, new_cat if cat_changed else None,
                                               new_sens if sens_changed else None)
        result["_new_text"] = f"---{new_block}---{body}"
    else:
        result["status"] = "ok"

    return result


def find_files() -> list[Path]:
    if not KB_DIR.exists():
        print(f"❌ KB dir not found: {KB_DIR}")
        sys.exit(1)
    out = []
    for p in KB_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".md", ".txt"}:
            out.append(p)
    return sorted(out)


def print_report(results: list[dict], verbose: bool) -> None:
    by_status = defaultdict(list)
    for r in results:
        by_status[r["status"]].append(r)

    transitions = Counter()
    for r in results:
        if r["status"] == "will-change" and r["old_category"] != r["new_category"]:
            transitions[(r["old_category"], r["new_category"])] += 1

    sens_transitions = Counter()
    for r in results:
        old_s = r["old_sensitivity"]
        new_s = r["new_sensitivity"]
        if isinstance(old_s, str) and old_s != new_s:
            sens_transitions[(old_s, new_s)] += 1

    print("\n" + "=" * 78)
    print("TAXONOMY CONSOLIDATION — DRY RUN REPORT")
    print("=" * 78)
    print(f"Total files scanned:       {len(results)}")
    print(f"  ✅ ok (no change):        {len(by_status['ok'])}")
    print(f"  ✏️  will-change:           {len(by_status['will-change'])}")
    print(f"  ❓ unknown-category:       {len(by_status['unknown-category'])}")
    print(f"  ⚠️  missing-category:      {len(by_status['missing-category'])}")
    print(f"  ⛔ no-frontmatter:        {len(by_status['no-frontmatter'])}")
    print(f"  💥 error:                 {len(by_status['error'])}")

    print("\n── Category transitions (top 30) ────────────────────────────────────")
    if not transitions:
        print("  (none — all categories already canonical)")
    else:
        for (old, new), n in transitions.most_common(30):
            print(f"  {n:>4}  {old:<40} → {new}")

    print("\n── Sensitivity transitions (case fixes) ─────────────────────────────")
    if not sens_transitions:
        print("  (none)")
    else:
        for (old, new), n in sens_transitions.most_common():
            print(f"  {n:>4}  {old} → {new}")

    if by_status["unknown-category"]:
        print("\n── Unknown categories (need manual mapping) ─────────────────────────")
        unk = Counter(r["old_category"] for r in by_status["unknown-category"])
        for cat, n in unk.most_common():
            print(f"  {n:>4}  {cat}")

    if by_status["no-frontmatter"]:
        print("\n── Files with no frontmatter (will be skipped at ingest) ────────────")
        for r in by_status["no-frontmatter"]:
            print(f"     {r['rel']}")

    if by_status["missing-category"]:
        print("\n── Files with frontmatter but missing 'category' ────────────────────")
        for r in by_status["missing-category"]:
            print(f"     {r['rel']}")

    if verbose:
        print("\n── Detailed will-change list ────────────────────────────────────────")
        for r in by_status["will-change"]:
            print(f"  {r['rel']}")
            if r["old_category"] != r["new_category"]:
                print(f"     category:    {r['old_category']!r:<40} → {r['new_category']!r}")
            if r["old_sensitivity"] != r["new_sensitivity"]:
                print(f"     sensitivity: {r['old_sensitivity']!r:<40} → {r['new_sensitivity']!r}")

    print("\n── Canonical taxonomy after consolidation ───────────────────────────")
    final_counts: Counter = Counter()
    for r in results:
        if r["status"] in ("ok", "will-change") and r["new_category"]:
            final_counts[r["new_category"]] += 1
        elif r["status"] == "unknown-category" and r["old_category"]:
            final_counts[r["old_category"]] += 1
    for cat, n in sorted(final_counts.items(), key=lambda x: -x[1]):
        marker = "  " if cat in CANONICAL_CATEGORIES else "❓"
        print(f"  {marker} {n:>4}  {cat}")
    print()


def apply_changes(results: list[dict]) -> None:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = BACKUP_DIR / ts
    backup_root.mkdir(parents=True, exist_ok=True)
    print(f"\nBackups → {backup_root}\n")

    n_applied = 0
    for r in results:
        if r["status"] != "will-change":
            continue
        path: Path = r["path"]
        # Backup
        rel = path.relative_to(KB_DIR)
        backup_path = backup_root / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        # Write
        path.write_text(r["_new_text"], encoding="utf-8")
        n_applied += 1
        print(f"  ✏️  {rel}")

    print(f"\n✅ Applied {n_applied} changes. Backups in {backup_root}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually rewrite files (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Show planned changes without writing (default)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show full file-by-file change list")
    args = parser.parse_args()

    if args.apply and args.dry_run:
        print("❌ Cannot use --apply and --dry-run together")
        sys.exit(1)

    files = find_files()
    print(f"Scanning {len(files)} files in {KB_DIR}...")

    results = [process_file(f) for f in files]
    print_report(results, verbose=args.verbose)

    if args.apply:
        apply_changes(results)
    else:
        print("DRY RUN — no files were modified. Run with --apply to write changes.\n")


if __name__ == "__main__":
    main()
