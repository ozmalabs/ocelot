"""test_audience_production_cognition -- AUDIENCE-DRIVEN PRODUCTION COGNITION: the
agent's own authored rules that USE `domains.audience_driven_production` (a
speaker-models-listener midpoint fed by a GROUNDED audience model), not just call it.
Fast pytest twin of `scripts/jabberwock_tailors_to_audience.py` (read that script's
module docstring for the full narrative).

THE MACHINERY (read-only here, never modified): `domains/audience_driven_production.py`
(`audience_model` / `residual_vs_audience` / `select_utterance`) and `domains/
audience_production_dispatch.py` (`scan_and_speak_to_audience` / `mint_produce_for_
audience_request` -- the mechanical host hook that calls it and wires `req -has_audience_
model-> sm`, the same "mechanical exposure of an already-computed flag to the rule
engine" idiom `domains.reflective_faculty.ensure_grounding_gap_edges` uses for
`GroundingGap`, and `domains.system_model_dispatch.scan_and_model` uses for
`has_system_model`).

THIS FILE covers the follow-on: the agent's OWN decision about WHETHER to tailor an
utterance to a modelled audience or fall back to explicit. Per CLAUDE.md's discipline,
no test here hand-installs the three audience-produce rules -- every test either (a)
proves the concern genuinely walls before the new cue exists, or (b) drives
`induce_concern` -> `ground_concern` and reads back what the agent's own composer
(`seeds/composer_audience_produce_graph.json`, dispatched via the new 'audience_produce'
RelationCue + 'tailor' ComposerCue) authored, or (c) drives the full request -> model ->
mode pipeline on a real booted agent and reads the graph state back.

No seed file is mutated at runtime by anything this file exercises (`teach` is never
called by `ground_concern`'s composer-dispatch path, nor by `domains.audience_production_
dispatch.scan_and_speak_to_audience`) so no snapshot-guard fixture is needed for
seeds/relation_vocabulary.json / seeds/composer_dispatch.json / seeds/
composer_audience_produce_graph.json -- the same claim tests/test_system_model_cognition.py
makes for its own seeds.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core                              # noqa: E402
from substrate.seed_loader import manifest_for                         # noqa: E402
import domains.reflective_faculty as rf                                # noqa: E402
from domains import audience_production_dispatch as apd                # noqa: E402

LEXICON = [
    {"form": "dinner", "concept": "dinner"},
    {"form": "seven pm", "concept": "seven_pm"},
    {"form": "the italian place", "concept": "italian_place"},
    {"form": "a reservation", "concept": "reservation"},
    {"form": "table for two", "concept": "table_for_two"},
]
MEANING = {"dinner", "seven_pm", "italian_place", "reservation", "table_for_two"}
SHARED = ["dinner", "seven_pm", "italian_place"]


class _Agent:
    """Minimal duck-typed agent wrapper -- identical shape to
    tests/test_system_model_cognition.py's own `_Agent` (harness glue only, no source
    modified)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _ground(ag, cue_clause, name_hint):
    ind = rf.induce_concern(ag, [cue_clause], name_hint=name_hint)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "graph", g
    return g


def _ground_audience_produce(ag, tag="ap_t"):
    return _ground(ag, ["tailor", "UTTERANCE", "to", "AUDIENCE"], tag)


# ===========================================================================
# 1. the vocabulary genuinely walls before this change (proof, not assumed)
# ===========================================================================
def test_existing_vocabulary_walls_on_tailor_before_new_cue():
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    m = dict(manifest_for("relation_vocabulary"))
    m["nodes"] = [n for n in m["nodes"] if n["attrs"].get("name") != "audience_produce"]
    ag.s._inner.load_seed_manifest(m, ag.agent)

    ind = rf.induce_concern(ag, [["tailor", "UTTERANCE", "to", "AUDIENCE"]], name_hint="wall_probe")
    assert ind.get("minted") is True
    res = rf.ground_concern(ag, [ind["capability_key"]])
    assert res.get("grounded") is False
    assert res.get("path") == "predicate_grounding"


def test_tailor_cue_loads_and_dispatches_to_audience_produce_composer():
    ag = _fresh_agent()
    name = rf._pick_composer(ag.s, ag.inner, ag.agent, {"tailor"})
    assert name == "audience_produce"


