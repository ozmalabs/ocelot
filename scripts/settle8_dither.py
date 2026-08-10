"""SETTLE-8 STEP 2c — IS THE ENGINE'S NON-TERMINATION A DITHER OR A DYNAMICS?

Two questions STEP 2b raised and could not close, both measured HERE rather than
reasoned about:

**(1) THE ACTIVE SET IS THE MECHANISM, AND IT DEPENDS ON `aff`.** STEP 2b found
`c=4` TRUE-limit-cycling at `n_side=3` (**9/9 units active**, amplitude 1.1e-02)
and CONVERGING at `n_side=4,5` (**12/16, 21/25 active**, amplitude ~1e-16). The
reason is the ReLU: **the checkerboard eigenvector needs the WHOLE bipartite
lattice, and a lattice with units clamped to 0 is no longer bipartite.** So
whether λ_min=−1 actually bites is a property of the ACTIVE SET, hence of `aff`
— not of the lattice alone. **One `aff` draw cannot establish that.** Measured
here over many draws.

**(2) WHAT IS THE ENGINE ACTUALLY DOING WHEN IT BURNS THE CAP?** Read
`|act − act_next|` off the graph AFTER the cap is burned:

* **~1e-16** ⇒ the sheet HAS settled and `run_rules`' EXACT-equality test simply
  cannot terminate on a last-bit dither;
* **O(1)** ⇒ a genuine undamped orbit, the sibling's reading.

**These are different diagnoses with the same symptom** — 200000/200000 — and
this arc's standing lesson is that a symptom read without its mechanism is how
four results got retracted.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402

engine_preamble()

from scripts.settle8_spectrum import operator, wired_adjacency  # noqa: E402
from scripts.settle_lib import build_sheet  # noqa: E402

CAP = 200_000


def sweep_to_repeat(M, aff, *, max_sweeps=50_000):
    """Iterate the RECTIFIED map to a byte-repeat; report amplitude + active set."""
    act = np.zeros(len(aff))
    seen, hist = {}, []
    for k in range(1, max_sweeps + 1):
        nxt = np.maximum(aff + M @ act, 0.0)
        hist.append(nxt.copy())
        key = nxt.tobytes()
        if key in seen:
            orbit = hist[seen[key] - 1:k - 1]
            amp = float(np.max([np.max(np.abs(o - orbit[0])) for o in orbit])) \
                if len(orbit) > 1 else 0.0
            return k, amp, int(np.sum(nxt > 0)), len(aff)
        seen[key] = k
        act = nxt
    return max_sweeps, float("nan"), int(np.sum(act > 0)), len(aff)


def aff_sensitivity(n_side, connectivity, *, draws=200, sparsity=None, seed=0):
    """Over many `aff` draws: how often is the 2-cycle a TRUE cycle vs a dither?"""
    A, _u, _e = wired_adjacency(n_side, connectivity)
    M, _P, _d = operator(A)
    n = A.shape[0]
    rng = np.random.default_rng(seed)
    true_cycle, dither, amps, actives = 0, 0, [], []
    for _ in range(draws):
        aff = rng.random(n)
        if sparsity is not None:                 # a SPARSE aff, like a wavefront
            aff = aff * (rng.random(n) < sparsity)
        k, amp, n_act, N = sweep_to_repeat(M, aff)
        amps.append(amp)
        actives.append(n_act)
        if amp > 1e-12:
            true_cycle += 1
        else:
            dither += 1
    return {
        "n_side": n_side, "c": connectivity, "N": n, "draws": draws,
        "sparsity": sparsity, "true_cycle": true_cycle, "dither": dither,
        "frac_true": true_cycle / draws,
        "median_amp": float(np.median(amps)),
        "max_amp": float(np.max(amps)),
        "mean_active": float(np.mean(actives)),
        "frac_all_active": float(np.mean([a == n for a in actives])),
    }


def engine_residual(*, n_side, connectivity, steps=6, seed=0):
    """Run the engine, burn the cap, then read |act - act_next| OFF THE GRAPH."""
    w, us, _e = build_sheet(seed=seed, n_side=n_side, connectivity=connectivity,
                            settle=1.0, bubble=0.0)
    out = []
    for i in range(steps):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
        n_apps = int(w.s.tick(CAP))
        act = np.array([float(w.s.node(u)["attrs"].get("act", 0.0)) for u in us])
        nxt = np.array([float(w.s.node(u)["attrs"].get("act_next", 0.0))
                        for u in us])
        aff = np.array([float(w.s.node(u)["attrs"].get("aff", 0.0)) for u in us])
        resid = float(np.max(np.abs(act - nxt)))
        scale = float(np.max(np.abs(act))) if len(act) else 0.0
        out.append({
            "step": i, "apps": n_apps, "resid": resid, "scale": scale,
            "rel": resid / scale if scale > 0 else 0.0,
            "n_active": int(np.sum(act > 0)), "N": len(us),
            "aff_nonzero": int(np.sum(aff != 0)),
        })
    return out


def main():
    print(provenance_line())
    print()
    print("STEP 2c — DITHER OR DYNAMICS? (burned seed 0 only)")
    print("=" * 86)

    print()
    print("(1) THE ACTIVE SET IS THE MECHANISM — over 200 random `aff` draws")
    print("    A TRUE cycle needs the checkerboard, which needs the FULL bipartite")
    print("    lattice. The ReLU clamps units -> the active set is not bipartite.")
    print(f"{'c':>2} {'n':>2} {'N':>3} {'true cyc':>9} {'dither':>7} "
          f"{'frac_true':>10} {'med amp':>10} {'max amp':>10} "
          f"{'mean act':>9} {'all-active':>11}")
    print("-" * 86)
    for c in (4, 8):
        for n_side in (3, 4, 5):
            r = aff_sensitivity(n_side, c, draws=200)
            print(f"{r['c']:>2} {r['n_side']:>2} {r['N']:>3} "
                  f"{r['true_cycle']:>9} {r['dither']:>7} {r['frac_true']:>10.3f} "
                  f"{r['median_amp']:>10.2e} {r['max_amp']:>10.2e} "
                  f"{r['mean_active']:>9.2f} {r['frac_all_active']:>11.3f}")
        print("-" * 86)

    print()
    print("(1b) A SPARSE `aff` — a travelling WAVEFRONT drives few units, which is")
    print("     the regime the sheet is actually in (sparsity=0.3)")
    print(f"{'c':>2} {'n':>2} {'frac_true':>10} {'med amp':>10} {'mean act':>9} "
          f"{'all-active':>11}")
    print("-" * 86)
    for c in (4, 8):
        for n_side in (3, 4, 5):
            r = aff_sensitivity(n_side, c, draws=200, sparsity=0.3)
            print(f"{r['c']:>2} {r['n_side']:>2} {r['frac_true']:>10.3f} "
                  f"{r['median_amp']:>10.2e} {r['mean_active']:>9.2f} "
                  f"{r['frac_all_active']:>11.3f}")
        print("-" * 86)

    print()
    print("(2) THE ENGINE — |act - act_next| READ OFF THE GRAPH after the cap")
    print(f"{'c':>2} {'n':>2} {'step':>4} {'apps':>7} {'|act-act_next|':>15} "
          f"{'scale':>10} {'relative':>10} {'active':>8} {'aff!=0':>7}")
    print("-" * 86)
    for c in (4, 8):
        for row in engine_residual(n_side=4, connectivity=c):
            print(f"{c:>2} {4:>2} {row['step']:>4} {row['apps']:>7} "
                  f"{row['resid']:>15.3e} {row['scale']:>10.3e} "
                  f"{row['rel']:>10.3e} {row['n_active']:>3}/{row['N']:<3} "
                  f"{row['aff_nonzero']:>7}")
        print("-" * 86)

    print()
    print("READ THIS AS: a residual at ~1e-16 with the cap burned means the sheet")
    print("SETTLED and the ENGINE could not SEE it. Convergence of the DYNAMICS and")
    print("termination of the FIXPOINT are DIFFERENT PROPERTIES.")


if __name__ == "__main__":
    main()
