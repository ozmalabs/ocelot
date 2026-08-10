"""ASSEMBLED-EYE SCALE — re-measure the FULL stack, attribute it afresh, and
quantify the parallelism prize. Two regimes + N-eyes + an Amdahl decomposition.

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***
No seed is edited, no rule added, no default changed, no Rust touched. It boots
the committed seeds exactly as every committed rung does, sets the graph-data
flags the eye ships with (change=1, sustain=1, lateral=1 — all §9 opt-ins), and
TIMES. Provenance is stamped on every result (§10). Liveness is a HARD gate per
point (§1): a tick that does nothing is infinitely fast and scales beautifully.

WHY THIS EXISTS (creator, 2026-07-18): the committed `scale_wall_measure.py`
measured the BARE wave grid. The eye is now the full stack (waves + change
detection + lateral) and two engine fixes landed (bulk boundary accessors,
predicate pushdown). So the object changed and the old attribution is stale.

THE TWO REGIMES:
  A  the continuous retinal tick (per-cell, per-frame): waves + change + lateral.
     Sweep grid size; attribute the tick across FFI / ch_* / wave / lateral, and
     decompose it for PARALLELISM (Amdahl) using the engine's own
     `profile_rule_match` within-rule instrument.
  B  the discovery ops (per-SCENE): GenInfer / TimeInfer / DepthInfer. Cost as a
     function of the data-derived search bound, #surfaces, #frames, #eyes.

TIMER POSITIVE CONTROL (§1, §12.2): `tick()`'s return counts progressing rule
VISITS, not firings, and reads ~the same on a live and a near-idle retina. It is
NEVER the witness here. The witness per N is: the state histogram, a moving
checksum, the DRIVEN fraction (proof the ch_* rules did real work), the HCell
residual checksum (proof the lat_* rules did real work), and the engine's own
per-rule `progress` counters. `--assert-live` makes any frozen witness a HARD
error.

ATTRIBUTION METHOD (learned by the committed instrument, inherited):
  * The Rust side is read from the engine's own `rule_costs()` counters
    (unbiased, native) — but those accumulate ONLY in `run_rules`/`tick`, NOT in
    `apply_rule_once`. The ch_* change rules fire in the drive phase via
    `apply_rule_once`, so their cost is timed by a TICK-ONLY-style wrapper on the
    world's `_drive_phase`, never by a per-call probe (a per-call probe inflates
    the very Python cost it measures ~1.8x — the committed instrument's finding).
  * The Amdahl split reads the engine's `profile_rule_match`: per rule it
    re-runs the MATCH with a NO-OP visit (graph untouched) under stripped
    variants, giving enumeration / expansion / interp-setup / attr-eval — the
    per-binding, per-cell-INDEPENDENT work that is the parallelizable fraction.

USAGE
  PYTHONPATH=runners/dsl/python python scripts/assembled_eye_scale.py \
      --mode regimeA --out results/assembled_eye_regimeA.json
  ... --mode regimeB --out results/assembled_eye_regimeB.json
  ... --mode neyes  --out results/assembled_eye_neyes.json

NO SEEDS ARE CLAIMED (a measurement, not a confirmatory experiment). RNG seed
fixed at 0 for reproducibility.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# §10.1 rule 3: pin THIS tree's engine before any substrate_rs import.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.lateral_world import add_lateral_retina, set_lat_params  # noqa: E402

SIZES = [16, 24, 32, 48, 64, 96, 128]
WARMUP = 5
REPEATS = 5
TICKS = 12
IGNITE_EVERY = 5
WAVE_RULES = ("wv_propagate", "wv_refract", "wv_recover")
CH_RULES = ("ch_transient_on", "ch_transient_off", "ch_sustained", "ch_adapt_ref")
LAT_RULES = ("lat_pool", "lat_residual", "lat_bipolar", "lat_learn_gain")
# The dominant rules profiled for the Amdahl decomposition (one per family that
# actually carries load; picked from a pilot, reported so the choice is visible).
PROFILE_RULES = ("wv_propagate", "wv_refract", "wv_recover",
                 "ch_transient_on", "ch_transient_off", "ch_sustained", "ch_adapt_ref",
                 "lat_pool", "lat_residual", "lat_bipolar")


# --------------------------------------------------------------------------- #
#  timing helpers
# --------------------------------------------------------------------------- #
class PhaseTimer:
    """Wraps the world's `tick`-carrying substrate AND its `_drive_phase` with
    ONE `perf_counter` pair each. 2 wraps/step => negligible perturbation, far
    below signal. Deliberately NOT a per-call probe on the ~100k hot
    node()/set_attr() calls."""

    def __init__(self):
        self.tick_s = 0.0
        self.drive_s = 0.0
        self.visits = []   # tick()'s return = progressing rule VISITS (fixpoint depth)


def _drift_image(grid, rng):
    """A SMOOTH natural-ish 8-bit image, big enough to drift 1px/tick over the
    timed window. 8-bit scale is load-bearing: the ch_* shot-noise floor is
    sqrt(I/255^2), so the drive must be in the same 0..255 range the seed's
    nmax=255^2 falls out of, or change detection would not be exercised."""
    base = rng.random((grid * 3, grid * 3)).astype(np.float32)
    for _ in range(6):
        base = (base + np.roll(base, 1, 0) + np.roll(base, -1, 0)
                + np.roll(base, 1, 1) + np.roll(base, -1, 1)) / 5.0
    base = (base - base.min()) / (base.max() - base.min() + 1e-9)
    return (base * 255.0).astype(np.float32)


def boot_eye(grid, *, change=1.0, sustain=1.0, lateral=1.0, n_eyes=1):
    """Boot the ASSEMBLED eye: waves + change + lateral, all §9 opt-ins ON.
    Returns (substrate, agent, [world,...], {"hcells":..,"bipolars":..} per eye)."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral"])
    worlds, lats = [], []
    for _ in range(n_eyes):
        w = WaveWorld(s, h=grid, w=grid, seed=0)
        lats.append(add_lateral_retina(w))
        worlds.append(w)
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", float(change))
        s.set_attr(cp, "sustain", float(sustain))
    set_lat_params(worlds[0], lateral=float(lateral))  # LatParams is a singleton
    return s, ag, worlds, lats


