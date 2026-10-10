"""IMPROVEMENT INTEGRITY (tranche 19): the self-improvement loop may not vary
or adopt changes to the self-improvement loop itself.

Pinned claims:
  * every active rule naming a held protected node type
    (seeds/improvement_integrity.json) is stamped improvement_machinery and
    non-skippable after any RuleSummary provenance mirror runs, so no
    variation family's candidate filter can pick it;
  * the adoption gate denies replacing such a rule, and denies installing an
    added rule that names a protected type;
  * the protected list is itself frozen and loaded with the variation repertoire;
  * measured case: a reported concern asking to loosen the steering promotion
    rule no longer builds a variant of it (it did on the tranche-18 tree).
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import domains.reflective_faculty as rf          # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402
from substrate.boot_all import load_all_seeds     # noqa: E402


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops", "variation_credit", "instruction_repair_retry"))
    for fn in (rf._ensure_acting_rule_provenance, rf._ensure_reply_rule_provenance,
               rf._ensure_where_literal_rule_provenance, rf._ensure_general_rule_provenance):
        fn(a.s, a.inner)
    return a


def _summaries(a, name):
    return [a.s.node(n)["attrs"] for n in a.s.nodes("RuleSummary") if a.s.node(n)["attrs"].get("name") == name]


def test_protected_list_is_frozen_and_rides_with_the_variation_repertoire(agent):
    types = rf._improvement_protected_types(agent.s)
    assert {"SelfConcern", "Experiment", "Adoption", "VariationPolicy", "ImprovementIntegrity"} <= set(types)
    ss = [agent.s.node(n)["attrs"] for n in agent.s.nodes("SeedSummary")
          if agent.s.node(n)["attrs"].get("seed_id") == "improvement_integrity"]
    assert ss and ss[0]["skippable"] == 0.0
    vo = json.load(open(os.path.join(ROOT, "seeds", "variation_ops.json")))
    assert "improvement_integrity" in vo["depends_on"]


def test_every_machinery_rule_is_stamped_and_unselectable(agent):
    types = rf._improvement_protected_types(agent.s)
    machinery = {r["name"] for r in agent.inner.export_rules()
                 if isinstance(r, dict) and r.get("active", True) and rf._rule_names_protected_type(r, types)}
    assert {"steer_promote_concern", "note_reported_gap", "irr_request_retry"} <= machinery
    leaks = [at["name"] for n in agent.s.nodes("RuleSummary")
             for at in [agent.s.node(n)["attrs"]]
             if at.get("name") in machinery and at.get("skippable") == 1.0]
    assert leaks == []
    for name in ("steer_promote_concern", "note_reported_gap", "irr_request_retry"):
        assert all(at.get("improvement_machinery") == 1.0 for at in _summaries(agent, name)), name
        denied, why = rf._rule_denylisted(agent.s, name)
        assert denied and "machinery" in why, (name, why)


def test_ordinary_rule_is_still_adoptable(agent):
    # a reading rule the tranche-14 gate varied stays an ordinary candidate
    name = next(at["name"] for n in agent.s.nodes("RuleSummary") for at in [agent.s.node(n)["attrs"]]
                if at.get("writes_where_literal") == 1.0 and at.get("skippable") == 1.0)
    assert rf._rule_denylisted(agent.s, name)[0] is False


def test_promotion_gate_concern_no_longer_varies_the_promotion_rule(agent):
    import jabberwock_daemon as jd
    content = ("you promote concerns too eagerly, test whether the hardcoded steer promote "
               "concern floor is too low")
    sc = agent.s.add_node("SelfConcern", {"kind": "reported", "status": "noted", "source": "explicit",
                                          "content": content})
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", sc)
    assert jd.promote_self_concern(agent, str(sc.value)).get("ok")
    standing = next(iter(agent.inner.neighbours(sc, "promoted_to")))
    key = agent.s.node(standing)["attrs"]["name"]
    v = rf._compose_rule_literal_variant(agent, [key], "integrity")
    varied = v.get("rule_name") or v.get("act_rule_varied") or ""
    assert varied != "steer_promote_concern"
    if v.get("built"):
        assert rf._rule_denylisted(agent.s, varied)[0] is False or "machinery" not in rf._rule_denylisted(agent.s, varied)[1]


def test_adoption_denies_an_added_rule_naming_a_protected_type(agent):
    a = agent
    rule = {"name": "df_variant_integrity_probe", "match": [["agent", "has_self_concern", "sc"]],
            "where": {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "sc"}, "key": "kind"},
                      "b": {"type": "Lit", "value": "reported"}},
            "effects": [["set_attr", "sc", "status", "retired"]]}
    assert rf._rule_names_protected_type(rule, rf._improvement_protected_types(a.s)) is False  # names no type
    rule["where"] = {"type": "Exists", "source": {"type": "NodesOfType", "node_type": "SelfConcern"},
                     "var_name": "x", "predicate": {"type": "Lit", "value": True}}
    exp = a.s.add_node("Experiment", {"adopt_ready": True, "game": "conversation", "status": "done",
                                      "outcome": "supported"})
    d = a.s.add_node("SeedDelta", {"datum_feedback_edit": 1.0, "datum_feedback_belief_attr": "x_belief",
                                   "add_rules": json.dumps([rule])})
    a.inner.add_edge_unchecked(exp, "has_delta", d)
    before = len(a.inner.export_rules())
    out = rf.perform_adoptions(a)
    mine = [r for r in out if r.get("experiment") == str(exp)]
    assert mine and mine[0].get("denied") is True
    assert a.s.node(exp)["attrs"].get("adopt_denied") is True
    assert len(a.inner.export_rules()) == before
