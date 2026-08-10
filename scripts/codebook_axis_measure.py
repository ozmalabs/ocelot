#!/usr/bin/env python3
"""THE CODEBOOK AXIS (K) — Step 0 (G5 on BOTH axes) and Phase 1.

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***

Pre-registration: `VISION_CODEBOOK_AXIS_PREREG.md`, committed at `e22db8dd`
BEFORE this file existed and before any measurement.

WHY. `VISION_VIDEO_PROBE_RERUN_RESULTS.md` found the sd/identity layer is linear
in signature cells AND linear in codebook size — a coefficient times K, not an
exponent. The binding quantity is N x K. **K has never been measured.**

STEP 0 IS NOT A FORMALITY. The predecessor's `term_unit` family was validated by
G5 on an N sweep AT K=1 ONLY, and that same rung recorded ShapeDecode's own unit
sites as INERT. A counter validated on one axis is not validated on another, so
G5 runs here on SWEEP-N *and* SWEEP-K before any headline. The verdict is NOT
reimplemented in Python: `AUDIT.scale_audit_g5_verdict` hands off to
`runners/dsl/src/g5.rs`, the same function its own unit tests exercise.

SEEDS: block 68000-68999 (prereg §7).

USAGE
    python scripts/codebook_axis_measure.py --out results/codebook_axis.json
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3 -- a non-pytest entrypoint pins its OWN tree's engine.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

from scripts.scale_split_measure import AUDIT, counters  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

# --------------------------------------------------------------------------- #
SEED_BASE = 68000          # prereg §7 -- block 68000-68999
M_POINTS = 7               # 7 sweep points, 7 control repeats (predecessor's shape)
DT = ["pred", "coord:r", "coord:c", "val"]
SLOTS = len(DT) - 1        # `s` in the model: slots per relation beyond the predicate

# THE SHIPPED GENERATOR CODEBOOK -- read from the seed, never written down here.
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

    length 1 : sum(P)                    -- every generator x every k
    length 2 : sum(P)^2 - sum(P^2)       -- ordered pairs of DISTINCT generators
    Derived from `eval_dim_infer`'s own loop structure (shape_decode.rs:1930+),
    not fitted to any measurement."""
    ps = generator_params()
    sp = sum(ps)
    l1 = sp
    l2 = sp * sp - sum(p * p for p in ps)
    return l1, l2, l1 + l2


# --------------------------------------------------------------------------- #
def load_state() -> dict:
    with open("/proc/loadavg") as fh:
        p = fh.read().split()
    return {"load1": float(p[0]), "load5": float(p[1]), "load15": float(p[2])}


def machine() -> dict:
    return {"platform": platform.platform(), "python": sys.version.split()[0],
            "cpu_count": os.cpu_count()}


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


