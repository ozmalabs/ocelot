"""SCALE WALL — the WALL-CLOCK truth of the batched drive, MACHINE ALONE.

Pre-registration: `VISION_SCALE_WALL_PUSH_PREREG.md` (committed at 1d8c1fc1e0
BEFORE this ran). Block 131000-131999.

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***
No seed is edited (the OFF arm strips the `batch` flag into a TEMP copy, exactly
as `batch_apply_measure`), no rule added, no default changed, no Rust touched.

WHY IT EXISTS. The scale wall was attributed by three prior rungs entirely in
COUNTS, because the machine was always contended and every one correctly refused
wall-clock. The batch fix (`batch:true` on the five ch_* rules + apply_rule_batch)
is the committed default and was proven byte-identical IN COUNTS -- but its
WALL-CLOCK effect and the NEW real-time ceiling were never measured. This rung
has the machine to itself and converts the counted attribution into wall-clock.

METHOD (inherited verbatim where possible -- a reimplementation would be a second
instrument, and this arc has caught eleven inert ones):
  * boot / frames / counters / buckets / fit / liveness / conservation from
    `scripts/scale_split_measure` (SS);
  * arm toggle / state_record / state_digest / CELL_ATTRS from
    `scripts/batch_apply_measure` (BA).
  * ADDED here and ONLY here: multi-trial wall-clock with median + IQR + bootstrap
    95% CI (the quiet-machine measurement prior rungs could not take), the
    real-time CEILING at the video probe's own 41.7 ms budget, the OFF/ON speedup,
    and an in-process byte-identity comparison localised to cell+attr.

TIMING RIGOR (§ timing): loadavg recorded at start AND end INSIDE this process;
fresh boot per trial; gc.collect before each timed region; WARMUP ticks discarded;
T trials per point; NO single-shot verdict. The measurement is deterministic
(WaveWorld seed 0, frame seed 11), so it consumes NO block seed.

USAGE
    PYTHONPATH=runners/dsl/python:. python scripts/scale_wall_push_measure.py \
        --out results/scale_wall_push.json
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: pin THIS tree's engine before any substrate_rs import.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402
from substrate_rs import _native  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
import domains.wave_world as wave_world  # noqa: E402

import scripts.scale_split_measure as SS  # noqa: E402
import scripts.batch_apply_measure as BA  # noqa: E402

AUDIT = _native.Substrate

# The video probe's four grids + two larger for range. Per-grid trial counts:
# small grids get many trials (cheap, tight CI); the O(N^2) OFF arm at large
# grids gets fewer (each trial is seconds). ALL fixed here, before any number.
GRIDS = [12, 16, 24, 32, 48, 64]
TRIALS = {12: 9, 16: 9, 24: 9, 32: 7, 48: 5, 64: 3}
TICKS = 20      # SS.TICKS -- the committed per-point tick count
WARMUP = 5      # SS.WARMUP -- discarded
RT_BUDGET_MS = 1000.0 / 23.976   # 41.7 ms/tick: 23.976 fps, the video probe's own budget


def _loadavg():
    try:
        return list(os.getloadavg())
    except OSError:
        return None


def _bootstrap_ci(xs, n=10000, alpha=0.05, seed=131000):
    """Bootstrap CI of the MEDIAN. `seed` is a numpy-internal RNG for the
    resampling only -- it touches no graph and consumes no block seed (the
    measurement itself is deterministic); recorded for reproducibility."""
    if len(xs) < 2:
        return (float(xs[0]), float(xs[0])) if xs else (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    arr = np.asarray(xs, float)
    meds = np.median(rng.choice(arr, size=(n, len(arr)), replace=True), axis=1)
    return (float(np.percentile(meds, 100 * alpha / 2)),
            float(np.percentile(meds, 100 * (1 - alpha / 2))))


def _timed_trial(g, *, batch):
    """One fresh boot; WARMUP untimed; TICKS timed. Returns (ms_per_tick,
    counters, state_record) -- the state after the identical deterministic
    schedule, for the byte-identity comparison."""
    gc.collect()
    s, ag, world = BA.build_world(g, batch=batch)
    frames = SS._frames(g)
    SS._run(world, WARMUP, g, "constant", frames)
    chk0 = SS._checksum(s, world)

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    s._inner.reset_rule_costs()
    t0 = time.perf_counter()
    SS._run(world, TICKS, g, "constant", frames)
    ms = (time.perf_counter() - t0) / TICKS * 1000.0
    AUDIT.scale_audit_set_enabled(False)
    c = SS.counters()

    chk1 = SS._checksum(s, world)
    # ---- HARD LIVENESS GATE (§1) ----
    if chk0 == chk1:
        raise SystemExit(f"FROZEN WORLD g={g} batch={batch}: {chk0} unmoved.")
    if c["cand_enum"] == 0:
        raise SystemExit(f"DEAD INSTRUMENT g={g} batch={batch}: 0 cand_enum.")
    # ---- CONSERVATION (imported instrument's own) ----
    assert c["cand_enum_first"] + c["cand_enum_repeat"] == c["cand_enum"], (g, c)
    assert (c["cand_enum_scan"] + c["cand_enum_local"] + c["cand_enum_hinted"]
            == c["cand_enum"]), (g, c)
    assert c["where_evals_first"] + c["where_evals_repeat"] == c["where_evals"], (g, c)

    rec = BA.state_record(s, world)
    del world, s, ag
    return ms, c, rec


def sweep_arm(arm, grids):
    """arm in {'off','on'}. OFF strips the batch flag from the DATA the adapter
    loads (a graph-data control, not a code fork). Returns per-grid rows +
    trial-0 state records (for byte-identity)."""
    batch = arm == "on"
    tmp = None
    if not batch:
        tmp = BA._strip_batch_seed()
        wave_world._CHANGE_SEED = tmp
    else:
        wave_world._CHANGE_SEED = os.path.join(ROOT, "domain_data", "vision_change.json")

    dispatch = BA._drive_dispatch_name()
    rows, states = [], {}
    for g in grids:
        T = TRIALS[g]
        mss, digests = [], []
        c0, rec0 = None, None
        for t in range(T):
            ms, c, rec = _timed_trial(g, batch=batch)
            mss.append(ms)
            digests.append(BA.state_digest(rec))
            if t == 0:
                c0, rec0 = c, rec
        # determinism positive control: every trial's final state is identical
        det_ok = len(set(digests)) == 1
        med = float(statistics.median(mss))
        lo, hi = _bootstrap_ci(mss)
        q1, q3 = (float(np.percentile(mss, 25)), float(np.percentile(mss, 75)))
        rows.append({
            "grid": g, "cells": g * g, "arm": arm, "batch": batch,
            "trials": T, "ms_per_tick_raw": [round(x, 5) for x in mss],
            "ms_per_tick_median": med,
            "ms_per_tick_ci95": [lo, hi], "ms_per_tick_iqr": [q1, q3],
            "ms_per_tick_min": float(min(mss)), "ms_per_tick_max": float(max(mss)),
            "counters": c0, "buckets": SS.buckets(c0), "shares": SS.shares(c0),
            "cross_epoch": SS.reattributed(c0, ticks=TICKS),
            "state_digest": digests[0],
            "determinism_across_trials_ok": det_ok,
            "us_per_cell_median": med * 1000.0 / (g * g),
        })
        states[g] = rec0
        print(f"  [{arm}] g={g:3d} cells={g*g:6d} T={T} "
              f"median={med:10.4f} ms/tick  CI95=[{lo:.4f},{hi:.4f}] "
              f"IQR=[{q1:.4f},{q3:.4f}]  digest={digests[0]} det_ok={det_ok}",
              flush=True)
    if tmp:
        os.unlink(tmp)
    return rows, states, dispatch


def fit_median(rows):
    """log-log OLS of MEDIAN ms/tick vs cells, with r2."""
    x = np.log(np.array([r["cells"] for r in rows], float))
    y = np.log(np.array([r["ms_per_tick_median"] for r in rows], float))
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return {"exponent": float(coef[0]), "intercept": float(coef[1]),
            "r2": (1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan"),
            "n_points": len(rows)}


def ceiling(fit, budget_ms=RT_BUDGET_MS):
    """Affordable field at the real-time budget -- FALLS OUT of the fit and the
    frame rate (§13, nothing chosen)."""
    cells = (budget_ms / np.exp(fit["intercept"])) ** (1.0 / fit["exponent"])
    return {"budget_ms": budget_ms, "affordable_cells": float(cells),
            "affordable_grid": float(np.sqrt(cells))}


def project(fit, cells):
    return float(np.exp(fit["intercept"]) * cells ** fit["exponent"])


def byte_identity(states_off, states_on):
    """Per-cell, per-attr comparison of the OFF and ON final states, localised.
    NO tolerance (prereg): exact reprs must match."""
    out = []
    for g in sorted(states_off):
        off, on = states_off[g], states_on[g]
        mism = []
        if len(off) != len(on):
            mism.append({"cell_count": (len(off), len(on))})
        else:
            for ro, rn in zip(off, on):
                if ro != rn:  # exact list-of-reprs comparison
                    # localise: cell key at [0], attrs after
                    diffs = [(BA.CELL_ATTRS[i - 1], ro[i], rn[i])
                             for i in range(1, len(ro)) if ro[i] != rn[i]]
                    mism.append({"cell": ro[0], "attr_diffs": diffs})
                    if len(mism) >= 20:
                        break
        out.append({"grid": g, "cells": g * g,
                    "digest_off": BA.state_digest(off),
                    "digest_on": BA.state_digest(on),
                    "digests_equal": BA.state_digest(off) == BA.state_digest(on),
                    "n_mismatched_cells": len(mism),
                    "mismatches_sample": mism[:20]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grids", default=None, help="comma list; default the fixed set")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    grids = [int(x) for x in a.grids.split(",")] if a.grids else GRIDS

    prov = provenance_line()
    load0 = _loadavg()
    print(prov, flush=True)
    print(SS._machine(), flush=True)
    print(f"loadavg at start: {load0}", flush=True)

    res = {"provenance": prov, "machine": SS._machine(),
           "grids": grids, "trials_per_grid": {str(g): TRIALS[g] for g in grids},
           "ticks": TICKS, "warmup": WARMUP, "rt_budget_ms": RT_BUDGET_MS,
           "cpu_governor": _governor(),
           "native_has_apply_rule_batch": hasattr(_native.Substrate, "apply_rule_batch"),
           "seed_batch_flags_AS_COMMITTED": BA._seed_batch_flags(),
           "loadavg_at_start": load0,
           "block_seeds_drawn": 0,
           "note_deterministic": "WaveWorld seed 0 + frame seed 11; no block seed consumed"}

    print("== OFF arm (batch STRIPPED -> apply_rule_once, the pre-batch O(N^2) drive) ==", flush=True)
    off_rows, off_states, off_disp = sweep_arm("off", grids)
    print("== ON arm (batch:true LIVE -> batch_apply_rule, the committed default) ==", flush=True)
    on_rows, on_states, on_disp = sweep_arm("on", grids)

    res["off"] = {"rows": off_rows, "dispatch": off_disp}
    res["on"] = {"rows": on_rows, "dispatch": on_disp}

    fit_off = fit_median(off_rows)
    fit_on = fit_median(on_rows)
    res["fit_off_wall"] = fit_off
    res["fit_on_wall"] = fit_on
    res["ceiling_off"] = ceiling(fit_off)
    res["ceiling_on"] = ceiling(fit_on)
    # exponent of the FFI bucket (should be ~linear on BOTH arms per the count rung)
    res["fit_off_F_bucket"] = SS.fit(off_rows, "buckets.F")
    res["fit_on_F_bucket"] = SS.fit(on_rows, "buckets.F")
    res["fit_off_C_bucket"] = SS.fit(off_rows, "buckets.C")
    res["fit_on_C_bucket"] = SS.fit(on_rows, "buckets.C")
    res["fit_off_ops_total"] = SS.fit(off_rows, "buckets.total")
    res["fit_on_ops_total"] = SS.fit(on_rows, "buckets.total")

    # per-grid speedup
    speed = []
    on_by = {r["grid"]: r for r in on_rows}
    for r in off_rows:
        on = on_by[r["grid"]]
        speed.append({"grid": r["grid"], "cells": r["cells"],
                      "off_ms": r["ms_per_tick_median"], "on_ms": on["ms_per_tick_median"],
                      "speedup": r["ms_per_tick_median"] / on["ms_per_tick_median"]})
    res["speedup_per_grid"] = speed

    # byte identity
    res["byte_identity"] = byte_identity(off_states, on_states)
    all_equal = all(b["digests_equal"] and b["n_mismatched_cells"] == 0
                    for b in res["byte_identity"])
    res["byte_identity_ALL_EQUAL"] = bool(all_equal)

    # projections to real fields
    res["projections_off"] = {lbl: project(fit_off, n) for n, lbl in
                              ((4096, "64x64"), (76800, "320x240"), (2073600, "1920x1080"))}
    res["projections_on"] = {lbl: project(fit_on, n) for n, lbl in
                             ((4096, "64x64"), (76800, "320x240"), (2073600, "1920x1080"))}

    load1 = _loadavg()
    res["loadavg_at_end"] = load1

    # ---- headline print ----
    print("\n== RESULT ==", flush=True)
    print(f"  OFF wall exponent = {fit_off['exponent']:.3f} (r2 {fit_off['r2']:.4f}) "
          f"-> ceiling {res['ceiling_off']['affordable_grid']:.1f}^2 "
          f"({res['ceiling_off']['affordable_cells']:.0f} cells) @ {RT_BUDGET_MS:.1f}ms", flush=True)
    print(f"  ON  wall exponent = {fit_on['exponent']:.3f} (r2 {fit_on['r2']:.4f}) "
          f"-> ceiling {res['ceiling_on']['affordable_grid']:.1f}^2 "
          f"({res['ceiling_on']['affordable_cells']:.0f} cells) @ {RT_BUDGET_MS:.1f}ms", flush=True)
    print(f"  ceiling push: {res['ceiling_off']['affordable_grid']:.1f}^2 -> "
          f"{res['ceiling_on']['affordable_grid']:.1f}^2 "
          f"(x{res['ceiling_on']['affordable_grid']/res['ceiling_off']['affordable_grid']:.2f} per side, "
          f"x{res['ceiling_on']['affordable_cells']/res['ceiling_off']['affordable_cells']:.2f} in cells)", flush=True)
    print(f"  largest-grid speedup = x{speed[-1]['speedup']:.2f} at {speed[-1]['grid']}^2", flush=True)
    print(f"  FFI(F) exponent OFF={res['fit_off_F_bucket']['exponent']:.3f} "
          f"ON={res['fit_on_F_bucket']['exponent']:.3f}  |  "
          f"C(compare) exponent OFF={res['fit_off_C_bucket']['exponent']:.3f} "
          f"ON={res['fit_on_C_bucket']['exponent']:.3f}", flush=True)
    print(f"  BYTE-IDENTITY all grids equal = {all_equal}", flush=True)
    print(f"  loadavg start={load0} end={load1}", flush=True)

    d = os.path.dirname(a.out)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(res, fh, indent=2, default=str)
    print("wrote", a.out, flush=True)


def _governor():
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor") as f:
            return f.read().strip()
    except OSError:
        return "unknown"


if __name__ == "__main__":
    main()
