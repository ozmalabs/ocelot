#!/usr/bin/env python3
"""THE IDENTITY-COST ANATOMY — Step 0 (G5 on THREE axes), the post-fix
per-variant profile, and the coverage attribution.

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***

Pre-registration: `VISION_IDENTITY_COST_ANATOMY_PREREG.md`, committed at
`9d7195da` BEFORE this file existed and before any measurement.

WHY. `VISION_VIDEO_PROBE_RERUN_RESULTS.md` put the sd/identity layer's
coefficient at **698 us/cell, 55x the drive's 12.6 us**. That number was
measured on engine `4d451d8f6ed0`. `VISION_CODEBOOK_AXIS_RESULTS.md` then
removed **91.16%** of `DimInfer`'s interior work **on the recognising path** and
shipped engine `863706852555`. The 698 us/cell workload (K=1, literal
self-identity) **IS** the recognising path. **Nobody has re-measured it.**

STEP 0 IS NOT A FORMALITY, AND THIS RUNG ADDS A THIRD AXIS. The term-eval rung
validated `term_unit` on N at K=1 (and recorded ShapeDecode's own sites INERT);
the codebook rung had to extend it to K. This rung varies **PATH** as well, and
reads the profile POST-fix where the formerly dominant term has been cut 11x. A
counter validated when `DimInfer` carried 99.92% of the work is not thereby
validated on the profile that replaced it. The verdict is NOT reimplemented in
Python: `AUDIT.scale_audit_g5_verdict` hands off to `runners/dsl/src/g5.rs`.

THE COVERAGE CHECK (prereg §1.1) is the part most likely to matter. `term_unit`
counts work INSIDE Term evaluation. The codebook rung's own residual records
"7.3x wall against 11.3x counted -- the gap is the fixed rule-matching cost
outside DimInfer". Post-fix that gap may be the whole remaining coefficient, and
a profile built from `term_unit` alone would attribute 100% of a coefficient it
only partly covers. So wall is fitted against `term_units_total` and the
INTERCEPT is reported as a first-class term.

SEEDS: block 78000-78999 (prereg §2).

USAGE
    python scripts/identity_cost_anatomy.py --out results/identity_cost_anatomy.json
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3 -- a non-pytest entrypoint pins its OWN tree's engine.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402

from scripts.scale_split_measure import AUDIT, counters  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

# --------------------------------------------------------------------------- #
SEED_BASE = 78000          # prereg §2 -- block 78000-78999
M_POINTS = 7               # sweep points and control repeats (predecessors' shape)
DT = ["pred", "coord:r", "coord:c", "val"]
SLOTS = len(DT) - 1

GEN_SEED = os.path.join(ROOT, "seeds", "shape_decode_loop.json")


def generator_params() -> list[int]:
    """`params` length per DimensionGenerator, in seed order. FALLS OUT of the
    seed file (PROTOCOL §13) -- no constant is chosen in this script."""
    with open(GEN_SEED) as fh:
        d = json.load(fh)
    return [len(n["attrs"].get("params") or [])
            for n in d.get("nodes", [])
            if n.get("type") == "DimensionGenerator"]


def attempts_per_part() -> tuple[int, int, int]:
    """(length-1, length-2, total) attempts per ELIGIBLE part, closed form.
    Derived from `eval_dim_infer`'s own loop structure, not fitted."""
    ps = generator_params()
    sp = sum(ps)
    return sp, sp * sp - sum(p * p for p in ps), sp + (sp * sp - sum(p * p for p in ps))


# --------------------------------------------------------------------------- #
def load_state() -> dict:
    with open("/proc/loadavg") as fh:
        p = fh.read().split()
    return {"load1": float(p[0]), "load5": float(p[1]), "load15": float(p[2])}


def machine() -> dict:
    return {"platform": platform.platform(), "python": sys.version.split()[0],
            "cpu_count": os.cpu_count()}


def fit(xs, ys):
    """log-log power fit -- the exponent form."""
    if len(xs) < 3:
        return None
    x, y = np.log10(np.asarray(xs, float)), np.log10(np.asarray(ys, float))
    A = np.vstack([x, np.ones_like(x)]).T
    (m, b), res, *_ = np.linalg.lstsq(A, y, rcond=None)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    ss_res = float(res[0]) if len(res) else 0.0
    return {"exponent": float(m), "intercept_log10": float(b),
            "r2": (1.0 - ss_res / ss_tot) if ss_tot else None, "n_points": len(xs)}