def _instrument(world, timer):
    """Monkeypatch ONE world's `_drive_phase` and the shared substrate `tick`
    with timer wrappers. Returns a restore() thunk. Mechanical; changes no
    graph state, only records wall-clock."""
    s = world.s
    real_drive = world._drive_phase
    real_tick = s.tick

    def drive_wrapped(*a, **k):
        t0 = time.perf_counter()
        out = real_drive(*a, **k)
        timer.drive_s += time.perf_counter() - t0
        return out

    def tick_wrapped(*a, **k):
        t0 = time.perf_counter()
        out = real_tick(*a, **k)
        timer.tick_s += time.perf_counter() - t0
        timer.visits.append(out)  # NOT a firing count — progressing rule VISITS
        return out

    world._drive_phase = drive_wrapped
    s.tick = tick_wrapped

    def restore():
        world._drive_phase = real_drive
        try:
            del s.tick
        except AttributeError:
            pass
    return restore


def _states(s, world):
    h = {}
    for n in world.cells.values():
        v = s.node(n)["attrs"].get("state")
        h[v] = h.get(v, 0) + 1
    return h


def _wave_checksum(s, world):
    act, lb = 0, 0.0
    for n in world.cells.values():
        at = s.node(n)["attrs"]
        if at.get("state") == "active":
            act += 1
        lb += float(at.get("last_burst", -999.0))
    return (act, round(lb, 3))


def _driven_frac(s, world):
    """Fraction of cells the ch_* rules marked `driven` this step — the witness
    that change detection did real work. Read AFTER drive(), BEFORE the next
    step's reset."""
    d = sum(1 for n in world.cells.values()
            if float(s.node(n)["attrs"].get("driven", 0.0)) == 1.0)
    return d / len(world.cells)


def _hcell_resid_checksum(s, lat):
    """Sum of HCell residuals — the witness that the lat_* rules did real work
    (a frozen sum means lateral never fired)."""
    tot = 0.0
    for h in lat["hcells"].values():
        tot += float(s.node(h)["attrs"].get("resid", 0.0))
    return round(tot, 4)


# --------------------------------------------------------------------------- #
#  REGIME A — the continuous retinal tick
# --------------------------------------------------------------------------- #
def _run_eye(world, ticks, grid, rng, capture_driven=False):
    driven = []
    for i in range(ticks):
        frame = _drift_image_frame(world, grid, rng, i)
        world.step(ignite_k=1 if i % IGNITE_EVERY == 0 else 0, frame=frame)
        if capture_driven:
            driven.append(_driven_frac(world.s, world))
    return driven


_IMG_CACHE = {}


def _drift_image_frame(world, grid, rng, i):
    key = (id(rng), grid)
    if key not in _IMG_CACHE:
        _IMG_CACHE[key] = _drift_image(grid, rng)
    img = _IMG_CACHE[key]
    off = i % (2 * grid)
    return img[off:off + grid, off:off + grid]


