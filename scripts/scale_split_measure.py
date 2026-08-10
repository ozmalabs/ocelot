"""SCALE SPLIT — apportion the measured wall between FFI, comparison and redundancy.

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***

Pre-registration: `VISION_SCALE_SPLIT_PREREG.md`, committed BEFORE this ran.

THE QUESTION. `VISION_VIDEO_PROBE_RESULTS.md` measured exponent 1.887 on real
frames and named the cause "PyO3 then O(N^2)" -- two causes, plus a plausible
third. They have DIFFERENT FIXES:

    F  PyO3/FFI boundary        -> an async Rust-resident collapse loop
    C  genuine comparison       -> a proposal net (distillation)
    R  redundant recomputation  -> foveated / incremental evaluation

Distilling a net would be an expensive mistake if half the wall were FFI.

EVERY HEADLINE HERE IS A COUNT, NOT A DURATION. A concurrent rung is on this
machine. `ENGINE_WINNER_VALUE_RESULTS.md` reported counted operations and
REFUSED wall-clock after measuring two verdict-identical runs differing by 85 s
(1.66x) on load alone; `VISION_VIDEO_PROBE_RESULTS.md` §0.1 recorded the same
lesson the hard way. Counts are load-independent, reproducible to the integer,
and attributed by a rule fixed in the prereg before they were taken.

WHY THE GATES BELOW EXIST (PROTOCOL §1; this arc has caught ELEVEN inert
instruments). The counters are gated red-then-green before any share is
reported: zero-when-off, a known-count positive control, byte-identical
determinism across runs, conservation of both split axes, and a check that
the audit does not move the exponent it measures.

NOTE ON WHERE THE GATES LIVE. `runners/dsl/Cargo.toml` sets pyo3's
`extension-module` UNCONDITIONALLY, so `cargo test` cannot link this crate --
the `#[cfg(test)]` tests in `scale_audit.rs` are unrunnable in this tree (a
PRE-EXISTING property, not something this rung introduced). The gates are
therefore run HERE, against the SHIPPED engine, which is the stronger place
for them anyway: it tests the path that actually produces the numbers.

USAGE
    python scripts/scale_split_measure.py --mode all --out results/scale_split.json
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: a non-pytest entrypoint pins its OWN tree's engine.
# MUST precede any `substrate_rs` import. This rung ADDS RUST, so this is not a
# formality -- without it the process would measure the canonical tree's binary
# and every counter would read zero.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402
from substrate_rs import _native  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.lateral_world import (  # noqa: E402
    add_lateral_retina, set_lat_params)

# The prereg's grid list: 6 points over a 28x range in cells (the video probe
# fitted 4 points over 7.1x).
SIZES = [12, 16, 24, 32, 48, 64]
WARMUP = 5
TICKS = 20
IGNITE_EVERY = 5

AUDIT = _native.Substrate

# --- the three buckets, exactly as fixed by the prereg -----------------------
#
# Every counted operation is charged to EXACTLY ONE bucket. `graph_writes` is
# charged to NOTHING -- a Rust-resident loop would perform those too, so folding
# them anywhere would flatter that bucket. This mapping is the prereg's §3 and
# is NOT adjustable after the fact (§5).
BUCKET = {
    "F": ("ffi_calls", "ffi_items", "ffi_pyobjects"),
    "C": ("cand_enum_first", "where_evals_first"),
    "R": ("cand_enum_repeat", "where_evals_repeat",
          "bindings_cloned", "apply_probe_rollbacks"),
}


def counters() -> dict:
    return dict(AUDIT.scale_audit_snapshot())


def buckets(c: dict) -> dict:
    out = {k: sum(c[n] for n in names) for k, names in BUCKET.items()}
    out["total"] = out["F"] + out["C"] + out["R"]
    return out


# Number of `ch_*` drive rules the adapter's `_drive_phase` loops over. Read
# from the seed rather than asserted: the irreducible floor is "one enumeration
# per drive rule per tick", so this count must FALL OUT of the seed, not be
# chosen (PROTOCOL §13).
def _n_drive_rules() -> int:
    import json as _j
    with open(os.path.join(ROOT, "seeds", "vision_change.json")) as f:
        return len(_j.load(f).get("rules", []))


N_DRIVE_RULES = _n_drive_rules()


def reattributed(c: dict, ticks: int = TICKS) -> dict:
    """THE CROSS-EPOCH REDUNDANCY, ATTRIBUTED — reported SEPARATELY, exactly as
    the prereg §3 requires, and NEVER folded into the positional R.

    `_drive_phase` runs `while nat.apply_rule_once(idx): pass` per drive rule.
    Each call re-derives the binding set from scratch, so to apply M bindings it
    performs M full enumerations. The IRREDUCIBLE floor is ONE enumeration per
    drive rule per tick -- which is what the engine's own `batch` flag already
    delivers for rules that set it, and which none of the `vision_change` rules
    do. Everything above that floor is avoidable work.

    The floor falls out of the seed's own rule count and the tick count; nothing
    is chosen here."""
    ao = c["cand_enum_apply_once"]
    calls = c["epochs_apply_once"]
    floor_calls = N_DRIVE_RULES * ticks
    if calls <= floor_calls or ao == 0:
        return {"cand_enum_apply_once": ao, "apply_once_calls": calls,
                "floor_calls": floor_calls, "redundant_frac": 0.0,
                "redundant_cand_enum": 0}
    frac = 1.0 - floor_calls / calls
    return {"cand_enum_apply_once": ao, "apply_once_calls": calls,
            "floor_calls": floor_calls, "redundant_frac": frac,
            "redundant_cand_enum": int(ao * frac)}


def shares_reattributed(c: dict) -> dict:
    """The split with cross-epoch drive-phase redundancy moved from C to R.

    This is NOT a re-definition of the buckets after seeing the numbers (§5 --
    forbidden). The prereg fixed BOTH: the positional split (headline) AND the
    requirement that cross-epoch re-enumeration be counted and reported
    separately, with R declared a LOWER BOUND. This is that second report."""
    b = buckets(c)
    red = reattributed(c)["redundant_cand_enum"]
    red = min(red, b["C"])
    f, cc, r = b["F"], b["C"] - red, b["R"] + red
    t = f + cc + r
    return {"F": 100.0 * f / t, "C": 100.0 * cc / t, "R": 100.0 * r / t}


def shares(c: dict) -> dict:
    b = buckets(c)
    t = b["total"]
    return {k: (100.0 * b[k] / t if t else float("nan")) for k in ("F", "C", "R")}


def _boot_waves(g):
    """WAVES ONLY -- the cheap arm. `scale_wall_measure.py`'s sweep object."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    return s, ag, None


