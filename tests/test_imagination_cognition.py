"""test_imagination_cognition -- TIER 3 COGNITION: active cognition now
IMAGINES a detached counterfactual when escalated, instead of only
re-grinding. Fast pytest twin of scripts/jabberwock_imagines_when_stuck.py
(read that script's module docstring for the full narrative).

THE MACHINERY (read-only here, never modified): `domains/imagination.py`
(`imagine`/`reground`/`commit_imagination` -- snapshot / cut grounded_in /
inject / tick / diff / reground / gated commit, pure host I/O per that
module's own docstring).

THIS FILE covers the follow-on this codebase's CLAUDE.md calls for: the
agent's OWN DECISION about WHEN to imagine and WHAT to do with the result.
Per CLAUDE.md's discipline, no test here hand-installs the engage/judge
rules -- every test either (a) proves escalation WITHOUT the new
composer's rules still only re-grinds (the contrast), or (b) drives
`induce_concern` -> `ground_concern` and reads back what the agent's own
composer (`seeds/composer_imagination_graph.json`, dispatched via the new
'imagine' RelationCue + ComposerCue) authored, or (c) drives the full
escalate -> engage -> `domains.imagination_dispatch.scan_and_imagine` ->
judge pipeline on a real booted agent and reads the graph state back.

No seed file is mutated at runtime by anything this file exercises (`teach`
is never called by `ground_concern`'s composer-dispatch path, nor by
`domains.imagination_dispatch.scan_and_imagine`, nor by
`domains.reflective_faculty.ensure_grounding_gap_edges`) so no snapshot-
guard fixture is needed for seeds/relation_vocabulary.json /
seeds/composer_dispatch.json / seeds/composer_imagination_graph.json --
verified by inspection of every function this file calls (same claim
tests/test_grounding_guard.py makes for its own seeds).
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
from domains import grounding_reach as gr           # noqa: E402
from domains import imagination_dispatch as idisp   # noqa: E402


class _Agent:
    """Minimal duck-typed agent wrapper -- identical shape to
    tests/test_grounding_guard.py's own `_Agent` (harness glue only, no
    source modified)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent(*, with_autonomy=True) -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    if with_autonomy:
        ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _ground(ag, cue_clause, name_hint):
    ind = rf.induce_concern(ag, [cue_clause], name_hint=name_hint)
    assert ind.get("minted") is True, ind
    g = rf.ground_concern(ag, [ind["capability_key"]])
    assert g.get("grounded") is True and g.get("served_by") == "graph", g
    return g


def _install_guard_and_gate(ag):
    g1 = _ground(ag, ["escalate", "COLLAPSE", "when", "UNGROUNDED"], "grounding_guard_t")
    g2 = _ground(ag, ["worth", "REFINEMENT", "by", "RESIDUAL_MINUS_COST"], "escalation_gate_t")
    g3 = _ground(ag, ["imagine", "COLLAPSE", "from", "IMPASSE"], "imagination_t")
    return g1, g2, g3


def _install_survive_discard_fixture(ag):
    """See scripts/jabberwock_imagines_when_stuck.py's twin for the full
    rationale -- reused verbatim (test-fixture rules only, not the agent's
    authored engage/judge rules)."""
    def _foc_ungrounded():
        return {"type": "Eq", "a": {"type": "Count", "source": {
            "type": "Neighbours", "node": {"type": "Var", "name": "foc"},
            "edge_type": "grounded_in"}}, "b": {"type": "Lit", "value": 0}}

    def _not_yet(var, edge_type):
        return {"type": "Eq", "a": {"type": "Count", "source": {
            "type": "Neighbours", "node": {"type": "Var", "name": var},
            "edge_type": edge_type}}, "b": {"type": "Lit", "value": 0}}

    ag.s.add_node("Rule", {
        "id": "derive_conclusion_when_ungrounded",
        "match": [["h", "contradicts", "foc"]],
        "where": {"type": "And", "items": [_foc_ungrounded(), _not_yet("h", "yields")]},
        "effect": [["add_node", "c", "Conclusion", {"derived_from_imagination": True}],
                   ["add_edge", "h", "yields", "c", {}]],
    })
    ag.s.add_node("Rule", {
        "id": "mutate_implied_when_ungrounded",
        "match": [["h", "contradicts", "foc"], ["foc", "implies", "tgt"]],
        "where": {"type": "And", "items": [_foc_ungrounded(), _not_yet("h", "revised")]},
        "effect": [["set_attr", "tgt", "value", "MUTATED_BY_IMAGINATION"],
                   ["add_edge", "h", "revised", "tgt", {}]],
    })