# ===========================================================================
# 2. the jabberwock AUTHORS the three audience-produce rules via the composer
# ===========================================================================
def test_agent_authors_three_audience_produce_rules_via_graph_composer():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, [["tailor", "UTTERANCE", "to", "AUDIENCE"]], name_hint="ap_authors")
    key = ind["capability_key"]
    before = ag.inner.rule_count()
    g = rf.ground_concern(ag, [key])
    after = ag.inner.rule_count()

    assert g.get("grounded") is True, g.get("wall")
    assert g.get("served_by") == "graph"
    assert g.get("path") == "compose_audience_produce_rule"
    assert after - before == 3, "exactly three rules authored"

    by_name = {r["name"]: r for r in g["rules"]}

    req_rule = by_name["request_produce_for_audience_" + key]
    assert req_rule["match"] == [["g", "has_subgoal", "sg"], ["sg", "for_audience", "aud"]]
    assert req_rule["effects"][0][:3] == ["add_node", "req", "ProduceForAudienceRequest"]
    assert req_rule["effects"][1][:4] == ["add_edge", "sg", "requests_audience_produce", "req"]
    assert req_rule["effects"][2][:4] == ["add_edge", "req", "for_goal", "sg"]
    assert req_rule["effects"][3][:4] == ["add_edge", "req", "for_interlocutor", "aud"]

    default_rule = by_name["default_explicit_produce_" + key]
    assert default_rule["match"] == [["req", "has_audience_model", "sm"]]
    assert default_rule["effects"] == [["set_attr", "req", "mode", "explicit"]]
    # NEVER a set_attr on the matched system model (self-inclusion discipline)
    assert all(eff[1] != "sm" for eff in default_rule["effects"])

    tailor_rule = by_name["tailor_when_grounded_" + key]
    assert tailor_rule["match"] == [["req", "has_audience_model", "sm"]]
    assert tailor_rule["effects"] == [["set_attr", "req", "mode", "tailor"]]
    assert all(eff[1] != "sm" for eff in tailor_rule["effects"])


def test_re_grounding_is_idempotent_no_rechurn():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, [["tailor", "UTTERANCE", "to", "AUDIENCE"]], name_hint="ap_idem")
    key = ind["capability_key"]
    rf.ground_concern(ag, [key])
    rc1 = ag.inner.rule_count()
    rf.ground_concern(ag, [key])
    rc2 = ag.inner.rule_count()
    assert rc1 == rc2