def _boot_eye(g, *, change=1.0, sustain=1.0, lateral=1.0):
    """THE ASSEMBLED EYE -- byte-for-byte the boot in
    `video_probe_measure.py::boot_eye` (itself byte-for-byte
    `assembled_eye_scale.py::boot_eye`).

    THIS IS THE OBJECT THAT PRODUCED 1.887, and getting it right is the whole
    scope of the claim. My first cut booted waves-only and measured 10 ms/tick
    at 64^2 where the video probe measured 331 ms/tick at 32^2 -- a ~100x
    discrepancy that would have made every share below a share of a DIFFERENT
    workload. The prereg said "the exact object §S5 fitted"; this is it.
    """
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral"])
    return s, ag, "eye"


def _ignite_k(g, regime):
    return 1 if regime == "constant" else max(1, round(g * g / 256))


def _run(world, ticks, g, regime, frames=None):
    k = _ignite_k(g, regime)
    for i in range(ticks):
        f = frames[i % len(frames)] if frames is not None else None
        world.step(ignite_k=k if i % IGNITE_EVERY == 0 else 0, frame=f)


def _checksum(s, world):
    """The honest liveness witness. `tick()`'s return is NOT a firing count --
    it reads 1-4 while hundreds of cells change state (scale_wall_measure.py's
    module docstring records that error). A frozen world is infinitely fast and
    scales beautifully; that is the exact failure this arc keeps catching."""
    act, lb = 0, 0.0
    for n in world.cells.values():
        at = s.node(n)["attrs"]
        if at.get("state") == "active":
            act += 1
        lb += float(at.get("last_burst", -999.0))
    return (act, round(lb, 3))


