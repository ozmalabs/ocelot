"""SETTLE-8 STEP 2b — THE 2-CYCLE'S AMPLITUDE. THE DISCRIMINATOR STEP 2 LACKED.

**`settle8_converge.py` reported "LIMIT CYCLE period 2" for BOTH c=4 and c=8 —
and they are NOT THE SAME OBJECT. My detector tested `array_equal` (exact bytes)
and called everything that failed it a limit cycle. That is a LOOKUP, not a
measurement** (§1.1's disease in a new costume: an absence off an exact-equality
test is evidence of a comparison, not of a dynamics).

**THE DISCRIMINATOR IS AMPLITUDE:**

* a **TRUE limit cycle** — an undamped mode — oscillates at **O(1)**;
* a **ULP DITHER** — a CONVERGED iteration whose last bits alternate — oscillates
  at **~1e-16**, i.e. at float64 resolution.

The sweep counts already whispered it and I nearly walked past: at `c=8, n_side=5`
the cycle appeared after **158** sweeps, and `log(1e-16)/log(ρ)` with STEP 1's
measured `ρ = 0.800156` is **≈165**. That is geometric convergence to machine
precision, arriving exactly on schedule. At `c=4`, `ρ = 1.000000` — **nothing
decays, ever**.

This script measures the amplitude directly and settles it.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

from scripts.settle8_spectrum import operator, wired_adjacency  # noqa: E402


def cycle_amplitude(n_side, connectivity, *, max_sweeps=200_000, seed=0):
    """Iterate to a repeat and report the AMPLITUDE of whatever it lands on."""
    A, _u, _e = wired_adjacency(n_side, connectivity)
    M, _P, _d = operator(A)
    n = A.shape[0]
    rng = np.random.default_rng(seed)
    aff = rng.random(n)
    act = np.zeros(n)

    seen, hist = {}, []
    for k in range(1, max_sweeps + 1):
        nxt = np.maximum(aff + M @ act, 0.0)
        hist.append(nxt.copy())
        key = nxt.tobytes()
        if key in seen:
            start = seen[key]
            period = k - start
            orbit = hist[start - 1:k - 1]
            amp = float(np.max([np.max(np.abs(o - orbit[0])) for o in orbit])) \
                if len(orbit) > 1 else 0.0
            # the step-to-step residual ON the orbit
            resid = float(np.max(np.abs(hist[k - 1] - hist[k - 2])))
            scale = float(np.max(np.abs(nxt)))
            return {
                "n_side": n_side, "c": connectivity, "sweeps": k,
                "period": period, "amp": amp, "resid": resid, "scale": scale,
                "rel_amp": amp / scale if scale > 0 else 0.0,
                "n_active": int(np.sum(nxt > 0)), "N": n,
            }
        seen[key] = k
        act = nxt
    return {"n_side": n_side, "c": connectivity, "sweeps": max_sweeps,
            "period": -1, "amp": float("nan"), "resid": float("nan"),
            "scale": float("nan"), "rel_amp": float("nan"),
            "n_active": -1, "N": n}


def predicted_sweeps(rho, eps=2.2e-16):
    """log(eps)/log(rho) — sweeps for a geometric contraction to reach the ULP."""
    if rho >= 1.0:
        return float("inf")
    return float(np.log(eps) / np.log(rho))


def main():
    print(provenance_line())
    print()
    print("STEP 2b — IS THE 2-CYCLE A DYNAMICS OR A LAST-BIT DITHER?")
    print("=" * 84)
    print("A TRUE limit cycle oscillates at O(1). A CONVERGED iteration dithers at ~1e-16.")
    print()
    # STEP 1's measured rho, quoted so the prediction is checkable.
    rho = {(4, 3): 1.000000, (4, 4): 1.000000, (4, 5): 1.000000,
           (8, 3): 0.452753, (8, 4): 0.667941, (8, 5): 0.800156}
    hdr = (f"{'c':>2} {'n':>2} {'rho(M)':>9} {'pred sw':>8} {'sweeps':>7} "
           f"{'period':>6} {'AMPLITUDE':>12} {'rel_amp':>10} {'resid':>11} "
           f"{'active':>7}")
    print(hdr)
    print("-" * 84)
    rows = []
    for c in (4, 8):
        for n_side in (3, 4, 5):
            r = cycle_amplitude(n_side, c)
            r["rho"] = rho[(c, n_side)]
            r["pred"] = predicted_sweeps(r["rho"])
            rows.append(r)
            pred = "inf" if r["pred"] == float("inf") else f"{r['pred']:.0f}"
            print(f"{r['c']:>2} {r['n_side']:>2} {r['rho']:>9.6f} {pred:>8} "
                  f"{r['sweeps']:>7} {r['period']:>6} {r['amp']:>12.3e} "
                  f"{r['rel_amp']:>10.3e} {r['resid']:>11.3e} "
                  f"{r['n_active']:>3}/{r['N']:<3}")
        print("-" * 84)

    print()
    print("VERDICT — the amplitude, at float64 eps = 2.22e-16:")
    for r in rows:
        if r["amp"] < 1e-12:
            v = ("CONVERGED — a LAST-BIT DITHER of a settled solution. "
                 "The dynamics reached a fixed point to machine precision.")
        elif r["amp"] > 1e-3:
            v = "TRUE LIMIT CYCLE — an undamped mode oscillating at O(1)."
        else:
            v = "AMBIGUOUS — report honestly, do not classify."
        print(f"  c={r['c']} n_side={r['n_side']}: amp={r['amp']:.3e} -> {v}")

    print()
    print("THE CONSEQUENCE FOR THE ENGINE:")
    print("  run_rules terminates on EXACT value equality. A last-bit dither NEVER")
    print("  reaches exact equality — so a sheet that has PHYSICALLY converged to")
    print("  ~1e-16 still burns the cap. Convergence of the DYNAMICS and termination")
    print("  of the FIXPOINT are different properties, and only one of them is the")
    print("  engine's criterion.")


if __name__ == "__main__":
    main()
