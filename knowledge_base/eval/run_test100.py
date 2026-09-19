"""Run the 100-question grounded test set through the live assistant.

For each question: record the model's answer, its citations, and compare against the
expected answer derived from the source documents. Output -> build/test100_results.json

The `match` field is an automated HINT only (key-fact overlap: numbers and proper
nouns from the expected answer found in the model's answer). It is not ground truth —
the PDF shows both answers side by side so a human can judge.
"""
import json, re, sys, time, unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ai.integration import answer_chat
from ai.prompts.system_prompts import NO_INFO_SENTENCE

REFUSAL = NO_INFO_SENTENCE.strip(' "')
TESTS = Path(__file__).resolve().parent / "test100.jsonl"
OUT = ROOT / "knowledge_base" / "build" / "test100_results.json"

STOP = {"pour", "avec", "dans", "les", "des", "une", "est", "sont", "par", "sur",
        "aux", "que", "qui", "aut", "chaque", "plus", "leur", "cette", "elle"}


class Prospective:
    student_status = "prospective"
    academic_year = None


def _norm(t):
    t = unicodedata.normalize("NFD", (t or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def key_facts(expected):
    """Distinctive tokens: numbers/dates and capitalised names."""
    facts = set(re.findall(r"\d[\d\s.,/-]*\d|\d", expected))
    for w in re.findall(r"\b[A-ZÉÈÀÂÎÔÛÇ][\wÉÈÀÂÎÔÛçéèêàôû'-]{2,}", expected):
        if _norm(w) not in STOP:
            facts.add(w)
    return {f.strip() for f in facts if len(f.strip()) > 1}


def match_hint(expected, got):
    facts = key_facts(expected)
    if not facts:
        return "n/a", 0.0
    g = _norm(got)
    hit = sum(1 for f in facts if _norm(f) in g)
    r = hit / len(facts)
    return ("MATCH" if r >= 0.6 else "PARTIAL" if r >= 0.3 else "MISS"), round(r, 2)


def ask(q, tries=4):
    for i in range(tries):
        try:
            return answer_chat(q, student=Prospective())
        except Exception as e:
            if i == tries - 1:
                return {"answer": f"[ERROR: {e}]", "citations": []}
            time.sleep(3 * (i + 1))  # back off on rate limits


PARTIAL = OUT.parent / "test100_partial.jsonl"


def main():
    tests = [json.loads(l) for l in open(TESTS, encoding="utf-8") if l.strip()]

    # Resume: a full run is ~20 min and can be interrupted. Each answer is appended
    # to PARTIAL as it lands, so a restart picks up where it stopped.
    done = {}
    if PARTIAL.exists():
        for line in PARTIAL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done[r["id"]] = r
        print(f"resuming: {len(done)}/100 already answered", flush=True)

    results = []
    t0 = time.time()
    for i, t in enumerate(tests, 1):
        if t["id"] in done:
            results.append(done[t["id"]])
            continue
        res = ask(t["q"])
        ans = res.get("answer") or ""
        refused = REFUSAL in ans
        verdict, ratio = ("REFUSED", 0.0) if refused else match_hint(t["expected"], ans)
        row = {
            **t,
            "answer": ans.strip(),
            "citations": res.get("citations", []),
            "refused": refused,
            "match": verdict,
            "ratio": ratio,
        }
        results.append(row)
        with open(PARTIAL, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"[{i:3d}/100] {verdict:8s} {t['q'][:58]}", flush=True)

    n = len(results)
    summary = {
        "total": n,
        "answered": sum(1 for r in results if not r["refused"]),
        "refused": sum(1 for r in results if r["refused"]),
        "with_citations": sum(1 for r in results if r["citations"]),
        "match": sum(1 for r in results if r["match"] == "MATCH"),
        "partial": sum(1 for r in results if r["match"] == "PARTIAL"),
        "miss": sum(1 for r in results if r["match"] == "MISS"),
        "elapsed_s": round(time.time() - t0),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(
        {"generated": datetime.now(timezone.utc).isoformat(),
         "summary": summary, "results": results},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nSUMMARY:", json.dumps(summary, ensure_ascii=False))
    print("->", OUT)


if __name__ == "__main__":
    main()