# --------------------------------------------------------------------------- #
def synth_cells(n, seed=SEED_BASE):
    """Deterministic pseudo-random cell set of exactly `n` relations.

    Byte-identical in FORM to `g5_responsiveness_sweep.synth_cells` (a plain LCG,
    auditable in three lines) but drawn from THIS rung's seed block, so no seed
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


def point_S(n_cells, k_codebook=1, typed=True):
    """ONE sd/identity decode: K held signatures, one observation of N cells.

    `typed` controls whether the held parts carry `dim_types` -- i.e. whether
    they are K_eligible or merely K_total. That distinction is the whole of
    prereg §3.1 and is a PARAMETER here rather than an assumption."""
    cells = synth_cells(n_cells)
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for i in range(k_codebook):
        sig = cells if i == 0 else synth_cells(n_cells, seed=SEED_BASE + 1 + i)
        attrs = {"name": f"held{i}", "signature": json.dumps(sig),
                 "kind": "faculty", "faculty": f"held{i}"}
        if typed:
            attrs["dim_types"] = DT
        s.add_node("ShapeSignature", attrs)
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation",
                     {"signature": cells, "key": ["probe"], "status": "decoded",
                      "residual": cells, "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)

    c, ms, _ = _counted(native.run_rules)
    # LIVENESS (PROTOCOL §1.1: "scores at the floor" is satisfied by DEATH).
    status = s.node(obs)["attrs"].get("status")
    del s, ag, native
    return c, ms, status


# --------------------------------------------------------------------------- #
# SWEEP-N -- the predecessor's axis, replicated at K=1. If this does not come
# back RESPONSIVE the instrument has regressed and nothing else here is readable.
# SWEEP-K -- THE NEW AXIS. N held fixed; only the codebook grows.
N_VALUES = [12, 20, 37, 58, 93, 123, 142]
K_VALUES = [1, 2, 3, 5, 8, 12, 16]
N_FIXED_FOR_K = 58
K_FIXED_FOR_N = 1

SWEEPS = {
    "N": ("sd signature cells (K held at 1)",
          lambda v: point_S(v, k_codebook=K_FIXED_FOR_N), N_VALUES, "cells"),
    "K": ("sd CODEBOOK ENTRIES (N held at %d)" % N_FIXED_FOR_K,
          lambda v: point_S(N_FIXED_FOR_K, k_codebook=v), K_VALUES, "codebook entries"),
}


def run_sweep(axis):
    label, fn, values, ivname = SWEEPS[axis]
    print(f"[SWEEP-{axis}] {label}", flush=True)
    rows = []
    for v in values:
        c, ms, status = fn(v)
        rows.append({"value": v, "axis_x": float(v), "counters": c,
                     "wall_ms_CONTAMINABLE": ms, "liveness": status})
        print(f"  x={v:>5} {ms:8.1f} ms  term_units={c.get('term_units_total')} "
              f"term_evals={c.get('term_evals_total')}  {status or ''}", flush=True)

    # THE CONTROL -- same counter, same repetition count, axis held FIXED at the
    # sweep's first value. The MEASURED noise floor G5's criterion is written
    # against; nothing is assumed to be zero.
    print(f"[SWEEP-{axis}] control at x={values[0]} x{M_POINTS}", flush=True)
    ctrl = []
    for _ in range(M_POINTS):
        c, ms, _ = fn(values[0])
        ctrl.append({"counters": c, "wall_ms_CONTAMINABLE": ms})

    return {"axis": axis, "label": label, "iv": ivname, "values": values,
            "rows": rows, "control": ctrl,
            "axis_fold_range": max(r["axis_x"] for r in rows) / min(r["axis_x"] for r in rows)}


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
    """STEP 0 -- is MY instrument responsive on BOTH axes of THIS rung?"""
    out = {}
    for axis, sw in sweeps.items():
        names = sorted({n for r in sw["rows"] + sw["control"] for n in r["counters"]
                        if n.startswith("term_unit")})
        out[axis] = [g5_for(sw, n) for n in names]
    return out


# --------------------------------------------------------------------------- #
def exhaustiveness(sweeps):
    """PHASE 1 §3.2 -- measured `term_unit:DimInfer` vs the model's prediction.

    model: units = I x K_eligible x A x N x (1 + s)
    `I` (DimInfer invocations) is READ from `term_eval:DimInfer`, never assumed,
    so the ratio tests the LOOP STRUCTURE rather than the invocation count."""
    l1, l2, a = attempts_per_part()
    out = []
    for axis, sw in sweeps.items():
        for r in sw["rows"]:
            c = r["counters"]
            n = N_FIXED_FOR_K if axis == "K" else r["value"]
            k = r["value"] if axis == "K" else K_FIXED_FOR_N
            inv = int(c.get("term_eval:DimInfer", 0))
            measured = int(c.get("term_unit:DimInfer", 0))
            pred = inv * k * a * n * (1 + SLOTS)
            out.append({"axis": axis, "value": r["value"], "N": n, "K": k,
                        "dim_infer_invocations": inv,
                        "measured_units": measured, "predicted_units": pred,
                        "ratio": (measured / pred) if pred else None,
                        "attempts_len1_per_part": l1, "attempts_len2_per_part": l2,
                        "attempts_total_per_part": a})
    return out


# --------------------------------------------------------------------------- #
def codebook_census():
    """PHASE 1 §3.1 -- K_total vs K_eligible, per shipped seed manifest.

    STATIC census of the manifests: how many `ShapeSignature` nodes each seed
    ships, and how many of them carry `dim_types` (the `:1930` eligibility gate).
    These are DIFFERENT numbers and conflating them would be the whole error."""
    import glob
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "seeds", "*.json"))):
        try:
            with open(f) as fh:
                d = json.load(fh)
        except Exception:
            continue
        sigs = [n for n in (d.get("nodes") or []) if n.get("type") == "ShapeSignature"]
        if not sigs:
            continue
        typed = [n for n in sigs if n.get("attrs", {}).get("dim_types")]
        rows.append({"seed": os.path.basename(f), "K_total": len(sigs),
                     "K_eligible": len(typed)})
    return rows


def codebook_attempting_census():
    """PHASE 1 §3.1, THE REFINEMENT THE STATIC CENSUS FORCED.

    `dim_types` alone does NOT make a part reach the generator loops.
    `dims_are_coord` (`shape_decode.rs:535`) requires the generator's
    `coord_dims` slots to be typed with the **`coord:` prefix**. A part whose
    `dim_types` are e.g. `['pred','idx','val','val','val']` is loaded, walked,
    and then contributes ZERO attempts — it is K_total and K_eligible but NOT
    K_attempting.

    Three different numbers. Reporting only the first two would have overstated
    the real codebook cost by the entire stroke corpus."""
    import glob
    gens = []
    with open(GEN_SEED) as fh:
        for n in json.load(fh).get("nodes", []):
            if n.get("type") == "DimensionGenerator":
                gens.append(n["attrs"].get("coord_dims") or [])

    def attempting(dim_types):
        if not dim_types:
            return False
        return any(cd and all(
            (i < len(dim_types) and str(dim_types[i]).startswith("coord:"))
            for i in cd) for cd in gens)

    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "seeds", "*.json"))):
        try:
            with open(f) as fh:
                d = json.load(fh)
        except Exception:
            continue
        sigs = [n for n in (d.get("nodes") or []) if n.get("type") == "ShapeSignature"]
        if not sigs:
            continue
        rows.append({
            "seed": os.path.basename(f),
            "K_total": len(sigs),
            "K_eligible": sum(1 for n in sigs if n.get("attrs", {}).get("dim_types")),
            "K_attempting": sum(1 for n in sigs
                                if attempting(n.get("attrs", {}).get("dim_types"))),
        })
    return rows


def real_vision_codebook():
    """PHASE 1 §3.1 on the arc's CANONICAL REAL workload, not a synthetic probe.

    `sdloop_vision` is where coord-typed signatures actually come from (no
    shipped seed produces them — they are minted at runtime by the vision world
    adapters). This is therefore the only place a REAL K on this axis exists."""
    import numpy as np  # noqa: F401  (imported by the measure script's boot)
    from scripts.sdloop_vision_measure import run_arm
    out = []
    for n in (2, 3, 4, 6, 12):
        thetas = [i * 180.0 / n for i in range(n)]
        rows, cb, alive = run_arm(SEED_BASE + 100 + n, thetas,
                                  label="kcensus", with_sdloop=True)
        supports = [sz for _, _, sz in rows]
        out.append({"n_thetas": n, "codebook": cb, "alive": alive,
                    "support_N_min": min(supports), "support_N_max": max(supports),
                    "support_N_mean": sum(supports) / len(supports)})
        print(f"  n_thetas={n:<3} mints={cb['mints']:<3} "
              f"shape_signatures={cb['shape_signatures']:<3} "
              f"N={min(supports)}-{max(supports)}", flush=True)
    return out


def codebook_census_live():
    """The same census on a LIVE boot -- what the codebook loop at
    `shape_decode.rs:243` would actually walk after `boot_core`."""
    s, ag = boot_core()
    ids = s.nodes("ShapeSignature")
    total = len(ids)
    elig = 0
    for nid in ids:
        if s.node(nid)["attrs"].get("dim_types"):
            elig += 1
    del s, ag
    return {"K_total": total, "K_eligible": elig}


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/codebook_axis.json")
    args = ap.parse_args()

    print(provenance_line(), flush=True)
    load_before = load_state()

    sweeps = {a: run_sweep(a) for a in ("N", "K")}
    l1, l2, a = attempts_per_part()

    doc = {
        "provenance": provenance_line(),
        "prereg_commit": "e22db8dd",
        "seed_block": "68000-68999",
        "machine": machine(),
        "load_before_CONTAMINABLE": load_before,
        "load_after_CONTAMINABLE": load_state(),
        "generator_params": generator_params(),
        "attempts_per_part": {"length1": l1, "length2": l2, "total": a,
                              "length2_share": l2 / a},
        "sweeps": sweeps,
        "step0_g5": step0(sweeps),
        "exhaustiveness": exhaustiveness(sweeps),
        "codebook_census_static": codebook_census(),
        "codebook_census_attempting": codebook_attempting_census(),
        "codebook_census_live_boot": codebook_census_live(),
        "real_vision_codebook": real_vision_codebook(),
    }
    os.makedirs(os.path.dirname(os.path.join(ROOT, args.out)), exist_ok=True)
    with open(os.path.join(ROOT, args.out), "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    print(f"\nwrote {args.out}", flush=True)

    print("\n=== STEP 0 — G5 on BOTH axes ===")
    for axis, rows in doc["step0_g5"].items():
        for r in rows:
            print(f"  SWEEP-{axis}  {r['counter']:<28} {r['verdict']:<12} {r['sweep']}")
    print("\n=== PHASE 1 §3.2 — EXHAUSTIVENESS ===")
    for r in doc["exhaustiveness"]:
        rt = f"{r['ratio']:.4f}" if r["ratio"] is not None else "n/a"
        print(f"  {r['axis']} x={r['value']:<4} N={r['N']:<4} K={r['K']:<3} "
              f"I={r['dim_infer_invocations']:<3} measured={r['measured_units']:<12} "
              f"predicted={r['predicted_units']:<12} ratio={rt}")
    print("\n=== PHASE 1 §3.1 — CODEBOOK CENSUS (static manifests) ===")
    for r in doc["codebook_census_attempting"]:
        print(f"  {r['seed']:<40} K_total={r['K_total']:<5} "
              f"K_eligible={r['K_eligible']:<5} K_attempting={r['K_attempting']}")
    print(f"  LIVE boot_core: {doc['codebook_census_live_boot']}")
    print("\n=== PHASE 1 §3.1 — REAL VISION WORKLOAD (sdloop_vision) ===")
    for r in doc["real_vision_codebook"]:
        print(f"  n_thetas={r['n_thetas']:<3} mints={r['codebook']['mints']:<3} "
              f"shape_signatures={r['codebook']['shape_signatures']:<3} "
              f"support_N={r['support_N_min']}-{r['support_N_max']}")


if __name__ == "__main__":
    main()