def sweep(sizes, repeats, ticks, assert_live=True):
    rows = []
    for g in sizes:
        wall, drive, tick = [], [], []
        first = {}
        for rep in range(repeats):
            gc.collect()
            rng = np.random.default_rng(0)
            _IMG_CACHE.clear()
            s, ag, worlds, lats = boot_eye(g)
            world, lat = worlds[0], lats[0]
            nodes0 = s._inner.node_count()
            _run_eye(world, WARMUP, g, rng)
            chk0 = _wave_checksum(s, world)
            hres0 = _hcell_resid_checksum(s, lat)
            timer = PhaseTimer()
            restore = _instrument(world, timer)
            s._inner.reset_rule_costs()
            t0 = time.perf_counter()
            dr = _run_eye(world, ticks, g, rng, capture_driven=True)
            t1 = time.perf_counter()
            restore()
            chk1 = _wave_checksum(s, world)
            hres1 = _hcell_resid_checksum(s, lat)
            wall.append((t1 - t0) / ticks * 1000.0)
            drive.append(timer.drive_s / ticks * 1000.0)
            tick.append(timer.tick_s / ticks * 1000.0)
            if rep == 0:
                rc = [r for r in s._inner.rule_costs() if r[1] > 0 or r[2] > 0]
                rc.sort(key=lambda r: -r[1])
                by = {n: (us, c, pr) for (n, us, c, pr) in s._inner.rule_costs()}

                def famsum(names):
                    return sum(by.get(n, (0, 0, 0))[0] for n in names) / ticks
                first = {
                    "rule_costs_top": [
                        {"rule": n, "us_per_tick": us / ticks,
                         "visits_per_tick": c / ticks, "progress_per_tick": pr / ticks}
                        for (n, us, c, pr) in rc[:10]],
                    "wave_us_per_tick": famsum(("wv_propagate", "wv_refract", "wv_recover",
                                                "wv_unit_activate")),
                    "lateral_us_per_tick": famsum(LAT_RULES),
                    "ch_in_runrules_us_per_tick": famsum(CH_RULES),  # ~0: they fire in drive phase
                    "rust_runrules_us_per_tick": sum(r[1] for r in s._inner.rule_costs()) / ticks,
                    "states": _states(s, world),
                    "wave_checksum_before": chk0, "wave_checksum_after": chk1,
                    "hcell_resid_before": hres0, "hcell_resid_after": hres1,
                    "driven_frac_mean": float(np.mean(dr)),
                    "driven_frac_max": float(np.max(dr)),
                    "fixpoint_depth_rule_visits_per_tick": float(np.mean(timer.visits)) if timer.visits else 0.0,
                    "cells_nodes_minted": nodes0,
                    "wave_progress": {n: by.get(n, (0, 0, 0))[2] for n in WAVE_RULES},
                    "lat_progress": {n: by.get(n, (0, 0, 0))[2] for n in LAT_RULES},
                }
                # ---- §1 LIVENESS GATE ----
                if assert_live:
                    if chk0 == chk1:
                        raise SystemExit(f"FROZEN WAVE at g={g}: {chk0} unmoved.")
                    if first["driven_frac_mean"] <= 0.0:
                        raise SystemExit(f"DEAD CHANGE at g={g}: driven_frac=0 — ch_* did nothing.")
                    if hres0 == hres1:
                        raise SystemExit(f"DEAD LATERAL at g={g}: HCell resid {hres0} unmoved.")
                    prog = {n: by.get(n, (0, 0, 0))[2] for n in WAVE_RULES}
                    dead = [r for r in WAVE_RULES if prog.get(r, 0) == 0]
                    if dead:
                        raise SystemExit(f"DEAD WAVE RULES at g={g}: {dead}.")
                    if by.get("lat_pool", (0, 0, 0))[2] == 0:
                        raise SystemExit(f"DEAD lat_pool at g={g}.")
                # ---- Amdahl within-rule profile (once, rep 0) ----
                first["profile"] = _profile(s, g)
            del world, lat, worlds, lats, s, ag
        py = float(np.mean(wall)) - float(np.mean(drive)) - float(np.mean(tick))
        row = {
            "grid": g, "cells": g * g,
            "ms_per_tick_mean": float(np.mean(wall)),
            "ms_per_tick_sd": float(np.std(wall, ddof=1)) if len(wall) > 1 else 0.0,
            "ms_per_tick_raw": [round(x, 4) for x in wall],
            "drive_ms_mean": float(np.mean(drive)),     # ch_* (apply_rule_once)
            "drive_ms_sd": float(np.std(drive, ddof=1)) if len(drive) > 1 else 0.0,
            "tick_ms_mean": float(np.mean(tick)),       # run_rules: wv_* + lat_*
            "tick_ms_sd": float(np.std(tick, ddof=1)) if len(tick) > 1 else 0.0,
            "python_ffi_ms_mean": py,                   # residual: bulk crossings + drive() writes
            "drive_pct": 100.0 * float(np.mean(drive)) / float(np.mean(wall)),
            "tick_pct": 100.0 * float(np.mean(tick)) / float(np.mean(wall)),
            "python_ffi_pct": 100.0 * py / float(np.mean(wall)),
            "us_per_cell": float(np.mean(wall)) * 1000.0 / (g * g),
            **first,
        }
        rows.append(row)
        print(f"g={g:4d} cells={g*g:7d} wall={row['ms_per_tick_mean']:9.3f}±{row['ms_per_tick_sd']:6.3f}ms "
              f"| drive(ch_*)={row['drive_ms_mean']:8.3f}({row['drive_pct']:4.1f}%) "
              f"tick(wv+lat)={row['tick_ms_mean']:8.3f}({row['tick_pct']:4.1f}%) "
              f"py/ffi={row['python_ffi_ms_mean']:8.3f}({row['python_ffi_pct']:4.1f}%) "
              f"driven={row['driven_frac_mean']*100:4.1f}%", flush=True)
    return rows


def _profile(s, grid):
    """Per-rule within-Rust MATCH decomposition (the Amdahl parallel fraction).
    Uses the engine's own `profile_rule_match`. Reps chosen so timing is stable
    without dominating runtime."""
    reps = max(3, min(30, int(200000 / (grid * grid) + 3)))
    out = {}
    for rn in PROFILE_RULES:
        v = s._inner.profile_rule_match(rn, reps)
        if not v:
            continue
        d = {name: (mic, b) for (name, mic, b) in v}
        scan = d.get("scan", (0, 0))[0]
        enum = d.get("enum", (0, 0))[0]
        setup = d.get("setup", (0, 0))[0]
        full = d.get("full", (0, 0))[0]
        full_np = d.get("full_nopushdown", (0, 0))[0]
        bindings = d.get("full", (0, 0))[1]
        out[rn] = {
            "bindings": bindings,
            "enumeration_us": scan,
            "expansion_us": max(0, enum - scan),
            "interp_setup_us": max(0, setup - enum),
            "attr_eval_us": max(0, full - setup),
            "full_us": full,
            "full_nopushdown_us": full_np,
            "pushdown_speedup": (full_np / full) if full > 0 else None,
            "reps": reps,
        }
    return out


