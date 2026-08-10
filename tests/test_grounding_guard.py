"""test_grounding_guard — the CONFIDENT-WRONG-OUTSIDE-ITS-RANGE guard, the
agent-authored RESPONSE to domains/grounding_reach.py's GroundingGap flag
(that module is the read-only SUBSTRATE this file consumes, never modified
here — see its own module docstring and tests/test_grounding_reach.py).

THE THEORY: a cheap-model basin-snap that is confidently WRONG has LOW
residual within its own basin, so residual alone can't catch it. What DOES
distinguish it from a genuinely-solved collapse is whether its grounding
chain reaches something EXTERNAL to the agent's own generative loop (an
anchor) or loops back into itself. `flag_ungrounded_confident` already
computes that discriminator and mints a `GroundingGap` node; THIS file
covers the agent's own authored RESPONSE to it: escalate to active
cognition instead of trusting the snap.

Per CLAUDE.md's discipline: no test here hand-installs the guard rule. Every
test either (a) proves the EXISTING RelationCue vocabulary genuinely walls
on the confident-but-ungrounded concern (the proof step before any new
vocabulary was added), or (b) drives `induce_concern` -> `ground_concern`
and reads back what the agent's own composer (the NEW 'grounding_guard'
composer, seeds/composer_grounding_guard_graph.json) authored.

No seed file is mutated at runtime by anything this file exercises (`teach`
is never called by `ground_concern`'s composer-dispatch path, nor by
`domains.reflective_faculty.ensure_grounding_gap_edges`, nor by
`domains.grounding_reach`'s functions) so no snapshot-guard fixture is
needed for seeds/relation_vocabulary.json / seeds/composer_dispatch.json /
seeds/composer_grounding_guard_graph.json — verified by inspection of every
function this file calls.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core          # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402
import domains.reflective_faculty as rf             # noqa: E402
from domains import grounding_reach as gr            # noqa: E402


class _Agent:
    """Minimal duck-typed agent wrapper — identical shape to
    tests/test_experiment_composer_graph.py's own `_Agent` (harness glue
    only, no source modified)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent_with_lexicon() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    return ag


def _fresh_agent_with_prior_lexicon() -> _Agent:
    """The vocabulary AS IT STOOD BEFORE this change: relation_vocabulary
    minus the new `grounding_escalate` cue. Reconstructs the exact
    pre-change state live (rather than asserting a one-time historical
    fact that can no longer be reproduced once the new cue is part of the
    seed) so the STEP-1 wall is a real, re-runnable proof, not a comment."""
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    m = dict(manifest_for("relation_vocabulary"))
    m["nodes"] = [n for n in m["nodes"] if n["attrs"].get("name") != "grounding_escalate"]
    ag.s._inner.load_seed_manifest(m, ag.agent)
    return ag


def _agent_with_autonomy() -> _Agent:
    """+ seeds/autonomy.json, whose ALREADY-SEEDED `mint_goal_from_surprise`
    rule is the standing 'unexplained -> goal' machinery the guard's
    escalation plugs into (an `agent -surprised_by-> impasse` edge is all
    the guard rule mints; this rule is what turns it into a wanted Goal)."""
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _axis(ag, tag, preds):
    return ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "induced": 1.0,
        "residual_predicates": preds, "from_observation": 1.0, "source": "concern_induction",
    })


# ---------------------------------------------------------------------------
# STEP 1 — the held vocabulary, AS-IS, genuinely walls (proof this wasn't
# assumed: the existing 45 RelationCues do not cover escalate/ungrounded/
# reground/anchor-reachability).
# ---------------------------------------------------------------------------
def test_existing_vocabulary_walls_on_confident_but_ungrounded():
    """induce_concern keys the residual on each CLAUSE's FIRST WORD (the
    documented gotcha) -- a single 5-word clause is ONE relation whose
    predicate is its first word, 'ground'. Driven through the REAL
    induce_concern -> ground_concern seam (not the `_axis` shortcut, which
    would bypass that first-word extraction), against the vocabulary as it
    stood BEFORE this change."""
    ag = _fresh_agent_with_prior_lexicon()
    ind = rf.induce_concern(ag, [["ground", "the", "collapse", "when", "ungrounded"]],
                             name_hint="wall_probe")
    assert ind.get("minted") is True
    res = rf.ground_concern(ag, [ind["capability_key"]])
    assert res.get("grounded") is False
    assert res.get("path") == "predicate_grounding"
    assert "NO held structural relation" in res.get("wall", "")