def _mk_grounding_gap_scenario(ag):
    s = ag.s
    anchor = s.add_node("RealityAnchor", {})
    tgt = s.add_node("Fact", {"value": "blue"})
    s._inner.add_edge_unchecked(tgt, "grounded_in", anchor)
    foc = s.add_node("Collapse", {"residual": 0.01, "confidence": 0.97})
    s._inner.add_edge_unchecked(foc, "implies", tgt)
    return {"anchor": anchor, "tgt": tgt, "foc": foc}


def _mk_cost_worth_scenario(ag):
    """Same shape composer_escalation_gate_graph's own dispatch needs:
    a CapabilityAxis frontier_pick whose shortfall+(1-saturation)-cost is
    positive (worth refining)."""
    s = ag.s
    ax = s.add_node("CapabilityAxis", {"shortfall": 0.8, "saturation": 0.1, "cost": 0.1})
    s._inner.add_edge_unchecked(ag.agent, "frontier_pick", ax)
    return ax


# ---------------------------------------------------------------------------
# 1. the vocabulary genuinely walls before this change (proof, not assumed)
# ---------------------------------------------------------------------------
def test_existing_vocabulary_walls_on_imagine_before_new_cue():
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    m = dict(manifest_for("relation_vocabulary"))
    m["nodes"] = [n for n in m["nodes"] if n["attrs"].get("name") != "imagine_counterfactual"]
    ag.s._inner.load_seed_manifest(m, ag.agent)

    ind = rf.induce_concern(ag, [["imagine", "COLLAPSE", "from", "IMPASSE"]], name_hint="wall_probe")
    assert ind.get("minted") is True
    res = rf.ground_concern(ag, [ind["capability_key"]])
    assert res.get("grounded") is False
    assert res.get("path") == "predicate_grounding"


def test_imagine_cue_loads_and_dispatches_to_imagination_composer():
    ag = _fresh_agent(with_autonomy=False)
    name = rf._pick_composer(ag.s, ag.inner, ag.agent, {"imagine"})
    assert name == "imagination"


# ---------------------------------------------------------------------------
# 2. the jabberwock AUTHORS the engage + judge rules via the composer
# ---------------------------------------------------------------------------
def test_agent_authors_engage_and_judge_rules_via_graph_composer():
    ag = _fresh_agent(with_autonomy=False)
    ind = rf.induce_concern(ag, [["imagine", "COLLAPSE", "from", "IMPASSE"]],
                             name_hint="imagination_authors")
    key = ind["capability_key"]
    before = ag.inner.rule_count()
    g = rf.ground_concern(ag, [key])
    after = ag.inner.rule_count()

    assert g.get("grounded") is True, g.get("wall")
    assert g.get("served_by") == "graph"
    assert g.get("path") == "compose_imagination_rule"
    assert after - before == 3, "exactly three rules authored (2 engage + 1 judge)"

    by_name = {r["name"]: r for r in g["rules"]}
    engage_gap = by_name["engage_imagine_grounding_gap_" + key]
    assert engage_gap["match"] == [["ag", "surprised_by", "imp"], ["imp", "about_gap", "gap"]]
    assert engage_gap["effects"][0][:3] == ["add_node", "ir", "ImagineRequest"]
    assert engage_gap["effects"][0][3]["kind"] == "grounding_gap"
    assert engage_gap["effects"][1] == ["add_edge", "ir", "focuses_on_gap", "gap", {}]
    assert engage_gap["effects"][2] == ["add_edge", "ir", "about_impasse", "imp", {}]
    assert engage_gap["effects"][3] == ["set_attr", "imp", "imagine_requested", True]

    engage_cost = by_name["engage_imagine_cost_worth_" + key]
    assert engage_cost["match"] == [["ag", "surprised_by", "imp"], ["imp", "about_axis", "ax"]]
    assert engage_cost["effects"][0][3]["kind"] == "cost_worth_refining"
    assert engage_cost["effects"][1] == ["add_edge", "ir", "focuses_on_axis", "ax", {}]

    judge = by_name["judge_imagined_conclusion_" + key]
    assert judge["match"] == [["ag", "produced_imagination", "imn"], ["imn", "imagined", "concl"]]
    assert judge["effects"] == [["set_attr", "concl", "acted", True],
                                 ["add_edge", "ag", "wants_to_commit", "imn", {}]]


