"""Seed boot: declarative principles must not warn the Rust engine loader."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.seed_loader import engine_rules_only, manifest_for, normalize_declarative
from substrate.boot_all import load_all_seeds
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


def test_load_all_seeds_emits_no_malformed_rule_warnings(capsys):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    err = capsys.readouterr().err
    assert "skipping malformed rule" not in err