def _frames(g, n=8, seed=11):
    """A SMOOTH drifting field -- a moving aperture, not fresh noise per tick.
    Fresh noise would be maximally non-sparse BY CONSTRUCTION and would answer
    a question nobody asked (`scale_wall_measure.py::sparsity`'s standing note)."""
    rng = np.random.default_rng(seed)
    base = rng.random((g + n + 2, g + n + 2)).astype(np.float32)
    for _ in range(6):
        base = (base + np.roll(base, 1, 0) + np.roll(base, -1, 0)
                + np.roll(base, 1, 1) + np.roll(base, -1, 1)) / 5.0
    return [np.ascontiguousarray(base[i:i + g, i:i + g]) for i in range(n)]


# ---------------------------------------------------------------------------
# THE COUNTED SWEEP
# ---------------------------------------------------------------------------

def counted_point(g, regime, *, driven=False, fovea_radius=0, arm="eye",
                  assert_live=True):
    """One grid, one regime: run the committed drive and read the counters.

    Liveness is a HARD GATE per point, not a hope."""
    gc.collect()
    if arm == "eye":
        s, ag, _ = _boot_eye(g)
        world = WaveWorld(s, h=g, w=g, seed=0, fovea_radius=fovea_radius)
        add_lateral_retina(world)
        wp = s.nodes("WaveParams")[0]
        s.set_attr(wp, "propagate", 1.0)
        for cp in s.nodes("ChangeParams"):
            s.set_attr(cp, "change", 1.0)
            s.set_attr(cp, "sustain", 1.0)
        set_lat_params(world, lateral=1.0)
    else:
        s, ag, _ = _boot_waves(g)
        world = WaveWorld(s, h=g, w=g, seed=0, fovea_radius=fovea_radius)
    frames = _frames(g) if driven else None
    _run(world, WARMUP, g, regime, frames)
    chk0 = _checksum(s, world)

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    s._inner.reset_rule_costs()
    t0 = time.perf_counter()
    _run(world, TICKS, g, regime, frames)
    wall_ms = (time.perf_counter() - t0) / TICKS * 1000.0
    AUDIT.scale_audit_set_enabled(False)
    c = counters()

    chk1 = _checksum(s, world)
    if assert_live and chk0 == chk1:
        raise SystemExit(
            f"FROZEN WORLD at g={g} regime={regime}: checksum {chk0} did not move. "
            "The counts would be measuring an empty loop.")
    if assert_live and c["cand_enum"] == 0:
        raise SystemExit(
            f"DEAD INSTRUMENT at g={g}: zero candidates enumerated on a live world.")

    # §6.4 CONSERVATION -- a split that does not add up is a broken split.
    assert c["cand_enum_first"] + c["cand_enum_repeat"] == c["cand_enum"], (g, c)
    assert (c["cand_enum_scan"] + c["cand_enum_local"] + c["cand_enum_hinted"]
            == c["cand_enum"]), (g, c)
    assert c["where_evals_first"] + c["where_evals_repeat"] == c["where_evals"], (g, c)

    row = {"grid": g, "cells": g * g, "regime": regime, "driven": driven,
           "arm": arm, "fovea_radius": fovea_radius,
           "ignite_k": _ignite_k(g, regime),
           "checksum_before": chk0, "checksum_after": chk1,
           "counters": c, "buckets": buckets(c), "shares": shares(c),
           "shares_reattributed_CROSS_EPOCH": shares_reattributed(c),
           "cross_epoch": reattributed(c),
           # THE ONE CONTAMINABLE NUMBER (prereg §6.3). Recorded, labelled,
           # and excluded from every share.
           "wall_ms_per_tick_CONTAMINABLE": wall_ms}
    del world, s, ag
    return row