def test_existing_vocabulary_walls_even_on_a_richer_clause():
    """A richer word-list (one clause per word, including 'reach'/'anchor')
    still does not genuinely ground on the PRIOR vocabulary: an accidental
    substring hit (e.g. 'reach' containing 'each', matching the held
    iterate_each cue) still walls at generate_from_residual for lack of a
    feed-forward step -- not a real semantic match."""
    ag = _fresh_agent_with_prior_lexicon()
    words = ["ground", "escalate", "reach", "anchor", "reground", "trust", "confident", "active", "cognition"]
    ind = rf.induce_concern(ag, [[w] for w in words], name_hint="wall_probe_2")
    assert ind.get("minted") is True
    res = rf.ground_concern(ag, [ind["capability_key"]])
    assert res.get("grounded") is False


# ---------------------------------------------------------------------------
# STEP 2 — the MINIMAL new vocabulary (one RelationCue, one ComposerCue).
# ---------------------------------------------------------------------------
def test_grounding_escalate_cue_loads():
    ag = _fresh_agent_with_lexicon()
    cues = {at["name"]: at for at in (ag.s.node(n)["attrs"] for n in ag.s.nodes("RelationCue"))}
    assert "grounding_escalate" in cues
    assert json.loads(cues["grounding_escalate"]["relation"]) == ["escalate", "COLLAPSE", "when", "UNGROUNDED"]


def test_composer_dispatch_routes_escalate_to_grounding_guard():
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    name = rf._pick_composer(ag.s, ag.inner, ag.agent, {"escalate"})
    assert name == "grounding_guard"


# ---------------------------------------------------------------------------
# STEP 3 — the jabberwock AUTHORS the guard rule via the composer.
# ---------------------------------------------------------------------------
def test_agent_authors_the_guard_rule_via_graph_composer():
    ag = _fresh_agent_with_lexicon()
    ind = rf.induce_concern(ag, [["escalate", "COLLAPSE", "when", "UNGROUNDED"]],
                             name_hint="grounding_guard_concern")
    assert ind.get("minted") is True, ind.get("note")
    key = ind["capability_key"]

    before = ag.inner.rule_count()
    g = rf.ground_concern(ag, [key])
    after = ag.inner.rule_count()

    assert g.get("grounded") is True, g.get("wall")
    assert g.get("served_by") == "graph"
    assert g.get("path") == "compose_grounding_guard_rule"
    assert after - before == 1, "exactly one guard rule authored"

    rule = g["rule"]
    assert rule["name"] == "escalate_grounding_gap_" + key
    assert rule["match"] == [["ag", "has_grounding_gap", "gap"]]
    assert rule["where"] == {"type": "Eq",
                              "a": {"type": "Attr", "node": {"type": "Var", "name": "gap"}, "key": "escalated"},
                              "b": {"type": "Lit", "value": None}}
    ops = rule["effects"]
    assert ops[0][:3] == ["add_node", "mi", "Impasse"]
    assert ops[0][3]["kind"] == "grounding_gap"
    assert ops[1] == ["add_edge", "ag", "surprised_by", "mi", {}]
    assert ops[2] == ["add_edge", "mi", "about_gap", "gap", {}]
    assert ops[3] == ["set_attr", "gap", "escalated", True]


def test_re_grounding_is_idempotent_no_rechurn():
    """A second `wants_grounding_guard_rule` request (same tag) must not
    mint a second copy of the rule -- the meta-rule's own Lt(composed,0.5)
    guard."""
    ag = _fresh_agent_with_lexicon()
    ind = rf.induce_concern(ag, [["escalate", "COLLAPSE", "when", "UNGROUNDED"]],
                             name_hint="grounding_guard_idem")
    key = ind["capability_key"]
    rf.ground_concern(ag, [key])
    rc1 = ag.inner.rule_count()
    rf.ground_concern(ag, [key])
    rc2 = ag.inner.rule_count()
    assert rc1 == rc2


