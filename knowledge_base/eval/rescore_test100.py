"""Re-score the saved 100-question answers with a fairer matcher (no new LLM calls).

The first matcher produced false negatives: it compared surface forms, so a CORRECT
answer was marked MISS purely on formatting --
    expected "3428"        vs model "3 428"
    expected "12/09/2024"  vs model "12 septembre 2024"
    expected "quatre mois" vs model "4 mois"
This normalises numbers, spelled-out numerals and dates before comparing.
Read the model answers as-is from disk; only the scoring changes.
"""
import json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge_base" / "build" / "test100_results.json"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MONTHS = {"01": "janvier", "02": "fevrier", "03": "mars", "04": "avril", "05": "mai",
          "06": "juin", "07": "juillet", "08": "aout", "09": "septembre",
          "10": "octobre", "11": "novembre", "12": "decembre"}
WORDNUM = {"un": "1", "deux": "2", "trois": "3", "quatre": "4", "cinq": "5", "six": "6",
           "sept": "7", "huit": "8", "neuf": "9", "dix": "10", "onze": "11", "douze": "12",
           "trente": "30", "vingt": "20"}
STOP = {"pour", "avec", "dans", "les", "des", "une", "est", "sont", "par", "sur", "aux",
        "que", "qui", "chaque", "plus", "leur", "cette", "elle", "oui", "non", "apres",
        "voici", "selon", "entre", "jusqu", "entre", "entre"}


def norm(t):
    t = unicodedata.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace(" ", " ").replace(" ", " ")
    t = re.sub(r"(?<=\d)[  ](?=\d)", "", t)          # "3 428" -> "3428"
    t = re.sub(r"(?<=\d)[.,](?=\d{3}\b)", "", t)     # "1.100" -> "1100"
    for w, d in WORDNUM.items():                      # "quatre mois" -> "4 mois"
        t = re.sub(rf"\b{w}\b", d, t)
    return t


def variants(fact):
    """Surface forms a correct answer might legitimately use."""
    f = norm(fact)
    out = {f}
    m = re.fullmatch(r"(\d{1,2})/(\d{2})/(\d{4})", f)     # 12/09/2024
    if m:
        d, mo, y = m.groups()
        out.add(f"{int(d)} {MONTHS[mo]} {y}")
        out.add(f"{int(d)}/{int(mo)}/{y}")
    m = re.fullmatch(r"(\d{1,2})/(\d{2})", f)             # 15/08
    if m:
        d, mo = m.groups()
        out.add(f"{int(d)} {MONTHS[mo]}")
    if f.isdigit():
        out.add(f.lstrip("0"))
    return {v for v in out if v}


def key_facts(expected):
    facts = set()
    for tok in re.findall(r"\d{1,2}/\d{2}/\d{4}|\d{1,2}/\d{2}|\d[\d ]*\d|\d", expected):
        facts.add(tok.strip())
    for w in re.findall(r"\b[A-ZÉÈÀÂÎÔÛÇ][\wÉÈÀÂÎÔÛçéèêàôû'’-]{2,}", expected):
        if norm(w) not in STOP:
            facts.add(w)
    for w in re.findall(r"\b(?:quatre|six|trois|deux|trente)\b", expected.lower()):
        facts.add(w)
    return {f for f in facts if len(f.strip()) > 1}


def score(expected, got):
    facts = key_facts(expected)
    if not facts:
        return "n/a", 0.0
    g = norm(got)
    hit = sum(1 for f in facts if any(v in g for v in variants(f)))
    r = hit / len(facts)
    return ("MATCH" if r >= 0.6 else "PARTIAL" if r >= 0.3 else "MISS"), round(r, 2)


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    changed = []
    for r in d["results"]:
        if r["refused"]:
            r["match"], r["ratio"] = "REFUSED", 0.0
            continue
        old = r["match"]
        r["match"], r["ratio"] = score(r["expected"], r["answer"])
        if old != r["match"]:
            changed.append((r["id"], old, r["match"], r["q"][:46]))

    res = d["results"]
    d["summary"].update({
        "match": sum(1 for r in res if r["match"] == "MATCH"),
        "partial": sum(1 for r in res if r["match"] == "PARTIAL"),
        "miss": sum(1 for r in res if r["match"] == "MISS"),
        "rescored": True,
    })
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    print("RECLASSIFIED (scoring fix only, answers untouched):")
    for c in changed:
        print(f"  #{c[0]:3d} {c[1]:8s} -> {c[2]:8s}  {c[3]}")
    print("\nNEW SUMMARY:", json.dumps(d["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
