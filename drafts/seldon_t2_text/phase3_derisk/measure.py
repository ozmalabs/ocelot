"""
measure — run both typers over study_set.json and compute the frozen metrics
(PHASE3_DERISK_PREREG.md §5). Rules-only = REAL [RUN] numbers. MODEL_ENDPOINT = [MOCK]
architecture check only (no live accuracy).

Emits a JSON blob to stdout that the results write-up quotes verbatim.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rules_typer import type_claim as rules_type  # noqa: E402
import model_endpoint_typer as me  # noqa: E402

LABELS = ["up", "down", "none"]


def load_study():
    with open(os.path.join(HERE, "study_set.json")) as fh:
        return json.load(fh)["snippets"]


def prf(gold, pred):
    """per-class precision/recall/f1 + overall accuracy + confusion."""
    conf = {g: Counter() for g in LABELS}
    for gy, py in zip(gold, pred):
        conf[gy][py] += 1
    n = len(gold)
    acc = sum(1 for gy, py in zip(gold, pred) if gy == py) / n
    per = {}
    for c in LABELS:
        tp = conf[c][c]
        fp = sum(conf[g][c] for g in LABELS if g != c)
        fn = sum(conf[c][p] for p in LABELS if p != c)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per[c] = {"precision": round(prec, 3), "recall": round(rec, 3),
                  "f1": round(f1, 3), "support": tp + fn}
    return acc, per, conf


def directional_metrics(gold, pred):
    """forecast-usable directional recall + wrong-direction rate over up/down snippets."""
    dir_idx = [i for i, g in enumerate(gold) if g in ("up", "down")]
    ndir = len(dir_idx)
    correct = sum(1 for i in dir_idx if pred[i] == gold[i])
    wrong = sum(1 for i in dir_idx if pred[i] in ("up", "down") and pred[i] != gold[i])
    abstain = sum(1 for i in dir_idx if pred[i] == "none")
    return {
        "n_directional": ndir,
        "usable_directional_recall": round(correct / ndir, 3),
        "wrong_direction_rate": round(wrong / ndir, 3),
        "abstain_rate": round(abstain / ndir, 3),
        "n_correct": correct, "n_wrong": wrong, "n_abstain": abstain,
    }


def confusion_ascii(conf):
    hdr = "gold\\pred | " + " ".join(f"{c:>5s}" for c in LABELS)
    lines = [hdr, "-" * len(hdr)]
    for g in LABELS:
        lines.append(f"{g:>9s} | " + " ".join(f"{conf[g][p]:5d}" for p in LABELS))
    return "\n".join(lines)


def main():
    snips = load_study()
    gold = [s["gold"] for s in snips]

    # ---- Typer A: RULES-ONLY  [RUN] ----
    rpred, rrows = [], []
    for s in snips:
        d, dbg = rules_type(s["text"])
        rpred.append(d)
        rrows.append({"id": s["id"], "gold": s["gold"], "pred": d,
                      "rule": dbg.get("rule"), "trap": bool(s.get("trap")),
                      "unit": s["unit"], "doc_type": s["doc_type"]})
    r_acc, r_per, r_conf = prf(gold, rpred)
    r_dir = directional_metrics(gold, rpred)

    # trap subset (ids flagged in prereg §2)
    TRAP_IDS = {"s01", "s02", "s07", "s09", "s12", "s16", "s19", "s21", "s22", "s23",
                "s29", "s31", "s32", "s34", "s39", "s41", "s46", "s50"}
    trap_rows = [row for row in rrows if row["id"] in TRAP_IDS]
    trap_acc = sum(1 for row in trap_rows if row["pred"] == row["gold"]) / len(trap_rows)

    # per doc_type accuracy
    by_dt = defaultdict(lambda: [0, 0])
    for row in rrows:
        by_dt[row["doc_type"]][1] += 1
        if row["pred"] == row["gold"]:
            by_dt[row["doc_type"]][0] += 1
    dt_acc = {k: {"correct": v[0], "n": v[1], "acc": round(v[0] / v[1], 3)}
              for k, v in by_dt.items()}

    # ---- Typer B: MODEL_ENDPOINT  [MOCK] architecture check ----
    mock_ok, mock_examples = 0, []
    for s in snips:
        d, dbg = me.type_claim(s["text"], me.mock_transport)
        if d in LABELS and dbg.get("parse") == "json":
            mock_ok += 1
        if len(mock_examples) < 1:
            url, headers, payload = me.build_request(s["text"])
            resp = me.mock_transport(url, headers, payload)
            mock_examples.append({"request_url": url,
                                  "request_payload_keys": sorted(payload.keys()),
                                  "response": resp, "parsed_direction": d})

    out = {
        "n_snippets": len(snips),
        "gold_distribution": dict(Counter(gold)),
        "rules_only_RUN": {
            "overall_accuracy": round(r_acc, 3),
            "per_class": r_per,
            "confusion_matrix": {g: dict(r_conf[g]) for g in LABELS},
            "confusion_ascii": confusion_ascii(r_conf),
            "directional": r_dir,
            "trap_subset_accuracy": round(trap_acc, 3),
            "trap_n": len(trap_rows),
            "by_doc_type": dt_acc,
            "per_snippet": rrows,
        },
        "model_endpoint_MOCK": {
            "architecture": "build_request -> transport -> parse_response -> map",
            "well_formed_typings": f"{mock_ok}/{len(snips)}",
            "live_accuracy": "NOT OBTAINED — requires house MODEL_ENDPOINT; not fabricated",
            "example": mock_examples[0] if mock_examples else None,
        },
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