# ---------------------------------------------------------------------------
# THE DISCRIMINATIVE GATE — grounding, not confidence/residual, gates trust.
# ---------------------------------------------------------------------------
def _install_guard(ag) -> str:
    ind = rf.induce_concern(ag, [["escalate", "COLLAPSE", "when", "UNGROUNDED"]],
                             name_hint="grounding_guard_gate")
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "graph"
    return ind["capability_key"]


def _mk_scenarios(ag):
    """Same shapes tests/test_grounding_reach.py's own `_mk()` fixture
    reconstructs (scenarios c/d/e there), built here on the SAME agent the
    guard rule will run over."""
    s = ag.s
    n = {}
    n["percept"] = s.add_node("VisionPercept", {})
    s._inner.add_edge_unchecked(ag.agent, "perceives", n["percept"])

    n["trusted"] = s.add_node("Collapse", {"residual": 0.01, "confidence": 0.97})
    s._inner.add_edge_unchecked(n["trusted"], "grounded_in", n["percept"])

    n["untrusted"] = s.add_node("Collapse", {"residual": 0.01, "confidence": 0.97})

    n["axis_sat_ungrounded"] = s.add_node("CapabilityAxis", {
        "residual": 0.0, "confidence": 0.99, "saturation": 1.0})

    n["run"] = s.add_node("Run", {"status": "done", "score": 12.0, "frames": 12.0})
    n["experiment"] = s.add_node("Experiment", {"status": "requested", "outcome": "supported"})
    s._inner.add_edge_unchecked(n["experiment"], "produced", n["run"])
    n["axis_sat_grounded"] = s.add_node("CapabilityAxis", {
        "residual": 0.0, "confidence": 0.99, "saturation": 1.0})
    s._inner.add_edge_unchecked(n["axis_sat_grounded"], "grounded_in", n["experiment"])
    return n


def _run_guard(ag, n):
    gr.ensure_grounding_edges(ag)
    gr.flag_ungrounded_confident(ag, node_types=["Collapse", "CapabilityAxis"])
    rf.ensure_grounding_gap_edges(ag)
    ag.inner.run_rules(2000)

    s = ag.s
    gap_by_node = {}
    for gnode in s.nodes("GroundingGap"):
        gap_by_node[s.node(gnode)["attrs"]["node"]] = gnode

    def verdict(key):
        node = n[key]
        gap = gap_by_node.get(node)
        escalated = False
        wants = False
        if gap is not None:
            for mi in s.nodes("Impasse"):
                if s.has_edge(mi, "about_gap", gap):
                    escalated = s.has_edge(ag.agent, "surprised_by", mi)
                    wants = s.has_edge(ag.agent, "wants", mi)
                    break
        return {"flagged": gap is not None, "escalated": escalated, "wants_goal": wants}

    return {k: verdict(k) for k in ("trusted", "untrusted", "axis_sat_ungrounded", "axis_sat_grounded")}


def test_grounded_node_never_flagged_or_escalated():
    ag = _fresh_agent_with_lexicon()
    _install_guard(ag)
    n = _mk_scenarios(ag)
    v = _run_guard(ag, n)
    assert v["trusted"] == {"flagged": False, "escalated": False, "wants_goal": False}


def test_ungrounded_node_is_flagged_and_escalated():
    ag = _fresh_agent_with_lexicon()
    _install_guard(ag)
    n = _mk_scenarios(ag)
    v = _run_guard(ag, n)
    assert v["untrusted"]["flagged"] is True
    assert v["untrusted"]["escalated"] is True, "the guard rule must fire: surprised_by an Impasse about the gap"


def test_ungrounded_node_becomes_a_wanted_goal_via_existing_autonomy_machinery():
    """The full active-cognition engagement: with seeds/autonomy.json loaded
    (its OWN already-seeded mint_goal_from_surprise, not reimplemented
    here), the guard's `surprised_by` edge becomes a wanted Goal on its
    own -- proof the escalation actually reaches active cognition, not a
    dangling edge."""
    ag = _agent_with_autonomy()
    _install_guard(ag)
    n = _mk_scenarios(ag)
    v = _run_guard(ag, n)
    assert v["untrusted"] == {"flagged": True, "escalated": True, "wants_goal": True}


