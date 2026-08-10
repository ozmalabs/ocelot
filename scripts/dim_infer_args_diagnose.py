#!/usr/bin/env python3
"""NAMING THE MECHANISM behind `distinct` = 10 against `I` = 17.

*** DIAGNOSTIC. IT CHANGES NO BEHAVIOUR AND DEFINES NO STATISTIC. ***

The headline (`distinct_ordered` = `distinct_unordered` = 10, `I` = 17, at
N=142 K=1 exact) was measured and COMMITTED at `37510dff`, BEFORE this file
existed. Nothing here can move it -- this only explains it. A redundancy
fraction with no account of WHICH invocations repeat is a number nobody can
act on, and "name the mechanism, do not fix it" is the brief.

Two questions, both answered by reading the recorded encodings back:

  1. WHICH CALLS REPEAT -- the call-order trace of distinct-tuple indices.
  2. WHICH DETERMINANT MOVES between the 10 distinct tuples -- by diffing the
     encodings on the field prefixes `encode_dim_infer_args` writes
     (`md` / `fd` / `np` / `ng` / `goal`).

SEEDS: block 88000-88999 (shared with `dim_infer_args.py`, same rung, same
workload -- this re-runs THAT construction rather than inventing another).

USAGE
    python scripts/dim_infer_args_diagnose.py --out results/dim_infer_args_diagnose.json
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

from scripts.scale_split_measure import AUDIT, counters  # noqa: E402
from scripts.dim_infer_args import synth_cells, DT, SEED_BASE, DECOY_BASE  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402


def run_point(n_cells=142, k_codebook=1, path="exact"):
    """The IDENTICAL construction `dim_infer_args.point_S` measures, re-run
    with the trace and the encodings read back."""
    cells = synth_cells(n_cells)
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for i in range(k_codebook):
        sig = cells if (path == "exact" and i == 0) else synth_cells(n_cells, seed=DECOY_BASE + i)
        s.add_node("ShapeSignature",
                   {"name": f"held{i}", "signature": json.dumps(sig),
                    "kind": "faculty", "faculty": f"held{i}", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation",
                     {"signature": cells, "key": ["probe"], "status": "decoded",
                      "residual": cells, "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)

    gc.collect()
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    try:
        native.run_rules()
    finally:
        AUDIT.scale_audit_set_enabled(False)
    c = counters()
    trace = list(AUDIT.scale_audit_dim_infer_arg_trace())
    encs = [bytes(e) for e in AUDIT.scale_audit_dim_infer_arg_encodings()]
    status = s.node(obs)["attrs"].get("status")
    return c, trace, encs, status


# --------------------------------------------------------------------------- #
FIELDS = ["md", "fd", "np", "ng", "goal"]


def split_fields(enc: bytes) -> dict:
    """Split an encoding on the field markers `encode_dim_infer_args` writes.
    Structural, not a substring guess: the encoder emits
    `md<..>|fd<..>|np<n>|<parts>|ng<n>|<gens>|goal<n>[...]` and this reads
    exactly those boundaries."""
    s = enc.decode("utf-8", "replace")
    out = {}
    out["md"] = s.split("|", 1)[0]
    rest = s.split("|", 1)[1]
    out["fd"] = rest.split("|", 1)[0]
    rest = rest.split("|", 1)[1]
    np_i = rest.index("|ng")
    out["parts"] = rest[:np_i]
    rest2 = rest[np_i + 1:]
    goal_i = rest2.index("|goal")
    out["gens"] = rest2[:goal_i]
    out["goal"] = rest2[goal_i + 1:]
    return out


def which_fields_differ(encs: list[bytes]) -> dict:
    """For each field, how many DISTINCT values it takes across the recorded
    tuples. A field with 1 value is constant and explains nothing; the fields
    with >1 are the mechanism."""
    parsed = [split_fields(e) for e in encs]
    out = {}
    for k in ("md", "fd", "parts", "gens", "goal"):
        vals = {p[k] for p in parsed}
        out[k] = {"distinct_values": len(vals),
                  "constant": len(vals) == 1,
                  "lengths": sorted({len(p[k]) for p in parsed})}
    return out


def trace_summary(trace: list[int]) -> dict:
    """Which calls repeated which tuple."""
    first_seen, repeats = {}, []
    for pos, idx in enumerate(trace):
        if idx in first_seen:
            repeats.append({"call": pos, "repeats_call": first_seen[idx], "tuple": idx})
        else:
            first_seen[idx] = pos
    counts = {}
    for idx in trace:
        counts[idx] = counts.get(idx, 0) + 1
    return {"trace": trace, "n_calls": len(trace), "n_distinct": len(set(trace)),
            "repeat_events": repeats, "n_repeats": len(repeats),
            "per_tuple_call_count": {str(k): v for k, v in sorted(counts.items())}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/dim_infer_args_diagnose.json")
    args = ap.parse_args()
    print(provenance_line(), flush=True)

    doc = {"provenance": provenance_line(), "seed_block": [SEED_BASE, SEED_BASE + 999],
           "headline_pinned_at": "37510dff", "points": {}}

    for label, kw in (("exact_N142_K1", dict(n_cells=142, k_codebook=1, path="exact")),
                      ("novel_N142_K1", dict(n_cells=142, k_codebook=1, path="novel")),
                      ("exact_N58_K16", dict(n_cells=58, k_codebook=16, path="exact"))):
        c, trace, encs, status = run_point(**kw)
        ts = trace_summary(trace)
        fd = which_fields_differ(encs)
        doc["points"][label] = {
            "kw": kw, "liveness": status,
            "I": int(c.get("term_eval:DimInfer", 0)),
            "calls": int(c.get("dim_infer_arg_calls", 0)),
            "distinct_ordered": int(c.get("dim_infer_arg_distinct_ordered", 0)),
            "distinct_unordered": int(c.get("dim_infer_arg_distinct_unordered", 0)),
            "trace": ts, "fields": fd,
        }
        print(f"\n=== {label} ({status}) ===")
        print(f"  I={c.get('term_eval:DimInfer')} calls={c.get('dim_infer_arg_calls')} "
              f"distinct={c.get('dim_infer_arg_distinct_ordered')}")
        print(f"  trace           = {trace}")
        print(f"  repeats         = {ts['n_repeats']} "
              f"({[(r['call'], r['repeats_call']) for r in ts['repeat_events']]})")
        print(f"  calls per tuple = {ts['per_tuple_call_count']}")
        for k, v in fd.items():
            mark = "CONSTANT" if v["constant"] else f"VARIES ({v['distinct_values']} values)"
            print(f"    {k:<6} {mark}  lengths={v['lengths'][:4]}")

    os.makedirs(os.path.dirname(os.path.join(ROOT, args.out)), exist_ok=True)
    with open(os.path.join(ROOT, args.out), "w") as fh:
        json.dump(doc, fh, indent=2)
    print(f"\n[out] {args.out}")


if __name__ == "__main__":
    main()