def linfit(xs, ys):
    """LINEAR fit y = m*x + c -- the COVERAGE form (prereg §1.1). The intercept
    is the quantity of interest: the cost that does NOT scale with counted
    interior Term units, i.e. the part `term_unit` cannot see."""
    if len(xs) < 3:
        return None
    x, y = np.asarray(xs, float), np.asarray(ys, float)
    A = np.vstack([x, np.ones_like(x)]).T
    (m, c), res, *_ = np.linalg.lstsq(A, y, rcond=None)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    ss_res = float(res[0]) if len(res) else 0.0
    return {"slope": float(m), "intercept": float(c),
            "r2": (1.0 - ss_res / ss_tot) if ss_tot else None, "n_points": len(xs)}


def _counted(fn):
    """Run `fn` with the audit ON; return (counters, wall_ms, fn's return)."""
    gc.collect()
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    t0 = time.perf_counter()
    try:
        out = fn()
    finally:
        AUDIT.scale_audit_set_enabled(False)
    ms = (time.perf_counter() - t0) * 1000.0
    return counters(), ms, out


def _untimed_counted(fn):
    """Counters only, audit ON -- used where wall is not wanted."""
    gc.collect()
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    try:
        fn()
    finally:
        AUDIT.scale_audit_set_enabled(False)
    return counters()


# --------------------------------------------------------------------------- #
def synth_cells(n, seed=SEED_BASE):
    """Deterministic pseudo-random cell set of exactly `n` relations. A plain
    LCG, auditable in three lines, drawn from THIS rung's seed block so no seed
    is shared across rungs."""
    x = seed
    out, seen = [], set()
    while len(out) < n:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        r, c = (x >> 7) % 64, (x >> 17) % 64
        if (r, c) in seen:
            continue
        seen.add((r, c))
        out.append(["cell", r, c, f"v{(x >> 3) % 4}"])
    return out