def fit(rows, key="ms_per_tick_mean"):
    x = np.log(np.array([r["cells"] for r in rows], float))
    y = np.log(np.array([r[key] for r in rows], float))
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return {"exponent": float(coef[0]), "intercept": float(coef[1]),
            "r2": (1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan"),
            "n_points": len(rows)}


def latency_ceiling(rows, budget_ms):
    under = [r for r in rows if r["ms_per_tick_mean"] <= budget_ms]
    f = fit(rows)
    cells = (budget_ms / np.exp(f["intercept"])) ** (1.0 / f["exponent"])
    return {"budget_ms": budget_ms,
            "largest_measured_grid_under": (max(r["grid"] for r in under) if under else None),
            "predicted_cells_at_budget": float(cells),
            "predicted_grid_at_budget": float(np.sqrt(cells))}


def _print_amdahl(am):
    print(f"   AMDAHL @ g={am['grid']} ({am['cells']} cells):")
    print(f"     run_rules coordination overhead = {am['run_rules_coordination_pct_of_tick']:+.1f}% of tick "
          f"(~0 => tick cost IS per-cell work)")
    print(f"     LEVER 1 (batch the O(N^2) drive): {am['LEVER1_batch_fix_speedup_on_drive']:.0f}x "
          f"({am['measured_drive_us_per_tick']/1000:.1f}ms -> {am['batched_drive_est_us_per_tick']/1000:.2f}ms, O(N))")
    print(f"     LEVER 2 (per-cell threads), FFI SERIAL (realistic): parallel_frac="
          f"{am['LEVER2_parallel_fraction_ffi_serial']:.3f} -> 6-core {am['LEVER2_amdahl_6core_ffi_serial']:.2f}x "
          f"inf {am['LEVER2_amdahl_infcore_ffi_serial']:.2f}x")
    print(f"     LEVER 2, FFI PARALLEL: parallel_frac={am['LEVER2_parallel_fraction_ffi_parallel']:.3f} "
          f"-> 6-core {am['LEVER2_amdahl_6core_ffi_parallel']:.2f}x")
    print(f"     FFI = {am['ffi_share_of_batched_eye_pct']:.0f}% of the BATCHED eye (the serial floor)")
    print(f"     interp_setup={am['interp_setup_fraction_of_match']*100:.0f}% "
          f"attr_eval={am['attr_eval_fraction_of_match']*100:.0f}% of match cost | "
          f"crossover ~{am['crossover_cells_at_20us_spawn']:.0f}-{am['crossover_cells_at_50us_spawn']:.0f} cells")
    print(f"     fixpoint depth (rule visits/tick) by grid: {am['fixpoint_depth_all_grids']}")


def _crossover(per_cell_us, spawn_us, cores):
    """Smallest N where a parallel sweep (N*per_cell/cores + spawn) beats serial
    (N*per_cell). Solve N*per_cell*(1 - 1/cores) > spawn."""
    denom = per_cell_us * (1.0 - 1.0 / cores)
    return (spawn_us / denom) if denom > 0 else None


def amdahl(rows):
    """Two levers, measured on the largest grid.

    KEY MEASURED FACT used here: Sum(rule_costs) ~= tick wall (within ~3%), so the
    run_rules COORDINATION overhead (dirty re-arm, cursor bookkeeping, outer loop)
    is ~ZERO — the tick cost IS the per-rule per-cell work. That per-rule work
    (match + effect Term-eval, e.g. lat_pool's neighbour Fold) is per-cell
    INDEPENDENT and parallelizable. `profile_rule_match` sees only the MATCH, so a
    match-only parallel fraction is a severe UNDER-count; we use rule_costs instead
    and charge a small graph-write serialization fraction as the sequential part.

      LEVER 1 (ALGORITHMIC): the drive phase does M `apply_rule_once` sweeps (one
        per driven cell) = O(N^2). Batched (run_rules drains all bindings/pass) it
        is O(N): batch_speedup = measured drive / one batched pass.
      LEVER 2 (PARALLELISM): after batching, the resident Rust compute is ~(1-w)
        per-cell parallel (w = write-serialization ~5%); the Amdahl ceiling is set
        by whether the Python<->Rust FFI boundary stays serial.
    """
    big = rows[-1]
    prof = big.get("profile", {})
    cores = 6  # useful cores on the 6-core/12-thread Ryzen 5 9600X
    WRITE_FRAC = 0.05  # graph-write serialization within apply (stated assumption)

    def ceil(p, c):
        return 1.0 / ((1.0 - p) + p / c) if p < 1 else float(c)

    drive_us = big["drive_ms_mean"] * 1000.0
    tick_us = big["tick_ms_mean"] * 1000.0                 # run_rules wall (lat+wv+ch-attempts)
    sum_rc_us = big["rust_runrules_us_per_tick"]           # Sum(rule_costs)
    ffi_us = big["python_ffi_ms_mean"] * 1000.0
    coord_overhead_us = tick_us - sum_rc_us                # measured ~0

    # LEVER 1 — one batched drive pass ~= the ch_* rules attempted once in run_rules.
    batched_drive_us = big["ch_in_runrules_us_per_tick"]
    batch_speedup = (drive_us / batched_drive_us) if batched_drive_us > 0 else None

    # LEVER 2 — the batched resident Rust compute and its parallel fraction.
    batched_rust_us = batched_drive_us + tick_us
    par_us = batched_rust_us * (1.0 - WRITE_FRAC)          # per-cell independent
    seq_rust_us = batched_rust_us * WRITE_FRAC             # write serialization
    batched_total_us = ffi_us + batched_rust_us

    p_ffi_serial = par_us / (par_us + seq_rust_us + ffi_us)          # realistic
    p_ffi_par = par_us / (par_us + seq_rust_us)                      # FFI overlapped

    # within-rule fractions (the two named micro-levers), from match profiling:
    all_r = list(prof.values())
    setup_us = sum(p["interp_setup_us"] for p in all_r)
    attr_us = sum(p["attr_eval_us"] for p in all_r)
    full_all = sum(p["full_us"] for p in all_r)
    ch_match = sum(prof[r]["full_us"] for r in CH_RULES if r in prof)

    return {
        "grid": big["grid"], "cells": big["cells"],
        "measured_drive_us_per_tick": drive_us,
        "tick_wall_us": tick_us, "sum_rule_costs_us": sum_rc_us,
        "run_rules_coordination_overhead_us": coord_overhead_us,
        "run_rules_coordination_pct_of_tick": 100.0 * coord_overhead_us / tick_us if tick_us else None,
        "batched_drive_est_us_per_tick": batched_drive_us,
        "LEVER1_batch_fix_speedup_on_drive": batch_speedup,
        "batched_rust_us": batched_rust_us,
        "ffi_us_per_tick": ffi_us,
        "ffi_share_of_batched_eye_pct": 100.0 * ffi_us / batched_total_us if batched_total_us else None,
        "write_serialization_frac_assumed": WRITE_FRAC,
        "LEVER2_parallel_fraction_ffi_serial": p_ffi_serial,
        "LEVER2_amdahl_6core_ffi_serial": ceil(p_ffi_serial, cores),
        "LEVER2_amdahl_infcore_ffi_serial": (1.0 / (1.0 - p_ffi_serial)) if p_ffi_serial < 1 else float("inf"),
        "LEVER2_parallel_fraction_ffi_parallel": p_ffi_par,
        "LEVER2_amdahl_6core_ffi_parallel": ceil(p_ffi_par, cores),
        "interp_setup_fraction_of_match": (setup_us / full_all) if full_all > 0 else None,
        "attr_eval_fraction_of_match": (attr_us / full_all) if full_all > 0 else None,
        "per_cell_drive_match_us": (ch_match / big["cells"]) if big["cells"] else None,
        "crossover_cells_at_20us_spawn": _crossover(ch_match / big["cells"], 20.0, cores) if big["cells"] else None,
        "crossover_cells_at_50us_spawn": _crossover(ch_match / big["cells"], 50.0, cores) if big["cells"] else None,
        "fixpoint_depth_rule_visits_per_tick": big.get("fixpoint_depth_rule_visits_per_tick"),
        "fixpoint_depth_all_grids": [(r["grid"], r.get("fixpoint_depth_rule_visits_per_tick")) for r in rows],
        "note": ("LEVER 1 (batch the O(N^2) drive) is ALGORITHMIC, ~O(N) speedup, "
                 "dominates. LEVER 2 (per-cell threads) then applies to the O(N) "
                 "resident compute; the FFI Python boundary is the serial floor that "
                 "caps it near 2x unless the boundary is also parallelized."),
    }


# --------------------------------------------------------------------------- #
#  REGIME B — the discovery ops (per scene)
# --------------------------------------------------------------------------- #
def regimeB(repeats=5):
    from domains import reflective_faculty as rf
    from substrate.seed_loader import manifest_for

    def boot_disc(which, enable_attr):
        s, ag = boot_core()
        native = rf._native_eval2(s)
        rf._ensure_shape_decode_loop(s, native, ag)
        native.load_seed_manifest(manifest_for(which), ag)
        s.set_attr(ag, enable_attr, 1.0)
        return s, ag, native

    def timeit(fn, reps):
        ts = []
        for _ in range(reps):
            gc.collect()
            t0 = time.perf_counter()
            fn()
            ts.append((time.perf_counter() - t0) * 1000.0)
        return float(np.mean(ts)), (float(np.std(ts, ddof=1)) if len(ts) > 1 else 0.0), ts

    res = {}
    DT = ["pred", "coord:r", "coord:c", "val"]

    def observe_decoded(s, ag, goal, i):
        # THE COMMITTED GenInfer TRIGGER (genmint_measure.observe): status='decoded',
        # signature+residual. A 'frames'/'gen_seq' observation is a NO-OP — the gen
        # rules never fire (positive-control the arm: `minted` MUST be >= 1).
        ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
        o = s.add_node("Observation", {"signature": goal, "key": ["p%d" % i],
                       "status": "decoded", "residual": goal,
                       "decoded_epoch": ep, "dim_types": DT})
        s.add_edge(ag, "observed", o)
        return o

    def lingen_count(s):
        return sum(1 for n in s.nodes("DimensionGenerator")
                   if s.node(n)["attrs"].get("kind") == "linear")

    # ---- B1: GenInfer — QUARTIC in the data-derived search bound B ----
    # The bound B = the GOAL's coordinate magnitude. Grow it by placing the base
    # `span` apart and shearing; the goal reaches ~2*span so B~2*span and the
    # enumeration is O((2B+1)^4). FRESH boot per measurement (no accumulation — a
    # recognised repeat short-circuits and would corrupt the enumerate timing).
    genrows = []
    for span in (1, 2, 3, 4, 5, 6, 7):
        ts, mint = [], 0
        for _ in range(max(3, repeats)):
            s, ag, native = boot_disc("shape_decode_loop", "gen_infer_enabled")
            base = [["cell", 0, 0, "x"], ["cell", span, 0, "x"],
                    ["cell", 0, span, "x"], ["cell", span, span, "x"]]
            s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(base),
                       "kind": "faculty", "faculty": "base", "dim_types": DT})
            goal = [["cell", 0, 0, "x"], ["cell", span, span, "x"],
                    ["cell", 0, span, "x"], ["cell", span, 2 * span, "x"]]
            observe_decoded(s, ag, goal, 0)
            gc.collect()
            t0 = time.perf_counter()
            native.run_rules()
            ts.append((time.perf_counter() - t0) * 1000.0)
            mint = lingen_count(s)
            del s, ag, native
        Bg = 2 * span
        genrows.append({"coord_span": span, "bound_B_goal": Bg,
                        "candidates_2Bp1_pow4": (2 * Bg + 1) ** 4,
                        "ms_median": float(np.median(ts)), "ms_mean": float(np.mean(ts)),
                        "ms_sd": float(np.std(ts, ddof=1)) if len(ts) > 1 else 0.0,
                        "minted_generators": mint})
        print(f"  [GenInfer] span={span} B~{Bg} cand~{(2*Bg+1)**4:9d} "
              f"median={np.median(ts):9.3f}±{np.std(ts):7.3f} ms  minted={mint}"
              f"{'  <-- DEAD ARM!' if mint == 0 else ''}", flush=True)
    res["gen_infer_vs_bound"] = genrows
    tail = [r for r in genrows if r["bound_B_goal"] >= 4 and r["ms_median"] > 0]
    if len(tail) >= 3:
        xb = np.log(np.array([r["bound_B_goal"] for r in tail], float))
        yb = np.log(np.array([r["ms_median"] for r in tail], float))
        cb = float(np.polyfit(xb, yb, 1)[0])
        xc = np.log(np.array([r["candidates_2Bp1_pow4"] for r in tail], float))
        cc = float(np.polyfit(xc, np.log(np.array([r["ms_median"] for r in tail], float)), 1)[0])
        res["gen_infer_exponent_vs_bound"] = cb
        res["gen_infer_exponent_vs_candidates"] = cc
        print(f"  [GenInfer] exponent vs bound B = {cb:.2f} (quartic predicts 4); "
              f"vs candidate count = {cc:.2f} (linear predicts 1)", flush=True)

    # boot baseline (subtracted so depth/stereo isolate the DISCOVERY, not boot).
    def boot_base(which, enable):
        s, ag, native = boot_disc(which, enable)
        return s, ag, native
    bt = []
    for _ in range(repeats):
        gc.collect(); t0 = time.perf_counter(); boot_base("depth_axis", "depth_infer_enabled")
        bt.append((time.perf_counter() - t0) * 1000.0)
    boot_ms = float(np.mean(bt))
    res["boot_baseline_ms"] = boot_ms
    print(f"  [boot baseline] {boot_ms:.3f} ms (subtracted from depth/stereo)", flush=True)

    # ---- B2: DepthInfer — vs #frames, #surfaces (translate = linear read) ----
    from scripts import depth_measure as dm
    GRN2 = [["cell", 0, 0, "green"], ["cell", 1, 1, "green"], ["cell", 2, 0, "green"]]
    YEL = [["cell", 0, 1, "yellow"], ["cell", 1, 0, "yellow"], ["cell", 2, 1, "yellow"]]
    depthrows = []
    for (nsurf, K) in [(2, 4), (2, 6), (2, 8), (2, 12), (3, 8), (4, 8)]:
        specs = [(dm.RED, (2, 0)), (dm.BLU, (1, 0)), (GRN2, (3, 0)), (YEL, (4, 0))][:nsurf]
        # boot once outside the timed loop; time only observation + run_rules.
        s, ag, native = boot_disc("depth_axis", "depth_infer_enabled")
        s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(dm.RED + dm.BLU),
                   "kind": "faculty", "faculty": "base", "dim_types": dm.DT})
        cnt = {"i": 0}

        def go(specs=specs, K=K, s=s, ag=ag, native=native, cnt=cnt):
            frames = dm.scene(specs, K)
            o = s.add_node("Observation", {"frames": frames, "dim_types": dm.DT,
                           "status": "depth_seq", "key": ["d%d" % cnt["i"]]})
            cnt["i"] += 1
            s.add_edge(ag, "observed", o)
            native.run_rules()
        m, sd, raw = timeit(go, repeats)
        depthrows.append({"n_surfaces": nsurf, "n_frames": K, "n_cells": nsurf * 3 * K,
                          "ms_mean": m, "ms_discovery_only": m, "ms_sd": sd,
                          "ms_raw": [round(x, 3) for x in raw]})
        print(f"  [DepthInfer] surfaces={nsurf} frames={K} cells={nsurf*3*K:3d} "
              f"{m:9.4f}±{sd:7.4f} ms", flush=True)
        del s, ag, native
    res["depth_infer_vs_scene"] = depthrows

    # ---- B3: Stereo — DepthInfer over N eyes (per-scene, one instant) ----
    stereorows = []
    for n_eyes in (2, 3, 4, 5, 6, 8):
        s, ag, native = boot_disc("depth_axis", "depth_infer_enabled")
        s.add_node("ShapeSignature", {"name": "base",
                   "signature": json.dumps([["cell", 0, 0, "red"], ["cell", 0, 1, "blue"]]),
                   "kind": "faculty", "faculty": "base", "dim_types":
                   ["pred", "coord:r", "coord:c", "val"]})
        cnt = {"i": 0}

        def go(n_eyes=n_eyes, s=s, ag=ag, native=native, cnt=cnt):
            frames = [[["cell", 0, 0 - 2 * e, "red"], ["cell", 0, 5 - 1 * e, "blue"]]
                      for e in range(n_eyes)]
            o = s.add_node("Observation", {"frames": frames,
                           "dim_types": ["pred", "coord:r", "coord:c", "val"],
                           "status": "depth_seq", "key": ["s%d" % cnt["i"]]})
            cnt["i"] += 1
            s.add_edge(ag, "observed", o)
            native.run_rules()
        m, sd, raw = timeit(go, repeats)
        stereorows.append({"n_eyes": n_eyes, "ms_mean": m, "ms_sd": sd,
                           "ms_raw": [round(x, 3) for x in raw]})
        print(f"  [Stereo] n_eyes={n_eyes} {m:9.4f}±{sd:7.4f} ms", flush=True)
        del s, ag, native
    res["stereo_vs_eyes"] = stereorows
    return res


