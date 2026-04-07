"""
Evaluation harness for the RAG retrieval pipeline.

Runs a fixed dataset of test queries against retrieve_internal() and measures:
  - Category Hit Rate @ K     — ratio of queries where at least one top-K result
                                 matches one of the expected categories
  - Keyword Hit Rate @ K      — ratio of queries where at least one top-K result
                                 contains at least one expected keyword
  - Category MRR              — mean reciprocal rank of first category match
  - Avg top score             — sanity check on similarity scores
  - Min-score pass rate       — ratio of queries hitting the per-query min_score

Usage:
    python tests/eval_retrieval.py                  # run with default top_k=5
    python tests/eval_retrieval.py --top-k 10       # override top_k
    python tests/eval_retrieval.py --save baseline  # save results to tests/results/<label>.json
    python tests/eval_retrieval.py --compare baseline  # compare current run to saved baseline

The dataset lives in tests/eval_dataset.yaml.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Make src/ importable
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from retrieve import retrieve_internal  # noqa: E402


DATASET_PATH = _ROOT / "tests" / "eval_dataset.yaml"
RESULTS_DIR = _ROOT / "tests" / "results"


def load_dataset() -> list[dict]:
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["questions"]


def normalize(text: str) -> str:
    return (text or "").lower()


def evaluate_question(question: dict, top_k: int) -> dict:
    query = question["query"]
    expected_cats = set(question.get("expected_categories", []))
    expected_kws = [normalize(k) for k in question.get("expected_keywords", [])]
    min_score = question.get("min_score", 0.0)

    results = retrieve_internal(query, top_k=top_k)

    # Category hit
    category_hit = False
    category_rank = None
    for rank, r in enumerate(results, start=1):
        cat = r.get("metadata", {}).get("category")
        if cat and cat in expected_cats:
            category_hit = True
            category_rank = rank
            break

    # Keyword hit
    keyword_hit = False
    matched_keyword = None
    for r in results:
        text = normalize(r.get("text", ""))
        for kw in expected_kws:
            if kw and kw in text:
                keyword_hit = True
                matched_keyword = kw
                break
        if keyword_hit:
            break

    top_score = results[0]["score"] if results else 0.0
    score_pass = top_score >= min_score

    return {
        "id": question["id"],
        "query": query,
        "top_score": round(top_score, 4),
        "min_score": min_score,
        "score_pass": score_pass,
        "category_hit": category_hit,
        "category_rank": category_rank,
        "keyword_hit": keyword_hit,
        "matched_keyword": matched_keyword,
        "top_categories": [r.get("metadata", {}).get("category") for r in results],
        "num_results": len(results),
    }


def aggregate(per_question: list[dict]) -> dict:
    n = len(per_question) or 1
    cat_hits = sum(1 for r in per_question if r["category_hit"])
    kw_hits = sum(1 for r in per_question if r["keyword_hit"])
    score_pass = sum(1 for r in per_question if r["score_pass"])
    avg_top_score = sum(r["top_score"] for r in per_question) / n

    # MRR on categories
    reciprocal_ranks = [
        1.0 / r["category_rank"] if r["category_rank"] else 0.0
        for r in per_question
    ]
    mrr = sum(reciprocal_ranks) / n

    return {
        "n_questions": n,
        "category_hit_rate": round(cat_hits / n, 4),
        "keyword_hit_rate": round(kw_hits / n, 4),
        "min_score_pass_rate": round(score_pass / n, 4),
        "category_mrr": round(mrr, 4),
        "avg_top_score": round(avg_top_score, 4),
    }


def print_report(agg: dict, per_question: list[dict], top_k: int) -> None:
    print("\n" + "=" * 70)
    print(f"RAG EVALUATION REPORT  (top_k={top_k})")
    print("=" * 70)
    print(f"Questions evaluated:       {agg['n_questions']}")
    print(f"Category Hit Rate @ {top_k}:      {agg['category_hit_rate'] * 100:.1f}%")
    print(f"Keyword Hit Rate @ {top_k}:       {agg['keyword_hit_rate'] * 100:.1f}%")
    print(f"Category MRR:              {agg['category_mrr']:.4f}")
    print(f"Min-score pass rate:       {agg['min_score_pass_rate'] * 100:.1f}%")
    print(f"Avg top-1 score:           {agg['avg_top_score']:.4f}")
    print("=" * 70)

    print(f"\n{'ID':<6}{'Score':<9}{'Cat':<6}{'KW':<5}{'Rank':<6}Query")
    print("-" * 70)
    for r in per_question:
        cat_mark = "✓" if r["category_hit"] else "✗"
        kw_mark = "✓" if r["keyword_hit"] else "✗"
        rank = str(r["category_rank"]) if r["category_rank"] else "-"
        query_short = r["query"][:45] + ("…" if len(r["query"]) > 45 else "")
        print(f"{r['id']:<6}{r['top_score']:<9.4f}{cat_mark:<6}{kw_mark:<5}{rank:<6}{query_short}")

    # Failures summary
    failures = [r for r in per_question if not (r["category_hit"] and r["keyword_hit"])]
    if failures:
        print(f"\n⚠️  {len(failures)} question(s) failed either category or keyword hit:")
        for r in failures:
            missing = []
            if not r["category_hit"]:
                missing.append("category")
            if not r["keyword_hit"]:
                missing.append("keyword")
            print(f"   {r['id']}: missing {', '.join(missing)} — top cats: {r['top_categories']}")
    print()


def save_results(label: str, agg: dict, per_question: list[dict], top_k: int) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    payload = {
        "label": label,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "top_k": top_k,
        "aggregate": agg,
        "per_question": per_question,
    }
    path = RESULTS_DIR / f"{label}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def compare_to(label: str, current_agg: dict) -> None:
    path = RESULTS_DIR / f"{label}.json"
    if not path.exists():
        print(f"\n(No saved baseline '{label}' found at {path} — skipping compare.)")
        return
    with open(path, "r", encoding="utf-8") as f:
        baseline = json.load(f)
    base_agg = baseline["aggregate"]

    print("\n" + "=" * 70)
    print(f"COMPARISON vs baseline '{label}'  (saved {baseline['timestamp']})")
    print("=" * 70)
    metrics = [
        ("Category Hit Rate", "category_hit_rate", True),
        ("Keyword Hit Rate", "keyword_hit_rate", True),
        ("Category MRR", "category_mrr", True),
        ("Min-score pass rate", "min_score_pass_rate", True),
        ("Avg top-1 score", "avg_top_score", True),
    ]
    for label_, key, higher_is_better in metrics:
        base = base_agg.get(key, 0)
        cur = current_agg.get(key, 0)
        diff = cur - base
        arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "=")
        good = (diff > 0) == higher_is_better if diff != 0 else True
        marker = "✅" if good and diff != 0 else ("❌" if not good else "  ")
        print(f"  {label_:<22}  {base:.4f} → {cur:.4f}  {arrow} {diff:+.4f}  {marker}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval quality.")
    parser.add_argument("--top-k", type=int, default=5, help="Top K results to retrieve (default: 5)")
    parser.add_argument("--save", type=str, help="Save results under this label (e.g. 'baseline')")
    parser.add_argument("--compare", type=str, help="Compare current run to a saved label")
    parser.add_argument("--only", type=str, help="Run only question IDs matching comma-separated list")
    args = parser.parse_args()

    questions = load_dataset()
    if args.only:
        ids = {x.strip() for x in args.only.split(",")}
        questions = [q for q in questions if q["id"] in ids]

    print(f"Running evaluation on {len(questions)} questions (top_k={args.top_k})...")
    per_question = []
    for q in questions:
        try:
            res = evaluate_question(q, top_k=args.top_k)
        except Exception as e:
            print(f"  ERROR on {q['id']}: {e}")
            res = {
                "id": q["id"],
                "query": q["query"],
                "top_score": 0.0,
                "min_score": q.get("min_score", 0.0),
                "score_pass": False,
                "category_hit": False,
                "category_rank": None,
                "keyword_hit": False,
                "matched_keyword": None,
                "top_categories": [],
                "num_results": 0,
                "error": str(e),
            }
        per_question.append(res)

    agg = aggregate(per_question)
    print_report(agg, per_question, top_k=args.top_k)

    if args.compare:
        compare_to(args.compare, agg)

    if args.save:
        path = save_results(args.save, agg, per_question, top_k=args.top_k)
        print(f"Saved results → {path}\n")


if __name__ == "__main__":
    main()
