"""Seed boot: declarative principles must not warn the Rust engine loader."""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.seed_loader import engine_rules_only, manifest_for, normalize_declarative
from substrate.boot_all import (
    _read_seed_index,
    _read_seeds,
    _topo_order,
    load_all_seeds,
)
from substrate.world_adapter import WorldAdapter


def test_engine_rules_only_strips_declarative_principles():
    m = manifest_for("philosophy")
    raw = engine_rules_only({"rules": [
        {"name": "Gettier_invalidates_naive_JTB", "if": ["x"], "then": ["y"]},
        {"name": "real_rule", "match": [["a", "b", "c"]], "effects": []},
    ]})
    assert len(raw["rules"]) == 1
    assert raw["rules"][0]["name"] == "real_rule"
    # philosophy has many declarative rules, few/no engine rules
    eng = engine_rules_only(m if "rules" in m else {"rules": []})
    for r in eng.get("rules") or []:
        assert isinstance(r.get("match"), list)


def test_normalize_declarative_shares_principle_detection():
    m = {"concepts": [{"name": "c", "definition": "d"}],
         "rules": [{"name": "p", "head": "h", "body": "b"}]}
    n = normalize_declarative(m)
    assert "concepts" not in n
    assert n["rules"] == []
    types = [x["type"] for x in n["nodes"]]
    assert "Concept" in types
    assert "Principle" in types


def test_seed_index_preserves_dependency_order_and_generated_override(tmp_path):
    generated = tmp_path / "generated"
    generated.mkdir()
    manifests = {
        tmp_path / "base.json": {
            "id": "base", "depends_on": [], "category": "core",
            "capability_keys": ["base_cap"],
            "nodes": [{"type": "Base", "attrs": {"name": "base_node"}}],
        },
        tmp_path / "child.json": {
            "id": "child", "depends_on": ["base"],
            "rules": [{"name": "child_rule"}],
        },
        tmp_path / "self_load.json": {
            "id": "self_load", "self_load_only": True,
        },
        generated / "child.json": {
            "id": "child", "depends_on": ["base"],
            "nodes": [{"type": "GeneratedChild"}],
        },
    }
    for path, payload in manifests.items():
        path.write_text(json.dumps(payload), encoding="utf-8")

    full = _read_seeds(str(tmp_path))
    index, paths = _read_seed_index(str(tmp_path))

    assert set(index) == set(full) == {"base", "child"}
    assert set(index["base"]) == {
        "id", "depends_on", "category", "microtheory", "capability_keys",
        "group_keys", "node_types", "content_keys",
    }
    assert index["base"]["group_keys"] == [
        "capability:base_cap", "category:core",
    ]
    assert index["base"]["node_types"] == ["Base"]
    assert "base_node" in index["base"]["content_keys"]
    assert paths["child"] == str(generated / "child.json")
    order = _topo_order(index)
    assert order.index("base") < order.index("child")


def test_load_all_seeds_emits_no_malformed_rule_warnings(capsys):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    err = capsys.readouterr().err
    assert "skipping malformed rule" not in err
