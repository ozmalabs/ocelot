"""P3.A6.1 engine behavior checks used to freeze the executor predicates."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from tests.test_geninfer_grain_migrated import BLOCK, DT3, JIT, _rot


def test_targeted_redecode_miss_returns_to_decoded_with_dimension_checked():
    s, agent = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, agent)
    s.add_node("ShapeSignature", {
        "name": "block", "signature": json.dumps(BLOCK), "kind": "faculty",
        "faculty": "block", "dim_types": DT3,
    })
    signature = _rot(JIT)
    obs = s.add_node("Observation", {
        "signature": signature, "key": ["spike"], "status": "decoded",
        "residual": signature, "decoded_epoch": 0.0, "dim_types": DT3,
    })
    s.add_edge(agent, "observed", obs)
    native.run_rules()
    first = s.node(obs)["attrs"]
    assert first["status"] == "minted"
    assert first["dim_checked"] == 1
    assert first.get("dim_explained") != 1
    assert first.get("gen_checked") == 1

    s.set_attr(obs, "decoded_epoch", -1.0)
    native.run_rules()
    after = s.node(obs)["attrs"]
    assert after["status"] == "decoded"
    assert after["dim_checked"] == 1
    assert after.get("dim_explained") != 1
    assert after["gen_checked"] == 1


def test_set_attr_none_matches_literal_null_in_rule():
    s, agent = boot_core()
    native = rf._native_eval2(s)
    probe = s.add_node("Probe", {})
    try:
        s._inner.add_edge_unchecked(agent, "has_probe", probe, {})
    except TypeError:
        s._inner.add_edge_unchecked(agent, "has_probe", probe)
    native.add_rule({
        "name": "null_attr_probe",
        "match": [["agent", "has_probe", "probe"]],
        "where": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "probe"}, "key": "x"}, "b": {"type": "Lit", "value": None}},
        "effects": [["set_attr", "probe", "null_matched", 1.0]],
    })
    s.set_attr(probe, "x", None)
    native.run_rules()
    assert s.node(probe)["attrs"]["null_matched"] == 1.0
