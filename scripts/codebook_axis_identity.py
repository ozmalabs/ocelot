#!/usr/bin/env python3
"""BYTE-IDENTITY + PROPERTY-COST harness for the Occam short-circuit.

*** THIS SCRIPT CHANGES NO BEHAVIOUR. IT CAPTURES VERDICTS. ***

Pre-registration `VISION_CODEBOOK_AXIS_PREREG.md` @ `e22db8dd` (§4.1, §6).

THE GATE. `eval_dim_infer`'s length-2 arm is skipped when any length-1 success
exists. That is exact by the Occam comparator's definition, but "exact by
argument" is what byte-identity exists to check rather than accept. This script
dumps EVERY field of EVERY DimInfer verdict across a grid that exercises BOTH
branches, so the diff is over values and not over reasoning.

  * `checked` IS INCLUDED, and is the sharpest cell in the table. The prereg
    declared it as the fix's one hazard BEFORE the fix existed (it is a RETURNED
    field, so a naive skip shrinks it). The implementation places the skip after
    `checked += 1` specifically to preserve it, so `checked` moving here would
    mean the preservation failed — it is a live tripwire, not decoration.

  * A move in any VERDICT field (`explained`/`base`/`generator`/`k`/`length`/
    `generators`/`ks`/`latent_name`/`transforms`/`dims`/`identity`) means the
    prune dropped a candidate that could have won. Per prereg §4.1 that STOPS
    the fix and is reported as a finding. It is not a tuning signal.

THE PROPERTY-COST CHECK (§6). Batch-apply held byte-identity over 235,200 values
and still destroyed compute-∝-surprise, unnoticed for two rungs. Byte-identity
is NOT property-identity. So this script also records `term_unit:DimInfer` per
arm, split by whether the observation was EXPLAINED at length 1, and reports the
unexplained:explained cost ratio. A fix that FLATTENS that ratio is rejected even
with byte-identity green.

SEEDS: block 68000-68999.

USAGE
    python scripts/codebook_axis_identity.py --out results/codebook_axis_identity_NEW.json
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

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

SEED_BASE = 68000
DT = ["pred", "coord:r", "coord:c", "val"]


def synth_cells(n, seed):
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


def rot90(cells, times):
    """A GENUINE rotation of the observation, so the length-1 arm actually
    succeeds and the short-circuit actually FIRES. Without a branch that fires,
    a byte-identity pass would prove nothing about the skip."""
    out = [list(c) for c in cells]
    for _ in range(times % 4):
        out = [[c[0], c[2], -c[1]] + list(c[3:]) for c in out]
    # Re-base to a non-negative origin (the generators origin-normalize).
    if out:
        mr = min(c[1] for c in out)
        mc = min(c[2] for c in out)
        out = [[c[0], c[1] - mr, c[2] - mc] + list(c[3:]) for c in out]
    return out


def _norm(v):
    """JSON-safe, order-stable normalisation. Tuples and lists both land as
    lists so a container-type difference cannot masquerade as a value change
    (and `native.evaluate()` returning TUPLES not lists is a documented trap in
    this tree)."""
    if isinstance(v, dict):
        return {str(k): _norm(v[k]) for k in sorted(v, key=str)}
    if isinstance(v, (list, tuple)):
        return [_norm(x) for x in v]
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def one_case(n_cells, k_codebook, obs_kind, seed):
    """One decode. Returns (verdict_record, counters)."""
    held = synth_cells(n_cells, seed)
    if obs_kind == "exact":
        obs_cells = held
    elif obs_kind == "rot1":
        obs_cells = rot90(held, 1)
    elif obs_kind == "rot2":
        obs_cells = rot90(held, 2)
    elif obs_kind == "novel":
        obs_cells = synth_cells(n_cells, seed + 500)
    else:
        raise ValueError(obs_kind)

    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for i in range(k_codebook):
        sig = held if i == 0 else synth_cells(n_cells, seed + 1000 + i)
        s.add_node("ShapeSignature",
                   {"name": f"held{i}", "signature": json.dumps(sig),
                    "kind": "faculty", "faculty": f"held{i}", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation",
                     {"signature": obs_cells, "key": ["probe"], "status": "decoded",
                      "residual": obs_cells, "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)

    gc.collect()
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    try:
        native.run_rules()
    finally:
        AUDIT.scale_audit_set_enabled(False)
    c = counters()

    at = s.node(obs)["attrs"]
    rec = {
        "case": {"N": n_cells, "K": k_codebook, "obs": obs_kind, "seed": seed},
        # THE FULL DimInfer RESULT DICT -- every field, `checked` included.
        "dim_infer": _norm(at.get("dim_infer")),
        # The surrounding verdict the seed rules derived from it.
        "status": _norm(at.get("status")),
        "covered_by": _norm(at.get("covered_by")),
        "transform_checked": _norm(at.get("transform_checked")),
        "transform_explained": _norm(at.get("transform_explained")),
        "dim_checked": _norm(at.get("dim_checked")),
        "dim_explained": _norm(at.get("dim_explained")),
        "transforms": [_norm(s.node(t)["attrs"]) for t in s.neighbours(obs, "has_transform")],
        "latent_dims": sorted(_norm(s.node(t)["attrs"].get("name"))
                              for t in s.nodes("LatentDimension")),
    }
    cost = {"term_unit:DimInfer": int(c.get("term_unit:DimInfer", 0)),
            "term_units_total": int(c.get("term_units_total", 0)),
            "term_eval:DimInfer": int(c.get("term_eval:DimInfer", 0))}
    del s, ag, native
    return rec, cost


def count_values(obj):
    """How many scalar cells the diff actually covers -- reported rather than
    claimed, so 'byte-identical over X values' is an audited number."""
    if isinstance(obj, dict):
        return sum(count_values(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return sum(count_values(v) for v in obj)
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    print(provenance_line(), flush=True)

    records, costs = [], []
    # THE GRID -- both branches, deliberately. `exact`/`rot1`/`rot2` are
    # explained at length 1 (short-circuit FIRES); `novel` is explained by
    # nothing (short-circuit does NOT fire, all 147 attempts run).
    for obs_kind in ("exact", "rot1", "rot2", "novel"):
        for n in (12, 20, 37, 58):
            for k in (1, 2, 3, 5, 8):
                seed = SEED_BASE + 200 + n * 10 + k
                rec, cost = one_case(n, k, obs_kind, seed)
                records.append(rec)
                costs.append({"case": rec["case"], **cost})
                print(f"  {obs_kind:<6} N={n:<3} K={k:<2} "
                      f"status={rec['status']} dim_expl={rec['dim_explained']} "
                      f"units={cost['term_unit:DimInfer']}", flush=True)

    doc = {"provenance": provenance_line(), "prereg_commit": "e22db8dd",
           "seed_block": "68000-68999",
           "records": records, "costs": costs,
           "n_cases": len(records), "n_values": count_values(records)}
    with open(os.path.join(ROOT, args.out), "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    print(f"\nwrote {args.out}  ({doc['n_cases']} cases, {doc['n_values']} values)")


if __name__ == "__main__":
    main()
