"""General-cognition gates for Pareto counterexample-based goal revision."""
from __future__ import annotations

from domains.cognitive_pareto import (
    evaluate_pareto_profile,
    goal_revision_requests,
    install_pareto_profile,
    pareto_frontier,
    publish_pareto_candidate,
)
from scripts import gen_cognitive_pareto_seed, gen_embodied_pareto_profile_seed
from substrate.world_adapter import WorldAdapter


def _profile(agent, goal):
    owner = agent.s.add_node("Deliberation", {})
    return install_pareto_profile(agent, owner, (
        {"name": "progress", "ordinal": 0, "direction": "maximize"},
        {"name": "cost", "ordinal": 1, "direction": "minimize"},
    ), context="is_my_goal_wrong", goal=goal)


def test_dominating_alternative_falsifies_incumbent_without_replacing_goal():
    agent = WorldAdapter(seeds=("cognitive_pareto",))
    goal = agent.s.add_node("Goal", {"status": "active"})
    profile = _profile(agent, goal)
    incumbent = publish_pareto_candidate(
        agent, profile, {"progress": 4, "cost": 8},
        identity="current_goal", incumbent=True,
    )
    counterexample = publish_pareto_candidate(
        agent, profile, {"progress": 5, "cost": 7},
        identity="better_goal",
    )
    incomparable = publish_pareto_candidate(
        agent, profile, {"progress": 3, "cost": 2},
        identity="cheaper_but_slower",
    )

    report = evaluate_pareto_profile(agent, profile)

    assert report["system_two_escalations"] == 1
    assert agent.inner.neighbours(
        incumbent, "is_dominated_by_pareto_candidate") == [counterexample]
    assert set(pareto_frontier(agent, profile)) == {counterexample, incomparable}
    requests = goal_revision_requests(agent, profile)
    assert len(requests) == 1
    request = requests[0]
    assert agent.inner.neighbours(request, "about_goal") == [goal]
    assert agent.inner.neighbours(
        request, "proposed_by_pareto_candidate") == [counterexample]
    assert agent.s.node(goal)["attrs"]["status"] == "active"
    assert agent.s.node(goal)["attrs"]["pareto_status"] == "dominated"


def test_incomparable_alternative_does_not_claim_the_goal_is_wrong():
    agent = WorldAdapter(seeds=("cognitive_pareto",))
    goal = agent.s.add_node("Goal", {"status": "active"})
    profile = _profile(agent, goal)
    publish_pareto_candidate(
        agent, profile, {"progress": 4, "cost": 8},
        identity="current_goal", incumbent=True,
    )
    publish_pareto_candidate(
        agent, profile, {"progress": 3, "cost": 2},
        identity="tradeoff",
    )

    evaluate_pareto_profile(agent, profile)

    assert goal_revision_requests(agent, profile) == ()
    assert agent.s.node(goal)["attrs"].get("pareto_status") is None


def test_dominance_can_join_dimensions_by_shared_graph_identity():
    agent = WorldAdapter(seeds=("cognitive_pareto",))
    profile = agent.s.add_node("ParetoProfile", {
        "epoch": 0,
        "dimension_count": 2,
        "candidate_count": 2,
    })
    incumbent = agent.s.add_node("ParetoCandidate", {"dominated": 0})
    alternative = agent.s.add_node("ParetoCandidate", {"dominated": 0})
    agent.inner.add_edge_unchecked(
        profile, "has_pareto_candidate", incumbent, {})
    agent.inner.add_edge_unchecked(
        profile, "has_pareto_candidate", alternative, {})

    dimensions = [agent.s.add_node("Goal", {}) for _ in range(2)]
    for owner, coordinates in ((incumbent, (4, -8)), (alternative, (5, -7))):
        for dimension, signed_value in zip(dimensions, coordinates):
            value = agent.s.add_node("ParetoValue", {
                "verified": 1,
                "signed_value": signed_value,
            })
            agent.inner.add_edge_unchecked(
                owner, "has_pareto_value", value, {})
            agent.inner.add_edge_unchecked(
                value, "measures_goal", dimension, {})

    evaluate_pareto_profile(agent, {"profile": profile})

    assert agent.inner.neighbours(
        incumbent, "is_dominated_by_pareto_candidate") == [alternative]


