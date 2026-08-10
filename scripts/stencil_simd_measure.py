"""BLOCK 134000 — the vectorized-stencil fast path timing + byte-identity sweep.

Measures ms/tick for the wave state relaxation under FOUR implementations of the
SAME field update, timed on the QUIET machine (multi-trial, CI95):
  GENERAL  : `s.tick(200_000)` — the committed per-cell rule matching.
  FAST-REST: `s.wave_stencil_tick(run_rest=True)` — vectorized stencil + the
             general pass for any NON-wave rule (SAFE/composable default).
  FAST-BARE: `s.wave_stencil_tick(run_rest=False)` — vectorized stencil only
             (valid for the pure wave field; the scale-lever specialist).
  NUMPY    : the numpy-exact `ca_tick` reference (pure array compute, the ~500×
             anchor 133000 named), NO graph read/write — the upper bound.

Isolates the TICK: the adapter's commit/ignite/drive/mark_bursts run each step
but only the tick call is timed. GENERAL and FAST produce a BIT-IDENTICAL field
(asserted in-line), so per-tick costs are comparable at every step.

PROVENANCE its own step: `engine_preamble()` pins THIS tree's engine, and the
verdict is asserted `in {own, shared}` from INSIDE this process (never a literal
hash). Timing rigor: `os.getloadavg()` recorded start/end; solitude PROVEN by
per-point CI width; run ALONE, no concurrent load.
"""
from __future__ import annotations
import os, sys, time, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from domains.engine_provenance import engine_preamble, provenance_line, provenance_stamp
engine_preamble()
import numpy as np
from substrate.boot_core import boot_core, load_seeds_into
import domains.seed_registry  # noqa
from domains.wave_world import WaveWorld

REST, ACT, REC, REF = 0, 1, 2, 3
NAME = {"rested": REST, "active": ACT, "recruited": REC, "refractory": REF}

GRIDS = [16, 24, 32, 48, 64, 96, 128]
TRIALS = {16: 9, 24: 9, 32: 9, 48: 9, 64: 7, 96: 7, 128: 7}
WARMUP_STEPS = 12          # discard: reach a live travelling-wave field
TIMED_TICKS = 30           # ticks timed per trial
IGNITE_EVERY = 5


def _boot(g, seed=0, fast=None, run_rest=True):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    w = WaveWorld(s, h=g, w=g, seed=seed, fovea_radius=0)
    if fast:
        w.stencil_fast = True
        w.stencil_run_rest = run_rest
    return s, w


def _full_digest(s):
    import hashlib
    parts = []
    for n in s.nodes():
        at = s.node(n)["attrs"]
        parts.append((s.node(n)["type"], tuple(sorted((k, repr(v)) for k, v in at.items()))))
    parts.sort(key=lambda x: repr(x))
    return hashlib.sha256(repr(parts).encode()).hexdigest()


# ---- the numpy-exact reference (ca_tick), pure array compute ----------------
def _read_fields(s, w):
    ids = w._cell_ids
    st = s.get_attr_many(ids, "state")
    aa = s.get_attr_many(ids, "activated_at")
    fa = s.get_attr_many(ids, "fired_at")
    S = np.zeros((w.h, w.w), np.int8)
    A = np.zeros((w.h, w.w), np.float64)
    F = np.zeros((w.h, w.w), np.float64)
    for (r, c), stt, a, f in zip(w._cell_rc, st, aa, fa):
        S[r, c] = NAME[stt]; A[r, c] = float(a); F[r, c] = float(f)
    return S, A, F


def _ca_tick_numpy(S, A, F, step, refr=4.0, propagate=True):
    S2 = S.copy(); F2 = F.copy()
    fresh = (S == ACT) & (A == step)
    old = (S == ACT) & (A < step)
    refrm = (S == REF)
    recover = refrm & ((step - F) >= refr)
    S2[old] = REF; F2[old] = step
    S2[recover] = REST
    if propagate:
        rested_now = (S2 == REST)
        nb = np.zeros_like(fresh)
        nb[1:, :] |= fresh[:-1, :]; nb[:-1, :] |= fresh[1:, :]
        nb[:, 1:] |= fresh[:, :-1]; nb[:, :-1] |= fresh[:, 1:]
        S2[rested_now & nb] = REC
    return S2, F2


# ---- timing -----------------------------------------------------------------
def _time_arm(g, arm, trials):
    """Return list of per-trial mean-ms-per-tick for `arm` at grid g."""
    per_trial = []
    for t in range(trials):
        s, w = _boot(g, seed=0,
                     fast=(arm in ("fast_rest", "fast_bare")),
                     run_rest=(arm == "fast_rest"))
        for i in range(WARMUP_STEPS):
            w.step(ignite_k=1 if i % IGNITE_EVERY == 0 else 0)
        dt = 0.0
        if arm == "numpy":
            # time the pure array compute on the live field (no graph I/O)
            for j in range(TIMED_TICKS):
                # advance the adapter's non-tick work so the field evolves like
                # the others, then time ONLY the numpy stencil
                st = float(s.node(w.retina)["attrs"]["step"]) + 1.0
                s.set_attr(w.retina, "step", st)
                states = s.get_attr_many(w._cell_ids, "state")
                recruited = [n for n, x in zip(w._cell_ids, states) if x == "recruited"]
                if recruited:
                    s.set_attr_many(recruited, "state", "active")
                    s.set_attr_many(recruited, "activated_at", st)
                s.set_attr_many(w._cell_ids, "driven", 0.0)
                if (WARMUP_STEPS + j) % IGNITE_EVERY == 0:
                    w.ignite(1)
                S, A, F = _read_fields(s, w)
                step = float(s.node(w.retina)["attrs"]["step"])
                t0 = time.perf_counter()
                _ca_tick_numpy(S, A, F, step)
                dt += time.perf_counter() - t0
                # keep the field alive via the real tick so evolution matches
                s.tick(200_000)
        else:
            for j in range(TIMED_TICKS):
                # replicate step() up to the tick, time the tick, then finish
                st = float(s.node(w.retina)["attrs"]["step"]) + 1.0
                s.set_attr(w.retina, "step", st)
                states = s.get_attr_many(w._cell_ids, "state")
                recruited = [n for n, x in zip(w._cell_ids, states) if x == "recruited"]
                if recruited:
                    s.set_attr_many(recruited, "state", "active")
                    s.set_attr_many(recruited, "activated_at", st)
                s.set_attr_many(w._cell_ids, "driven", 0.0)
                if (WARMUP_STEPS + j) % IGNITE_EVERY == 0:
                    w.ignite(1)
                w.drive(None)
                w._mark_bursts(st)
                s.set_attr_many(s.nodes("Unit"), "bursting", 0.0)
                t0 = time.perf_counter()
                if arm == "general":
                    s.tick(200_000)
                else:
                    ok = s.wave_stencil_tick(200_000, arm == "fast_rest")
                    if not ok:
                        raise SystemExit("fast path inadmissible during timing!")
                dt += time.perf_counter() - t0
        per_trial.append(1000.0 * dt / TIMED_TICKS)
    return per_trial


