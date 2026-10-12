"""Plan P3 (2026-10-10): one generic whole-delta adoption path, plus the
integrity gap.

  * every family's fold-back goes through reflective_faculty._adopt_whole_delta,
    which records the FULL prior state on the Adoption; revert_adoption undoes
    it for any family (disposition_generalise adoptions used to be
    unrevertable; a deep_reader_correct revert left every added rule live);
  * a delta with no family marker (`whole_delta`) is adopted as written;
  * the integrity gate reads the whole delta: a node-attr edit or node
    addition of a protected_node_types type (or of the gate's own
    RuleSummary/SeedSummary evidence) is denied at adoption and refused by
    the child appliers (gate G3: a knob delta targeting VariationPolicy);
  * a reverted adoption is not silently re-adopted.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds             # noqa: E402
from domains.experiment_dispatch import mint_experiment   # noqa: E402
import domains.reflective_faculty as rf                   # noqa: E402

_PROTECTED = json.load(open(os.path.join(ROOT, "seeds", "improvement_integrity.json")))[
    "nodes"][0]["attrs"]["protected_node_types"]
_TEACH_SEEDS = [os.path.join(ROOT, "seeds", f) for f in
                ("experiment_conclusions.json", "comprehend_instruction.json", "interlocutor_shapes.json")]


@pytest.fixture(autouse=True)
def _guard_taught_seeds():
    """teach() persists into checked-in seeds; restore them."""
    before = {p: (open(p).read() if os.path.exists(p) else None) for p in _TEACH_SEEDS}
    try:
        yield
    finally:
        for p, text in before.items():
            if text is None:
                if os.path.exists(p):
                    os.unlink(p)
            else:
                with open(p, "w") as f:
                    f.write(text)


@pytest.fixture()
def light():
    """A bare agent holding only the integrity list and one adoptable seed."""
    a = WorldAdapter(seeds=())
    a.s.add_node("ImprovementIntegrity", {"protected_node_types": list(_PROTECTED)})
    a.s.add_node("SeedSummary", {"seed_id": "sample_seed", "skippable": 1.0})
    return a


def _rule(name, key="k"):
    return {"name": name, "match": [["m", "sample_flag", "m"]],
            "effects": [["set_attr", "m", key, 1.0]]}


def _held_rule(a, name):
    a.inner.add_rule(_rule(name))
    a.s.add_node("RuleSummary", {"name": name, "from_seed": "sample_seed", "skippable": 1.0})


def _live(a):
    return sorted(r["name"] for r in a.inner.export_rules() if r.get("active", True))


def _ready(a, exp):
    a.inner.set_attr(exp, "status", "done")
    a.inner.set_attr(exp, "outcome", "supported")
    a.inner.set_attr(exp, "regressions", 0)
    a.inner.set_attr(exp, "adopt_ready", True)


def _delta(a, exp):
    return next(d for d in a.inner.neighbours(exp, "has_delta"))


# --- the integrity gap (gate G3) ------------------------------------------------

def test_knob_delta_targeting_variation_policy_is_denied():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    assert list(a.s.nodes("ImprovementIntegrity")), "the integrity seed is part of the boot"
    pol = next(iter(a.s.nodes("VariationPolicy")), None)
    if pol is None:   # seeds/variation_credit.json's policy row (that seed loads on demand)
        vc = json.load(open(os.path.join(ROOT, "seeds", "variation_credit.json")))
        row = next(n for n in vc["nodes"] if n["type"] == "VariationPolicy")
        pol = a.s.add_node("VariationPolicy", dict(row["attrs"]))
    name = a.s.node(pol)["attrs"]["name"]
    before = a.s.node(pol)["attrs"].get("use_credit")
    exp = mint_experiment(a, "knob on the loop's own policy", "conversation",
                          set_node_attrs=[{"type": "VariationPolicy", "key_attr": "name",
                                           "key_value": name, "attrs": {"use_credit": 0}}])
    d = _delta(a, exp)
    for k, v in (("knob_edit", 1.0), ("knob_node_type", "VariationPolicy"), ("knob_key_attr", "name"),
                 ("knob_key_value", name), ("knob_attr", "use_credit"), ("knob_old_value", before),
                 ("knob_new_value", 0)):
        a.inner.set_attr(d, k, v)
    _ready(a, exp)
    recs = [r for r in rf.perform_adoptions(a) if r.get("experiment") == str(exp)]
    assert len(recs) == 1 and recs[0].get("denied") is True, recs
    assert "VariationPolicy" in recs[0]["reason"]
    assert a.s.node(exp)["attrs"].get("adopt_denied") is True
    assert a.s.node(pol)["attrs"].get("use_credit") == before
    assert not list(a.s.nodes("Adoption"))


def test_child_appliers_refuse_loop_and_provenance_types(light):
    from arc_child_run import apply_node_attr_delta, apply_concept_delta
    a = light
    a.s.add_node("VariationPolicy", {"name": "p", "use_credit": 1})
    a.s.add_node("ApertureBudget", {"register": "conversational", "x": 0.5})
    delta = {"set_node_attrs": [
        {"type": "VariationPolicy", "key_attr": "name", "key_value": "p", "attrs": {"use_credit": 0}},
        {"type": "SeedSummary", "key_attr": "seed_id", "key_value": "sample_seed", "attrs": {"skippable": 0.0}},
        {"type": "ApertureBudget", "key_attr": "register", "key_value": "conversational", "attrs": {"x": 0.6}}],
        "add_concepts": [{"type": "VariationOp", "attrs": {"name": "evil"}},
                         {"type": "Concept", "attrs": {"name": "fine"}}]}
    changed = apply_node_attr_delta(a, delta)
    added = apply_concept_delta(a, delta)
    assert changed == [("ApertureBudget", "conversational", "x")]
    assert added == ["fine"]
    assert not list(a.s.nodes("VariationOp"))
    pol = next(iter(a.s.nodes("VariationPolicy")))
    assert a.s.node(pol)["attrs"]["use_credit"] == 1
    assert len(delta["integrity_refused"]) == 3


def test_node_addition_of_protected_type_is_denied(light):
    a = light
    exp = mint_experiment(a, "shape of a loop type", "conversation",
                          add_concepts=[{"type": "VariationOp", "attrs": {"name": "x_op"}}])
    d = _delta(a, exp)
    a.inner.set_attr(d, "shape_mint_edit", 1.0)
    a.inner.set_attr(d, "shape_mint_name", "x_op")
    _ready(a, exp)
    recs = rf.perform_adoptions(a)
    assert len(recs) == 1 and recs[0]["denied"] is True
    assert not list(a.s.nodes("VariationOp"))


def test_provenance_edit_is_denied(light):
    a = light
    exp = mint_experiment(a, "open the gate", "conversation",
                          set_node_attrs=[{"type": "SeedSummary", "key_attr": "seed_id",
                                           "key_value": "frozen", "attrs": {"skippable": 1.0}}])
    a.inner.set_attr(_delta(a, exp), "whole_delta", 1.0)
    _ready(a, exp)
    recs = rf.perform_adoptions(a)
    assert len(recs) == 1 and recs[0]["denied"] is True and "SeedSummary" in recs[0]["reason"]


# --- revert works for every family ------------------------------------------------

def test_generalise_adoption_is_now_revertable_and_not_readopted(light):
    a = light
    exp = mint_experiment(a, "generalise", "conversation", add_rules=[_rule("gen_a"), _rule("gen_b")])
    d = _delta(a, exp)
    a.inner.set_attr(d, "generalise_edit", 1.0)
    a.inner.set_attr(d, "generalise_basis", "basis")
    a.inner.set_attr(d, "generalise_source_rule", "src")
    _ready(a, exp)
    before = _live(a)
    recs = rf.perform_adoptions(a)
    assert len(recs) == 1 and recs[0]["rule_added"] == "gen_a,gen_b"
    assert {"gen_a", "gen_b"} <= set(_live(a))
    r = rf.revert_adoption(a, recs[0]["adoption"])
    assert r["reverted"] is True and sorted(r["tombstoned_rules"]) == ["gen_a", "gen_b"]
    assert _live(a) == before
    assert rf.perform_adoptions(a) == []          # not silently re-adopted
    assert _live(a) == before


def test_deep_reader_revert_removes_every_added_rule(light):
    a = light
    _held_rule(a, "misreading_rule")
    exp = mint_experiment(a, "deep reader", "conversation",
                          add_rules=[_rule("misreading_rule_deep"), _rule("receipt_rule")],
                          remove_rules=["misreading_rule"])
    d = _delta(a, exp)
    a.inner.set_attr(d, "deep_reader_edit", 1.0)
    a.inner.set_attr(d, "act_rule_varied", "misreading_rule")
    a.inner.set_attr(d, "deep_reader_pair", "statement>question")
    _ready(a, exp)
    before = _live(a)
    recs = rf.perform_adoptions(a)
    assert recs[0]["rule_removed"] == "misreading_rule"
    assert "misreading_rule" not in _live(a) and "receipt_rule" in _live(a)
    r = rf.revert_adoption(a, recs[0]["adoption"])
    assert r["reverted"] is True
    assert _live(a) == before


def test_whole_delta_round_trip(light):
    a = light
    _held_rule(a, "old_rule")
    knob = a.s.add_node("ApertureBudget", {"register": "conversational", "x": 0.5})
    a.s.add_node("Concept", {"name": "stale_cue", "instruction_route": "r"})
    exp = mint_experiment(a, "whole", "conversation",
                          add_rules=[_rule("new_rule")], remove_rules=["old_rule"],
                          set_node_attrs=[{"type": "ApertureBudget", "key_attr": "register",
                                           "key_value": "conversational", "attrs": {"x": 0.7, "y": 1}}],
                          add_concepts=[{"type": "Concept", "attrs": {"name": "fresh_cue"}}],
                          remove_concepts=["stale_cue"])
    a.inner.set_attr(_delta(a, exp), "whole_delta", 1.0)
    _ready(a, exp)
    before_rules = _live(a)
    concepts = lambda: sorted(a.s.node(n)["attrs"].get("name") for n in a.s.nodes("Concept"))
    before_concepts = concepts()
    recs = rf.perform_adoptions(a)
    assert len(recs) == 1 and not recs[0].get("denied"), recs
    assert "new_rule" in _live(a) and "old_rule" not in _live(a)
    assert a.s.node(knob)["attrs"]["x"] == 0.7 and a.s.node(knob)["attrs"]["y"] == 1
    assert "fresh_cue" in concepts() and "stale_cue" not in concepts()
    state = json.loads(a.s.node(recs[0]["adoption"])["attrs"]["prior_state"])
    assert state["removed_rules"][0]["name"] == "old_rule"
    assert {s["attr"]: s["old"] for s in state["set_attrs"]} == {"x": 0.5, "y": None}
    r = rf.revert_adoption(a, recs[0]["adoption"])
    assert r["reverted"] is True, r
    assert _live(a) == before_rules
    assert a.s.node(knob)["attrs"]["x"] == 0.5
    assert concepts() == before_concepts
    assert a.s.node(exp)["attrs"].get("adopted") is False


def test_stale_plan_changes_nothing(light):
    a = light
    exp = mint_experiment(a, "stale", "conversation", add_rules=[_rule("gone_rule_v")],
                          remove_rules=["gone_rule"])
    a.inner.set_attr(_delta(a, exp), "whole_delta", 1.0)
    a.s.add_node("RuleSummary", {"name": "gone_rule", "from_seed": "sample_seed", "skippable": 1.0})
    _ready(a, exp)
    before = _live(a)
    assert rf.perform_adoptions(a) == []
    assert _live(a) == before and not list(a.s.nodes("Adoption"))
