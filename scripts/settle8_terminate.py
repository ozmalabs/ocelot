"""SETTLE-8 STEP 2 (FINAL) — THE TERMINATION RATE, AND THE DITHER'S MECHANISM.

**The pre-registered STEP 2 verdict (`VISION_SETTLE8_PREREG.md` §2) is decided
here.** PASS required `c=8` to terminate **well under the cap on EVERY step**,
with `c=4` hitting it on every step as the paired control.

WHAT THE TICK-BY-TICK ALREADY ESTABLISHED (`settle8_diagnose.py`)
-----------------------------------------------------------------
At `c=4`, one application per tick, forever, alternating exactly:

    tick 0: apps=1   d_act_next = 8.882e-16   (st_settle writes act_next)
    tick 1: apps=1   d_act      = 8.882e-16   (st_commit writes act <- act_next)
    tick 2: apps=1   d_act_next = 8.882e-16   ... and so on, without end

**8.882e-16 is ONE ULP at act's scale (~8.6).** The sheet has SETTLED; it is
oscillating between two ADJACENT FLOATS. `run_rules` terminates on EXACT value
equality, which this never reaches.

**AND IT EXPLAINS WHY:** `ρ(M) = 1.000000` at c=4 means the checkerboard mode is
MARGINAL — round-off noise injected into it **never decays**, so the last bit
alternates forever. At `c=8`, `ρ(M) = 0.668 < 1` **damps round-off too**, so the
iteration can land on an EXACT float fixed point (`apps = 0`, every delta 0).

**A CAUTION THIS RUNG EARNED THE HARD WAY:** `|act − act_next|` read after a tick
is **PHASE-DEPENDENT** — it is 0 on the post-commit phase and 1 ULP on the
post-settle phase. Sampling it once reads **0.000e+00 on a sheet that is
dithering forever**, which is exactly the wrong conclusion. **The tick-by-tick is
the instrument; the single snapshot is a lookup** (§1.1's disease, in float).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

from scripts.settle_lib import build_sheet  # noqa: E402

CAP = 200_000


def termination_rate(connectivity, *, n_side=4, steps=20, seed=0):
    """apps per wave step over `steps`. The pre-registered STEP 2 statistic."""
    w, us, n_edges = build_sheet(seed=seed, n_side=n_side,
                                 connectivity=connectivity,
                                 settle=1.0, bubble=0.0)
    apps, scales = [], []
    for i in range(steps):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
        apps.append(int(w.s.tick(CAP)))
        act = np.array([float(w.s.node(u)["attrs"].get("act", 0.0)) for u in us])
        scales.append(float(np.max(np.abs(act))))
    return {"c": connectivity, "apps": apps, "scales": scales,
            "n_term": sum(1 for a in apps if a < CAP),
            "steps": steps, "edges": n_edges}


def ulp_check(connectivity, *, n_side=4, seed=0, find_capped=True, probe=8):
    """On a step that BURNS the cap, watch tick-by-tick and measure the orbit."""
    w, us, _e = build_sheet(seed=seed, n_side=n_side,
                            connectivity=connectivity, settle=1.0, bubble=0.0)
    for i in range(20):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
        n = int(w.s.tick(CAP))
        capped = n >= CAP
        if capped == find_capped:
            break
    else:
        return None

    def rd(k):
        return np.array([float(w.s.node(u)["attrs"].get(k, 0.0)) for u in us])

    rows = []
    prev_a, prev_n = rd("act"), rd("act_next")
    for t in range(probe):
        apps = int(w.s.tick(1))
        a, nx = rd("act"), rd("act_next")
        rows.append((t, apps, float(np.max(np.abs(a - prev_a))),
                     float(np.max(np.abs(nx - prev_n))),
                     float(np.max(np.abs(a - nx)))))
        prev_a, prev_n = a, nx
    scale = float(np.max(np.abs(prev_a)))
    return {"c": connectivity, "step": i, "capped": capped, "rows": rows,
            "scale": scale, "ulp": float(np.spacing(scale))}


def main():
    print(provenance_line())
    print()
    print("STEP 2 FINAL — THE TERMINATION RATE (burned seed 0 only)")
    print("=" * 78)
    print()
    print("(a) apps per wave step, 20 steps, n_side=4")
    res = {}
    for c in (4, 8):
        r = termination_rate(c)
        res[c] = r
        term = "".join("." if a < CAP else "X" for a in r["apps"])
        print(f"  c={c}: terminated {r['n_term']:>2}/{r['steps']}   "
              f"[{term}]   ( . = terminated, X = burned the 200000 cap )")
    print()
    print("  PRE-REGISTERED PASS (§2): c=8 terminates on EVERY step, c=4 on none.")
    ok8 = res[8]["n_term"] == res[8]["steps"]
    ok4 = res[4]["n_term"] == 0
    print(f"  c=8 terminates on every step : {ok8}")
    print(f"  c=4 (paired control) fails    : {ok4}")
    print(f"  => STEP 2 {'PASSES' if (ok8 and ok4) else 'FAILS'} "
          f"its pre-registered criterion.")

    print()
    print("(b) THE ORBIT ON A CAP-BURNING STEP — is it a dither or a dynamics?")
    for c in (4, 8):
        u = ulp_check(c, find_capped=True)
        if u is None:
            print(f"  c={c}: no cap-burning step found in 20 — "
                  f"it terminates everywhere.")
            continue
        print(f"  c={c}, step {u['step']}: act scale = {u['scale']:.4f}, "
              f"1 ULP at that scale = {u['ulp']:.3e}")
        print(f"    {'tick':>4} {'apps':>5} {'d_act':>11} {'d_act_next':>11} "
              f"{'|act-next|':>11}")
        for (t, apps, da, dn, resid) in u["rows"]:
            print(f"    {t:>4} {apps:>5} {da:>11.3e} {dn:>11.3e} {resid:>11.3e}")
        amp = max(max(r[2], r[3]) for r in u["rows"])
        print(f"    => max delta on the orbit = {amp:.3e}  "
              f"({amp / u['ulp']:.1f} ULP)  -> "
              f"{'ULP DITHER of a SETTLED sheet' if amp <= 8 * u['ulp'] else 'O(1) DYNAMICS'}")
        print()

    print("THE READING:")
    print("  rho(M) = 1.000000 (c=4) is MARGINAL: round-off in the checkerboard mode")
    print("  never decays, so the last bit alternates forever. rho(M) = 0.668 (c=8)")
    print("  damps round-off as well, so the iteration CAN land exactly -- but only")
    print("  when the fixed point is EXACTLY REPRESENTABLE. When it is not, a")
    print("  CONTRACTING loop still dithers between the two nearest floats, and")
    print("  run_rules' EXACT-equality test cannot terminate on that either.")


if __name__ == "__main__":
    main()