def point_S(n_cells, k_codebook=1, path="exact", audit=True, timed=True):
    """ONE sd/identity decode.

    `path` is THIS rung's new axis and it is the one the codebook fix is
    conditional on:
      exact -- held[0] IS the target ⇒ explained at length 1 ⇒ the
               short-circuit FIRES (the recognising path).
      novel -- the target is in NO codebook entry ⇒ nothing is explained ⇒
               the short-circuit CANNOT fire (bit-for-bit the pre-fix cost).
    """
    cells = synth_cells(n_cells)
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for i in range(k_codebook):
        if path == "exact" and i == 0:
            sig = cells
        else:
            # decoys from this rung's block, disjoint from the target's draw
            sig = synth_cells(n_cells, seed=SEED_BASE + 100 + i)
        s.add_node("ShapeSignature",
                   {"name": f"held{i}", "signature": json.dumps(sig),
                    "kind": "faculty", "faculty": f"held{i}", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation",
                     {"signature": cells, "key": ["probe"], "status": "decoded",
                      "residual": cells, "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)

    if audit and timed:
        c, ms, _ = _counted(native.run_rules)
    elif audit:
        c, ms = _untimed_counted(native.run_rules), None
    else:
        gc.collect()
        AUDIT.scale_audit_set_enabled(False)
        t0 = time.perf_counter()
        native.run_rules()
        ms, c = (time.perf_counter() - t0) * 1000.0, {}
    # LIVENESS (PROTOCOL §1.1: "scores at the floor" is satisfied by DEATH).
    status = s.node(obs)["attrs"].get("status")
    del s, ag, native
    return c, ms, status


# --------------------------------------------------------------------------- #
N_VALUES = [12, 20, 37, 58, 93, 123, 142]
K_VALUES = [1, 2, 3, 5, 8, 12, 16]
P_VALUES = ["exact", "novel"]
N_FIXED = 58
K_FIXED = 1

SWEEPS = {
    "N": ("sd signature cells (K=1, path=exact)",
          lambda v: point_S(v, k_codebook=K_FIXED, path="exact"), N_VALUES, "cells"),
    "K": ("sd CODEBOOK ENTRIES (N=%d, path=exact)" % N_FIXED,
          lambda v: point_S(N_FIXED, k_codebook=v, path="exact"), K_VALUES, "codebook entries"),
    "P": ("PATH -- exact vs novel (N=%d, K=1)" % N_FIXED,
          lambda v: point_S(N_FIXED, k_codebook=K_FIXED, path=v), P_VALUES, "path"),
}


def run_sweep(axis):
    label, fn, values, ivname = SWEEPS[axis]
    print(f"[SWEEP-{axis}] {label}", flush=True)
    rows = []
    for v in values:
        c, ms, status = fn(v)
        # the path axis is CATEGORICAL: it has no numeric x. G5 needs none
        # (it compares spans), and rho is reported as None rather than faked.
        ax = float(v) if axis != "P" else None
        rows.append({"value": v, "axis_x": ax, "counters": c,
                     "wall_ms_CONTAMINABLE": ms, "liveness": status,
                     "load": load_state()})
        print(f"  x={str(v):>6} {ms:8.1f} ms  units={c.get('term_units_total')} "
              f"evals={c.get('term_evals_total')}  {status or ''}", flush=True)

    print(f"[SWEEP-{axis}] control at x={values[0]} x{M_POINTS}", flush=True)
    ctrl = []
    for _ in range(M_POINTS):
        c, ms, _ = fn(values[0])
        ctrl.append({"counters": c, "wall_ms_CONTAMINABLE": ms})

    out = {"axis": axis, "label": label, "iv": ivname, "values": values,
           "rows": rows, "control": ctrl}
    if axis != "P":
        out["axis_fold_range"] = max(r["axis_x"] for r in rows) / min(r["axis_x"] for r in rows)
    return out


# --------------------------------------------------------------------------- #
def series(rows, name):
    return [int(r["counters"].get(name, 0)) for r in rows]


def g5_for(sweep, name):
    """G5 verdict, HANDED OFF to `runners/dsl/src/g5.rs`. A second copy in
    Python is a copy that drifts."""
    sw = series(sweep["rows"], name)
    ct = series(sweep["control"], name)
    return {"counter": name, "axis": sweep["axis"], "sweep": sw, "control": ct,
            "verdict": AUDIT.scale_audit_g5_verdict(sw, ct)}


def step0(sweeps):
    """STEP 0 -- is MY instrument responsive on ALL THREE axes of THIS rung?

    Every `term_unit:*` AND `term_eval:*` counter is put through G5, not only
    the two the predecessors happened to report: the whole point of this rung is
    that the profile has CHANGED, so which counter carries the work is exactly
    what is unknown."""
    out = {}
    for axis, sw in sweeps.items():
        names = sorted({n for r in sw["rows"] + sw["control"] for n in r["counters"]
                        if n.startswith("term_unit") or n.startswith("term_eval")})
        out[axis] = [g5_for(sw, n) for n in names]
    return out


# --------------------------------------------------------------------------- #
def profile(n_cells=142, k=1, path="exact"):
    """THE PER-VARIANT PROFILE, never aggregated (the term-eval rung's whole
    point: DimInfer at 4% of invocations carried 99.92% of the work)."""
    c, ms, status = point_S(n_cells, k_codebook=k, path=path)
    evals = {n.split(":", 1)[1]: v for n, v in c.items()
             if n.startswith("term_eval:")}
    units = {n.split(":", 1)[1]: v for n, v in c.items()
             if n.startswith("term_unit:")}
    tot_u = int(c.get("term_units_total", 0))
    tot_e = int(c.get("term_evals_total", 0))
    rows = []
    for v in sorted(set(evals) | set(units),
                    key=lambda k_: (-int(units.get(k_, 0)), -int(evals.get(k_, 0)))):
        u, e = int(units.get(v, 0)), int(evals.get(v, 0))
        rows.append({"variant": v, "term_eval": e, "term_unit": u,
                     "unit_share": (u / tot_u) if tot_u else None,
                     "eval_share": (e / tot_e) if tot_e else None})
    return {"n_cells": n_cells, "K": k, "path": path,
            "wall_ms_CONTAMINABLE": ms, "load": load_state(), "liveness": status,
            "term_units_total": tot_u, "term_evals_total": tot_e,
            "term_units_unattributed": int(c.get("term_units_unattributed", 0)),
            "rows": rows, "all_counters": c}


def coverage(sweep_n):
    """PREREG §1.1 -- the declared coverage test. Fit wall against
    `term_units_total`. The INTERCEPT is the cost that does not scale with
    interior Term units: the fraction of the coefficient `term_unit` CANNOT
    SEE. Declared before measuring as a fully reportable outcome."""
    live = [r for r in sweep_n["rows"] if r["wall_ms_CONTAMINABLE"] is not None]
    xs = [int(r["counters"].get("term_units_total", 0)) for r in live]
    ys = [r["wall_ms_CONTAMINABLE"] for r in live]
    lf = linfit(xs, ys)
    top = max(ys) if ys else None
    return {"fit_wall_vs_units": lf,
            "us_per_unit": (lf["slope"] * 1000.0) if lf else None,
            "intercept_ms": lf["intercept"] if lf else None,
            "wall_ms_at_max_N": top,
            "intercept_frac_at_max_N": (lf["intercept"] / top) if (lf and top) else None,
            "units": xs, "wall_ms": ys}


def per_cell(sweep_n):
    """us/cell -- the quantity the 698 figure is stated in."""
    rows = []
    for r in sweep_n["rows"]:
        if r["wall_ms_CONTAMINABLE"] is None:
            continue
        rows.append({"n_cells": r["value"],
                     "wall_ms_CONTAMINABLE": r["wall_ms_CONTAMINABLE"],
                     "us_per_cell": r["wall_ms_CONTAMINABLE"] * 1000.0 / r["value"],
                     "load": r["load"]})
    return {"rows": rows,
            "fit_ms_vs_cells": fit([r["n_cells"] for r in rows],
                                   [r["wall_ms_CONTAMINABLE"] for r in rows])}


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/identity_cost_anatomy.json")
    ap.add_argument("--repeats", type=int, default=5,
                    help="repeats for the us/cell timing arm (median reported)")
    args = ap.parse_args()

    print(provenance_line(), flush=True)
    l1, l2, a = attempts_per_part()
    print(f"[gen] generator params {generator_params()} -> "
          f"length1={l1} length2={l2} A={a}", flush=True)

    sweeps = {axis: run_sweep(axis) for axis in ("N", "K", "P")}

    print("[step0] G5 on all three axes", flush=True)
    s0 = step0(sweeps)

    print("[profile] per-variant, N=142 K=1 exact", flush=True)
    prof_exact = profile(142, 1, "exact")
    print("[profile] per-variant, N=142 K=1 novel (the un-short-circuited path)",
          flush=True)
    prof_novel = profile(142, 1, "novel")

    print("[coverage] wall vs term_units_total", flush=True)
    cov = coverage(sweeps["N"])

    # us/cell, repeated -- the ONE careful wall-clock tie (prereg §2).
    print(f"[us/cell] timing arm, {args.repeats} repeats/point", flush=True)
    pc_rows = []
    for n in N_VALUES:
        samples = []
        for _ in range(args.repeats):
            _c, ms, st = point_S(n, k_codebook=1, path="exact", audit=False)
            samples.append(ms)
        med = statistics.median(samples)
        pc_rows.append({"n_cells": n, "ms_median": med,
                        "ms_min": min(samples), "ms_max": max(samples),
                        "spread_frac": (max(samples) - min(samples)) / max(med, 1e-9),
                        "us_per_cell": med * 1000.0 / n,
                        "samples": samples, "liveness": st,
                        "load": load_state()})
        print(f"  N={n:4d} {med:8.2f} ms  {med*1000.0/n:8.1f} us/cell "
              f"(spread {(max(samples)-min(samples))/max(med,1e-9)*100:.1f}%) {st}",
              flush=True)

    doc = {
        "provenance": provenance_line(),
        "machine": machine(),
        "load_at_start": load_state(),
        "prereg": "VISION_IDENTITY_COST_ANATOMY_PREREG.md @ 9d7195da",
        "seed_block": [78000, 78999],
        "generator": {"params": generator_params(),
                      "length1": l1, "length2": l2, "A": a},
        "sweeps": sweeps,
        "step0_g5": s0,
        "profile_exact": prof_exact,
        "profile_novel": prof_novel,
        "coverage": cov,
        "us_per_cell_timed": {"repeats": args.repeats, "rows": pc_rows,
                              "fit": fit([r["n_cells"] for r in pc_rows],
                                         [r["ms_median"] for r in pc_rows])},
    }
    os.makedirs(os.path.dirname(os.path.join(ROOT, args.out)), exist_ok=True)
    with open(os.path.join(ROOT, args.out), "w") as fh:
        json.dump(doc, fh, indent=2)
    print(f"[out] {args.out}", flush=True)

    # ---- console summary -------------------------------------------------- #
    print("\n=== STEP 0 (G5) ===")
    for axis, rows in s0.items():
        for r in rows:
            print(f"  [{axis}] {r['counter']:<34} {r['verdict']:<11} {r['sweep']}")
    print("\n=== PROFILE (N=142, K=1, exact) ===")
    for r in prof_exact["rows"]:
        sh = "" if r["unit_share"] is None else f"{r['unit_share']*100:6.2f}%"
        print(f"  {r['variant']:<20} evals={r['term_eval']:>8}  "
              f"units={r['term_unit']:>12}  {sh}")
    print(f"  TOTAL evals={prof_exact['term_evals_total']} "
          f"units={prof_exact['term_units_total']} "
          f"unattributed={prof_exact['term_units_unattributed']}")
    print("\n=== COVERAGE ===")
    print(f"  us/unit={cov['us_per_unit']}  intercept={cov['intercept_ms']} ms  "
          f"r2={cov['fit_wall_vs_units'] and cov['fit_wall_vs_units']['r2']}")
    print(f"  intercept as frac of wall at max N = {cov['intercept_frac_at_max_N']}")


if __name__ == "__main__":
    main()
