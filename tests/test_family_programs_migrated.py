"""Plan P4 (2026-10-10): rule-edit Terms and held family Programs.

  * EditAt / CharRunSub / StripChars and LitRepr of built strings
    (runners/dsl/src/term.rs);
  * seeds/family_programs.json holds disposition_generalise and
    deep_reader_correct as FamilyProgram nodes; their VariationOps name them
    (builder_program), and the held Program is the default builder;
  * FamilyProgram is a protected type (the loop may not edit its own families).
Builder parity is pinned in test_unanswered_generalise_migrated /
test_deep_reader_correct_migrated and swept by
evaluation/substrate_capability/family_program_parity_v1.py.
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter   # noqa: E402

L = lambda v: {"type": "Lit", "value": v}           # noqa: E731
V = lambda n: {"type": "Var", "name": n}            # noqa: E731


def _ev(term, env=None):
    return WorldAdapter(seeds=()).inner.evaluate(term, env or {})


def _edit(path, op, arg=None):
    return {"type": "EditAt", "tree": V("r"), "path": L(path), "op": L(op), "arg": L(arg)}


RULE = {"name": "x", "where": {"type": "And", "items": [{"type": "Eq", "a": 1, "b": 2}]},
        "effects": [["set_attr", "i", "k", 1]], "active": True}


def test_edit_at_set_append_drop_and_inert():
    a = WorldAdapter(seeds=())
    ev = lambda t: a.inner.evaluate(t, {"r": RULE})            # noqa: E731
    assert ev(_edit(["name"], "set", "y"))["name"] == "y"
    assert ev(_edit(["comment"], "set", "c"))["comment"] == "c"        # a missing final key is inserted
    assert "active" not in ev(_edit(["active"], "drop"))
    assert ev(_edit(["effects"], "append", ["set_attr", "i", "z", 2]))["effects"][-1] == ["set_attr", "i", "z", 2]
    assert ev(_edit(["where", "items", 0, "b"], "set", 5))["where"]["items"][0]["b"] == 5
    assert ev(_edit(["where", "items", -1, "a"], "set", 7))["where"]["items"][0]["a"] == 7
    assert ev(_edit(["nope", "x"], "set", 5)) is None                  # inert, never fabricated
    assert ev(_edit(["where", "items", 3], "set", 5)) is None
    assert ev(_edit(["name"], "explode", 5)) is None
    assert RULE["name"] == "x" and RULE["active"] is True             # pure


def test_slug_terms_match_python_re():
    keep = "abcdefghijklmnopqrstuvwxyz0123456789"
    for s in ("Instruction as-Statement!!", "statement_as_question_function", "__a__b__", "None", "x  y"):
        got = _ev({"type": "StripChars", "chars": L("_"),
                   "text": {"type": "CharRunSub", "text": L(s), "keep": L(keep), "repl": L("_")}})
        assert got == re.sub(r"[^a-z0-9]+", "_", s).strip("_"), s


def test_lit_repr_of_a_built_string():
    for s in ("abc", "it's", 'say "hi"', "a'b\"c"):
        built = {"type": "StringConcat", "parts": [L(s[:1]), L(s[1:])]}
        assert _ev({"type": "LitRepr", "value": built}) == repr(s), s


def test_family_programs_are_held_named_and_protected():
    seed = json.load(open(os.path.join(ROOT, "seeds", "family_programs.json")))
    names = {n["attrs"]["name"] for n in seed["nodes"] if n["type"] == "FamilyProgram"}
    assert names == {"family_disposition_generalise", "family_deep_reader_correct"}
    ops = {n["attrs"]["name"]: n["attrs"].get("builder_program")
           for n in json.load(open(os.path.join(ROOT, "seeds", "variation_ops.json")))["nodes"]
           if n["type"] == "VariationOp"}
    assert ops["disposition_generalise"] == "family_disposition_generalise"
    assert ops["deep_reader_correct"] == "family_deep_reader_correct"
    types = json.load(open(os.path.join(ROOT, "seeds", "improvement_integrity.json")))["nodes"][0]["attrs"][
        "protected_node_types"]
    assert "FamilyProgram" in types


def test_held_program_is_the_default_builder(monkeypatch):
    from substrate.boot_all import load_all_seeds
    import domains.reflective_faculty as rf
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    monkeypatch.delenv("OZMA_FAMILY_PROGRAM_PYTHON", raising=False)
    monkeypatch.delenv("OZMA_FAMILY_PROGRAM_PARITY", raising=False)
    b = rf._builder_for(a, "disposition_generalise")
    assert b is not rf._VARIATION_REGISTRY["disposition_generalise"]
    assert b(a, ["no_such_key"], "t") == {"built": False, "wall": "no StandingConcern carries this capability key"}
    monkeypatch.setenv("OZMA_FAMILY_PROGRAM_PYTHON", "1")
    assert rf._builder_for(a, "disposition_generalise") is rf._VARIATION_REGISTRY["disposition_generalise"]
    # a family with no held Program keeps its Python builder
    assert rf._builder_for(a, "knob_edit") is rf._VARIATION_REGISTRY["knob_edit"]
