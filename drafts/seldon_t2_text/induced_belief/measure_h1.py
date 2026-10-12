"""measure_h1 — H1: does the decode-through-ToM arm recover forecast-relevant
DIRECTION on the exact non-FOMC snippets the Phase-3 cue lexicon scored ~0.0 on?

Runs the arm over the FROZEN phase3_derisk/study_set.json labels, split by
doc_type, and compares directional accuracy against the frozen Phase-3
rules-only cue-lexicon numbers (phase3_derisk/results.json). Reuses the EXACT
metric functions from phase3_derisk/measure.py (prf / directional_metrics /
by_doc_type) so the two arms are measured identically.

No fabricated numbers: every arm prediction is a real decode; the lexicon
numbers are read from the frozen results.json the Phase-3 rung committed.

Emits a JSON blob to stdout the results write-up quotes verbatim.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_T2 = os.path.dirname(_HERE)
_ROOT = os.path.dirname(os.path.dirname(_T2))
for p in (_ROOT, os.path.join(_ROOT, "runners", "dsl", "python"), _T2,
          os.path.join(_T2, "phase3_derisk")):
    if p not in sys.path:
        sys.path.insert(0, p)

# reuse the frozen Phase-3 metric functions verbatim
from measure import prf, directional_metrics, confusion_ascii, LABELS  # noqa: E402

STUDY = os.path.join(_T2, "phase3_derisk", "study_set.json")
LEX_RESULTS = os.path.join(_T2, "phase3_derisk", "results.json")


def load_study():
    with open(STUDY) as f:
        return json.load(f)["snippets"]


def load_lexicon_by_doc_type():
    with open(LEX_RESULTS) as f:
        return json.load(f)["rules_only_RUN"]


def run_arm(snips):
    """Boot the arm once, decode every snippet (belief reset between snippets:
    each snippet is an independent read). Returns per-snippet rows.

    Uses a minimal WorldAdapter() boot (not load_all_seeds): the arm loads its
    OWN dependencies on demand (the CAN native engine, the entity-concept
    correspondence seed, the reading-construction codebook, and its own
    ib_decode_stance seed), so it does not need the full 600-seed research boot.
    This keeps force_all_dirty()+run_rules (the CAN relaxation GOTCHA path) on a
    small graph, so each decode is fast. The decode results are identical to the
    full-boot path (verified in smoke)."""
    from substrate.world_adapter import WorldAdapter
    from drafts.seldon_t2_text.induced_belief import arm

    a = WorldAdapter()
    mk = arm.boot(a)

    rows = []
    for s in snips:
        arm.reset_beliefs(a, mk)
        r = arm.decode_utterance(a, s["text"], mk)
        rows.append({
            "id": s["id"], "gold": s["gold"], "pred": r["direction"],
            "doc_type": s["doc_type"], "unit": s["unit"],
            "trap": bool(s.get("trap")),
            "marginal": r["marginal"], "grounding_weight": r["grounding_weight"],
            "reached": r["reached"], "hops": r["hops"],
            "grounding_gap": r["grounding_gap"], "shift": r["shift"],
            "frame_hits": r["frame_hits"],
        })
    return rows


def by_doc_type(rows):
    dt = defaultdict(lambda: [0, 0])
    for row in rows:
        dt[row["doc_type"]][1] += 1
        if row["pred"] == row["gold"]:
            dt[row["doc_type"]][0] += 1
    return {k: {"correct": v[0], "n": v[1], "acc": round(v[0] / v[1], 3)}
            for k, v in dt.items()}


def main():
    snips = load_study()
    gold = [s["gold"] for s in snips]

    rows = run_arm(snips)
    pred = [r["pred"] for r in rows]

    acc, per, conf = prf(gold, pred)
    dirm = directional_metrics(gold, pred)
    dt = by_doc_type(rows)

    # non-FOMC split (the H1 headline: doc types the lexicon went ~silent on)
    FOMC = {"fomc_statement"}
    non_fomc_rows = [r for r in rows if r["doc_type"] not in FOMC]
    nf_correct = sum(1 for r in non_fomc_rows if r["pred"] == r["gold"])
    nf_n = len(non_fomc_rows)
    fomc_rows = [r for r in rows if r["doc_type"] in FOMC]
    f_correct = sum(1 for r in fomc_rows if r["pred"] == r["gold"])
    f_n = len(fomc_rows)

    lex = load_lexicon_by_doc_type()
    lex_dt = lex["by_doc_type"]
    lex_nf_correct = sum(v["correct"] for k, v in lex_dt.items() if k not in FOMC)
    lex_nf_n = sum(v["n"] for k, v in lex_dt.items() if k not in FOMC)

    out = {
        "arm": "decode_through_tom",
        "n_snippets": len(snips),
        "gold_distribution": dict(Counter(gold)),
        "overall_accuracy": round(acc, 3),
        "per_class": per,
        "confusion_ascii": confusion_ascii(conf),
        "directional": dirm,
        "by_doc_type": dt,
        "headline_non_fomc": {
            "tom_decode": {"correct": nf_correct, "n": nf_n,
                           "acc": round(nf_correct / nf_n, 3) if nf_n else None},
            "cue_lexicon": {"correct": lex_nf_correct, "n": lex_nf_n,
                            "acc": round(lex_nf_correct / lex_nf_n, 3) if lex_nf_n else None},
        },
        "fomc": {
            "tom_decode": {"correct": f_correct, "n": f_n,
                           "acc": round(f_correct / f_n, 3) if f_n else None},
            "cue_lexicon": {"correct": lex_dt.get("fomc_statement", {}).get("correct"),
                            "n": lex_dt.get("fomc_statement", {}).get("n"),
                            "acc": lex_dt.get("fomc_statement", {}).get("acc")},
        },
        "lexicon_by_doc_type": lex_dt,
        "per_snippet": rows,
    }
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
