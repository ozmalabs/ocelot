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
    _select_seed_ids,
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
        tmp_path / "base_alt.json": {
            "id": "base_alt", "depends_on": [],
            "nodes": [{"type": "Base", "attrs": {"name": "base_node"}}],
        },
        tmp_path / "child.json": {
            "id": "child", "depends_on": ["base", "absent_dependency"],
            "rules": [{"name": "child_rule"}],
        },
        tmp_path / "self_load.json": {
            "id": "self_load", "self_load_only": True,
        },
        generated / "child.json": {
            "id": "child", "depends_on": ["absent_dependency"],
            "nodes": [{"local_id": 1, "type": "GeneratedChild"}],
            "extra_nodes": [{"type": "GeneratedChild", "name": "child_node"}],
            "edges": [{
                "src": {"type": "Base", "name": "base_node"},
                "type": "references", "tgt": {"local": 1},
            }],
            "relations": [{"src": "child_node", "edge": "references",
                           "tgt": "base_node"}],
        },
    }
    for path, payload in manifests.items():
        path.write_text(json.dumps(payload), encoding="utf-8")

    full = _read_seeds(str(tmp_path))
    index, paths = _read_seed_index(str(tmp_path))

    assert set(index) == set(full) == {"base", "base_alt", "child"}
    assert set(index["base"]) == {
        "id", "depends_on", "category", "microtheory", "capability_keys",
        "group_keys", "node_types", "content_keys", "content_dependencies",
        "content_load_dependencies", "missing_content_references",
        "missing_dependencies", "typed_content_reference_count",
        "name_content_reference_count", "ambiguous_content_reference_count",
    }
    assert index["base"]["group_keys"] == [
        "capability:base_cap", "category:core",
    ]
    assert index["base"]["node_types"] == ["Base"]
    assert "base_node" in index["base"]["content_keys"]
    assert index["child"]["content_dependencies"] == ["base", "base_alt"]
    assert index["child"]["content_load_dependencies"] == ["base", "base_alt"]
    assert index["child"]["missing_content_references"] == []
    assert index["child"]["typed_content_reference_count"] == 1
    assert index["child"]["name_content_reference_count"] == 2
    assert index["child"]["ambiguous_content_reference_count"] == 2
    assert "child_node" in index["child"]["content_keys"]
    assert paths["child"] == str(generated / "child.json")
    order = _topo_order(index)
    assert order.index("base") < order.index("child")
    selected, unresolved = _select_seed_ids(
        index,
        group_keys=["category:core"],
        content_keys=["not-present"],
    )
    assert selected == ["base"]
    assert unresolved == {
        "missing_seed_ids": [],
        "missing_content_keys": ["not-present"],
        "missing_dependencies": [],
        "missing_content_references": [],
    }
    selected, unresolved = _select_seed_ids(index, seed_ids=["child"])
    assert selected == ["base", "base_alt", "child"]
    assert unresolved == {
        "missing_seed_ids": [],
        "missing_content_keys": [],
        "missing_dependencies": [("child", "absent_dependency")],
        "missing_content_references": [],
    }
    selected, unresolved = _select_seed_ids(index, seed_ids=["unknown"])
    assert selected == []
    assert unresolved["missing_seed_ids"] == ["unknown"]
    selected, unresolved = _select_seed_ids(index, content_keys=["base_node"])
    assert selected == ["base", "base_alt"]
    assert unresolved["missing_content_keys"] == []


def test_load_all_seeds_emits_no_malformed_rule_warnings(capsys):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    err = capsys.readouterr().err
    assert "skipping malformed rule" not in err
