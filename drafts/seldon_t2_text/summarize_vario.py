"""Summarize the Phase-2 variogram records into the numbers reported in
PHASE12_RESULTS.md. Reads the raw per-(unit,arm,seed) records and prints the
paired deltas overall and by asset-class partition (pure UST curve vs FX/mixed).
No new scoring — pure aggregation of already-scored records."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "seldon_t2_poc"))
from t2_adapter import read_card

UNITS = "/home/matt/ozmadev/ocelot/.bigtmp/track2/units"


def partition(units):
    curve, fx = set(), set()
    for u in units:
        c = read_card(f"{UNITS}/{u}/card.toml")
        (curve if all(a.startswith("UST_") for a in c.asset_ids) else fx).add(u)
    return curve, fx


def paired(recs, subset):
    by = {}
    for r in recs:
        if r["unit"] not in subset:
            continue
        by.setdefault((r["unit"], r["seed"]), {})[r["arm"]] = r
    d = {k: [] for k in ("marginal", "joint", "tail", "composite")}
    for v in by.values():
        if "joint" in v and "independent" in v:
            for comp in d:
                d[comp].append(v["joint"][comp] - v["independent"][comp])
    return {k: np.asarray(v) for k, v in d.items()}


def show(recs, subset, label):
    d = paired(recs, subset)
    n_cells = len(d["joint"])
    print(f"\n### {label}  (units={len(subset)}, unit×seed cells={n_cells})")
    for comp in ("marginal", "joint", "tail", "composite"):
        a = d[comp]
        print(f"  {comp:10s}: mean(joint−indep)={a.mean():+.4f}  "
              f"median={np.median(a):+.4f}  joint-better={np.mean(a < 0):.1%}")
    dj = np.abs(d["joint"]).mean()
    print(f"  isolation: |marg d|={np.abs(d['marginal']).mean():.4f}  "
          f"|tail d|={np.abs(d['tail']).mean():.4f}  |joint d|={dj:.4f}")


def main():
    for tag, path in [("POSITIVE realized", "phase2_vario_records.json"),
                      ("SIGNED realized", "phase2_vario_records_signed.json")]:
        p = Path(__file__).resolve().parent / path
        if not p.exists():
            continue
        recs = json.loads(p.read_text())
        units = sorted(set(r["unit"] for r in recs))
        curve, fx = partition(units)
        print(f"\n========== {tag} ==========")
        show(recs, set(units), "ALL F3 multi-asset")
        show(recs, curve, "PURE UST yield-curve")
        show(recs, fx, "FX / mixed")


if __name__ == "__main__":
    main()
