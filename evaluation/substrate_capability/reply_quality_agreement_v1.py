#!/usr/bin/env python3
"""Gate Q0: does ReplyQuality v1 agree with human labels? (plan P0)

Reads evaluation/labels/reply_quality_heldout_v1.csv (the human `label`
column, 0/1/2; blank rows are skipped and counted) and the machine scores in
reply_quality_heldout_v1.meta.json. The machine score is recomputed from the
CURRENT criteria too, so a criteria change is visible as a separate column.

Preregistered gate (SUBSTRATE_REPLY_QUALITY_Q0_PREREG_20261010.md):
  Q0a  Cohen's kappa (unweighted, 3 classes) >= 0.6
  Q0b  precision of machine 'inappropriate' (0) against human 0 >= 0.8
  at least 200 labelled items.

Writes evaluation/reports/reply_quality_agreement_v1_20261010.json.
"""
import collections, csv, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT)]
CSV = ROOT / "evaluation/labels/reply_quality_heldout_v1.csv"
META = ROOT / "evaluation/labels/reply_quality_heldout_v1.meta.json"
OUT = ROOT / "evaluation/reports/reply_quality_agreement_v1_20261010.json"
MIN_LABELLED = 200


def kappa(pairs, classes=(0, 1, 2)):
    n = len(pairs)
    if not n:
        return None
    po = sum(1 for h, m in pairs if h == m) / n
    hc = collections.Counter(h for h, _ in pairs)
    mc = collections.Counter(m for _, m in pairs)
    pe = sum(hc[c] * mc[c] for c in classes) / (n * n)
    return round((po - pe) / (1 - pe), 4) if pe < 1 else None


def main():
    from domains import reply_quality as rq
    meta = json.loads(META.read_text())["items"]
    pairs, pairs_now, blank, by_class = [], [], 0, collections.defaultdict(list)
    for row in csv.DictReader(CSV.open()):
        lab = (row.get("label") or "").strip()
        if lab not in ("0", "1", "2"):
            blank += 1
            continue
        h = int(lab)
        m = meta[row["id"]]["machine"]
        now = rq.assess(row["inbound"], "" if row["reply"] == "(no reply)" else row["reply"])
        # primary: the CURRENT criteria (the version is recorded in the report);
        # the score stored at sheet-build time is kept as a secondary column
        pairs.append((h, now["score"]))
        pairs_now.append((h, m["score"]))
        by_class[now["reason"].split(" ")[0]].append((h, now["score"]))
    conf = collections.Counter(f"human{h}_machine{m}" for h, m in pairs)
    m0 = [h for h, m in pairs if m == 0]
    prec0 = round(sum(1 for h in m0 if h == 0) / len(m0), 4) if m0 else None
    rep = {"labelled": len(pairs), "blank": blank, "kappa": kappa(pairs), "kappa_sheet_build_scores": kappa(pairs_now), "criteria_version": rq.criteria()["version"],
           "precision_inappropriate": prec0, "confusion": dict(conf),
           "by_machine_class": {k: {"n": len(v), "agree": sum(1 for h, m in v if h == m)} for k, v in by_class.items()},
           "gate": {"Q0a_kappa_ge_0.6": (kappa(pairs) or 0) >= 0.6, "Q0b_precision0_ge_0.8": (prec0 or 0) >= 0.8,
                    "enough_labels": len(pairs) >= MIN_LABELLED}}
    rep["gate"]["pass"] = all(rep["gate"].values())
    OUT.write_text(json.dumps(rep, indent=1) + "\n")
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