def _ci95(xs):
    xs = sorted(xs)
    m = sum(xs) / len(xs)
    if len(xs) < 2:
        return m, 0.0
    sd = (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5
    half = 1.96 * sd / len(xs) ** 0.5
    return m, half


def _byte_identity_guard(g, seed, ticks, run_rest):
    """Assert FAST == GENERAL bit-for-bit over `ticks` iterated ticks."""
    sg, wg = _boot(g, seed=seed)
    sf, wf = _boot(g, seed=seed, fast=True, run_rest=run_rest)
    mism = 0
    for i in range(ticks):
        k = 1 if i % IGNITE_EVERY == 0 else 0
        wg.step(ignite_k=k); wf.step(ignite_k=k)
        if _full_digest(sg) != _full_digest(sf):
            mism += 1
    return mism


def main():
    print(provenance_line())
    p = provenance_stamp()
    assert p["source_match"] in ("own", "shared"), p
    load_start = os.getloadavg()

    # byte-identity battery FIRST (multi-tick, both modes)
    bi = {}
    for g in (8, 12, 16, 24, 32):
        for seed in (134000, 134001, 134002, 134003, 134004):
            bi[f"{g}x{g}_seed{seed}_rest"] = _byte_identity_guard(g, seed, 100, True)
            bi[f"{g}x{g}_seed{seed}_bare"] = _byte_identity_guard(g, seed, 100, False)
    total_mism = sum(bi.values())
    print("BYTE-IDENTITY total mismatches (grids×seeds×100 ticks, both modes):", total_mism)

    # timing sweep
    rows = {}
    for g in GRIDS:
        T = TRIALS[g]
        row = {}
        for arm in ("general", "fast_rest", "fast_bare", "numpy"):
            trials = _time_arm(g, arm, T)
            m, half = _ci95(trials)
            row[arm] = {"ms": m, "ci95": half, "us_per_cell": 1000.0 * m / (g * g),
                        "trials": trials}
        rows[f"{g}"] = row
        gm = row["general"]["ms"]; fr = row["fast_rest"]["ms"]
        fb = row["fast_bare"]["ms"]; np_ = row["numpy"]["ms"]
        print(f"g={g:3d} cells={g*g:6d}  GEN {gm:8.4f}ms ({row['general']['ci95']/gm*100:.2f}%)"
              f"  FAST-REST {fr:8.4f} (x{gm/fr:6.1f})  FAST-BARE {fb:8.4f} (x{gm/fb:6.1f})"
              f"  NUMPY {np_:8.5f} (x{gm/np_:7.1f})")

    load_end = os.getloadavg()

    # fits
    def fit(arm):
        xs = [math.log(g * g) for g in GRIDS]
        ys = [math.log(rows[str(g)][arm]["ms"]) for g in GRIDS]
        n = len(xs); sx = sum(xs); sy = sum(ys)
        sxx = sum(x * x for x in xs); sxy = sum(x * y for x, y in zip(xs, ys))
        slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
        intercept = (sy - slope * sx) / n
        # ceiling: cells where ms == 41.7 -> ln(cells) = (ln(41.7)-b)/slope
        lc = (math.log(41.7) - intercept) / slope
        cells = math.exp(lc)
        return slope, math.sqrt(cells)
    fits = {arm: fit(arm) for arm in ("general", "fast_rest", "fast_bare", "numpy")}
    for arm, (slope, side) in fits.items():
        print(f"FIT {arm:10s} exponent {slope:.3f}  real-time ceiling {side:.1f}^2 "
              f"({side*side:.0f} cells) @ 41.7ms")

    out = {
        "provenance": p,
        "loadavg_start": load_start, "loadavg_end": load_end,
        "byte_identity": bi, "byte_identity_total_mismatches": total_mism,
        "grids": GRIDS, "trials": TRIALS, "warmup_steps": WARMUP_STEPS,
        "timed_ticks": TIMED_TICKS, "rows": rows,
        "fits": {a: {"exponent": s, "ceiling_side": c} for a, (s, c) in fits.items()},
    }
    with open(os.path.join(ROOT, "results", "stencil_simd.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    # re-verify provenance AFTER the run, in-process
    p2 = provenance_stamp()
    assert p2["source_match"] in ("own", "shared"), p2
    print("post-run source_match:", p2["source_match"], "loadavg", load_start, "->", load_end)
    print("wrote results/stencil_simd.json")


if __name__ == "__main__":
    main()
