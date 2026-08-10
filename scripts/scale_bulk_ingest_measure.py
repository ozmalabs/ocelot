"""SCALE — ATTRIBUTE the 16.8 us/cell constant, then attack the batchable part.

Pre-registration: `VISION_SCALE_BULK_INGEST_PREREG.md` (committed BEFORE this
ran). Block 132000-132999. Extends 131000 (`scale_wall_push_measure`), which
proved the O(N^2) wall is SPENT (batched drive LINEAR, ~50x50) and NAMED the
residual as the linear per-cell constant (16.8 us/cell) + 11 idle cores, without
measuring how much of that constant a bulk boundary handoff can buy.

*** THIS IS A MEASURING INSTRUMENT + a NEW OPT-IN adapter path. ***
The bulk ingest is gated on `world.bulk_ingest` (DEFAULT OFF, the `detect_cycles`
precedent); with it OFF the committed per-cell path is byte-for-byte unchanged.
The Rust side adds ONE bulk method (`set_attr_each`), no Term, no seed.

TWO THINGS THIS DOES, IN ORDER (the prereg's load-bearing sequence):
  1. ATTRIBUTION FIRST -- decompose the per-tick wall into phases
     (luminance ingest / batched drive / wave tick / bookkeeping), on the
     COMMITTED batched drive, so the 16.8 us/cell splits into
     FFI-per-cell-write vs irreducible Rust compute vs glue. The batchable
     luminance share BOUNDS, by Amdahl, the MAXIMUM the bulk handoff can buy.
  2. THE LEVER -- measure the per-cell vs bulk luminance ingest: new per-cell
     constant, new ceiling (~50x50 -> N x N), new QVGA/1080p, BYTE-IDENTICAL.

METHOD reused verbatim from 131000 (`scale_wall_push_measure`, SWP) and its
imports (`scale_split_measure` SS, `batch_apply_measure` BA) -- a
reimplementation would be a second instrument, and this arc has caught eleven
inert ones. ADDED here and ONLY here: the per-phase timing decomposition and the
per-cell/bulk luminance arm.

TIMING RIGOR (PROTOCOL timing): loadavg at start AND end INSIDE this process;
fresh boot per trial; gc.collect before each timed region; WARMUP discarded; T
trials/point; median + IQR + bootstrap 95% CI; NO single-shot verdict.
Deterministic (WaveWorld seed 0, frame seed 11) -> consumes NO block seed.

USAGE
    PYTHONPATH=runners/dsl/python:. python scripts/scale_bulk_ingest_measure.py \
        --out results/scale_bulk_ingest.json
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
# This rung ADDS RUST -- without the preamble the process would measure the
# canonical binary and attribute numbers to source that did not produce them.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402
from substrate_rs import _native  # noqa: E402

import domains.seed_registry  # noqa: F401,E402

import scripts.scale_split_measure as SS  # noqa: E402
import scripts.batch_apply_measure as BA  # noqa: E402
import scripts.scale_wall_push_measure as SWP  # noqa: E402

AUDIT = _native.Substrate

GRIDS = [12, 16, 24, 32, 48, 64]
TRIALS = {12: 9, 16: 9, 24: 9, 32: 7, 48: 5, 64: 5}
TICKS = 20      # SS.TICKS
WARMUP = 5      # SS.WARMUP
RT_BUDGET_MS = 1000.0 / 23.976   # 41.7 ms/tick: 23.976 fps, the video probe's budget


def _loadavg():
    try:
        return list(os.getloadavg())
    except OSError:
        return None


def _phase_timed_run(world, ticks, g, frames):
    """Run `ticks` timed steps, accumulating per-PHASE wall time by wrapping the
    instance methods (measurement-only; the committed code is untouched).

    Phases of ONE step():
      drive_incl  = drive(frame)          -- luminance ingest + _drive_phase
      drivephase  = _drive_phase()        -- the batched rule application
      lumwrite    = drive_incl - drivephase  -- the per-cell luminance write
      tick        = s.tick(200_000)       -- the wave rules (Rust compute)
      markbursts  = _mark_bursts(st)      -- bulk bookkeeping
      step_total  = step()                -- the whole tick
      other       = step_total - drive_incl - tick - markbursts  -- recruit/driven glue
    """
    acc = {"drive_incl": 0.0, "drivephase": 0.0, "tick": 0.0,
           "markbursts": 0.0, "step_total": 0.0}
    o_drive = world.drive
    o_dphase = world._drive_phase
    o_tick = world.s.tick
    o_mb = world._mark_bursts
    o_step = world.step

    def w_drive(*a, **k):
        t = time.perf_counter(); r = o_drive(*a, **k); acc["drive_incl"] += time.perf_counter() - t; return r

    def w_dphase(*a, **k):
        t = time.perf_counter(); r = o_dphase(*a, **k); acc["drivephase"] += time.perf_counter() - t; return r

    def w_tick(*a, **k):
        t = time.perf_counter(); r = o_tick(*a, **k); acc["tick"] += time.perf_counter() - t; return r

    def w_mb(*a, **k):
        t = time.perf_counter(); r = o_mb(*a, **k); acc["markbursts"] += time.perf_counter() - t; return r

    def w_step(*a, **k):
        t = time.perf_counter(); r = o_step(*a, **k); acc["step_total"] += time.perf_counter() - t; return r

    world.drive = w_drive
    world._drive_phase = w_dphase
    world.s.tick = w_tick
    world._mark_bursts = w_mb
    world.step = w_step
    try:
        k = SS._ignite_k(g, "constant")
        for i in range(ticks):
            f = frames[i % len(frames)]
            world.step(ignite_k=k if i % SS.IGNITE_EVERY == 0 else 0, frame=f)
    finally:
        world.drive = o_drive
        world._drive_phase = o_dphase
        world.s.tick = o_tick
        world._mark_bursts = o_mb
        world.step = o_step

    per = {kk: vv / ticks * 1000.0 for kk, vv in acc.items()}   # ms/tick
    per["lumwrite"] = per["drive_incl"] - per["drivephase"]
    per["other"] = per["step_total"] - per["drive_incl"] - per["tick"] - per["markbursts"]
    return per


def _build(g, bulk):
    s, ag, world = BA.build_world(g, batch=True)   # committed batched drive, BOTH arms
    world.bulk_ingest = bool(bulk)
    return s, ag, world


def _timed_trial(g, *, bulk):
    """One fresh boot; WARMUP untimed; TICKS timed. Returns (ms_per_tick,
    counters, state_record) after the identical deterministic schedule."""
    gc.collect()
    s, ag, world = _build(g, bulk)
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
    if chk0 == chk1:
        raise SystemExit(f"FROZEN WORLD g={g} bulk={bulk}: {chk0} unmoved.")
    if c["cand_enum"] == 0:
        raise SystemExit(f"DEAD INSTRUMENT g={g} bulk={bulk}: 0 cand_enum.")
    assert c["cand_enum_first"] + c["cand_enum_repeat"] == c["cand_enum"], (g, c)
    assert (c["cand_enum_scan"] + c["cand_enum_local"] + c["cand_enum_hinted"]
            == c["cand_enum"]), (g, c)
    assert c["where_evals_first"] + c["where_evals_repeat"] == c["where_evals"], (g, c)

    rec = BA.state_record(s, world)
    del world, s, ag
    return ms, c, rec


def _phase_trial(g, *, bulk):
    """A SEPARATE fresh-boot trial that measures per-phase wall time (the
    wrappers add ~0.3us/call overhead, so they are NOT used in the headline
    ms/tick trial -- only for the attribution)."""
    gc.collect()
    s, ag, world = _build(g, bulk)
    frames = SS._frames(g)
    SS._run(world, WARMUP, g, "constant", frames)
    per = _phase_timed_run(world, TICKS, g, frames)
    del world, s, ag
    return per


def sweep_arm(arm, grids):
    bulk = arm == "bulk"
    rows, states = [], {}
    for g in grids:
        T = TRIALS[g]
        mss, digests = [], []
        for t in range(T):
            ms, c, rec = _timed_trial(g, bulk=bulk)
            mss.append(ms)
            digests.append(BA.state_digest(rec))
            if t == 0:
                rec0 = rec
        det_ok = len(set(digests)) == 1
        med = float(statistics.median(mss))
        lo, hi = SWP._bootstrap_ci(mss)
        q1, q3 = float(np.percentile(mss, 25)), float(np.percentile(mss, 75))
        # phase decomposition: median over 3 phase-trials (wrapper overhead is
        # common-mode; the SHARE is what we read)
        phases = [_phase_trial(g, bulk=bulk) for _ in range(3)]
        phase_med = {k: float(statistics.median([p[k] for p in phases]))
                     for k in phases[0]}
        rows.append({
            "grid": g, "cells": g * g, "arm": arm, "bulk": bulk, "trials": T,
            "ms_per_tick_raw": [round(x, 5) for x in mss],
            "ms_per_tick_median": med,
            "ms_per_tick_ci95": [lo, hi], "ms_per_tick_iqr": [q1, q3],
            "ms_per_tick_min": float(min(mss)), "ms_per_tick_max": float(max(mss)),
            "us_per_cell_median": med * 1000.0 / (g * g),
            "ci95_frac_of_median": (hi - lo) / 2.0 / med,
            "state_digest": digests[0],
            "determinism_across_trials_ok": det_ok,
            "phase_ms_per_tick_median": phase_med,
            "phase_us_per_cell": {k: v * 1000.0 / (g * g) for k, v in phase_med.items()},
        })
        states[g] = rec0
        print(f"  [{arm}] g={g:3d} cells={g*g:6d} T={T} "
              f"median={med:9.4f} ms/tick  CI95=[{lo:.4f},{hi:.4f}] "
              f"({100*(hi-lo)/2/med:+.3f}% ) us/cell={med*1000/(g*g):7.3f} "
              f"det_ok={det_ok}", flush=True)
        pm = phase_med
        print(f"        phase ms/tick: lumwrite={pm['lumwrite']:.4f} "
              f"drivephase={pm['drivephase']:.4f} tick={pm['tick']:.4f} "
              f"markbursts={pm['markbursts']:.4f} other={pm['other']:.4f} "
              f"| step={pm['step_total']:.4f}", flush=True)
    return rows, states


def attribution(percell_rows, bulk_rows):
    """Decompose the per-tick constant at the LARGEST grid, and state the Amdahl
    bound the batchable luminance share implies."""
    pc = percell_rows[-1]
    bk = bulk_rows[-1]
    g = pc["grid"]; cells = pc["cells"]
    ph_pc = pc["phase_ms_per_tick_median"]
    ph_bk = bk["phase_ms_per_tick_median"]
    step_pc = ph_pc["step_total"]
    # fractions of the per-tick wall (per-cell arm = the committed default)
    frac = {k: ph_pc[k] / step_pc for k in
            ("lumwrite", "drivephase", "tick", "markbursts", "other")}
    # the batchable part of the luminance write: what bulk removes from it
    lumwrite_saved = ph_pc["lumwrite"] - ph_bk["lumwrite"]
    amdahl_max_frac = lumwrite_saved / step_pc            # max whole-tick speedup fraction
    # attribution mapping to the prereg's (a)/(b)/(c)/(d)
    return {
        "grid": g, "cells": cells,
        "step_ms_per_tick_percell": step_pc,
        "step_us_per_cell_percell": step_pc * 1000.0 / cells,
        "phase_ms_per_tick_percell": ph_pc,
        "phase_ms_per_tick_bulk": ph_bk,
        "phase_us_per_cell_percell": {k: v * 1000.0 / cells for k, v in ph_pc.items()},
        "phase_fraction_of_tick_percell": frac,
        # (a)+(b): the per-cell luminance ingest (FFI + Python-side write)
        "lumwrite_fraction_of_tick": frac["lumwrite"],
        "lumwrite_us_per_cell_percell": ph_pc["lumwrite"] * 1000.0 / cells,
        "lumwrite_us_per_cell_bulk": ph_bk["lumwrite"] * 1000.0 / cells,
        # (c): irreducible Rust per-cell compute = drivephase + tick
        "irreducible_rust_fraction_of_tick": frac["drivephase"] + frac["tick"],
        "irreducible_rust_us_per_cell": (ph_pc["drivephase"] + ph_pc["tick"]) * 1000.0 / cells,
        # (d): bookkeeping glue = markbursts + other
        "glue_fraction_of_tick": frac["markbursts"] + frac["other"],
        # THE AMDAHL BOUND
        "lumwrite_saved_ms_per_tick": lumwrite_saved,
        "amdahl_max_wholetick_speedup_fraction": amdahl_max_frac,
        "amdahl_predicted_max_speedup_x": 1.0 / (1.0 - amdahl_max_frac) if amdahl_max_frac < 1 else float("inf"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grids", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    grids = [int(x) for x in a.grids.split(",")] if a.grids else GRIDS

    prov = provenance_line()
    load0 = _loadavg()
    print(prov, flush=True)
    print(SS._machine(), flush=True)
    print(f"loadavg at start: {load0}", flush=True)
    print(f"native has set_attr_each: {hasattr(_native.Substrate, 'set_attr_each')}", flush=True)

    res = {"provenance": prov, "machine": SS._machine(), "grids": grids,
           "trials_per_grid": {str(g): TRIALS[g] for g in grids},
           "ticks": TICKS, "warmup": WARMUP, "rt_budget_ms": RT_BUDGET_MS,
           "cpu_governor": SWP._governor(),
           "native_has_set_attr_each": hasattr(_native.Substrate, "set_attr_each"),
           "seed_batch_flags_AS_COMMITTED": BA._seed_batch_flags(),
           "loadavg_at_start": load0, "block_seeds_drawn": 0,
           "note_deterministic": "WaveWorld seed 0 + frame seed 11; no block seed consumed"}

    print("== PERCELL arm (bulk_ingest=False -> the committed per-cell luminance loop) ==", flush=True)
    pc_rows, pc_states = sweep_arm("percell", grids)
    print("== BULK arm (bulk_ingest=True -> one-crossing set_attr_each ingest) ==", flush=True)
    bk_rows, bk_states = sweep_arm("bulk", grids)

    res["percell"] = {"rows": pc_rows}
    res["bulk"] = {"rows": bk_rows}

    fit_pc = SWP.fit_median(pc_rows)
    fit_bk = SWP.fit_median(bk_rows)
    res["fit_percell_wall"] = fit_pc
    res["fit_bulk_wall"] = fit_bk
    res["ceiling_percell"] = SWP.ceiling(fit_pc)
    res["ceiling_bulk"] = SWP.ceiling(fit_bk)

    # per-grid speedup
    speed = []
    bk_by = {r["grid"]: r for r in bk_rows}
    for r in pc_rows:
        b = bk_by[r["grid"]]
        speed.append({"grid": r["grid"], "cells": r["cells"],
                      "percell_ms": r["ms_per_tick_median"], "bulk_ms": b["ms_per_tick_median"],
                      "speedup": r["ms_per_tick_median"] / b["ms_per_tick_median"],
                      "percell_us_per_cell": r["us_per_cell_median"],
                      "bulk_us_per_cell": b["us_per_cell_median"]})
    res["speedup_per_grid"] = speed

    # attribution + Amdahl
    res["attribution"] = attribution(pc_rows, bk_rows)

    # byte-identity (percell vs bulk)
    res["byte_identity"] = SWP.byte_identity(pc_states, bk_states)
    res["byte_identity_ALL_EQUAL"] = bool(all(
        b["digests_equal"] and b["n_mismatched_cells"] == 0 for b in res["byte_identity"]))

    # projections
    res["projections_percell"] = {lbl: SWP.project(fit_pc, n) for n, lbl in
                                  ((4096, "64x64"), (76800, "320x240"), (2073600, "1920x1080"))}
    res["projections_bulk"] = {lbl: SWP.project(fit_bk, n) for n, lbl in
                               ((4096, "64x64"), (76800, "320x240"), (2073600, "1920x1080"))}

    load1 = _loadavg()
    res["loadavg_at_end"] = load1

    att = res["attribution"]
    print("\n== RESULT ==", flush=True)
    print(f"  ATTRIBUTION @ {att['grid']}^2 (per-tick {att['step_us_per_cell_percell']:.2f} us/cell):", flush=True)
    for k in ("lumwrite", "drivephase", "tick", "markbursts", "other"):
        print(f"    {k:11s} {att['phase_fraction_of_tick_percell'][k]*100:6.2f}% "
              f"= {att['phase_us_per_cell_percell'][k]:7.3f} us/cell", flush=True)
    print(f"  (a)+(b) luminance-write share = {att['lumwrite_fraction_of_tick']*100:.2f}%  "
          f"(c) irreducible Rust = {att['irreducible_rust_fraction_of_tick']*100:.2f}%  "
          f"(d) glue = {att['glue_fraction_of_tick']*100:.2f}%", flush=True)
    print(f"  AMDAHL max whole-tick speedup from bulk ingest = "
          f"x{att['amdahl_predicted_max_speedup_x']:.3f} "
          f"(saves {att['amdahl_max_wholetick_speedup_fraction']*100:.2f}% of the tick)", flush=True)
    print(f"  PERCELL wall exp {fit_pc['exponent']:.3f} (r2 {fit_pc['r2']:.4f}) -> "
          f"ceiling {res['ceiling_percell']['affordable_grid']:.1f}^2", flush=True)
    print(f"  BULK    wall exp {fit_bk['exponent']:.3f} (r2 {fit_bk['r2']:.4f}) -> "
          f"ceiling {res['ceiling_bulk']['affordable_grid']:.1f}^2", flush=True)
    print(f"  ceiling push: {res['ceiling_percell']['affordable_grid']:.1f}^2 -> "
          f"{res['ceiling_bulk']['affordable_grid']:.1f}^2 "
          f"(x{res['ceiling_bulk']['affordable_grid']/res['ceiling_percell']['affordable_grid']:.3f}/side)", flush=True)
    print(f"  largest-grid speedup = x{speed[-1]['speedup']:.3f} "
          f"({speed[-1]['percell_us_per_cell']:.2f} -> {speed[-1]['bulk_us_per_cell']:.2f} us/cell)", flush=True)
    print(f"  QVGA percell {res['projections_percell']['320x240']:.1f} ms -> bulk "
          f"{res['projections_bulk']['320x240']:.1f} ms | 1080p percell "
          f"{res['projections_percell']['1920x1080']/1000:.1f} s -> bulk "
          f"{res['projections_bulk']['1920x1080']/1000:.1f} s", flush=True)
    print(f"  BYTE-IDENTITY all grids equal = {res['byte_identity_ALL_EQUAL']}", flush=True)
    print(f"  loadavg start={load0} end={load1}", flush=True)

    d = os.path.dirname(a.out)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(res, fh, indent=2, default=str)
    print("wrote", a.out, flush=True)


if __name__ == "__main__":
    main()
