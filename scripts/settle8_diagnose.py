"""SETTLE-8 — WHAT IS ACTUALLY BURNING THE CAP? A tick-by-tick diagnosis.

**The anomaly this exists to resolve, and it broke my clean story:** at `c=4`,
`n_side=4`, step 0, the engine burned **200000** applications while
`|act − act_next|` read **0.000e+00 EXACTLY** off the graph. A deterministic map
sitting at `act == act_next` **is** a fixed point — both `st_settle` and
`st_commit` would land the same value and make no progress. **So at c=4 the
non-termination is NOT the settling residual, and my dither explanation does not
cover it.**

Rather than reason about it, watch it: `tick(1)` at a time, recording `act`,
`act_next` and every other SUnit attr, and find **what changes**.

This is §12's rule turned on my own instrument: I inferred a mechanism from a
symptom (200000) and a proxy (`|act−act_next|`). Neither is the thing itself.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

from scripts.settle_lib import build_sheet  # noqa: E402

KEYS = ("act", "act_next", "aff", "aff_step", "act_step", "rate", "bursting")


def snap(w, us):
    out = {}
    for k in KEYS:
        out[k] = np.array([float(w.s.node(u)["attrs"].get(k, 0.0)) for u in us])
    return out


def diagnose(connectivity, *, n_side=4, seed=0, n_probe=40):
    print(f"\n{'=' * 78}")
    print(f"c={connectivity}  n_side={n_side}")
    print("=" * 78)
    w, us, n_edges = build_sheet(seed=seed, n_side=n_side,
                                 connectivity=connectivity,
                                 settle=1.0, bubble=0.0)
    # One world step, whose internal tick(200_000) has already run.
    w.step(ignite_k=1)
    retina = w.retina
    print(f"after step(): retina.step = "
          f"{w.s.node(retina)['attrs'].get('step')}")

    prev = snap(w, us)
    print(f"{'tick':>5} {'apps':>6} " +
          " ".join(f"{('d_' + k):>11}" for k in KEYS))
    print("-" * 78)
    for i in range(n_probe):
        apps = int(w.s.tick(1))
        cur = snap(w, us)
        deltas = [np.max(np.abs(cur[k] - prev[k])) for k in KEYS]
        print(f"{i:>5} {apps:>6} " + " ".join(f"{d:>11.3e}" for d in deltas))
        prev = cur

    print()
    print("A tick(1) that returns 1 with EVERY delta at 0.0 means a rule is")
    print("APPLYING without CHANGING anything -- i.e. the engine counts the")
    print("application as progress even though the SetAttr is a no-op.")
    return w, us


def main():
    print(provenance_line())
    print("\nWHAT IS BURNING THE CAP? (burned seed 0 only)")
    for c in (8, 4):
        diagnose(c)


if __name__ == "__main__":
    main()