def test_dominance_rejects_float_coordinates_at_integer_cognition_boundary():
    agent = WorldAdapter(seeds=("cognitive_pareto",))
    profile = _profile(agent, agent.s.add_node("Goal", {"status": "active"}))
    incumbent = publish_pareto_candidate(
        agent, profile, {"progress": 4, "cost": 8},
        identity="current_goal", incumbent=True,
    )
    alternative = publish_pareto_candidate(
        agent, profile, {"progress": 5, "cost": 7},
        identity="malformed_float",
    )
    malformed_value = agent.inner.neighbours(
        alternative, "has_pareto_value")[0]
    agent.inner.set_attr(malformed_value, "signed_value", 5.5)

    evaluate_pareto_profile(agent, profile)

    assert agent.inner.neighbours(
        incumbent, "is_dominated_by_pareto_candidate") == []


def test_frozen_profile_is_history_not_a_live_system_two_search_space():
    for frozen_attrs in (
        {"pareto_suspended": 1},
        {"status": "continued"},
        {"status": "replan_required"},
        {"status": "selected"},
    ):
        agent = WorldAdapter(seeds=("cognitive_pareto",))
        goal = agent.s.add_node("Goal", {"status": "active"})
        profile = _profile(agent, goal)
        incumbent = publish_pareto_candidate(
            agent, profile, {"progress": 4, "cost": 8},
            identity="historical_incumbent", incumbent=True,
        )
        publish_pareto_candidate(
            agent, profile, {"progress": 5, "cost": 7},
            identity="historical_alternative",
        )
        for key, value in frozen_attrs.items():
            agent.inner.set_attr(profile["profile"], key, value)

        evaluate_pareto_profile(agent, profile)

        assert not agent.inner.neighbours(
            incumbent, "is_dominated_by_pareto_candidate")
        assert not goal_revision_requests(agent, profile)


def test_current_pareto_rule_is_refreshable_on_checkpoint_resume():
    from scripts import jabberwock_daemon as daemon

    assert "cognitive_pareto" in daemon._REFRESHABLE_SEEDS


def test_general_faculty_is_integer_native_and_embodied_is_only_a_bridge():
    agent = WorldAdapter(seeds=("cognitive_pareto",))
    goal = agent.s.add_node("Goal", {"status": "active"})
    profile = _profile(agent, goal)
    publish_pareto_candidate(
        agent, profile, {"progress": 4, "cost": 8},
        identity="current_goal", incumbent=True,
    )
    for node_type in ("ParetoProfile", "ParetoDimension", "ParetoCandidate", "ParetoValue"):
        for node in agent.s.nodes(node_type):
            for value in agent.s.node(node)["attrs"].values():
                assert not isinstance(value, float)

    general = gen_cognitive_pareto_seed.manifest()
    compatibility = gen_embodied_pareto_profile_seed.manifest()
    assert general["area"] == "cognitive_pareto"
    assert {rule["name"] for rule in general["rules"]} == {
        "cp_recognize_relational_dominance",
        # Recognition caches a dominance counterexample permanently and stops
        # re-scanning the candidate. That is sound for an immutable frontier
        # and wrong for a learning one, whose candidates have their Pareto
        # values rewritten by every receipt: stale counterexamples accumulated
        # until 43 of 43 live motor candidates were dominated, the frontier was
        # empty, and trial production stopped dead. Recognition without
        # retraction is only half a relation, so the pair is pinned together.
        "cp_retract_stale_relational_dominance",
        "cp_settle_dominated_flag_from_surviving_counterexamples",
        "cp_falsify_dominated_incumbent_goal",
    }
    assert compatibility["depends_on"] == ["cognitive_pareto"]
    assert compatibility["area"] == "compatibility"
    routed = compatibility["rules"][0]
    assert routed["name"] == "epp_route_legacy_relations_through_cognitive_pareto"
    assert routed["area"] == "cognitive_pareto"
