"""The cross-capability matrix, cut CORRECTLY.

The first cut defined the diagonal as "every file that installs the ablated
seed", which absorbed the entire effect and reported a vacuous zero
off-diagonal everywhere. The redundancy question is finer, and needs THREE
cells, not two:

  OWN        the seed's own gate file (tests/test_<seed>_migrated.py) --
             the POSITIVE CONTROL that the ablation took effect at all.
  CO-LOADED  files that INSTALL the seed but are not its own gate. **This is
             the cross-capability question.** A zero here, on a seed whose
             rules FIRE, is genuine redundancy: another capability had the
             seed live in its substrate and did not need it.
  UNRELATED  files that never install the seed. Structurally forced to zero
             (PREREG §1.1); reported only to confirm nothing leaked.

Also reports the NULL-ABLATION CONTROL: six of the 25 target seeds declare ZERO
rules, so "withhold all rules" is a genuine no-op. Those six runs are a
free negative control on bench flakiness, and they are read as such.
"""
from __future__ import annotations

import collections
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results", "redundancy")
SEEDMAP = json.load(open(os.path.join(ROOT, "results", "redundancy_seed_map.json")))
CENSUS = (json.load(open(os.path.join(RES, "census.json"))) or {}).get("census_progress", {})

LOADERS: dict[str, set[str]] = collections.defaultdict(set)
for _f, _seeds in SEEDMAP.items():
    for _s in _seeds:
        LOADERS[_s].add(_f)


def own_gate(sid: str) -> set[str]:
    """The seed's own gate file(s), by the tree's naming convention."""
    cands = {f"tests/test_{sid}_migrated.py", f"tests/test_{sid}.py"}
    return {os.path.basename(c) for c in cands
            if os.path.exists(os.path.join(ROOT, c))}


def rules_of(sid):
    with open(os.path.join(ROOT, "seeds", f"{sid}.json")) as fh:
        return [r.get("name", "") for r in json.load(fh).get("rules", [])]


def main() -> None:
    base = json.load(open(os.path.join(RES, "baseline_0.json")))
    bf = {f: v.get("passed", 0) for f, v in base["per_file"].items()}
    targets = sorted(os.path.basename(p)[len("whole__"):-5]
                     for p in glob.glob(os.path.join(RES, "whole__*.json")))

    print("=" * 100)
    print("CROSS-CAPABILITY MATRIX -- OWN gate (control) | CO-LOADED (the question) | UNRELATED")
    print("=" * 100)
    print(f"{'seed':24s} {'n':>3s} {'live':>4s} {'loaders':>7s} {'OWN':>5s} {'CO-LOAD':>8s} "
          f"{'UNREL':>6s}  co-loaded losses")
    rows = []
    for sid in targets:
        rec = json.load(open(os.path.join(RES, f"whole__{sid}.json")))
        pf = {f: v.get("passed", 0) for f, v in (rec.get("per_file") or {}).items()}
        loaders = LOADERS.get(sid, set())
        own = own_gate(sid) & loaders
        own_l = co_l = un_l = 0
        co_detail = []
        for f, b in bf.items():
            d = b - pf.get(f, 0)
            if d <= 0:
                continue
            if f in own:
                own_l += d
            elif f in loaders:
                co_l += d
                co_detail.append(f"{f}(-{d})")
            else:
                un_l += d
        n = len(rules_of(sid))
        live = sum(1 for r in rules_of(sid) if CENSUS.get(r, 0) > 0)
        rows.append({"seed": sid, "n": n, "live": live, "loaders": len(loaders),
                     "own": own_l, "co": co_l, "unrelated": un_l,
                     "co_detail": co_detail, "total": rec["passed"]})
        print(f"{sid:24s} {n:3d} {live:4d} {len(loaders):7d} {own_l:5d} {co_l:8d} "
              f"{un_l:6d}  {' '.join(co_detail) if co_detail else '-'}")

    print()
    print("=" * 100)
    print("NULL-ABLATION CONTROL -- target seeds declaring ZERO rules: the ablation is a NO-OP,")
    print("so any deviation from 200 is BENCH FLAKINESS, not an effect.")
    print("=" * 100)
    noop = [r for r in rows if r["n"] == 0]
    for r in noop:
        flag = "" if r["total"] == 200 else "   <-- FLAKE (no-op ablation, yet not 200)"
        print(f"  {r['seed']:24s} passed={r['total']}{flag}")
    devs = [abs(200 - r["total"]) for r in noop]
    print(f"  n_noop={len(noop)}  max|deviation|={max(devs) if devs else 0}  "
          f"=> effects of magnitude <= {max(devs) if devs else 0} are INSIDE the null-ablation spread")

    out = {"rows": rows, "noop_control": noop,
           "noise_floor": max(devs) if devs else 0}
    with open(os.path.join(ROOT, "results", "redundancy_matrix.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print("\n[written] results/redundancy_matrix.json")


if __name__ == "__main__":
    main()
