"""tests/test_dimgen_program_ir_migrated.py — gate for
docs/research/engine_substrate/DIMGEN_PROGRAM_IR_PREREG.md /
DIMGEN_PROGRAM_IR_RESULTS.md (CROSS_DOMAIN_SHAPE_SPIKE.md §7.4's slice):

"A physical transform and its formula are the same cross-frame map, and the
substrate can be made to demonstrate that behaviourally with no new
encoding."

Three gates:

1. AR-1 — the `linear` `DimensionGenerator` kind, exercised through the
   real `DimInfer` Term (which internally calls `apply_linear_once`,
   `runners/dsl/src/shape_decode.rs`), renders IDENTICALLY to `ProgEval`
   executing a graph-resident Program IR subgraph for the same pointwise
   formula, over a fixed integer lattice — a three-way chain through one
   common Python-reference computation, the same shape of comparison
   `RULE_SIGNATURE_TO_RUST_RESULTS.md` §4.1 ran for a different algorithm.
2. AR-2/3 — the five SHIPPED `DimensionGenerator`s (`seeds/
   shape_decode_loop.json`) are each P1-Program-IR-expressible at the
   per-cell-map grain, via the real unmodified `emit_prog_ir` harness.
3. The payoff — ONE edge type (`denotes_map`) linking a `DimensionGenerator`
   node to a Program IR root (`Term.ProgSeq`), gated by a REAL `Γ`
   `Production` (never `add_edge_unchecked`): a negative control proves the
   edge is refused with NO production declared (Type-2, vocabulary absent),
   and a positive case proves it is admitted once the production exists —
   paying off the debt `RULE_SIGNATURE_TO_RUST_RESULTS.md` §4.2 named and
   left unpaid ("declaring a real Γ production... is NOT done here").

This is test/measurement code exercising real graph mutations through the
substrate's own admissibility checker — not agent decision logic (no
conditional here decides agent behaviour; every assertion is a test
oracle). The `DimensionGenerator{kind:"linear"}` fixture and the
`denotes_map` production are test-scoped only: nothing here is installed
into any shipped seed.
"""
from __future__ import annotations

import inspect
import json

import pytest

pytest.importorskip("substrate_rs")
import substrate_rs  # noqa: E402

from substrate.boot_core import boot_core  # noqa: E402
from domains.prog_ir_emit import emit_prog_ir  # noqa: E402


# --------------------------------------------------------------------------- #
# Shared fixtures — the lattice + matrix from the PREREG, and the five
# shipped generators' per-cell maps.
# --------------------------------------------------------------------------- #
LATTICE = [(2, 5), (2, 7), (4, 5), (4, 7)]
VAL = "x"
PRED = "cell"
M00, M01, M10, M11 = 0, -1, 1, 0


def _python_reference_goal():
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


def rotation90_point(r, c, min_r, min_c, max_r0):
    r0 = r - min_r
    c0 = c - min_c
    new_r = c0
    new_c = max_r0 - r0
    return (new_r, new_c)


def reflection_point(v, max_v):
    return max_v - v


def scale2_point(v, min_v):
    return (v - min_v) * 2


def modular_point(v, modulus):
    return (v + 1) % modulus


SHIPPED_GENERATORS = [
    ("rotation90", rotation90_point),
    ("reflection_r", reflection_point),
    ("reflection_c", reflection_point),
    ("scale2", scale2_point),
    ("cycle4", modular_point),
]


def _install_program_ir(native, fn):
    emitted = emit_prog_ir(inspect.getsource(fn))
    assert emitted.get("ok"), f"{fn.__name__} not P1-emittable: {emitted.get('blockers')}"
    root = native.add_term_subgraph(emitted["ir"])
    back = native.term_subgraph_json(root)
    ir = json.loads(back) if isinstance(back, str) else back
    assert ir == emitted["ir"], "graph-resident IR must round-trip byte-identical"
    return root, ir


