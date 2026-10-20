from __future__ import annotations

import json
import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from evaluation.substrate_capability import extended_thinking_instances_v1 as inst


def _dim_explained(goal, grain, base, dim_types):
    s, agent = boot_core()
    native = s._inner
    rf._ensure_shape_decode_loop(s, native, agent)
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(base),
        "kind": "faculty", "faculty": "base", "dim_types": dim_types})
    result = native.evaluate({"type": "DimInfer", "goal": {"type": "Lit", "value": goal},
        "max_dims": 2, "field": "explained", "grain": {"type": "Lit", "value": grain}}, {})
    return bool(result)


def test_seeded_instance_families_are_reproducible():
    for family in ("A", "B", "control_a", "control_b_value_noise", "control_b_quadratic"):
        assert inst.draw(family, 90123) == inst.draw(family, 90123)


def test_each_held_out_family_a_instance_needs_coarse_grain():
    for seed in range(32):
        case = inst.family_a(81000 + seed)
        assert not _dim_explained(case["goal"], 0, case["base"], case["dim_types"]), seed
        assert (_dim_explained(case["goal"], 1, case["base"], case["dim_types"])
                or _dim_explained(case["goal"], 2, case["base"], case["dim_types"])), seed


def test_family_b_generators_are_invertible_and_non_dihedral():
    for seed in range(32):
        case = inst.family_b(82000 + seed)
        a, b, c, d = case["matrix"]
        assert abs(a * d - b * c) == 1
        assert tuple(case["matrix"]) not in inst.DIHEDRAL
