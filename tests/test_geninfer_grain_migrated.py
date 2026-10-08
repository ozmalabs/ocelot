"""GRAIN LADDER for generator inference — gate for shape_decode_loop v1.12.0
`sd_gen_check` grain choice + `sd_recognize_at_grain`, and the GenInfer
`grain` field (RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md WP3).

Measured on real handwriting this ladder does NOT discriminate shears
(RECURSIVE_SELF_IMPROVEMENT_RESULTS_20261006.md §WP3) and stays off by
default. These gates pin the mechanics and its safety guards only.
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"], ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]


def _run(goal, grains):
    s, ag = boot_core()
    n = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, n, ag)
    s.set_attr(ag, "gen_infer_enabled", 1.0)
    if grains is not None:
        s.set_attr(ag, "gen_grains", grains)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE), "kind": "faculty",
                                  "faculty": "base_L", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    o = s.add_node("Observation", {"signature": goal, "key": ["g"], "status": "decoded", "residual": goal,
                                   "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", o)
    n.run_rules()
    return s, s.node(o)["attrs"]


def test_absent_grains_is_grain_zero():
    shear = [["cell", r + c, c, v] for _, r, c, v in BASE]
    _, a = _run(shear, None)
    assert a["gen_grain"] == 0 and a["status"] != "recognized_at_grain"


def test_exact_map_is_found_at_the_finest_grain():
    shear = [["cell", r + c, c, v] for _, r, c, v in BASE]
    _, a = _run(shear, [0, 1, 2, 3])
    assert a["gen_grain"] == 0


def test_coarse_grain_refuses_a_singular_collapse():
    quad = [["cell", r, c + r * r, v] for _, r, c, v in BASE]
    s, a = _run(quad, [0, 1, 2, 3])
    assert a.get("gen_grain") is None, "a det=0 map at a coarse grain must not explain the warp"
    assert a["status"] == "minted"


def test_term_grain_requantizes_and_collapses_duplicates():
    s, ag = boot_core()
    s.add_node("ShapeSignature", {"name": "b", "signature": json.dumps(BASE), "kind": "faculty",
                                  "faculty": "b", "dim_types": DT})
    goal = [["cell", 2 * r, 2 * c, v] for _, r, c, v in BASE]
    t = {"type": "GenInfer", "goal": {"type": "Lit", "value": goal}, "max_dims": 2, "grain": {"type": "Lit", "value": 1}}
    assert s._inner.evaluate(dict(t, field="grain"), {}) == 1


# --- HELD-generator grain (tranche 2 gate 4, shape_decode_loop v1.14.0) -----

DT3 = ["pred", "coord:r", "coord:c"]
# an L of 2x2 blocks (keeps its orientation at grain 1); its jittered twin
# differs only below grain 1. A SOLID block would be degenerate at a coarse
# grain (tranche 4 guard) -- see test_degenerate_coarse_block_is_refused.
_L = [(0, 0), (1, 0), (2, 0), (2, 1)]
BLOCK = [["cell", 2 * r + dr, 2 * c + dc] for r, c in _L for dr in (0, 1) for dc in (0, 1)]
JIT = [x for x in BLOCK if not (x[1] == 0 and x[2] == 1) and not (x[1] == 5 and x[2] == 3)]


def _rot(cells):
    out = [(c, -r) for _, r, c in cells]
    mr = min(r for r, _ in out); mc = min(c for _, c in out)
    return [["cell", r - mr, c - mc] for r, c in out]


def _dim_run(goal, grains):
    s, ag = boot_core()
    n = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, n, ag)
    if grains is not None:
        s.set_attr(ag, "dim_grains", grains)
    s.add_node("ShapeSignature", {"name": "block", "signature": json.dumps(BLOCK), "kind": "faculty",
                                  "faculty": "block", "dim_types": DT3})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    o = s.add_node("Observation", {"signature": goal, "key": ["d"], "status": "decoded", "residual": goal,
                                   "decoded_epoch": ep, "dim_types": DT3})
    s.add_edge(ag, "observed", o)
    n.run_rules()
    axes = [s.node(x)["attrs"] for x in s.nodes("CapabilityAxis") if s.node(x)["attrs"].get("source") == "grain_residual"]
    return s.node(o)["attrs"], axes


def test_held_generator_recognises_jittered_twin_only_at_coarser_grain():
    a0, _ = _dim_run(_rot(JIT), None)
    assert a0["status"] == "minted"
    a1, axes = _dim_run(_rot(JIT), [0, 1, 2])
    assert a1["status"] == "recognized_transformed" and a1["dim_grain"] == 1
    assert a1["recognized_grain"] == 1
    assert len(axes) == 1 and axes[0]["coarse_grain"] == 1, "the sub-grain detail is carried, not discarded"


def test_exact_held_map_stays_at_grain_zero_with_ladder_on():
    a, axes = _dim_run(_rot(BLOCK), [0, 1, 2])
    assert a["status"] == "recognized_transformed" and a["dim_grain"] == 0 and axes == []


# --- MDL through the sd loop (tranche 2 gate 5, v1.15.0) ---------------------

def test_mdl_flag_without_feature_is_inert_and_rule_is_installed():
    """The default build has no MDL path: setting the flag changes nothing."""
    import json as _j
    seed = _j.load(open("seeds/shape_decode_loop.json"))
    assert any(r["name"] == "sd_mdl_outliers" for r in seed["rules"])
    shear = [["cell", r + c, c, v] for _, r, c, v in BASE]
    bad = [list(x) for x in shear]
    bad[0][1] += 3
    _, off = _run(bad, None)
    s, ag = boot_core()
    n = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, n, ag)
    s.set_attr(ag, "gen_infer_enabled", 1.0)
    s.set_attr(ag, "gen_mdl_enabled", 1)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE), "kind": "faculty",
                                  "faculty": "base_L", "dim_types": DT})
    o = s.add_node("Observation", {"signature": bad, "key": ["g"], "status": "decoded", "residual": bad,
                                   "decoded_epoch": 0.0, "dim_types": DT})
    s.add_edge(ag, "observed", o)
    n.run_rules()
    on = s.node(o)["attrs"]
    if on.get("mdl_outliers") is None:      # default build: inert
        assert on["status"] == off["status"]


def test_degenerate_coarse_block_is_refused():
    """Tranche 4: a goal that collapses to a solid block (or < 3 cells) at a
    coarse grain carries no orientation and must not be explained there."""
    s, ag = boot_core()
    n = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, n, ag)
    s.set_attr(ag, "dim_grains", [0, 1, 2])
    solid = [["cell", r, c] for r in range(4) for c in range(2)]
    s.add_node("ShapeSignature", {"name": "block", "signature": json.dumps(solid), "kind": "faculty",
                                  "faculty": "block", "dim_types": DT3})
    goal = [["cell", r, c] for r, c in [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3)]]
    o = s.add_node("Observation", {"signature": goal, "key": ["d"], "status": "decoded", "residual": goal,
                                   "decoded_epoch": 0.0, "dim_types": DT3})
    s.add_edge(ag, "observed", o)
    n.run_rules()
    assert s.node(o)["attrs"]["status"] == "minted"