def test_re_grounding_is_idempotent_no_rechurn():
    ag = _fresh_agent(with_autonomy=False)
    ind = rf.induce_concern(ag, [["imagine", "COLLAPSE", "from", "IMPASSE"]], name_hint="imagination_idem")
    key = ind["capability_key"]
    rf.ground_concern(ag, [key])
    rc1 = ag.inner.rule_count()
    rf.ground_concern(ag, [key])
    rc2 = ag.inner.rule_count()
    assert rc1 == rc2


# ---------------------------------------------------------------------------
# 3. THE CONTRAST -- escalation WITHOUT the engage rule never imagines
# ---------------------------------------------------------------------------
def test_escalation_without_engage_rule_never_imagines():
    ag = _fresh_agent()
    _ground(ag, ["escalate", "COLLAPSE", "when", "UNGROUNDED"], "contrast_guard")
    _mk_grounding_gap_scenario(ag)
    gr.ensure_grounding_edges(ag)
    gr.flag_ungrounded_confident(ag, node_types=["Collapse"])
    rf.ensure_grounding_gap_edges(ag)
    ag.inner.run_rules(2000)

    assert len(list(ag.s.nodes("Impasse"))) >= 1, "the guard must still escalate"
    assert list(ag.s.nodes("ImagineRequest")) == [], \
        "WITHOUT the engage rule, an escalated impasse must never mint an ImagineRequest"


def test_absent_impasse_never_imagines_even_with_engage_rule_installed():
    ag = _fresh_agent()
    _install_guard_and_gate(ag)
    # no scenario, no flagging -- nothing surprised_by anything
    ag.inner.run_rules(2000)
    assert list(ag.s.nodes("ImagineRequest")) == []


# ---------------------------------------------------------------------------
# 4. ACTIVE COGNITION NOW IMAGINES -- the full pipeline, grounding_gap arm
# ---------------------------------------------------------------------------
def test_grounding_gap_escalation_mints_imagine_request():
    ag = _fresh_agent()
    _install_guard_and_gate(ag)
    _install_survive_discard_fixture(ag)
    _mk_grounding_gap_scenario(ag)
    gr.ensure_grounding_edges(ag)
    gr.flag_ungrounded_confident(ag, node_types=["Collapse"])
    rf.ensure_grounding_gap_edges(ag)
    ag.inner.run_rules(2000)

    requests = list(ag.s.nodes("ImagineRequest"))
    assert len(requests) >= 1
    kinds = {ag.s.node(r)["attrs"].get("kind") for r in requests}
    assert "grounding_gap" in kinds
    for r in requests:
        assert ag.s.node(r)["attrs"]["status"] == "requested"


def test_cost_worth_escalation_mints_imagine_request():
    ag = _fresh_agent()
    _install_guard_and_gate(ag)
    _mk_cost_worth_scenario(ag)
    ag.inner.run_rules(2000)

    requests = list(ag.s.nodes("ImagineRequest"))
    kinds = {ag.s.node(r)["attrs"].get("kind") for r in requests}
    assert "cost_worth_refining" in kinds
    cost_reqs = [r for r in requests if ag.s.node(r)["attrs"].get("kind") == "cost_worth_refining"]
    assert cost_reqs
    r = cost_reqs[0]
    axes = list(ag.inner.neighbours(r, "focuses_on_axis"))
    assert axes, "the cost_worth_refining request must point at the CapabilityAxis"


