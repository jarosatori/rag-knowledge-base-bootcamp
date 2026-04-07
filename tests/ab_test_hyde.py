"""
A/B test: HyDE query expansion vs. raw query.

For each test question we run two retrievals:
  A) raw query → embed → vector search → rerank → top_k
  B) raw query → Claude Haiku rewrites it as a hypothetical answer
     → embed THAT → vector search → rerank → top_k

Then we measure:
  - Category Hit Rate @ K     (does the retrieved set match expected categories?)
  - Top-1 score (rerank confidence)
  - Result overlap between A and B (Jaccard on chunk text hashes)
  - Latency per call

Uses the same dataset as eval_retrieval.py (tests/eval_dataset.yaml).

Usage:
    python tests/ab_test_hyde.py
    python tests/ab_test_hyde.py --top-k 5
    python tests/ab_test_hyde.py --only L01,M01,J02      # subset
    python tests/ab_test_hyde.py --multi                  # use multi-query instead of HyDE
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from retrieve import retrieve_internal  # noqa: E402

DATASET_PATH = _ROOT / "tests" / "eval_dataset.yaml"


def load_dataset() -> list[dict]:
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["questions"]


def hash_text(text: str) -> str:
    return hashlib.md5((text or "")[:200].encode("utf-8")).hexdigest()[:12]


def run_one(query: str, expected_cats: set, top_k: int, use_expansion: bool, mode: str) -> dict:
    t0 = time.time()
    results = retrieve_internal(
        query,
        top_k=top_k,
        use_query_expansion=use_expansion,
        expansion_mode=mode,
    )
    latency_ms = round((time.time() - t0) * 1000)

    hit = False
    rank = None
    for i, r in enumerate(results, 1):
        cat = r.get("metadata", {}).get("category")
        if cat and cat in expected_cats:
            hit = True
            rank = i
            break

    return {
        "results": results,
        "top_score": results[0]["score"] if results else 0.0,
        "category_hit": hit,
        "category_rank": rank,
        "latency_ms": latency_ms,
        "hashes": [hash_text(r.get("text", "")) for r in results],
        "top_categories": [r.get("metadata", {}).get("category") for r in results],
    }


def jaccard(a: list, b: list) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return round(len(sa & sb) / len(sa | sb), 3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--only", type=str, help="Comma-separated question IDs to run")
    parser.add_argument("--multi", action="store_true",
                        help="Use multi-query expansion instead of HyDE")
    args = parser.parse_args()

    mode = "multi" if args.multi else "hyde"

    questions = load_dataset()
    if args.only:
        wanted = {x.strip() for x in args.only.split(",")}
        questions = [q for q in questions if q["id"] in wanted]

    print(f"\n  A/B test — RAW vs {mode.upper()} expansion ({len(questions)} questions, top_k={args.top_k})\n")
    print("=" * 92)
    print(f"{'ID':<6}{'Query':<42}{'A_score':<10}{'B_score':<10}{'A_rank':<8}{'B_rank':<8}{'Jacc':<7}{'Δms'}")
    print("-" * 92)

    n_a_better = 0
    n_b_better = 0
    n_tie = 0
    n_a_hit = 0
    n_b_hit = 0
    sum_lat_a = 0
    sum_lat_b = 0
    sum_jacc = 0.0
    sum_score_a = 0.0
    sum_score_b = 0.0

    rows = []

    for q in questions:
        expected = set(q.get("expected_categories", []))
        try:
            a = run_one(q["query"], expected, args.top_k, use_expansion=False, mode=mode)
            b = run_one(q["query"], expected, args.top_k, use_expansion=True, mode=mode)
        except Exception as e:
            print(f"  ERROR {q['id']}: {e}")
            continue

        if a["category_hit"]:
            n_a_hit += 1
        if b["category_hit"]:
            n_b_hit += 1

        # Compare ranks: lower rank is better; None = miss
        ra = a["category_rank"] if a["category_rank"] else 999
        rb = b["category_rank"] if b["category_rank"] else 999
        if rb < ra:
            n_b_better += 1
            verdict = "B↑"
        elif ra < rb:
            n_a_better += 1
            verdict = "A↑"
        else:
            n_tie += 1
            verdict = "="

        jc = jaccard(a["hashes"], b["hashes"])
        sum_jacc += jc
        sum_lat_a += a["latency_ms"]
        sum_lat_b += b["latency_ms"]
        sum_score_a += a["top_score"]
        sum_score_b += b["top_score"]

        q_short = q["query"][:38] + "…" if len(q["query"]) > 38 else q["query"]
        a_rank_str = str(a["category_rank"]) if a["category_rank"] else "-"
        b_rank_str = str(b["category_rank"]) if b["category_rank"] else "-"
        delta_ms = b["latency_ms"] - a["latency_ms"]
        print(f"{q['id']:<6}{q_short:<42}{a['top_score']:<10.4f}{b['top_score']:<10.4f}"
              f"{a_rank_str:<8}{b_rank_str:<8}{jc:<7}{delta_ms:+}  {verdict}")

        rows.append((q, a, b, jc, verdict))

    n = len(questions) or 1
    print("-" * 92)
    print(f"\nSUMMARY")
    print(f"  Category Hit Rate    A (raw)   : {n_a_hit / n * 100:.1f}%   ({n_a_hit}/{n})")
    print(f"                        B ({mode}): {n_b_hit / n * 100:.1f}%   ({n_b_hit}/{n})")
    print(f"  Avg top-1 score      A         : {sum_score_a / n:.4f}")
    print(f"                        B         : {sum_score_b / n:.4f}   (Δ {sum_score_b/n - sum_score_a/n:+.4f})")
    print(f"  Better rank          A: {n_a_better}   B: {n_b_better}   tie: {n_tie}")
    print(f"  Avg result overlap (Jaccard): {sum_jacc / n:.3f}")
    print(f"  Avg latency          A: {sum_lat_a / n:.0f} ms   B: {sum_lat_b / n:.0f} ms   (+{(sum_lat_b - sum_lat_a) / n:.0f} ms)")
    print()

    # Show queries where verdict differs the most
    swings = [(r, abs((r[1]["category_rank"] or 999) - (r[2]["category_rank"] or 999))) for r in rows]
    swings = [s for s in swings if s[1] > 0 and s[1] < 900]
    swings.sort(key=lambda x: -x[1])
    if swings:
        print("Biggest rank swings (where the two methods most disagree):")
        for (q, a, b, jc, verdict), diff in swings[:5]:
            print(f"  {q['id']}: A_rank={a['category_rank']} B_rank={b['category_rank']} {verdict}  — \"{q['query']}\"")
            print(f"        A top cats: {a['top_categories']}")
            print(f"        B top cats: {b['top_categories']}")
        print()


if __name__ == "__main__":
    main()