# ===========================================================================
# 3. THE DECISION -- discriminative: a GROUNDED (observed) audience tailors
#    (terse); an UNGROUNDED (unobserved) audience falls back to explicit.
#    The branch is keyed on SystemModel.grounded read off the graph.
# ===========================================================================
def test_grounded_audience_request_tailors_and_is_terser():
    ag = _fresh_agent()
    _ground_audience_produce(ag)
    req = apd.mint_produce_for_audience_request(
        ag, MEANING, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    results = apd.scan_and_speak_to_audience(ag, LEXICON)
    assert len(results) == 1
    res = results[0]["result"]
    assert res["grounded_used"] is True

    sm = list(ag.inner.neighbours(req, "has_audience_model"))
    assert len(sm) == 1
    assert ag.s.node(sm[0])["attrs"].get("grounded") is True

    ag.inner.run_rules(2000)
    mode = ag.s.node(req)["attrs"].get("mode")
    utterance = ag.s.node(req)["attrs"].get("utterance")
    assert mode == "tailor"
    assert isinstance(utterance, str) and utterance
    # the tailored utterance never restates a shared (known) concept
    assert not any(w in utterance for w in ("dinner", "seven pm", "the italian place"))
    assert ag.s.node(req)["attrs"].get("status") == "modeled"


def test_ungrounded_audience_request_falls_back_to_explicit():
    ag = _fresh_agent()
    _ground_audience_produce(ag)
    req = apd.mint_produce_for_audience_request(
        ag, MEANING, {"id": "stranger", "observed": False})
    results = apd.scan_and_speak_to_audience(ag, LEXICON)
    assert len(results) == 1
    res = results[0]["result"]
    assert res["grounded_used"] is False

    sm = list(ag.inner.neighbours(req, "has_audience_model"))
    assert len(sm) == 1
    assert ag.s.node(sm[0])["attrs"].get("grounded") is False

    ag.inner.run_rules(2000)
    mode = ag.s.node(req)["attrs"].get("mode")
    utterance = ag.s.node(req)["attrs"].get("utterance")
    assert mode == "explicit"
    assert isinstance(utterance, str) and utterance
    # explicit fallback restates the FULL meaning
    for w in ("dinner", "seven pm", "the italian place", "a reservation", "table for two"):
        assert w in utterance


def test_grounded_vs_ungrounded_is_discriminative_same_meaning():
    """Same MEANING, only the observation differs -- the spouse-vs-stranger contrast,
    now the AGENT'S own graph-resident decision, not a Python branch."""
    ag_g = _fresh_agent()
    _ground_audience_produce(ag_g, "ap_disc_g")
    req_g = apd.mint_produce_for_audience_request(
        ag_g, MEANING, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    apd.scan_and_speak_to_audience(ag_g, LEXICON)
    ag_g.inner.run_rules(2000)

    ag_u = _fresh_agent()
    _ground_audience_produce(ag_u, "ap_disc_u")
    req_u = apd.mint_produce_for_audience_request(
        ag_u, MEANING, {"id": "stranger", "observed": False})
    apd.scan_and_speak_to_audience(ag_u, LEXICON)
    ag_u.inner.run_rules(2000)

    mode_g = ag_g.s.node(req_g)["attrs"].get("mode")
    mode_u = ag_u.s.node(req_u)["attrs"].get("mode")
    utt_g = ag_g.s.node(req_g)["attrs"].get("utterance")
    utt_u = ag_u.s.node(req_u)["attrs"].get("utterance")

    assert mode_g == "tailor"
    assert mode_u == "explicit"
    assert mode_g != mode_u
    assert len(utt_g.split()) < len(utt_u.split())


def test_known_hint_without_observation_is_never_credited_ungrounded_stays_explicit():
    """The epistemic discipline carries through the graph rule: passing known_concepts
    without observed=True must not leak into a 'tailor' decision -- grounding is
    required, a hint alone is not enough (mirrors domains.audience_driven_production's
    own test_unobserved_hint_is_never_credited_even_if_supplied)."""
    ag = _fresh_agent()
    _ground_audience_produce(ag, "ap_ghost")
    req = apd.mint_produce_for_audience_request(
        ag, MEANING, {"id": "ghost", "observed": False, "known_concepts": SHARED})
    apd.scan_and_speak_to_audience(ag, LEXICON)
    ag.inner.run_rules(2000)
    assert ag.s.node(req)["attrs"].get("mode") == "explicit"


def test_re_scan_does_not_rechurn_request():
    ag = _fresh_agent()
    _ground_audience_produce(ag)
    apd.mint_produce_for_audience_request(
        ag, MEANING, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    n1 = len(apd.scan_and_speak_to_audience(ag, LEXICON))
    n2 = len(apd.scan_and_speak_to_audience(ag, LEXICON))
    assert n1 == 1
    assert n2 == 0, "a modeled request must never be re-modeled by a re-scan"


def test_re_run_rules_does_not_rechurn_mode():
    ag = _fresh_agent()
    _ground_audience_produce(ag)
    req = apd.mint_produce_for_audience_request(
        ag, MEANING, {"id": "spouse", "observed": True, "known_concepts": SHARED})
    apd.scan_and_speak_to_audience(ag, LEXICON)
    ag.inner.run_rules(2000)
    mode1 = ag.s.node(req)["attrs"].get("mode")
    ag.inner.run_rules(2000)
    mode2 = ag.s.node(req)["attrs"].get("mode")
    assert mode1 == mode2 == "tailor"


# ===========================================================================
# 4. THE PRODUCE-GOAL PATH -- the agent's OWN request_produce_for_audience_<tag>
#    rule recognises a produce_utterance Goal carrying a for_audience edge.
# ===========================================================================
def test_produce_goal_with_audience_edge_autonomously_mints_request():
    ag = _fresh_agent()
    _ground_audience_produce(ag, "ap_goal")
    g = ag.s.add_node("Goal", {"kind": "describe_scene"})
    sg = ag.s.add_node("Goal", {"kind": "produce_utterance", "action": "produce_utterance"})
    aud = ag.s.add_node("Interlocutor", {"id": "spouse", "observed": True, "known_concepts": SHARED})
    ag.inner.add_edge_unchecked(g, "has_subgoal", sg)
    ag.inner.add_edge_unchecked(sg, "for_audience", aud)

    before = len(list(ag.s.nodes("ProduceForAudienceRequest")))
    ag.inner.run_rules(2000)
    after_reqs = list(ag.s.nodes("ProduceForAudienceRequest"))
    assert before == 0
    assert len(after_reqs) == 1
    req = after_reqs[0]
    assert ag.s.has_edge(sg, "requests_audience_produce", req)
    assert ag.s.has_edge(req, "for_goal", sg)
    assert ag.s.has_edge(req, "for_interlocutor", aud)


def test_produce_goal_without_audience_edge_never_mints_request():
    ag = _fresh_agent()
    _ground_audience_produce(ag, "ap_no_aud")
    g = ag.s.add_node("Goal", {"kind": "describe_scene"})
    sg = ag.s.add_node("Goal", {"kind": "produce_utterance", "action": "produce_utterance"})
    ag.inner.add_edge_unchecked(g, "has_subgoal", sg)
    ag.inner.run_rules(2000)
    assert list(ag.s.nodes("ProduceForAudienceRequest")) == []


def test_re_tick_does_not_rechurn_autonomous_request():
    ag = _fresh_agent()
    _ground_audience_produce(ag, "ap_goal_idem")
    g = ag.s.add_node("Goal", {"kind": "describe_scene"})
    sg = ag.s.add_node("Goal", {"kind": "produce_utterance", "action": "produce_utterance"})
    aud = ag.s.add_node("Interlocutor", {"id": "spouse", "observed": True, "known_concepts": SHARED})
    ag.inner.add_edge_unchecked(g, "has_subgoal", sg)
    ag.inner.add_edge_unchecked(sg, "for_audience", aud)
    ag.inner.run_rules(2000)
    n1 = len(list(ag.s.nodes("ProduceForAudienceRequest")))
    ag.inner.run_rules(2000)
    n2 = len(list(ag.s.nodes("ProduceForAudienceRequest")))
    assert n1 == n2 == 1


def test_absent_request_never_fires_either_branch_rule():
    ag = _fresh_agent()
    _ground_audience_produce(ag, "ap_absent")
    # no ProduceForAudienceRequest, no scan_and_speak_to_audience call
    ag.inner.run_rules(2000)
    assert list(ag.s.nodes("ProduceForAudienceRequest")) == []