def test_scan_and_imagine_runs_the_request_and_mints_the_trace():
    ag = _fresh_agent()
    _install_guard_and_gate(ag)
    _install_survive_discard_fixture(ag)
    _mk_grounding_gap_scenario(ag)
    gr.ensure_grounding_edges(ag)
    gr.flag_ungrounded_confident(ag, node_types=["Collapse"])
    rf.ensure_grounding_gap_edges(ag)
    ag.inner.run_rules(2000)

    assert list(ag.s.nodes("Imagination")) == []
    touched = idisp.scan_and_imagine(ag)
    assert len(touched) >= 1
    assert list(ag.s.nodes("Imagination")), "the imagine()/reground() trace must appear"
    assert list(ag.s.nodes("ImaginedConclusion"))
    for r in touched:
        assert ag.s.node(r)["attrs"]["status"] == "done"

    # idempotent: a second scan does nothing (no more requested requests)
    touched2 = idisp.scan_and_imagine(ag)
    assert touched2 == []


# ---------------------------------------------------------------------------
# 5. THE JUDGE + RETURN PATH -- discriminative both ways
# ---------------------------------------------------------------------------
def _run_full_pipeline(ag):
    _install_guard_and_gate(ag)
    _install_survive_discard_fixture(ag)
    n = _mk_grounding_gap_scenario(ag)
    gr.ensure_grounding_edges(ag)
    gr.flag_ungrounded_confident(ag, node_types=["Collapse"])
    rf.ensure_grounding_gap_edges(ag)
    ag.inner.run_rules(2000)
    idisp.scan_and_imagine(ag)
    ag.inner.run_rules(2000)   # let the agent's own judge rule fire
    return n


def test_judge_acts_on_survivors_not_on_discarded():
    ag = _fresh_agent()
    n = _run_full_pipeline(ag)

    conclusions = list(ag.s.nodes("ImaginedConclusion"))
    survived = [c for c in conclusions if ag.s.node(c)["attrs"].get("status") == "survived"]
    discarded = [c for c in conclusions if ag.s.node(c)["attrs"].get("status") == "discarded"]
    assert survived and discarded, "the fixture must produce BOTH a survivor and a discard"

    assert all(ag.s.node(c)["attrs"].get("acted") is True for c in survived)
    assert all(ag.s.node(c)["attrs"].get("acted") is not True for c in discarded)

    imaginations = list(ag.s.nodes("Imagination"))
    assert imaginations
    assert ag.s.has_edge(ag.agent, "wants_to_commit", imaginations[0]), \
        "the judge rule must request a gated commit for a surviving imagination"


