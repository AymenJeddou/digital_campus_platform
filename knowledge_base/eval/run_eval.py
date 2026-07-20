"""Retrieval-quality evaluation harness for FSB Nexus.

The shared scoreboard: it measures whether the right source document is retrieved
for a representative set of questions, and (with --full) whether the assistant
actually answers instead of refusing.

Metrics (retrieval, no LLM -- fast):
  hit@5    : fraction of answerable questions whose expected source is in the top 5
             (top 5 = what the production pipeline actually reads).
  recall@k : same, at k in {5,10,20}.
  MRR      : mean reciprocal rank of the first expected source (0 if not in top-K).

Metrics (--full, calls the LLM -- slower):
  answer_rate       : fraction of answerable questions that get a real answer
                      (not the NO_INFO refusal sentence).
  false_answer_rate : fraction of UNanswerable questions that got answered anyway
                      (must stay ~0 -- the anti-hallucination guardrail).

Index regime (to compare against the diagnostic):
  --probes N   : SET ivfflat.probes = N (default: server default = 1).
  --exact      : force exact seq scan (indexscan/bitmapscan off) = ground truth.

Usage:
  python knowledge_base/eval/run_eval.py                 # retrieval only, prod index
  python knowledge_base/eval/run_eval.py --exact         # retrieval, exact ground truth
  python knowledge_base/eval/run_eval.py --probes 200
  python knowledge_base/eval/run_eval.py --full          # add answer-rate (LLM)
  python knowledge_base/eval/run_eval.py --tag baseline  # label the saved report
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Windows consoles default to cp1252 and choke on Arabic/accented output.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from sqlalchemy import text
from ai.rag.db import get_session
from ai.rag.search import semantic_search

GOLDEN = Path(__file__).resolve().parent / "golden.jsonl"
REPORT_DIR = ROOT / "knowledge_base" / "build"
KS = (5, 10, 20)
RETRIEVE_K = max(KS)


def load_golden():
    items = []
    with open(GOLDEN, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def first_hit_rank(results, expect_sources):
    """1-based rank of the first result whose source matches an expected substring."""
    subs = [s.lower() for s in expect_sources]
    for i, r in enumerate(results):
        src = (r.get("source") or "").lower()
        if any(sub in src for sub in subs):
            return i + 1
    return None


def set_regime(session, probes, exact):
    if exact:
        session.execute(text("SET LOCAL enable_indexscan = off"))
        session.execute(text("SET LOCAL enable_bitmapscan = off"))
    if probes is not None:
        session.execute(text("SET LOCAL ivfflat.probes = :p"), {"p": probes})


def run(full, probes, exact, tag):
    golden = load_golden()
    session = get_session()

    answerable = [g for g in golden if g.get("answerable")]
    unanswerable = [g for g in golden if not g.get("answerable")]

    hits = {k: 0 for k in KS}
    rr_sum = 0.0
    per_q = []

    for g in answerable:
        session.rollback()  # fresh tx so SET LOCAL applies cleanly
        set_regime(session, probes, exact)
        # min_similarity=0.25 matches production (retrieve() default), so the
        # retrieval metric describes the same config as the end-to-end number.
        results = semantic_search(session, g["q"], top_k=RETRIEVE_K, min_similarity=0.25)
        rank = first_hit_rank(results, g["expect_sources"])
        rr_sum += (1.0 / rank) if rank else 0.0
        for k in KS:
            if rank and rank <= k:
                hits[k] += 1
        per_q.append({
            "q": g["q"], "expect": g["expect_sources"], "rank": rank,
            "top3": [r.get("source") for r in results[:3]],
        })

    n = len(answerable)
    metrics = {
        "n_answerable": n,
        "hit@5": round(hits[5] / n, 3),
        "recall@10": round(hits[10] / n, 3),
        "recall@20": round(hits[20] / n, 3),
        "MRR": round(rr_sum / n, 3),
    }

    full_metrics = None
    if full:
        from ai.integration import answer_chat
        from ai.prompts.system_prompts import NO_INFO_SENTENCE
        refusal = NO_INFO_SENTENCE.strip(' "')

        def answered(q):
            """Return (gave_an_answer, answer_had_citation)."""
            res = answer_chat(q)
            ans = res.get("answer") or ""
            gave = refusal not in ans
            cited = bool(res.get("citations"))
            return gave, cited

        ans_flags = [answered(g["q"]) for g in answerable]
        false_flags = [answered(g["q"]) for g in unanswerable]
        n_ans_ok = sum(1 for gave, _ in ans_flags if gave)
        n_ans_cited = sum(1 for gave, cited in ans_flags if gave and cited)
        n_false = sum(1 for gave, _ in false_flags if gave)
        full_metrics = {
            # deliverable: "answered questions WITH citations"
            "answer_rate": round(n_ans_ok / n, 3),
            "answer_with_citation_rate": round(n_ans_cited / n, 3),
            # deliverable: "unsupported answers remain blocked"
            "false_answer_rate": round(n_false / max(len(unanswerable), 1), 3),
            "n_unanswerable": len(unanswerable),
        }

    session.close()

    # ---- print scoreboard ----
    regime = "exact-seq" if exact else (f"probes={probes}" if probes else "prod-default")
    print(f"\n{'='*70}\nFSB Nexus retrieval eval  |  regime: {regime}  |  tag: {tag or '-'}")
    print(f"{'='*70}")
    for k, v in metrics.items():
        print(f"  {k:14s}: {v}")
    if full_metrics:
        for k, v in full_metrics.items():
            print(f"  {k:14s}: {v}")
    print(f"\n  Misses (expected source not in top 5):")
    for row in per_q:
        if not row["rank"] or row["rank"] > 5:
            print(f"    rank={str(row['rank']):>4}  {row['q'][:55]}")
            print(f"              top3={row['top3']}")

    # ---- persist ----
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tag": tag, "regime": regime,
        "metrics": metrics, "full_metrics": full_metrics,
        "per_question": per_q,
    }
    out = REPORT_DIR / f"eval_report{('_' + tag) if tag else ''}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  report -> {out}")
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="also measure end-to-end answer-rate (LLM)")
    ap.add_argument("--probes", type=int, default=None, help="SET ivfflat.probes = N")
    ap.add_argument("--exact", action="store_true", help="force exact seq scan (ground truth)")
    ap.add_argument("--tag", default=None, help="label for the saved report")
    args = ap.parse_args()
    run(args.full, args.probes, args.exact, args.tag)


if __name__ == "__main__":
    main()