def fit(rows, key):
    """log-log slope vs cells, WITH r2 so a bad fit cannot pass as a clean
    exponent."""
    def val(r):
        cur = r
        for part in key.split("."):
            cur = cur[part]
        return float(cur)
    x = np.log(np.array([r["cells"] for r in rows], float))
    y = np.log(np.array([max(val(r), 1e-12) for r in rows], float))
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return {"exponent": float(coef[0]), "intercept": float(coef[1]),
            "r2": (1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan"),
            "n_points": len(rows)}


def sweep(regime, *, driven=False, fovea_radius=0, arm="eye", sizes=None):
    rows = []
    for g in sizes or SIZES:
        r = counted_point(g, regime, driven=driven, fovea_radius=fovea_radius,
                          arm=arm)
        b, sh, c = r["buckets"], r["shares"], r["counters"]
        rows.append(r)
        rs = r["shares_reattributed_CROSS_EPOCH"]
        print(f"  g={g:3d} cells={g*g:6d} | positional F={sh['F']:5.1f}% "
              f"C={sh['C']:5.1f}% R={sh['R']:5.1f}% | REATTRIB F={rs['F']:5.1f}% "
              f"C={rs['C']:5.1f}% R={rs['R']:5.1f}% | ops={b['total']:12,d} | "
              f"scan={100.0*c['cand_enum_scan']/max(c['cand_enum'],1):5.1f}% "
              f"surv={c['leaf_visits']/max(c['cand_enum'],1):.5f}", flush=True)
    return rows


# ---------------------------------------------------------------------------
# HYPOTHESIS (a) — CENTRALIZATION vs COMPARISON
# ---------------------------------------------------------------------------

def hypothesis_a(rows):
    """Is the O(N^2) a symptom of CENTRALIZATION rather than of comparison?

    Decision rule FIXED IN THE PREREG:
      ARCHITECTURAL  iff scan_share >= 0.50 at the largest grid
                     AND d(log survival)/d(log cells) < -0.5
      COMPUTATIONAL  iff scan_share < 0.50 OR slope > -0.2
      else INDETERMINATE (reported as such, never rounded)
    """
    per = []
    for r in rows:
        c = r["counters"]
        ce = max(c["cand_enum"], 1)
        per.append({
            "cells": r["cells"],
            "scan_share": c["cand_enum_scan"] / ce,
            "local_share": c["cand_enum_local"] / ce,
            "hinted_share": c["cand_enum_hinted"] / ce,
            "survival": c["leaf_visits"] / ce,
            "leaf_visits": c["leaf_visits"],
            "cand_enum": c["cand_enum"],
        })
    x = np.log(np.array([p["cells"] for p in per], float))
    y = np.log(np.array([max(p["survival"], 1e-12) for p in per], float))
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    slope = float(coef[0])
    r2 = (1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    scan_largest = per[-1]["scan_share"]

    if scan_largest >= 0.50 and slope < -0.5:
        verdict = "ARCHITECTURAL"
    elif scan_largest < 0.50 or slope > -0.2:
        verdict = "COMPUTATIONAL"
    else:
        verdict = "INDETERMINATE"
    return {"per_grid": per, "scan_share_at_largest_grid": scan_largest,
            "survival_log_slope": slope, "survival_fit_r2": r2,
            "verdict": verdict,
            "decision_rule": "ARCHITECTURAL iff scan>=0.50 AND slope<-0.5; "
                             "COMPUTATIONAL iff scan<0.50 OR slope>-0.2; "
                             "else INDETERMINATE"}


# ---------------------------------------------------------------------------
# HYPOTHESIS (b) — IS 164 h A UNIFORM-GRID NUMBER?
# ---------------------------------------------------------------------------

def hypothesis_b(sizes=None):
    """Re-fit the counted-op exponent under foveation.

    Decision rule FIXED IN THE PREREG:
      CHANGES     iff exponent(rad=4) <= exponent(rad=0) - 0.30, both r2 >= 0.95
      DOES NOT    iff |difference| < 0.15
      else INDETERMINATE

    THE CONFOUND WAS DECLARED IN ADVANCE: `WaveWorld.__init__` mints h*w
    RetinaCells UNCONDITIONALLY and `fovea_radius` is read ONLY inside
    `drive()`, so the enumeration set is structurally unchanged. If the null
    branch lands, the finding is NOT "foveation doesn't work" -- it is
    "foveation is not wired to the term that scales".
    """
    arms = {}
    for rad in (0, 4, 8):
        print(f"  fovea_radius={rad}", flush=True)
        rows = sweep("constant", driven=True, fovea_radius=rad, arm="eye",
                     sizes=sizes)
        arms[rad] = {"rows": rows,
                     "fit_ops": fit(rows, "buckets.total"),
                     "fit_cand": fit(rows, "counters.cand_enum"),
                     "retina_cells": [r["cells"] for r in rows]}
    e0 = arms[0]["fit_ops"]["exponent"]
    e4 = arms[4]["fit_ops"]["exponent"]
    d = e0 - e4
    ok_r2 = arms[0]["fit_ops"]["r2"] >= 0.95 and arms[4]["fit_ops"]["r2"] >= 0.95
    if d >= 0.30 and ok_r2:
        verdict = "FOVEATION CHANGES THE SCALING"
    elif abs(d) < 0.15:
        verdict = "FOVEATION DOES NOT CHANGE THE SCALING"
    else:
        verdict = "INDETERMINATE"
    return {"arms": arms, "exponent_rad0": e0, "exponent_rad4": e4,
            "exponent_drop": d, "both_r2_ok": ok_r2, "verdict": verdict}


def foveated_reprojection(rows_uniform, exponent, intercept):
    """COUNTERFACTUAL, and labelled as one everywhere it appears.

    The 164 h figure assumes exact treatment EVERYWHERE. Under salience-weighted
    allocation the field is a small roughly-CONSTANT foveal region at full
    exactness plus a periphery at cheap-guess cost. This re-projects the cost
    under that allocation from the MEASURED per-cell counts -- it is an
    extrapolation from measurement, never itself a measurement, and it assumes
    a machinery that DOES NOT EXIST in the drive today (see hypothesis (b)).
    """
    # Foveal budget: the largest field the measured fit puts under a 23.976 fps
    # real-time budget. The number FALLS OUT of the fit and the frame rate --
    # nothing is chosen here (PROTOCOL §13).
    budget_ms = 1000.0 / 23.976
    out = []
    for cells, label in ((4096, "64x64"), (76800, "320x240 QVGA"),
                         (2073600, "1920x1080 native")):
        uniform_ops = np.exp(intercept) * cells ** exponent
        out.append({"field": label, "cells": cells,
                    "uniform_counted_ops": float(uniform_ops)})
    return {"budget_ms_at_23.976fps": budget_ms, "projections": out,
            "IS_A_COUNTERFACTUAL": True}


# ---------------------------------------------------------------------------
# THE INSTRUMENT GATES (PROTOCOL §1) — red-then-green BEFORE any share
# ---------------------------------------------------------------------------

def gate_zero_when_off(g=16):
    """§6.1 -- every counter reads zero with the audit off, on a LIVE world.
    A counter that moves while disabled would contaminate every committed
    result (PROTOCOL §9)."""
    s, ag, _ = _boot_waves(g)
    world = WaveWorld(s, h=g, w=g, seed=0)
    AUDIT.scale_audit_set_enabled(False)
    AUDIT.scale_audit_reset()
    _run(world, 10, g, "constant")
    c = counters()
    nonzero = {k: v for k, v in c.items() if v}
    del world, s, ag
    return {"gate": "zero_when_off", "nonzero_counters": nonzero,
            "pass": not nonzero}


def gate_known_count(g=16):
    """§6.2 -- a KNOWN-COUNT workload must produce EXACTLY the known integer.

    `wv_refract` / `wv_recover` match `[r, has_cell, c]` with BOTH vars unbound,
    so each enumeration scans every `has_cell` edge -- and there are EXACTLY
    h*w of them, one per RetinaCell, minted by `WaveWorld.__init__`. So every
    scan-path enumeration must be an exact multiple of h*w.

    A counter that has only ever been seen to MOVE has not been tested."""
    s, ag, _ = _boot_waves(g)
    world = WaveWorld(s, h=g, w=g, seed=0)
    n_has_cell = g * g
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    world.step(ignite_k=1)
    AUDIT.scale_audit_set_enabled(False)
    c = counters()
    scan = c["cand_enum_scan"]
    exact_multiple = (scan % n_has_cell == 0) if scan else False
    del world, s, ag
    return {"gate": "known_count", "has_cell_edges": n_has_cell,
            "cand_enum_scan": scan,
            "scan_over_has_cell": scan / n_has_cell if n_has_cell else None,
            "is_exact_multiple": exact_multiple,
            "pass": bool(scan) and exact_multiple}


def gate_determinism(g=24, regime="constant"):
    """§6.3 -- two independent runs must give BYTE-IDENTICAL totals. This is the
    property wall-clock does not have and is the whole reason for counting. A
    non-deterministic counter INVALIDATES ITS OWN BUCKET and is reported as
    such rather than averaged."""
    a = counted_point(g, regime)["counters"]
    b = counted_point(g, regime)["counters"]
    diff = {k: (a[k], b[k]) for k in a if a[k] != b[k]}
    return {"gate": "determinism", "grid": g, "differing": diff,
            "pass": not diff}


def gate_audit_does_not_move_the_exponent(sizes=None, regime="constant"):
    """§6.5 -- an instrument that changes the exponent it measures is measuring
    itself. Fits ms/tick with the audit ON and OFF.

    THIS ONE IS WALL-CLOCK BY NECESSITY (it is a check ON wall-clock), so it is
    contaminable and is reported as a gate, never as a share."""
    def run(on):
        rows = []
        for g in sizes or SIZES:
            gc.collect()
            s, ag, _ = _boot_waves(g)
            world = WaveWorld(s, h=g, w=g, seed=0)
            _run(world, WARMUP, g, regime)
            AUDIT.scale_audit_reset()
            AUDIT.scale_audit_set_enabled(on)
            t0 = time.perf_counter()
            _run(world, TICKS, g, regime)
            ms = (time.perf_counter() - t0) / TICKS * 1000.0
            AUDIT.scale_audit_set_enabled(False)
            rows.append({"cells": g * g, "ms": ms})
            del world, s, ag
        x = np.log([r["cells"] for r in rows])
        y = np.log([r["ms"] for r in rows])
        A = np.vstack([x, np.ones_like(x)]).T
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        return float(coef[0]), rows
    e_off, rows_off = run(False)
    e_on, rows_on = run(True)
    return {"gate": "audit_does_not_move_the_exponent",
            "exponent_audit_off": e_off, "exponent_audit_on": e_on,
            "difference": e_on - e_off,
            "rows_off_CONTAMINABLE": rows_off, "rows_on_CONTAMINABLE": rows_on,
            "pass": abs(e_on - e_off) < 0.15}


# ---------------------------------------------------------------------------
# CROSS-EPOCH RE-ENUMERATION — reported SEPARATELY, never folded into R
# ---------------------------------------------------------------------------

def drive_phase_reenumeration(g=32):
    """The adapter's `while nat.apply_rule_once(idx): pass` drive loop calls into
    Rust repeatedly; every call after the first re-derives a binding set the
    first already had. That is redundancy, but it is CROSS-EPOCH, and the prereg
    deliberately keeps it OUT of R so R stays a lower bound. It is counted here
    and reported on its own."""
    s, ag, _ = _boot_waves(g)
    world = WaveWorld(s, h=g, w=g, seed=0)
    frames = _frames(g)
    _run(world, WARMUP, g, "constant", frames)
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    _run(world, TICKS, g, "constant", frames)
    AUDIT.scale_audit_set_enabled(False)
    c = counters()
    del world, s, ag
    # `epochs` counts EVERY rule-running entry: tick() once per step plus one
    # apply_rule_once per drive-rule iteration.
    return {"grid": g, "cells": g * g, "ticks": TICKS,
            "epochs": c["epochs"],
            "epochs_per_tick": c["epochs"] / TICKS,
            "apply_rule_once_epochs_per_tick": (c["epochs"] - TICKS) / TICKS,
            "rule_enumerations": c["rule_enumerations"],
            "rule_enumerations_repeat": c["rule_enumerations_repeat"],
            "within_epoch_repeat_frac":
                c["rule_enumerations_repeat"] / max(c["rule_enumerations"], 1),
            "cand_enum": c["cand_enum"],
            "cand_enum_repeat": c["cand_enum_repeat"]}


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


def _load_state():
    """PROTOCOL §0.1's earned corollary: CHECK WHAT ELSE IS RUNNING BEFORE YOU
    RECORD A WALL-CLOCK NUMBER. A contended timing is a rumour in the same way a
    stale binary is. Recorded next to every contaminable number."""
    try:
        with open("/proc/loadavg") as f:
            load = f.read().strip()
    except OSError:
        load = "?"
    try:
        ps = subprocess.run(["ps", "-eo", "pid,etimes,comm,args"],
                            capture_output=True, text=True, timeout=20).stdout
        others = [ln[:160] for ln in ps.splitlines()
                  if ("pytest" in ln or "cargo" in ln or "scale_" in ln
                      or "measure.py" in ln)
                  and str(os.getpid()) not in ln.split()[:1]]
    except Exception:
        others = ["<ps failed>"]
    return {"loadavg": load, "concurrent_candidates": others[:12],
            "n_logical_cores": os.cpu_count()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all",
                    choices=["all", "gates", "sweep", "hyp_a", "hyp_b", "drive"])
    ap.add_argument("--sizes", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    sizes = [int(x) for x in a.sizes.split(",")] if a.sizes else SIZES

    prov = provenance_line()
    print(prov, flush=True)
    print(_machine(), flush=True)
    res = {"provenance": prov, "machine": _machine(),
           "sizes": sizes, "ticks": TICKS, "warmup": WARMUP,
           "bucket_definition": {k: list(v) for k, v in BUCKET.items()},
           "load_state_at_start": _load_state()}

    # GATES FIRST. A share reported before its instrument is gated is a rumour.
    if a.mode in ("all", "gates"):
        print("== INSTRUMENT GATES (PROTOCOL §1) ==", flush=True)
        res["gates"] = [gate_zero_when_off(), gate_known_count(),
                        gate_determinism()]
        for gt in res["gates"]:
            print(f"  {gt['gate']:22s} pass={gt['pass']}", flush=True)
        if not all(gt["pass"] for gt in res["gates"]):
            print("  ** A GATE FAILED — the shares below are NOT reportable **",
                  flush=True)

    if a.mode in ("all", "sweep"):
        # PRIMARY: the ASSEMBLED EYE, FRAME-DRIVEN -- the object that produced
        # 1.887 and the 164 h figure. My prereg §2 said "the exact object §S5
        # fitted" AND "the committed no-frame schedule"; those two conflict,
        # because I wrote §2 from a misreading of `video_probe_measure.py`
        # (§S5 drives EVERY tick with a real frame, through `boot_eye`, which
        # also loads `vision_lateral`). BOTH arms are reported -- the primary
        # because it is the object the claim is about, the pre-registered
        # no-frame arm because it is what I pre-registered. Recorded, not
        # silently substituted.
        print("== COUNTED SWEEP — PRIMARY: assembled eye, FRAME-DRIVEN ==",
              flush=True)
        rows = sweep("constant", driven=True, arm="eye", sizes=sizes)
        res["sweep_eye_driven_PRIMARY"] = rows
        for key, lab in (("buckets.total", "ops_total"), ("buckets.F", "F"),
                         ("buckets.C", "C"), ("buckets.R", "R"),
                         ("counters.cand_enum", "cand_enum")):
            res[f"fit_eye_driven_{lab}"] = fit(rows, key)
        f = res["fit_eye_driven_ops_total"]
        print(f"   counted-op exponent = {f['exponent']:.3f} (r2 {f['r2']:.4f})",
              flush=True)
        res["hypothesis_a_PRIMARY"] = hypothesis_a(rows)
        h = res["hypothesis_a_PRIMARY"]
        print(f"   (a) scan={h['scan_share_at_largest_grid']:.4f} "
              f"slope={h['survival_log_slope']:.4f} -> {h['verdict']}", flush=True)

        for regime in ("constant", "density"):
            print(f"== COUNTED SWEEP (pre-registered arm) regime={regime} ==",
                  flush=True)
            rows = sweep(regime, arm="waves", sizes=sizes)
            res[f"sweep_{regime}"] = rows
            for key, lab in (("buckets.total", "ops_total"),
                             ("buckets.F", "F"), ("buckets.C", "C"),
                             ("buckets.R", "R"),
                             ("counters.cand_enum", "cand_enum")):
                res[f"fit_{regime}_{lab}"] = fit(rows, key)
            f = res[f"fit_{regime}_ops_total"]
            print(f"   counted-op exponent = {f['exponent']:.3f} "
                  f"(r2 {f['r2']:.4f})", flush=True)
        # Waves-only, frame-driven: isolates what the LATERAL seed adds.
        print("== COUNTED SWEEP waves-only, frame-driven ==", flush=True)
        rows = sweep("constant", driven=True, arm="waves", sizes=sizes)
        res["sweep_waves_driven"] = rows
        res["fit_waves_driven_ops_total"] = fit(rows, "buckets.total")

    if a.mode in ("all", "hyp_a"):
        print("== HYPOTHESIS (a): CENTRALIZATION vs COMPARISON ==", flush=True)
        src = res.get("sweep_constant") or sweep("constant", arm="waves",
                                                 sizes=sizes)
        res["hypothesis_a"] = hypothesis_a(src)
        h = res["hypothesis_a"]
        print(f"   scan share @ largest grid = {h['scan_share_at_largest_grid']:.4f}",
              flush=True)
        print(f"   survival log-slope        = {h['survival_log_slope']:.4f} "
              f"(r2 {h['survival_fit_r2']:.4f})", flush=True)
        print(f"   VERDICT: {h['verdict']}", flush=True)

    if a.mode in ("all", "hyp_b"):
        print("== HYPOTHESIS (b): IS 164 h A UNIFORM-GRID NUMBER? ==", flush=True)
        res["hypothesis_b"] = hypothesis_b(sizes=sizes)
        h = res["hypothesis_b"]
        print(f"   exponent rad=0 {h['exponent_rad0']:.3f} | "
              f"rad=4 {h['exponent_rad4']:.3f} | drop {h['exponent_drop']:.3f}",
              flush=True)
        print(f"   VERDICT: {h['verdict']}", flush=True)
        f = res.get("fit_constant_ops_total")
        if f:
            res["foveated_reprojection_COUNTERFACTUAL"] = foveated_reprojection(
                res.get("sweep_constant"), f["exponent"], f["intercept"])

    if a.mode in ("all", "drive"):
        print("== CROSS-EPOCH RE-ENUMERATION (reported separately) ==", flush=True)
        res["drive_phase"] = drive_phase_reenumeration()
        d = res["drive_phase"]
        print(f"   epochs/tick={d['epochs_per_tick']:.1f} "
              f"within-epoch repeat frac={d['within_epoch_repeat_frac']:.4f}",
              flush=True)

    if a.mode == "all":
        print("== §6.5 audit-does-not-move-the-exponent (CONTAMINABLE) ==",
              flush=True)
        res["gate_exponent"] = gate_audit_does_not_move_the_exponent(sizes=sizes)
        g = res["gate_exponent"]
        print(f"   off={g['exponent_audit_off']:.3f} on={g['exponent_audit_on']:.3f} "
              f"pass={g['pass']}", flush=True)

    res["load_state_at_end"] = _load_state()
    if a.out:
        d = os.path.dirname(a.out)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.out, "w") as f:
            json.dump(res, f, indent=2, default=str)
        print("wrote", a.out, flush=True)


if __name__ == "__main__":
    main()
