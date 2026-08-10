#!/usr/bin/env python
"""arc6_valuelayer_searchspace — DID THE VALUE LAYER MOVE THE SEARCH SPACE?

Registered hazard: `op:TupleOf` blew distinct candidates **167 -> 14,709**
because tuples never collide and so defeat observational-equivalence
pruning (`PROGRAM_SYNTHESIS_ARC6_TIER0.md`). `Value::List` is exactly the
same kind of change — `synth_enumerate::canon_repr` now gives a `List` a
DIFFERENT prefix from a `Tuple`, so two candidates that used to be one
signature can become two.

So this is MEASURED, not assumed. It prints `distinct` / `enumerated` /
`halt_reason` / `found` for a fixed set of specs, on whichever engine is
loaded. Run it once on the FINAL engine and once on the archived baseline
(swap `runners/dsl/python/substrate_rs/_native.abi3.so`) and diff.

  OZMA_NO_LLM=1 python scripts/arc6_valuelayer_searchspace.py <label>
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains.engine_provenance import engine_preamble, provenance_stamp  # noqa: E402
engine_preamble()
import substrate_rs as srs  # noqa: E402

SUB = srs.Substrate()


def L(v):
    return {"type": "Lit", "value": v}


def synth(rows, ops=None, max_size=9, wire=True):
    if wire:
        # WITHOUT this the probe measures nothing: JSON has one array type,
        # so a list-expected and a tuple-expected spec arrive at the engine
        # IDENTICAL (both `Value::Tuple`) and the two rows below would be
        # the same experiment. `_wire` is the adapter's own type-faithful
        # `Lit` encoding (arc6_valuelayer_patch.py).
        from domains.prog_synthesis import _wire_rows
        rows = _wire_rows(rows)
    spec = {"type": "SynthEnumerate", "examples": L(rows),
            "max_size": max_size, "max_candidates": 0,
            "saturate_k": 0, "field": ""}
    if ops is not None:
        spec["ops"] = L(ops)
    return SUB._inner.evaluate(spec, {})


# Fixed specs, chosen to span the shapes the change can touch:
#   scalar-only (must be untouched), list-shaped with a LIST expected,
#   list-shaped with a TUPLE expected, and the TupleOf hazard's own shape.
SPECS = {
    "scalar_arith": ([{"inputs": {"a": 2, "b": 3}, "output": 5},
                      {"inputs": {"a": 4, "b": 1}, "output": 5},
                      {"inputs": {"a": 7, "b": 2}, "output": 9}], None),
    "scalar_len": ([{"inputs": {"xs": [1, 2, 3]}, "output": 3},
                    {"inputs": {"xs": [4]}, "output": 1},
                    {"inputs": {"xs": []}, "output": 0}], None),
    "list_expected_map": ([{"inputs": {"xs": [[1, 2], [3, 4]]}, "output": [1, 3]},
                           {"inputs": {"xs": [[9], [7, 8]]}, "output": [9, 7]}], None),
    "tuple_expected_map": ([{"inputs": {"xs": [[1, 2], [3, 4]]}, "output": (1, 3)},
                            {"inputs": {"xs": [[9], [7, 8]]}, "output": (9, 7)}], None),
    "list_expected_filter": ([{"inputs": {"xs": [1, -2, 3, -4]}, "output": [1, 3]},
                              {"inputs": {"xs": [-1, 5]}, "output": [5]}], None),
    "tupleof_pair": ([{"inputs": {"a": 1, "b": 2}, "output": (2, 1)},
                      {"inputs": {"a": 8, "b": 3}, "output": (3, 8)}], None),
}


def main() -> None:
    label = sys.argv[1] if len(sys.argv) > 1 else "snapshot"
    rows = {}
    for name, (ex, ops) in SPECS.items():
        for tag, wire in (("wired", True), ("bare_json_control", False)):
            try:
                out = synth(ex, ops, wire=wire)
            except Exception as e:  # noqa: BLE001 — the baseline engine has no _wire path
                rows[f"{name}::{tag}"] = {"error": str(e)[:120]}
                continue
            rows[f"{name}::{tag}"] = {k: out.get(k) for k in
                                      ("found", "distinct", "enumerated",
                                       "halt_reason", "size")}
            rows[f"{name}::{tag}"]["found"] = bool(out.get("found"))
    rec = {"label": label, "engine_provenance": provenance_stamp(), "specs": rows}
    out_path = os.path.join(ROOT, "results", "arc6_valuelayer_searchspace_%s.json" % label)
    with open(out_path, "w") as f:
        json.dump(rec, f, indent=2, sort_keys=True)
    print("engine", rec["engine_provenance"]["short"])
    for k, v in rows.items():
        print(f"  {k:24s} {v}")
    print("wrote", out_path)


if __name__ == "__main__":
    main()
