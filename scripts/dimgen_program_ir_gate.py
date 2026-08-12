"""dimgen_program_ir_gate.py — AR-1 live demonstration for
docs/research/engine_substrate/DIMGEN_PROGRAM_IR_PREREG.md.

MEASUREMENT / INVESTIGATION CODE, not agent decision logic (same class as
`scripts/rule_signature_program_gate.py`, whose three-way byte-identity
pattern this script reuses for a different pairing). No graph-state
conditionals, no agent behaviour — it boots a fresh substrate, mints ONE
isolated test-scoped `DimensionGenerator{kind:"linear"}` fixture (never
installed into any shipped seed), installs a Program IR subgraph for the
same formula, and compares three independently-computed renderings of one
integer lattice under one linear map:

  (a) a plain-Python reference implementation of the formula
      (`out_i = sum_j M[i][j] * (v_j - min_j)`), typed independently of
      either engine path;
  (b) the real Rust `DimInfer` Term (`native.evaluate`), which internally
      calls `apply_linear_once` (`runners/dsl/src/shape_decode.rs`) — read
      off via its `identity`/`explained`/`dims` output fields, since
      `apply_linear_once` itself has no direct Python binding (see
      PREREG §0);
  (c) `ProgEval` executing a Program IR subgraph for the identical
      pointwise formula, installed via `add_term_subgraph` and READ BACK
      via `term_subgraph_json` before execution — so what runs is what the
      graph holds, exactly like `domains/rule_signature.py::
      signature_program`.

Run standalone: `python3 scripts/dimgen_program_ir_gate.py`.
"""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble(strict=False)

from substrate.boot_core import boot_core  # noqa: E402
from domains.prog_ir_emit import emit_prog_ir  # noqa: E402


# --------------------------------------------------------------------------- #
# The lattice and the matrix — fixed, registered in the PREREG before this
# script's output was inspected.
# --------------------------------------------------------------------------- #
LATTICE = [(2, 5), (2, 7), (4, 5), (4, 7)]
VAL = "x"
PRED = "cell"
# Row-major 2x2, matching apply_linear_once's `matrix[i*n+j]` reading
# (shape_decode.rs:768-772): M = [[0,-1],[1,0]].
M00, M01, M10, M11 = 0, -1, 1, 0


def python_reference_goal():
    min_r = min(r for r, c in LATTICE)
    min_c = min(c for r, c in LATTICE)
    out = []
    for r, c in LATTICE:
        v0 = r - min_r
        v1 = c - min_c
        out0 = M00 * v0 + M01 * v1
        out1 = M10 * v0 + M11 * v1
        out.append((PRED, out0, out1, VAL))
    return out, min_r, min_c


def linear_map_point(v0, v1, min0, min1, m00, m01, m10, m11):
    x0 = v0 - min0
    x1 = v1 - min1
    out0 = m00 * x0 + m01 * x1
    out1 = m10 * x0 + m11 * x1
    return (out0, out1)


def main() -> int:
    goal, min_r, min_c = python_reference_goal()
    print("(a) python-reference goal:", goal)

    s, ag = boot_core()
    native = s._inner

    # --- (b) the real Rust DimInfer / apply_linear_once path -------------- #
    held_sig = [[PRED, r, c, VAL] for r, c in LATTICE]
    part = s.add_node("ShapeSignature", {
        "name": "dimgen_gate_linear_part",
        "signature": json.dumps(held_sig),
        "kind": "faculty",
        "faculty": "dimgen_gate_linear_part",
        "dim_types": ["pred", "coord:r", "coord:c", "val"],
    })
    gen = s.add_node("DimensionGenerator", {
        "name": "dimgen_gate_linear_demo",
        "kind": "linear",
        "coord_dims": [1, 2],
        "matrix": [M00, M01, M10, M11],
        "params": [1],
    })

    goal_lit = [list(row) for row in goal]
    dim_infer_out = native.evaluate(
        {"type": "DimInfer",
         "goal": {"type": "Lit", "value": goal_lit},
         "field": ""},
        {})
    print("(b) DimInfer output:", dim_infer_out)

    b_identity = bool(dim_infer_out.get("identity"))
    b_explained = bool(dim_infer_out.get("explained"))
    b_dims = dim_infer_out.get("dims")
    b_generator = dim_infer_out.get("generator")

    # --- (c) Program IR, installed as graph data, executed by ProgEval ---- #
    emitted = emit_prog_ir(inspect.getsource(linear_map_point))
    if not emitted.get("ok"):
        print("(c) emit_prog_ir FAILED:", emitted.get("blockers"))
        return 1
    root = native.add_term_subgraph(emitted["ir"])
    back = native.term_subgraph_json(root)
    ir = json.loads(back) if isinstance(back, str) else back
    assert ir == emitted["ir"], "graph-resident IR must round-trip byte-identical"

    c_rendered = []
    for r, c in LATTICE:
        env = {"v0": r, "v1": c, "min0": min_r, "min1": min_c,
               "m00": M00, "m01": M01, "m10": M10, "m11": M11}
        term = {"type": "ProgEval", "prog": ir,
                "env": {"type": "Lit", "value": env},
                "oracles": {"type": "Lit", "value": {}},
                "fuel": 100_000, "field": ""}
        out = native.evaluate(term, {})
        if out.get("trap") is not None or not out.get("halted"):
            print("(c) ProgEval TRAPPED on", (r, c), out)
            return 1
        c_rendered.append(tuple(out.get("result")))
    print("(c) ProgEval rendering:", c_rendered)

    a_rendered = [(row[1], row[2]) for row in goal]
    c_matches_a = (a_rendered == c_rendered)

    print()
    print("=== VERDICT ===")
    print(f"(a) vs (c) element-wise equal : {c_matches_a}")
    print(f"(b) DimInfer identity=True    : {b_identity}")
    print(f"(b) DimInfer explained=True   : {b_explained}")
    print(f"(b) DimInfer dims==()         : {b_dims == ()}")
    print(f"(b) DimInfer generator        : {b_generator!r}")

    go = c_matches_a and b_identity and b_explained and (b_dims == ())
    print()
    print("GATE:", "PASS (GO)" if go else "FAIL (NO-GO)")
    return 0 if go else 2


if __name__ == "__main__":
    raise SystemExit(main())