def test_residual_salience_reconstruction_saturated_ungrounded_escalates():
    """The 2026-07-02 residual-salience incident, reconstructed: a SATURATED
    axis (residual~0, confidence high) with NO live grounding must be
    escalated -- this is exactly what would have stopped the 24x re-grind
    (Argmax re-picking a flat-tied, unexplained 'solved' axis) instead of
    silently trusting it."""
    ag = _agent_with_autonomy()
    _install_guard(ag)
    n = _mk_scenarios(ag)
    v = _run_guard(ag, n)
    assert v["axis_sat_ungrounded"]["flagged"] is True
    assert v["axis_sat_ungrounded"]["escalated"] is True
    assert v["axis_sat_ungrounded"]["wants_goal"] is True


def test_residual_salience_reconstruction_saturated_grounded_is_not_escalated():
    """The SAME saturated shape, grounded in a real judged Experiment
    (ConsequenceAnchor), must NOT be escalated -- discriminative: grounding,
    not confidence/residual, gates trust."""
    ag = _agent_with_autonomy()
    _install_guard(ag)
    n = _mk_scenarios(ag)
    v = _run_guard(ag, n)
    assert v["axis_sat_grounded"] == {"flagged": False, "escalated": False, "wants_goal": False}


def test_full_discriminative_table_in_one_run():
    """All four scenarios on ONE agent, ONE guard install, ONE run_rules
    pass -- the table the task's gate calls for."""
    ag = _agent_with_autonomy()
    _install_guard(ag)
    n = _mk_scenarios(ag)
    v = _run_guard(ag, n)
    assert v["trusted"]["flagged"] is False and v["trusted"]["escalated"] is False
    assert v["untrusted"]["flagged"] is True and v["untrusted"]["escalated"] is True
    assert v["axis_sat_ungrounded"]["flagged"] is True and v["axis_sat_ungrounded"]["escalated"] is True
    assert v["axis_sat_grounded"]["flagged"] is False and v["axis_sat_grounded"]["escalated"] is False


def test_gap_is_never_re_escalated_once_marked():
    """Fixpoint safety: a GroundingGap escalated once (gap.escalated=True)
    must not mint a second Impasse on a later run_rules pass. Two of the
    four scenario nodes (untrusted, axis_sat_ungrounded) are genuinely
    ungrounded, so exactly TWO Impasses are expected -- and re-running
    run_rules must not grow that count."""
    ag = _agent_with_autonomy()
    _install_guard(ag)
    n = _mk_scenarios(ag)
    _run_guard(ag, n)
    impasse_count_1 = len(list(ag.s.nodes("Impasse")))
    ag.inner.run_rules(2000)
    ag.inner.run_rules(2000)
    impasse_count_2 = len(list(ag.s.nodes("Impasse")))
    assert impasse_count_1 == impasse_count_2 == 2


def test_new_grounding_gap_after_guard_installed_still_escalates():
    """A GroundingGap minted AFTER the guard rule already exists (a later
    tick's flag pass) must still be caught -- the rule matches generically,
    it was not authored FOR one specific node."""
    ag = _agent_with_autonomy()
    _install_guard(ag)
    n = _mk_scenarios(ag)
    _run_guard(ag, n)  # first pass: trusted/untrusted/axes resolved

    # a SECOND ungrounded confident node, appearing later
    late = ag.s.add_node("Collapse", {"residual": 0.01, "confidence": 0.97})
    gr.flag_ungrounded_confident(ag, node_types=["Collapse"])
    rf.ensure_grounding_gap_edges(ag)
    ag.inner.run_rules(2000)

    gap = None
    for gnode in ag.s.nodes("GroundingGap"):
        if ag.s.node(gnode)["attrs"]["node"] == late:
            gap = gnode
            break
    assert gap is not None
    escalated = any(ag.s.has_edge(mi, "about_gap", gap) and ag.s.has_edge(ag.agent, "surprised_by", mi)
                     for mi in ag.s.nodes("Impasse"))
    assert escalated is True
