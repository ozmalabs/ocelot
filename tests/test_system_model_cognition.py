"""test_system_model_cognition -- TIER 5 SYSTEM-MODEL COGNITION: the agent's
own authored rules that USE `SystemModel` (`domains/system_model.py`'s
`model_system` -- the generalisation of TIER 4's `CollapseModel` from SELF to
an ARBITRARY target: self / subgraph / foreign_snapshot / meta), not just
measure it. Fast pytest twin of `scripts/jabberwock_models_others.py` (read
that script's module docstring for the full narrative).

THE MACHINERY (read-only here, never modified): `domains/system_model.py`
(`model_system`) and `domains/system_model_dispatch.py` (`scan_and_model` /
`mint_model_request` -- the mechanical host hook that calls it and wires
`agent -has_system_model-> model`, the same "mechanical exposure of an
already-computed flag to the rule engine" idiom `domains.reflective_faculty.
ensure_grounding_gap_edges` uses for `GroundingGap`, and `domains.
collapse_watch.scan_and_predict` uses for `has_collapse_model`).

THIS FILE covers the follow-on: the agent's OWN decision about WHAT TO DO
with the model. Per CLAUDE.md's discipline, no test here hand-installs the
two system-model rules -- every test either (a) proves the concern genuinely
walls before the new cue exists, or (b) drives `induce_concern` ->
`ground_concern` and reads back what the agent's own composer (`seeds/
composer_system_model_graph.json`, dispatched via the new 'system_model'
RelationCue + 'regard' ComposerCue) authored, or (c) drives the full
model -> belief/recognize pipeline on a real booted agent and reads the graph
state back.

No seed file is mutated at runtime by anything this file exercises (`teach`
is never called by `ground_concern`'s composer-dispatch path, nor by
`domains.system_model_dispatch.scan_and_model`) so no snapshot-guard fixture
is needed for seeds/relation_vocabulary.json / seeds/composer_dispatch.json /
seeds/composer_system_model_graph.json -- the same claim
tests/test_collapse_cognition.py makes for its own seeds.
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

import substrate_rs as srs                                 # noqa: E402
from substrate.boot_core import boot_core                  # noqa: E402
from substrate.seed_loader import manifest_for              # noqa: E402
import domains.reflective_faculty as rf                     # noqa: E402
from domains import system_model_dispatch as smd            # noqa: E402
from domains.system_model import META                       # noqa: E402


class _Agent:
    """Minimal duck-typed agent wrapper -- identical shape to
    tests/test_collapse_cognition.py's own `_Agent` (harness glue only, no
    source modified)."""
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


def _ground_system_model(ag, tag="sm_t"):
    return _ground(ag, ["regard", "OTHER", "SYSTEM"], tag)


# ---------------------------------------------------------------------------
# foreign-graph builders -- same shapes tests/test_system_model.py uses
# (duplicated locally rather than imported, the established local-duplication
# convention this codebase's test suite already follows for _resolve-shaped
# helpers).
# ---------------------------------------------------------------------------
def _build_convergent_foreign_graph() -> dict:
    s = srs.Substrate()
    a = s.add_node("Anchor", {})
    b = s.add_node("Target", {"done": 0.0})
    s._inner.add_edge_unchecked(a, "trig", b)
    s.add_node("Rule", {
        "id": "converge_once",
        "match": [["a", "trig", "b"]],
        "where": {"type": "Lt", "a": {"type": "Attr", "node": {"type": "Var", "name": "b"}, "key": "done"},
                  "b": {"type": "Lit", "value": 0.5}},
        "effect": [["set_attr", "b", "done", 1.0]],
    })
    return s._inner.graph_to_dict()


def _build_divergent_foreign_graph() -> dict:
    s = srs.Substrate()
    a = s.add_node("Anchor", {})
    b = s.add_node("Target", {})
    s._inner.add_edge_unchecked(a, "trig", b)
    s.add_node("Rule", {
        "id": "diverge_always",
        "match": [["a", "trig", "b"]],
        "where": {"type": "Lit", "value": True},
        "effect": [["add_node", "x", "Thing", {}]],
    })
    return s._inner.graph_to_dict()


# ===========================================================================
# 1. the vocabulary genuinely walls before this change (proof, not assumed)
# ===========================================================================
def test_existing_vocabulary_walls_on_regard_before_new_cue():
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    m = dict(manifest_for("relation_vocabulary"))
    m["nodes"] = [n for n in m["nodes"] if n["attrs"].get("name") != "system_model"]
    ag.s._inner.load_seed_manifest(m, ag.agent)

    ind = rf.induce_concern(ag, [["regard", "OTHER", "SYSTEM"]], name_hint="wall_probe")
    assert ind.get("minted") is True
    res = rf.ground_concern(ag, [ind["capability_key"]])
    assert res.get("grounded") is False
    assert res.get("path") == "predicate_grounding"


def test_regard_cue_loads_and_dispatches_to_system_model_composer():
    ag = _fresh_agent()
    name = rf._pick_composer(ag.s, ag.inner, ag.agent, {"regard"})
    assert name == "system_model"


# ===========================================================================
# 2. the jabberwock AUTHORS the two system-model rules via the composer
# ===========================================================================
def test_agent_authors_two_system_model_rules_via_graph_composer():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, [["regard", "OTHER", "SYSTEM"]], name_hint="sm_authors")
    key = ind["capability_key"]
    before = ag.inner.rule_count()
    g = rf.ground_concern(ag, [key])
    after = ag.inner.rule_count()

    assert g.get("grounded") is True, g.get("wall")
    assert g.get("served_by") == "graph"
    assert g.get("path") == "compose_system_model_rule"
    assert after - before == 2, "exactly two rules authored"

    by_name = {r["name"]: r for r in g["rules"]}
    belief = by_name["model_other_belief_" + key]
    assert belief["match"] == [["ag", "has_system_model", "sm"]]
    assert len(belief["effects"]) == 4
    assert belief["effects"][0][:3] == ["add_node", "b", "Belief"]
    assert belief["effects"][1][:4] == ["add_edge", "ag", "expects", "b"]
    assert belief["effects"][2][:4] == ["add_edge", "b", "about_model", "sm"]
    assert belief["effects"][3][:4] == ["add_edge", "sm", "modeled_belief", "b"]
    # NEVER a set_attr on the matched system model (self-inclusion discipline)
    assert all(eff[0] != "set_attr" or eff[1] != "sm" for eff in belief["effects"])

    recog = by_name["recognize_modeling_terminates_" + key]
    assert recog["match"] == [["ag", "has_system_model", "sm"], ["sm", "fixed_point", "fp"]]
    assert len(recog["effects"]) == 1
    assert recog["effects"][0][:4] == ["add_edge", "ag", "recognizes_modeling_terminates", "fp"]
    # NEVER a set_attr on the matched fixed point (the frozen-core discipline)
    assert all(eff[0] != "set_attr" for eff in recog["effects"])


def test_re_grounding_is_idempotent_no_rechurn():
    ag = _fresh_agent()
    ind = rf.induce_concern(ag, [["regard", "OTHER", "SYSTEM"]], name_hint="sm_idem")
    key = ind["capability_key"]
    rf.ground_concern(ag, [key])
    rc1 = ag.inner.rule_count()
    rf.ground_concern(ag, [key])
    rc2 = ag.inner.rule_count()
    assert rc1 == rc2


# ===========================================================================
# 3. MODEL-ANOTHER-SYSTEM -- discriminative: grounded+divergent forms a
#    belief; grounded+convergent does not; ungrounded (even if divergent)
#    does not.
# ===========================================================================
def test_model_other_belief_fires_on_grounded_divergent_foreign_system():
    ag = _fresh_agent()
    _ground_system_model(ag)
    mr = smd.mint_model_request(ag, {"kind": "foreign_snapshot",
                                      "graph": _build_divergent_foreign_graph()})
    results = smd.scan_and_model(ag, horizon=3, imagine_steps=3)
    assert len(results) == 1
    res = results[0]
    assert res.converged is False
    assert res.grounded is True
    ag.inner.run_rules(2000)

    beliefs = [n for n in ag.s.nodes("Belief") if ag.s.node(n)["attrs"].get("kind") == "other_diverging"]
    assert len(beliefs) >= 1, "a grounded, divergent foreign model must form a belief the other diverges"
    assert ag.s.has_edge(ag.agent, "expects", beliefs[0])
    assert ag.s.has_edge(beliefs[0], "about_model", res.model_node)
    assert ag.s.has_edge(res.model_node, "modeled_belief", beliefs[0])
    assert ag.s.node(mr)["attrs"]["status"] == "done"


def test_model_other_belief_does_not_fire_on_convergent_foreign_system():
    ag = _fresh_agent()
    _ground_system_model(ag)
    smd.mint_model_request(ag, {"kind": "foreign_snapshot",
                                 "graph": _build_convergent_foreign_graph()})
    results = smd.scan_and_model(ag, horizon=3, imagine_steps=3)
    assert results[0].converged is True
    assert results[0].grounded is True
    ag.inner.run_rules(2000)

    beliefs = [n for n in ag.s.nodes("Belief") if ag.s.node(n)["attrs"].get("kind") == "other_diverging"]
    assert beliefs == [], "a converged foreign model must never form a diverging belief (discriminative)"


def test_model_other_belief_is_discriminative_between_convergent_and_divergent():
    ag1 = _fresh_agent()
    _ground_system_model(ag1)
    smd.mint_model_request(ag1, {"kind": "foreign_snapshot", "graph": _build_convergent_foreign_graph()})
    smd.scan_and_model(ag1, horizon=3, imagine_steps=3)
    ag1.inner.run_rules(2000)
    n_conv = len([n for n in ag1.s.nodes("Belief") if ag1.s.node(n)["attrs"].get("kind") == "other_diverging"])

    ag2 = _fresh_agent()
    _ground_system_model(ag2)
    smd.mint_model_request(ag2, {"kind": "foreign_snapshot", "graph": _build_divergent_foreign_graph()})
    smd.scan_and_model(ag2, horizon=3, imagine_steps=3)
    ag2.inner.run_rules(2000)
    n_div = len([n for n in ag2.s.nodes("Belief") if ag2.s.node(n)["attrs"].get("kind") == "other_diverging"])

    assert n_conv == 0
    assert n_div >= 1
    assert n_conv != n_div


def test_model_other_belief_does_not_trust_an_ungrounded_model():
    """Pin: the agent only trusts a model of ANOTHER system that is grounded
    in observation. `domains.system_model._model_foreign_snapshot` always
    grounds via a SensorAnchor (system_model.py is read-only here, not
    re-derived) -- so to prove the RULE's own gate actually discriminates on
    `grounded`, this test mints a `SystemModel` node directly (mechanical
    test setup, mirroring how tests/test_system_model.py's own foreign-graph
    builders construct raw graph state) with `grounded: False` on an
    otherwise identical divergent target, and confirms the belief-forming
    rule refuses it."""
    ag = _fresh_agent()
    _ground_system_model(ag)
    sm = ag.s.add_node("SystemModel", {
        "target_kind": "foreign_snapshot", "target_id": "ungrounded_probe",
        "converged": False, "residual": 1.0, "grounded": False,
    })
    ag.s.add_edge(ag.agent, "has_system_model", sm)
    ag.inner.run_rules(2000)

    beliefs = [n for n in ag.s.nodes("Belief") if ag.s.node(n)["attrs"].get("kind") == "other_diverging"]
    assert beliefs == [], "an ungrounded foreign model must never be trusted into a belief (discriminative)"


def test_re_scan_does_not_rechurn_belief():
    ag = _fresh_agent()
    _ground_system_model(ag)
    smd.mint_model_request(ag, {"kind": "foreign_snapshot", "graph": _build_divergent_foreign_graph()})
    smd.scan_and_model(ag, horizon=3, imagine_steps=3)
    ag.inner.run_rules(2000)
    n1 = len(list(ag.s.nodes("Belief")))
    ag.inner.run_rules(2000)
    n2 = len(list(ag.s.nodes("Belief")))
    assert n1 == n2, "the fixpoint guard must stop re-adding a belief every pass"


# ===========================================================================
# 4. REASON-OVER-OWN-MODELING (TIER 5) -- discriminative: a meta SystemModel
#    triggers reflexive termination-recognition; a non-meta one does not.
# ===========================================================================
def test_recognize_modeling_terminates_fires_on_meta_system_model():
    ag = _fresh_agent()
    _ground_system_model(ag)
    smd.mint_model_request(ag, META)
    results = smd.scan_and_model(ag)
    assert len(results) == 1
    res = results[0]
    assert res.target_kind == "meta"
    assert res.fixed_points.get("frozen_drive"), "the frozen 'understand' Drive must be a fixed point"
    ag.inner.run_rules(2000)

    fixed_ids = set(ag.inner.neighbours(res.model_node, "fixed_point"))
    recognized = set(ag.inner.neighbours(ag.agent, "recognizes_modeling_terminates"))
    assert fixed_ids, "the meta SystemModel must carry a non-empty fixed_point sample"
    assert fixed_ids <= recognized, "every sampled fixed point of the meta model must be recognised"

    drives = {n for n in fixed_ids if ag.s.node(n)["type"] == "Drive"}
    assert drives, "the frozen Drive must be among the recognised termination anchors"
    for d in drives:
        names = ag.s.node(d)["attrs"]
        # never mutated -- read-only recognition (frozen-core discipline)
        assert "understand" in [names.get("name")]


def test_recognize_modeling_terminates_does_not_fire_on_non_meta_system_model():
    ag = _fresh_agent()
    _ground_system_model(ag)
    smd.mint_model_request(ag, {"kind": "foreign_snapshot", "graph": _build_divergent_foreign_graph()})
    smd.scan_and_model(ag, horizon=3, imagine_steps=3)
    ag.inner.run_rules(2000)

    recognized = list(ag.inner.neighbours(ag.agent, "recognizes_modeling_terminates"))
    assert recognized == [], "a non-meta SystemModel must never trigger reflexive termination recognition"


def test_absent_system_model_never_fires_either_rule():
    ag = _fresh_agent()
    _ground_system_model(ag)
    # no ModelRequest, no scan_and_model call -- no has_system_model edge exists at all
    ag.inner.run_rules(2000)
    assert list(ag.s.nodes("Belief")) == []
    assert list(ag.inner.neighbours(ag.agent, "recognizes_modeling_terminates")) == []


def test_re_scan_does_not_rechurn_recognition_edges():
    ag = _fresh_agent()
    _ground_system_model(ag)
    smd.mint_model_request(ag, META)
    smd.scan_and_model(ag)
    ag.inner.run_rules(2000)
    n1 = len(list(ag.inner.neighbours(ag.agent, "recognizes_modeling_terminates")))
    ag.inner.run_rules(2000)
    n2 = len(list(ag.inner.neighbours(ag.agent, "recognizes_modeling_terminates")))
    assert n1 == n2, "the fixpoint guard must stop re-adding the same edge every pass"
