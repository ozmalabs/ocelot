"""SETTLE-8 STEP 2 — DOES THE RECTIFIED LOOP ACTUALLY TERMINATE? (§2)

**Pre-registered in `VISION_SETTLE8_PREREG.md` §2, committed at `536c0a31`
BEFORE STEP 1 ran.** Uses burned seed 0 only; **no confirmatory seed consumed**.

WHY THIS IS A SEPARATE MEASUREMENT FROM STEP 1
-----------------------------------------------
STEP 1 measured the spectrum of `M`, the **linear part**. The loop the engine
actually runs is `act ← max(aff + M·act, 0)` — **the ReLU is not `M`**. A
spectral radius under 1 is strong evidence about the linearisation and **not a
proof about the rectified map**. So it is measured on the real graph, through the
real engine, with the failing arm (`c=4`) run as the paired control.

HOW TERMINATION IS READ, AND WHY THIS WAY
------------------------------------------
`wave_world.step()` calls `s.tick(200_000)` internally and **discards the
return** — and it is another rung's file, so it is NOT edited (§11 rule 4).
So termination is read NON-INVASIVELY: after `step()` returns, call
`s.tick(200_000)` again and read ITS count.

* the sheet **reached a fixed point** inside `step()` ⇒ nothing progresses ⇒ the
  follow-up tick returns **~0**;
* the sheet is on a **limit cycle** ⇒ `step()` burned its cap mid-orbit ⇒ the
  follow-up tick continues the orbit and burns the cap **again** ⇒ **200000**.

**The c=4 arm is what validates this instrument** (§1 clause 4 pointed at the
reader): it is KNOWN to be on a period-2 orbit (λ_min = −1.000000 exactly,
reproduced in STEP 1), so it MUST read the cap. If c=4 read ~0, the instrument
would be measuring nothing and every number here would be void.
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

from scripts.settle8_spectrum import operator, wired_adjacency  # noqa: E402
from scripts.settle_lib import build_sheet, sheet_state  # noqa: E402

CAP = 200_000


def numpy_sweeps(n_side, connectivity, *, aff=None, max_sweeps=100_000, seed=0):
    """The MATHEMATICAL object: iterate `act <- max(aff + M act, 0)` in float64
    and count sweeps to an EXACT float fixed point (`run_rules`' own criterion).

    A cross-check on the engine, and a prediction of the sweep count. Not a
    substitute for it.
    """
    A, _u, _e = wired_adjacency(n_side, connectivity)
    M, _P, _d = operator(A)
    n = A.shape[0]
    rng = np.random.default_rng(seed)
    if aff is None:
        aff = rng.random(n)
    act = np.zeros(n)
    seen = {}
    for k in range(1, max_sweeps + 1):
        nxt = np.maximum(aff + M @ act, 0.0)
        if np.array_equal(nxt, act):
            return k, "FIXED POINT", float(np.linalg.norm(nxt - act))
        key = nxt.tobytes()
        if key in seen:
            return k, f"LIMIT CYCLE period {k - seen[key]}", float("nan")
        seen[key] = k
        act = nxt
    return max_sweeps, "NO TERMINATION (cap)", float("nan")


def engine_arm(*, n_side, connectivity, settle, bubble, steps=6, seed=0):
    """Build the sheet, run wave steps, and read the follow-up tick count."""
    w, us, n_edges = build_sheet(seed=seed, n_side=n_side,
                                 connectivity=connectivity,
                                 settle=settle, bubble=bubble)
    per_step, drifts = [], []
    prev = None
    t0 = time.time()
    for i in range(steps):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
        n_apps = w.s.tick(CAP)           # <- the measurement
        per_step.append(int(n_apps))
        st = sheet_state(w, us)
        act = st["act"]
        if prev is not None:
            den = np.linalg.norm(act)
            drifts.append(float(np.linalg.norm(act - prev) / den) if den > 0
                          else 0.0)
        prev = act.copy()
    return {
        "n_side": n_side, "c": connectivity, "settle": settle, "bubble": bubble,
        "edges": n_edges, "apps": per_step,
        "hit_cap": sum(1 for a in per_step if a >= CAP),
        "steps": steps, "wall_s": time.time() - t0,
        "drift": drifts, "state": sheet_state(w, us),
    }


def main():
    print(provenance_line())
    print()
    print("STEP 2 — DOES THE RECTIFIED LOOP TERMINATE? (burned seed 0 only)")
    print("=" * 78)

    print()
    print("(a) THE MATHEMATICAL OBJECT — numpy sweeps to an EXACT float fixpoint")
    print(f"{'c':>2} {'n_side':>6} {'sweeps':>7}  verdict")
    print("-" * 60)
    for c in (4, 8):
        for n_side in (3, 4, 5):
            k, verdict, _r = numpy_sweeps(n_side, c)
            print(f"{c:>2} {n_side:>6} {k:>7}  {verdict}")

    print()
    print("(b) THE ENGINE — follow-up tick applications per wave step")
    print("    c=4 is the PAIRED CONTROL and is KNOWN to fail (lam_min=-1).")
    print("    If c=4 does NOT hit the cap, the instrument is void.")
    print(f"{'c':>2} {'n':>2} {'settle':>6} {'bubble':>6} {'cap hits':>9} "
          f"{'apps/step':>28} {'wall_s':>7}")
    print("-" * 78)
    rows = []
    for c in (4, 8):
        for settle in (0.0, 1.0):
            r = engine_arm(n_side=4, connectivity=c, settle=settle, bubble=0.0)
            rows.append(r)
            apps = str(r["apps"][:6])
            print(f"{r['c']:>2} {r['n_side']:>2} {r['settle']:>6.1f} "
                  f"{r['bubble']:>6.1f} {r['hit_cap']:>4}/{r['steps']:<4} "
                  f"{apps:>28} {r['wall_s']:>7.1f}")

    print()
    print("(c) §2's OWN REQUIREMENT — drift ||act(t)-act(t-1)||/||act||")
    for r in rows:
        d = r["drift"]
        if d:
            print(f"  c={r['c']} settle={r['settle']:.0f}: "
                  f"drift {' '.join(f'{x:.4f}' for x in d)}")

    print()
    print("VERDICT (pre-registered §2):")
    for r in rows:
        if r["settle"] != 1.0:
            continue
        ok = r["hit_cap"] == 0
        print(f"  c={r['c']} settle=1: hit_cap={r['hit_cap']}/{r['steps']} -> "
              f"{'TERMINATES' if ok else 'HITS CAP (no fixed point)'}")


if __name__ == "__main__":
    main()