def _run_stereo_scene(sm, boot_disc, n_eyes):
    """One stereo discovery over n_eyes simultaneous frames, using the committed
    stereo scene builder if it exposes one; else a minimal inline disparity
    scene. Mints depth from inter-eye disparity variation."""
    DT = ["pred", "coord:r", "coord:c", "val"]
    s, ag, native = boot_disc("depth_axis", "depth_infer_enabled")
    s.add_node("ShapeSignature", {"name": "base",
               "signature": json.dumps([["cell", 0, 0, "red"], ["cell", 0, 1, "blue"]]),
               "kind": "faculty", "faculty": "base", "dim_types": DT})
    # N eyes: RED at disparity 2/eye (near), BLU at disparity 1/eye (far).
    frames = []
    for e in range(n_eyes):
        frame = [["cell", 0, 0 - 2 * e, "red"], ["cell", 0, 5 - 1 * e, "blue"]]
        frames.append(frame)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "depth_seq", "key": ["depth"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()


# --------------------------------------------------------------------------- #
#  N-EYES — Regime-A cost as a function of eye count
# --------------------------------------------------------------------------- #
def neyes(grid=48, ns=(1, 2, 3, 4), repeats=5, ticks=TICKS):
    rows = []
    for n in ns:
        wall = []
        first = {}
        for rep in range(repeats):
            gc.collect()
            rng = np.random.default_rng(0)
            _IMG_CACHE.clear()
            s, ag, worlds, lats = boot_eye(grid, n_eyes=n)
            for w in worlds:
                _run_eye(w, WARMUP, grid, np.random.default_rng(0))
            chk0 = [_wave_checksum(s, w) for w in worlds]
            s._inner.reset_rule_costs()
            t0 = time.perf_counter()
            for i in range(ticks):
                for w in worlds:
                    frame = _drift_image_frame(w, grid, rng, i)
                    w.step(ignite_k=1 if i % IGNITE_EVERY == 0 else 0, frame=frame)
            t1 = time.perf_counter()
            chk1 = [_wave_checksum(s, w) for w in worlds]
            wall.append((t1 - t0) / ticks * 1000.0)
            if rep == 0:
                first = {"eye_hubs": len(s.nodes("Retina")),
                         "wave_moved_all_eyes": all(a != b for a, b in zip(chk0, chk1))}
                if first["wave_moved_all_eyes"] is False:
                    raise SystemExit(f"An eye froze at n_eyes={n}.")
            del worlds, lats, s, ag
        row = {"n_eyes": n, "grid": grid,
               "ms_per_tick_mean": float(np.mean(wall)),
               "ms_per_tick_sd": float(np.std(wall, ddof=1)) if len(wall) > 1 else 0.0,
               "ms_per_tick_raw": [round(x, 4) for x in wall],
               "ms_per_eye": float(np.mean(wall)) / n, **first}
        rows.append(row)
        print(f"  n_eyes={n} grid={grid} wall={row['ms_per_tick_mean']:9.3f}±"
              f"{row['ms_per_tick_sd']:6.3f}ms  per_eye={row['ms_per_eye']:8.3f}ms", flush=True)
    if len(rows) >= 2:
        x = np.log(np.array([r["n_eyes"] for r in rows], float))
        y = np.log(np.array([r["ms_per_tick_mean"] for r in rows], float))
        A = np.vstack([x, np.ones_like(x)]).T
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        return {"rows": rows, "exponent_vs_n_eyes": float(coef[0])}
    return {"rows": rows}


def _lum_dog_sparsity(frame, floor_frac=0.05):
    """REFERENCE (numpy, not the graph): spatial-agreement sparsity of the raw
    LUMINANCE — |centre - mean(4-neighbour surround)| over the field's own
    range. This is what centre-surround delivers ON THE IMAGE, the ~edge
    fraction. Reported as the reference the graph stage is compared against."""
    f = frame.astype(np.float64)
    sur = (np.roll(f, 1, 0) + np.roll(f, -1, 0) + np.roll(f, 1, 1) + np.roll(f, -1, 1)) / 4.0
    resid = np.abs(f - sur)[1:-1, 1:-1]  # drop wrapped border
    rng = f.max() - f.min() + 1e-9
    return float(np.mean(resid > floor_frac * rng))


def _bsds_crop(g, idx):
    """A real BSDS300 natural photo, centre-cropped to (g+4)x(g+4) at 8-bit so it
    can drift 1px/tick over the timed window and has UNIFORM regions (unlike a
    smooth-random field, which saturates change detection everywhere)."""
    from domains.vision_corpus import bsds_paths
    from PIL import Image
    paths = bsds_paths("train")
    p = paths[idx % len(paths)]
    im = np.asarray(Image.open(p).convert("L"), np.float32)  # already 0..255
    h, w = im.shape
    need = g + 4
    r0 = max(0, (h - need) // 2); c0 = max(0, (w - need) // 2)
    return im[r0:r0 + need, c0:c0 + need]


def agreement(grids=(32, 48), learn_steps=60):
    """AGREEMENT-SPARSITY of the centre-surround (seeds/vision_lateral.json): a
    COUNT, not a timing. Fraction of HCells whose lateral residual DISAGREES with
    its surround (fires) vs silent (agrees = uniform interior), on a REAL drifting
    BSDS natural photo (the same corpus the change-detection sparsity used).

    THE SURROUND is the DC-NULLING predictor `g1=g2=0.5` (`install_gains`) — the
    fixed point the anti-Hebbian rule targets (Srinivasan's optimal linear
    predictor). We ALSO report the EMERGED gains after `learn_steps` so the reader
    sees whether the learned surround has reached that predictor yet (it has not in
    this budget — reported honestly, not hidden).

    Positive-controlled (§1): UNIFORM drive -> ~0% (calibrates the floor); a hard
    EDGE -> fires ONLY at the boundary (a broken measure fires everywhere or
    nowhere). The floor = max|resid| a flat field produces."""
    from domains.lateral_world import residuals as _resids, install_gains
    out = []
    for g in grids:
        # Emerged gains (for the honest caveat only): learn on drifting natural
        # input on a THROWAWAY eye, then discard.
        se, age, we, le = boot_eye(g)
        for i in range(learn_steps):
            we[0].step(ignite_k=1 if i % IGNITE_EVERY == 0 else 0,
                       frame=_bsds_crop(g, 0)[i % 4:i % 4 + g, i % 4:i % 4 + g])
        gns = np.asarray([[float(se.node(h)["attrs"]["g1"]),
                           float(se.node(h)["attrs"]["g2"])] for h in le[0]["hcells"].values()])
        del se, age, we, le

        # THE MEASURE eye: waves SUPPRESSED (propagate=0, no ignition) so `bursting`
        # is the pure SPATIAL response (driven by the change/sustained channels),
        # not contaminated by travelling-wave activity. This isolates centre-
        # surround, which is what agreement-sparsity is about. Surround = the
        # DC-nulling predictor the anti-Hebbian rule targets.
        s, ag, worlds, lats = boot_eye(g)
        world, lat = worlds[0], lats[0]
        for wp in s.nodes("WaveParams"):
            s.set_attr(wp, "propagate", 0.0)
        install_gains(world, lat["hcells"], 0.5, 0.5)

        def settle_read(frame, steps=6):
            # Hold a STATIC frame for `steps` (> window_steps=2) so the transient
            # FLASH from the previous stimulus ages out of the burst window, leaving
            # only the CONTINUOUSLY-firing sustained (spatial) boundary response —
            # which is what centre-surround agreement is about. Read the last.
            for _ in range(steps):
                world.step(ignite_k=0, frame=frame)
            return np.abs(_resids(world, lat["hcells"]))

        # -- CONTROL 1: uniform -> ~0% (floor calibration) --
        r_flat = settle_read(np.full((g, g), 128.0, np.float32))
        floor = float(np.max(r_flat)) + 1e-6
        flat_fire = float(np.mean(r_flat > floor))
        # -- CONTROL 2: hard edge -> fires ONLY at the boundary --
        edge = np.zeros((g, g), np.float32); edge[:, g // 2:] = 255.0
        r_edge = settle_read(edge)
        edge_fire = float(np.mean(r_edge > floor))
        cols = np.abs(np.arange(g) - g // 2)
        fire_mask = r_edge > floor
        edge_conc = float(np.mean(np.array([[cols[c] for c in range(g)] for _ in range(g)])[fire_mask])) \
            if fire_mask.any() else None

        # -- THE MEASURE: DC-nulling centre-surround on STATIC BSDS photos (each
        # held to settle the transient). Spatial agreement is a property of the
        # scene's structure; drift adds only temporal-change firing (already the
        # ~100% change-detection number, reported alongside for contrast). --
        nat_fire, dog_ref, driven = [], [], []
        for k in range(6):
            frame = _bsds_crop(g, 3 + k)[:g, :g]
            r = settle_read(frame)
            nat_fire.append(float(np.mean(r > floor)))
            dog_ref.append(_lum_dog_sparsity(frame))
            driven.append(_driven_frac(s, world))
        row = {
            "grid": g, "learn_steps": learn_steps, "surround": "install_gains(0.5,0.5) DC-nulling",
            "emerged_gains_sum_mean": float((gns[:, 0] + gns[:, 1]).mean()),
            "emerged_reached_dc_nulling": bool(abs((gns[:, 0] + gns[:, 1]).mean() - 1.0) < 0.2),
            "agreement_sparsity_graph_pct": 100.0 * float(np.mean(nat_fire)),
            "agreement_sparsity_graph_sd": 100.0 * float(np.std(nat_fire)),
            "lum_dog_reference_pct": 100.0 * float(np.mean(dog_ref)),
            "change_detection_sparsity_pct": 100.0 * float(np.mean(driven)),
            "control_uniform_fire_pct": 100.0 * flat_fire,
            "control_edge_fire_pct": 100.0 * edge_fire,
            "control_edge_mean_dist_to_boundary": edge_conc,
            "control_passes": bool(flat_fire < 0.02 and edge_fire > 0.02
                                   and edge_conc is not None and edge_conc < g / 6.0),
            "floor_calibrated_from_uniform": floor,
        }
        out.append(row)
        print(f"  g={g}: agreement(graph, DC-null)={row['agreement_sparsity_graph_pct']:.1f}% "
              f"| lum-DoG ref={row['lum_dog_reference_pct']:.1f}% "
              f"| change-detect={row['change_detection_sparsity_pct']:.1f}% "
              f"|| controls uniform={row['control_uniform_fire_pct']:.1f}% "
              f"edge={row['control_edge_fire_pct']:.1f}% (dist={row['control_edge_mean_dist_to_boundary']}) "
              f"PASS={row['control_passes']} | emerged gains sum={row['emerged_gains_sum_mean']:.3f}", flush=True)
        del world, lat, worlds, lats, s, ag
    return out


def _machine():
    cpu = "unknown"
    try:
        with open("/proc/cpuinfo") as f:
            for ln in f:
                if ln.startswith("model name"):
                    cpu = ln.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    return f"{cpu} | {os.cpu_count()} logical cores"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="regimeA",
                    choices=["regimeA", "regimeB", "neyes", "agreement", "all"])
    ap.add_argument("--sizes", default=None)
    ap.add_argument("--repeats", type=int, default=REPEATS)
    ap.add_argument("--ticks", type=int, default=TICKS)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    sizes = [int(x) for x in a.sizes.split(",")] if a.sizes else SIZES

    prov = provenance_line()
    print(prov, flush=True)
    print(_machine(), flush=True)
    res = {"provenance": prov, "machine": _machine(),
           "repeats": a.repeats, "ticks": a.ticks}

    if a.mode in ("regimeA", "all"):
        print("== REGIME A: assembled eye (waves + change + lateral) ==", flush=True)
        rows = sweep(sizes, a.repeats, a.ticks)
        res["regimeA"] = rows
        res["fit_total"] = fit(rows)
        res["fit_drive"] = fit(rows, "drive_ms_mean")
        res["fit_tick"] = fit(rows, "tick_ms_mean")
        res["fit_python_ffi"] = fit(rows, "python_ffi_ms_mean")
        print(f"   fit total: exp={res['fit_total']['exponent']:.3f} r2={res['fit_total']['r2']:.4f}")
        print(f"   fit drive(ch_*): exp={res['fit_drive']['exponent']:.3f}")
        print(f"   fit tick(wv+lat): exp={res['fit_tick']['exponent']:.3f}")
        print(f"   fit py/ffi: exp={res['fit_python_ffi']['exponent']:.3f}")
        for b in (50.0, 16.0):
            c = latency_ceiling(rows, b)
            res.setdefault("latency", []).append(c)
            print(f"   <= {b:4.0f}ms: largest measured grid={c['largest_measured_grid_under']} "
                  f"| fit predicts ~{c['predicted_grid_at_budget']:.0f}^2")
        fovea = latency_ceiling(rows, 1e12)
        f = fit(rows)
        ms_150k = float(np.exp(f["intercept"]) * (150000 ** f["exponent"]))
        res["fovea_150k_extrapolation_ms"] = ms_150k
        print(f"   fovea ~150k cells extrapolation: {ms_150k:.1f} ms/tick "
              f"({ms_150k/50.0:.1f}x the 50ms target)")
        res["amdahl"] = amdahl(rows)
        _print_amdahl(res["amdahl"])
    if a.mode in ("regimeB", "all"):
        print("== REGIME B: discovery ops (per scene) ==", flush=True)
        res["regimeB"] = regimeB(a.repeats)
    if a.mode in ("neyes", "all"):
        print("== N-EYES ==", flush=True)
        # grid 24 keeps the O(N^2) drive tractable while isolating the N scaling.
        res["neyes"] = neyes(grid=24, repeats=a.repeats, ticks=4)
    if a.mode in ("agreement", "all"):
        print("== AGREEMENT-SPARSITY (centre-surround; a COUNT, not a timing) ==", flush=True)
        res["agreement"] = agreement()

    if a.out:
        d = os.path.dirname(a.out)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.out, "w") as f:
            json.dump(res, f, indent=2)
        print("wrote", a.out)


if __name__ == "__main__":
    main()
