#!/usr/bin/env python3
"""THE `I` = 17 QUESTION — are the seventeen `DimInfer` invocations per
recognising fixpoint seventeen DISTINCT decodes, or sixteen re-derivations?

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***

Pre-registration: `VISION_DIM_INFER_ARGS_PREREG.md`, committed at `a04758ee`
BEFORE the instrument existed and before any measurement.

WHY. `VISION_IDENTITY_COST_ANATOMY_RESULTS.md` §5.4 closed the identity-cost
line with one unexplained factor. The coefficient is `I x K x SP x N x (1+s)`;
`N`, `(1+s)` and `K` are real data, `SP` = 13 was PROVED non-prunable by the
codebook rung, and `I` = 17 was measured INVARIANT across 11.8x of N and 16x of
K -- and 2 on the novel path. Because the recognising path spends 8.5x more
invocations than the failing one, `I` is what holds compute-proportional-to-
surprise down to a MAGNITUDE of 1.33 even though the codebook fix corrected its
SIGN. `I` caps the property the architecture wants.

No existing counter can settle it: `term_eval:DimInfer` counts invocations, and
an invocation counts the same whether or not it recomputes a value already
computed. So this rung records each invocation's ARGUMENTS (Rust:
`shape_decode.rs::encode_dim_infer_args` -> `scale_audit::dim_infer_args`) and
counts DISTINCT tuples.

STEP 0 IS THE WHOLE RISK HERE, AND IT IS A NEW KIND OF RISK. A DISTINCTNESS
statistic has two OPPOSITE failure modes and each one FAKES one of the two
hypotheses:

    encoding carries something incidental -> distinct == calls always
                                          -> fakes IRREDUCIBLE
    encoding collapses a real determinant -> distinct == 1 always
                                          -> fakes RE-DERIVATION

Neither is caught by any gate that asks "is it non-zero?". And critically,
NEITHER IS CAUGHT BY G5 ON THE INHERITED N / K / PATH AXES -- on N and K the
honest answer is a CONSTANT, so a broken counter and a correct one are
indistinguishable there. This rung therefore ADDS A FOURTH AXIS, DISTINCTNESS,
with ground truth known BY CONSTRUCTION (prereg §3). D-CODEBOOK is the control
that decides whether the rung can rule at all: it is the positive control for
the very mechanism the irreducibility hypothesis names.

The G5 verdict is NOT reimplemented in Python: `AUDIT.scale_audit_g5_verdict`
hands off to `runners/dsl/src/g5.rs`.

SEEDS: block 88000-88999 (prereg §4).

USAGE
    python scripts/dim_infer_args.py --out results/dim_infer_args.json
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import sys

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
SEED_BASE = 88000          # prereg §4 -- block 88000-88999
DECOY_BASE = SEED_BASE + 100
M_POINTS = 7
DT = ["pred", "coord:r", "coord:c", "val"]

ORD = "dim_infer_arg_distinct_ordered"
UNORD = "dim_infer_arg_distinct_unordered"
CALLS = "dim_infer_arg_calls"
I_COUNTER = "term_eval:DimInfer"


def load_state() -> dict:
    with open("/proc/loadavg") as fh:
        p = fh.read().split()
    return {"load1": float(p[0]), "load5": float(p[1]), "load15": float(p[2])}


def machine() -> dict:
    return {"platform": platform.platform(), "python": sys.version.split()[0],
            "cpu_count": os.cpu_count()}


def _counted(fn):
    """Run `fn` with the audit ON; return (counters, fn's return)."""
    gc.collect()
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    try:
        out = fn()
    finally:
        AUDIT.scale_audit_set_enabled(False)
    return counters(), out


# --------------------------------------------------------------------------- #
def synth_cells(n, seed=SEED_BASE):
    """Deterministic pseudo-random cell set of exactly `n` relations. A plain
    LCG, auditable in three lines, drawn from THIS rung's seed block."""
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


def point_S(n_cells, k_codebook=1, path="exact"):
    """ONE sd/identity decode through the seeded rule loop -- the same
    construction the identity-cost rung measured `I` = 17 on, rebuilt on THIS
    rung's seed block so no seed is shared across rungs.

      exact -- held[0] IS the target => explained at length 1 => the
               short-circuit FIRES (the recognising path, where I = 17).
      novel -- the target is in NO codebook entry => nothing is explained =>
               the short-circuit CANNOT fire (where I = 2).
    """
    cells = synth_cells(n_cells)
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for i in range(k_codebook):
        if path == "exact" and i == 0:
            sig = cells
        else:
            sig = synth_cells(n_cells, seed=DECOY_BASE + i)
        s.add_node("ShapeSignature",
                   {"name": f"held{i}", "signature": json.dumps(sig),
                    "kind": "faculty", "faculty": f"held{i}", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation",
                     {"signature": cells, "key": ["probe"], "status": "decoded",
                      "residual": cells, "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)

    c, _ = _counted(native.run_rules)
    # LIVENESS (PROTOCOL §1.1: "scores at the floor" is satisfied by DEATH).
    status = s.node(obs)["attrs"].get("status")
    del s, ag, native
    return c, status


# --------------------------------------------------------------------------- #
# THE DISTINCTNESS AXIS -- prereg §3. Ground truth KNOWN BY CONSTRUCTION.
#
# These drive `DimInfer` DIRECTLY (`native.evaluate`) rather than through the
# rule loop, because the point is to control the argument tuple exactly. They
# are the Python twins of `shape_decode.rs::dim_infer_tests`' D-controls, run
# against the SHIPPED ENGINE -- the stronger location, since it is the binary
# that produces every number below.
# --------------------------------------------------------------------------- #
TROMINO = [["cell", 0, 0, "red"], ["cell", 0, 1, "red"], ["cell", 1, 0, "red"]]
ROT_K1 = [["cell", 0, 0, "red"], ["cell", 0, 1, "red"], ["cell", 1, 1, "red"]]


def _d_boot(n_parts=1):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for i in range(n_parts):
        s.add_node("ShapeSignature",
                   {"name": f"Base{i}", "signature": json.dumps(TROMINO),
                    "kind": "faculty", "faculty": f"Base{i}", "dim_types": DT})
    return s, ag, native


def _di(native, goal):
    return native.evaluate({"type": "DimInfer", "goal": {"type": "Lit", "value": goal}}, {})


def _shift(goal, dr):
    return [[p, r + dr, c, v] for (p, r, c, v) in goal]


def d_red(n=M_POINTS):
    """D-RED -- the COLLAPSE DETECTOR. `n` evaluations of the SAME decode on an
    UNCHANGED graph. GROUND TRUTH: calls n, distinct 1, EXACTLY.

    A counter reading `n` is recording something that is not an argument, and
    would report IRREDUCIBLE no matter what the engine did."""
    s, ag, native = _d_boot()
    c, _ = _counted(lambda: [_di(native, ROT_K1) for _ in range(n)])
    return {"n": n, "calls": int(c.get(CALLS, 0)),
            "distinct_ordered": int(c.get(ORD, 0)),
            "distinct_unordered": int(c.get(UNORD, 0)),
            "ground_truth": {"calls": n, "distinct": 1}}


def d_green(n=M_POINTS):
    """D-GREEN -- DISCRIMINATION. `n` evaluations with DIFFERENT goals.
    GROUND TRUTH: calls n, distinct n, EXACTLY.

    A counter reading 1 has collapsed a real determinant and would report
    re-derivation that is not there."""
    s, ag, native = _d_boot()
    c, _ = _counted(lambda: [_di(native, _shift(ROT_K1, i)) for i in range(n)])
    return {"n": n, "calls": int(c.get(CALLS, 0)),
            "distinct_ordered": int(c.get(ORD, 0)),
            "distinct_unordered": int(c.get(UNORD, 0)),
            "ground_truth": {"calls": n, "distinct": n}}


def d_codebook(n=M_POINTS):
    """D-CODEBOOK -- **the control that decides whether this rung can rule at
    all.** `n` evaluations, SAME goal, the codebook GROWN BY ONE PART between
    each. GROUND TRUTH: calls n, distinct n, EXACTLY.

    The irreducibility hypothesis's entire content is "a decode mints graph
    state, so the next invocation sees something different". An encoder that
    covered only the goal would pass D-RED and D-GREEN and be STRUCTURALLY
    BLIND to exactly that -- it would read distinct = 1 and this rung would
    report re-derivation, confidently and wrongly."""
    s, ag, native = _d_boot()

    def go():
        for i in range(n):
            _di(native, ROT_K1)
            s.add_node("ShapeSignature",
                       {"name": f"Grown{i}",
                        "signature": json.dumps(_shift(TROMINO, 10 + i)),
                        "kind": "faculty", "faculty": f"Grown{i}", "dim_types": DT})

    c, _ = _counted(go)
    return {"n": n, "calls": int(c.get(CALLS, 0)),
            "distinct_ordered": int(c.get(ORD, 0)),
            "distinct_unordered": int(c.get(UNORD, 0)),
            "ground_truth": {"calls": n, "distinct": n}}


def d_sweep(m=M_POINTS):
    """D-SWEEP -- the G5 series on the distinctness axis. `J` distinct-goal
    decodes for J in 1..m must read distinct = 1,2,...,m; the fixed-J control
    must have span 0."""
    rows, ctrl = [], []
    for j in range(1, m + 1):
        s, ag, native = _d_boot()
        c, _ = _counted(lambda: [_di(native, _shift(ROT_K1, i)) for i in range(j)])
        rows.append({"J": j, "counters": c})
    for _ in range(m):
        s, ag, native = _d_boot()
        c, _ = _counted(lambda: [_di(native, ROT_K1)])
        ctrl.append({"counters": c})
    return {"axis": "D", "label": "DISTINCTNESS -- J distinct-goal decodes",
            "iv": "distinct goals", "values": list(range(1, m + 1)),
            "rows": rows, "control": ctrl}


# --------------------------------------------------------------------------- #
N_VALUES = [12, 20, 37, 58, 93, 123, 142]
K_VALUES = [1, 2, 3, 5, 8, 12, 16]
P_VALUES = ["exact", "novel"]
N_FIXED = 58
K_FIXED = 1

SWEEPS = {
    "N": ("sd signature cells (K=1, path=exact)",
          lambda v: point_S(v, k_codebook=K_FIXED, path="exact"), N_VALUES),
    "K": ("sd CODEBOOK ENTRIES (N=%d, path=exact)" % N_FIXED,
          lambda v: point_S(N_FIXED, k_codebook=v, path="exact"), K_VALUES),
    "P": ("PATH -- exact vs novel (N=%d, K=1)" % N_FIXED,
          lambda v: point_S(N_FIXED, k_codebook=K_FIXED, path=v), P_VALUES),
}


def run_sweep(axis):
    label, fn, values = SWEEPS[axis]
    print(f"[SWEEP-{axis}] {label}", flush=True)
    rows = []
    for v in values:
        c, status = fn(v)
        rows.append({"value": v, "axis_x": float(v) if axis != "P" else None,
                     "counters": c, "liveness": status, "load": load_state()})
        print(f"  x={str(v):>6} I={c.get(I_COUNTER)} calls={c.get(CALLS)} "
              f"distinct={c.get(ORD)}/{c.get(UNORD)}  {status or ''}", flush=True)

    print(f"[SWEEP-{axis}] control at x={values[0]} x{M_POINTS}", flush=True)
    ctrl = []
    for _ in range(M_POINTS):
        c, _ = fn(values[0])
        ctrl.append({"counters": c})
    return {"axis": axis, "label": label, "values": values,
            "rows": rows, "control": ctrl}


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
    """STEP 0 -- G5 on every axis this rung varies, for every `term_*` counter
    AND the three new `dim_infer_arg_*` ones."""
    out = {}
    for axis, sw in sweeps.items():
        names = sorted({n for r in sw["rows"] + sw["control"] for n in r["counters"]
                        if n.startswith("term_unit") or n.startswith("term_eval")
                        or n.startswith("dim_infer_arg")})
        out[axis] = [g5_for(sw, n) for n in names]
    return out


def conservation(sweeps):
    """PREREG §3.1 -- `dim_infer_arg_calls` MUST equal `term_eval:DimInfer` at
    every point. If it does not, the recording site is not on the path the
    invocation counter counts and the comparison to `I` is meaningless."""
    bad = []
    n = 0
    for axis, sw in sweeps.items():
        for r in sw["rows"] + sw["control"]:
            c = r["counters"]
            n += 1
            if int(c.get(CALLS, 0)) != int(c.get(I_COUNTER, 0)):
                bad.append({"axis": axis, "calls": int(c.get(CALLS, 0)),
                            "I": int(c.get(I_COUNTER, 0))})
    return {"points_checked": n, "mismatches": bad, "ok": not bad}


def headline():
    """THE READ -- N=142, K=1, path exact: the exact point at which `I` = 17
    was measured by the identity-cost rung."""
    c, status = point_S(142, k_codebook=1, path="exact")
    I = int(c.get(I_COUNTER, 0))
    o, u = int(c.get(ORD, 0)), int(c.get(UNORD, 0))
    return {"n_cells": 142, "K": 1, "path": "exact", "liveness": status,
            "I": I, "calls": int(c.get(CALLS, 0)),
            "distinct_ordered": o, "distinct_unordered": u,
            "verdict": ("IRREDUCIBLE" if o == I and u == I else "REDUCIBLE"),
            "redundant_fraction_ordered": ((I - o) / I) if I else None,
            "redundant_fraction_unordered": ((I - u) / I) if I else None,
            "all_counters": c, "load": load_state()}


def controls_pass(d):
    """PREREG §3 -- every control must hit its DECLARED ground truth exactly.
    If any fails, NO `distinct` figure is reported as a result: the rung's
    outcome is the instrument failure."""
    out = {}
    for name in ("d_red", "d_green", "d_codebook"):
        r = d[name]
        gt = r["ground_truth"]
        out[name] = (r["calls"] == gt["calls"]
                     and r["distinct_ordered"] == gt["distinct"]
                     and r["distinct_unordered"] == gt["distinct"])
    sw = series(d["d_sweep"]["rows"], ORD)
    ct = series(d["d_sweep"]["control"], ORD)
    out["d_sweep_series"] = sw == list(range(1, len(sw) + 1))
    out["d_sweep_g5"] = AUDIT.scale_audit_g5_verdict(sw, ct) == "RESPONSIVE"
    out["ALL"] = all(out.values())
    return out


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/dim_infer_args.json")
    args = ap.parse_args()

    print(provenance_line(), flush=True)

    print("[step0] THE DISTINCTNESS AXIS -- ground truth by construction",
          flush=True)
    d = {"d_red": d_red(), "d_green": d_green(), "d_codebook": d_codebook(),
         "d_sweep": d_sweep()}
    for k in ("d_red", "d_green", "d_codebook"):
        r = d[k]
        print(f"  {k:<12} calls={r['calls']:>3} distinct={r['distinct_ordered']:>3}"
              f"/{r['distinct_unordered']:<3} ground truth "
              f"calls={r['ground_truth']['calls']} distinct={r['ground_truth']['distinct']}",
              flush=True)
    cp = controls_pass(d)
    print(f"  CONTROLS: {cp}", flush=True)

    sweeps = {axis: run_sweep(axis) for axis in ("N", "K", "P")}
    sweeps_all = dict(sweeps)
    sweeps_all["D"] = d["d_sweep"]

    print("[step0] G5 on all four axes", flush=True)
    s0 = step0(sweeps_all)
    cons = conservation(sweeps)
    print(f"[conservation] calls == term_eval:DimInfer -> {cons['ok']} "
          f"({cons['points_checked']} points)", flush=True)

    print("[headline] N=142 K=1 exact", flush=True)
    hl = headline()

    doc = {
        "provenance": provenance_line(),
        "machine": machine(),
        "load_at_start": load_state(),
        "prereg": "VISION_DIM_INFER_ARGS_PREREG.md @ a04758ee",
        "seed_block": [88000, 88999],
        "distinctness_axis": d,
        "controls_pass": cp,
        "sweeps": sweeps_all,
        "step0_g5": s0,
        "conservation": cons,
        "headline": hl,
    }
    os.makedirs(os.path.dirname(os.path.join(ROOT, args.out)), exist_ok=True)
    with open(os.path.join(ROOT, args.out), "w") as fh:
        json.dump(doc, fh, indent=2)
    print(f"[out] {args.out}", flush=True)

    print("\n=== STEP 0 (G5) ===")
    for axis, rows in s0.items():
        for r in rows:
            if r["counter"].startswith("dim_infer_arg") or r["counter"] == I_COUNTER \
               or r["counter"] == "term_unit:DimInfer":
                print(f"  [{axis}] {r['counter']:<34} {r['verdict']:<11} {r['sweep']}")
    print("\n=== HEADLINE ===")
    print(f"  I (term_eval:DimInfer)      = {hl['I']}")
    print(f"  dim_infer_arg_calls         = {hl['calls']}")
    print(f"  distinct (ordered)          = {hl['distinct_ordered']}")
    print(f"  distinct (unordered)        = {hl['distinct_unordered']}")
    print(f"  VERDICT                     = {hl['verdict']}")
    print(f"  redundant fraction          = {hl['redundant_fraction_ordered']}")


if __name__ == "__main__":
    main()