def test_discarded_conclusion_never_acted_on_even_beside_a_trivial_survivor():
    """A fixture with ONLY the discard-producing derived rule installed
    (no `derive_conclusion_when_ungrounded` mint-a-fresh-Conclusion rule)
    still yields ONE trivial survivor: the injected `Hypothesis` node
    itself (`imagine()`'s own `conclusions` diff is taken against the
    PRE-hypothesis snapshot -- see domains/imagination.py's `imagine()` --
    so the injected assumption always shows up as a `node_added`
    conclusion, and a bare assumption has nothing live to contradict by
    identity, so it always survives; only what is DERIVED from it and
    contradicts a grounded live fact is discarded). The judge rule
    legitimately acts on that trivial survivor (requests commit for the
    bare assumption) -- what this test pins is that the GENUINE discard
    (the mutated, contradicting `tgt`) is NEVER marked acted, even though
    a sibling conclusion from the SAME imagination was."""
    ag = _fresh_agent()
    _install_guard_and_gate(ag)

    def _foc_ungrounded():
        return {"type": "Eq", "a": {"type": "Count", "source": {
            "type": "Neighbours", "node": {"type": "Var", "name": "foc"},
            "edge_type": "grounded_in"}}, "b": {"type": "Lit", "value": 0}}
    ag.s.add_node("Rule", {
        "id": "mutate_implied_when_ungrounded_only",
        "match": [["h", "contradicts", "foc"], ["foc", "implies", "tgt"]],
        "where": _foc_ungrounded(),
        "effect": [["set_attr", "tgt", "value", "MUTATED_BY_IMAGINATION"]],
    })
    _mk_grounding_gap_scenario(ag)
    gr.ensure_grounding_edges(ag)
    gr.flag_ungrounded_confident(ag, node_types=["Collapse"])
    rf.ensure_grounding_gap_edges(ag)
    ag.inner.run_rules(2000)
    idisp.scan_and_imagine(ag)
    ag.inner.run_rules(2000)

    conclusions = list(ag.s.nodes("ImaginedConclusion"))
    assert conclusions
    discarded = [c for c in conclusions if ag.s.node(c)["attrs"].get("status") == "discarded"]
    survived = [c for c in conclusions if ag.s.node(c)["attrs"].get("status") == "survived"]
    assert discarded, "the mutated, contradicting tgt must be discarded"
    assert all(ag.s.node(c)["attrs"].get("acted") is not True for c in discarded), \
        "a discarded (fantasy) conclusion must never be acted on"
    # the ONLY conclusions besides the genuine discard are the trivial
    # injected assumption itself (node_added Hypothesis) and the injected
    # `contradicts` edge (edge_added) -- both survive because there is
    # nothing live to contradict by identity; if reground found any OTHER
    # survivor this fixture's premise (discard-only derived rule) is wrong
    assert all(ag.s.node(c)["attrs"].get("kind") in ("node_added", "edge_added") for c in survived)


# ---------------------------------------------------------------------------
# 6. REVERSIBILITY -- the live domain fact is never mutated by imagine()/
#    reground()/the engage or judge rules, only by the (never-called-here)
#    gated commit_imagination path.
# ---------------------------------------------------------------------------
def test_reversibility_live_fact_untouched_through_full_pipeline():
    ag = _fresh_agent()
    n = _run_full_pipeline(ag)
    assert ag.s.node(n["tgt"])["attrs"]["value"] == "blue"
    assert list(ag.s.nodes("Commitment")) == [], "the judge only REQUESTS, never commits"


def test_reversibility_domain_node_count_stable_besides_trace():
    """Every node minted across the whole pipeline is either scenario setup
    (pre-imagine) or the sanctioned trace types -- imagine()/reground()
    itself adds nothing else to the live graph (see
    tests/test_imagination.py::test_reversibility_domain_untouched_by_imagine
    for the underlying machinery-level proof; this pins the SAME invariant
    survives composition with the engage/judge rules)."""
    ag = _fresh_agent()
    _install_guard_and_gate(ag)
    _install_survive_discard_fixture(ag)
    _mk_grounding_gap_scenario(ag)
    gr.ensure_grounding_edges(ag)
    gr.flag_ungrounded_confident(ag, node_types=["Collapse"])
    rf.ensure_grounding_gap_edges(ag)
    ag.inner.run_rules(2000)
    before = ag.s._inner.graph_to_dict()

    idisp.scan_and_imagine(ag)
    ag.inner.run_rules(2000)
    after = ag.s._inner.graph_to_dict()

    import substrate_rs as srs
    diff = srs._native.Substrate.graph_diff(before, after)
    assert diff["nodes_removed"] == []
    assert diff["edges_removed"] == []
    # only ImagineRequest (status/n_survived/n_discarded), Impasse
    # (imagine_requested), ImaginedConclusion (status/reason/acted) and
    # Imagination (status/n_survived/n_discarded, from a later reground) may
    # change -- never a pre-existing DOMAIN node (Fact/Collapse/CapabilityAxis).
    allowed_types = {"ImagineRequest", "Impasse", "Imagination", "ImaginedConclusion"}
    for entry in diff["nodes_changed"]:
        nid_val = entry["id"]
        import substrate_rs as _srs
        nid = _srs.NodeID(nid_val)
        if not ag.s.has_node(nid):
            continue
        t = ag.s.node(nid)["type"]
        assert t in allowed_types, f"unexpected node type changed: {t}"
