"""Graph-only self-tests rehearse inside detached cognition, not LS20 children."""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from domains.imagination_dispatch import scan_and_imagine
from substrate.world_adapter import WorldAdapter


def _edge(agent, source, edge_type, target):
    agent.inner.add_edge_unchecked(source, edge_type, target)


def _rule(name: str, value: str):
    return {
        "name": name,
        "match": [["trigger", "drives", "target"]],
        "where": {"type": "Lit", "value": True},
        "effects": [["set_attr", "target", "state", value]],
    }


def test_graph_hypothesis_uses_detached_cognition_and_keeps_live_state_unchanged():
    agent = WorldAdapter(seeds=("counterfactual_experiment",))
    axis = agent.s.add_node("CapabilityAxis", {"residual": 1})
    trigger = agent.s.add_node("CounterfactualTrigger", {})
    target = agent.s.add_node("CounterfactualTarget", {"state": "unresolved"})
    _edge(agent, axis, "monitors", target)
    _edge(agent, trigger, "drives", target)

    baseline = _rule("held_baseline", "baseline")
    variant = _rule("proposed_variant", "variant")
    agent.inner.add_rule(baseline)
    experiment = agent.s.add_node("Experiment", {
        "status": "counterfactual_requested",
        "epistemic_scope": "graph_counterfactual",
        "hypothesis": "the proposed rule changes the target",
    })
    delta = agent.s.add_node("SeedDelta", {
        "skip_seeds": "[]",
        "add_rules": json.dumps([variant]),
        "remove_rules": json.dumps(["held_baseline"]),
        "add_concepts": "[]",
        "remove_concepts": "[]",
        "set_node_attrs": "[]",
    })
    _edge(agent, axis, "tested_by", experiment)
    _edge(agent, experiment, "has_delta", delta)

    agent.tick()
    assert agent.s.node(target)["attrs"]["state"] == "baseline"
    requests = list(agent.s.nodes("ImagineRequest"))
    assert len(requests) == 1
    assert agent.s.node(experiment)["attrs"]["status"] == "counterfactual_running"

    assert scan_and_imagine(agent) == requests
    # The proposed variant only ran in the detached graph.
    assert agent.s.node(target)["attrs"]["state"] == "baseline"
    imaginations = list(agent.inner.neighbours(requests[0], "produced_imagination"))
    assert len(imaginations) == 1
    report = agent.s.node(imaginations[0])["attrs"]["rewrite_delta_report"]
    assert list(report["rules_removed"]) == ["held_baseline"]
    assert list(report["rules_added"]) == ["proposed_variant"]
    conclusions = list(agent.inner.neighbours(imaginations[0], "imagined"))
    assert any(agent.s.node(c)["attrs"].get("attrs_after", {}).get("state") == "variant"
               for c in conclusions)

    agent.tick()
    attrs = agent.s.node(experiment)["attrs"]
    assert attrs["status"] == "counterfactual_done"
    assert attrs["evidence_kind"] == "imagined"
    assert attrs["requires_external_validation"] == 1


def test_external_test_is_not_relabelled_as_counterfactual():
    agent = WorldAdapter(seeds=("counterfactual_experiment",))
    axis = agent.s.add_node("CapabilityAxis", {"residual": 1})
    experiment = agent.s.add_node("Experiment", {
        "status": "requested", "epistemic_scope": "external",
    })
    delta = agent.s.add_node("SeedDelta", {})
    _edge(agent, axis, "tested_by", experiment)
    _edge(agent, experiment, "has_delta", delta)
    agent.tick()
    assert not list(agent.s.nodes("ImagineRequest"))
    assert agent.s.node(experiment)["attrs"]["status"] == "requested"


def test_fresh_boot_delta_reports_counterfactual_capability_boundary():
    agent = WorldAdapter(seeds=("counterfactual_experiment",))
    axis = agent.s.add_node("CapabilityAxis", {"residual": 1})
    experiment = agent.s.add_node("Experiment", {
        "status": "counterfactual_requested",
        "epistemic_scope": "graph_counterfactual",
        "hypothesis": "withhold a whole seed",
    })
    delta = agent.s.add_node("SeedDelta", {
        "skip_seeds": json.dumps(["some_seed"]),
        "add_rules": "[]", "remove_rules": "[]",
        "add_concepts": "[]", "remove_concepts": "[]",
        "set_node_attrs": "[]",
    })
    _edge(agent, axis, "tested_by", experiment)
    _edge(agent, experiment, "has_delta", delta)
    agent.tick()
    request = list(agent.s.nodes("ImagineRequest"))[0]
    assert scan_and_imagine(agent) == [request]
    assert agent.s.node(request)["attrs"]["status"] == "needs_external_grounding"
    assert agent.s.node(experiment)["attrs"]["status"] == "counterfactual_blocked"