# ---------------------------------------------------------------------------
# 1 — AR-1: linear generator (DimInfer/apply_linear_once) vs ProgEval,
#     three-way through one Python reference, over a real integer lattice.
# ---------------------------------------------------------------------------
def test_linear_generator_and_program_ir_render_identically():
    goal, min_r, min_c = _python_reference_goal()
    a_rendered = [(row[1], row[2]) for row in goal]

    s, ag = boot_core()
    native = s._inner

    held_sig = [[PRED, r, c, VAL] for r, c in LATTICE]
    s.add_node("ShapeSignature", {
        "name": "dimgen_test_linear_part",
        "signature": json.dumps(held_sig),
        "kind": "faculty",
        "faculty": "dimgen_test_linear_part",
        "dim_types": ["pred", "coord:r", "coord:c", "val"],
    })
    s.add_node("DimensionGenerator", {
        "name": "dimgen_test_linear_demo",
        "kind": "linear",
        "coord_dims": [1, 2],
        "matrix": [M00, M01, M10, M11],
        "params": [1],
    })

    goal_lit = [list(row) for row in goal]
    dim_infer_out = native.evaluate(
        {"type": "DimInfer", "goal": {"type": "Lit", "value": goal_lit}, "field": ""}, {})

    assert dim_infer_out.get("explained") is True
    assert dim_infer_out.get("identity") is True
    assert dim_infer_out.get("dims") == ()
    assert dim_infer_out.get("generator") == "dimgen_test_linear_demo"

    root, ir = _install_program_ir(native, linear_map_point)

    c_rendered = []
    for r, c in LATTICE:
        env = {"v0": r, "v1": c, "min0": min_r, "min1": min_c,
               "m00": M00, "m01": M01, "m10": M10, "m11": M11}
        term = {"type": "ProgEval", "prog": ir,
                "env": {"type": "Lit", "value": env},
                "oracles": {"type": "Lit", "value": {}},
                "fuel": 100_000, "field": ""}
        out = native.evaluate(term, {})
        assert out.get("trap") is None and out.get("halted"), out
        c_rendered.append(tuple(out.get("result")))

    assert c_rendered == a_rendered, (
        "ProgEval's rendering of the Program IR formula must equal the "
        "plain-Python reference exactly, cell for cell")
    # Transitively: (b) DimInfer's apply_linear_once == (a) == (c) ProgEval.


# ---------------------------------------------------------------------------
# 2 — AR-3: the five SHIPPED DimensionGenerators are each P1-expressible
#     at the per-cell-map grain (real emit_prog_ir, no engine call needed).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name,fn", SHIPPED_GENERATORS)
def test_shipped_generator_pointwise_map_is_p1_expressible(name, fn):
    r = emit_prog_ir(inspect.getsource(fn))
    assert r.get("ok"), f"{name}: blockers={r.get('blockers')}"


# ---------------------------------------------------------------------------
# 3 — the payoff: ONE edge type + a REAL Γ production, never
#     add_edge_unchecked. Negative control (no production -> Type-2 refusal)
#     then positive (production declared -> admitted).
# ---------------------------------------------------------------------------
def test_denotes_map_edge_refused_without_production_admitted_with_it():
    s, ag = boot_core()
    native = s._inner

    root, _ir = _install_program_ir(native, linear_map_point)
    gen = s.add_node("DimensionGenerator", {
        "name": "dimgen_test_edge_demo",
        "kind": "linear",
        "coord_dims": [1, 2],
        "matrix": [M00, M01, M10, M11],
        "params": [1],
    })

    # Negative control: no production yet declared for
    # (DimensionGenerator, denotes_map, Term.ProgSeq) -> Type-2 refusal
    # (neither type is even in the grammar's vocabulary yet).
    with pytest.raises(substrate_rs.InadmissibleEdge):
        s.add_edge(gen, "denotes_map", root)

    # Declare the real production (never add_edge_unchecked).
    s.add_production({
        "src": {"type": "DimensionGenerator", "var": "g"},
        "edge_type": "denotes_map",
        "tgt": {"type": "Term.ProgSeq", "var": "p"},
        "provenance": "dimgen_program_ir:denotes_map",
    })

    # Positive: now admitted.
    s.add_edge(gen, "denotes_map", root)
    assert list(s.neighbours(gen, "denotes_map")) == [root]
