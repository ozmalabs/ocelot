"""Cross-domain gates for first-class, uncollapsed Pareto profiles."""
from __future__ import annotations

import pytest

from scripts import (
    gen_embodied_motor_priors_seed,
    gen_embodied_motor_program_seed,
    gen_embodied_pareto_profile_seed,
    gen_racing_cognition_seed,
)
from domains.embodied_pareto import (
    evaluate_pareto_profile,
    install_pareto_profile,
    pareto_frontier,
    publish_pareto_candidate,
)
from substrate.world_adapter import WorldAdapter


@pytest.mark.parametrize("context", ["humanoid_gait", "race_strategy", "flight_envelope"])
def test_same_relational_frontier_applies_across_motor_domains(context):
    try:
        agent = WorldAdapter(seeds=("embodied_pareto_profile",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    owner = agent.s.add_node("EmbodiedEpisode", {})
    profile = install_pareto_profile(agent, owner, (
        {"name": "task_effect", "ordinal": 0, "direction": "maximize"},
        {"name": "resource_cost", "ordinal": 1, "direction": "minimize"},
        {"name": "viability_cost", "ordinal": 2, "direction": "minimize"},
    ), context=context)
    dominated = publish_pareto_candidate(
        agent, profile,
        {"task_effect": 1.0, "resource_cost": 2.0, "viability_cost": 1.0},
        identity="dominated",
    )
    efficient = publish_pareto_candidate(
        agent, profile,
        {"task_effect": 2.0, "resource_cost": 1.0, "viability_cost": 1.0},
        identity="efficient",
    )
    conservative = publish_pareto_candidate(
        agent, profile,
        {"task_effect": 0.5, "resource_cost": 0.5, "viability_cost": 0.5},
        identity="conservative",
    )

    report = evaluate_pareto_profile(agent, profile)
    assert report["system_two_escalations"] == 1
    assert agent.inner.neighbours(
        dominated, "is_dominated_by_embodied_candidate"
    ) == [efficient]
    assert not agent.inner.neighbours(
        conservative, "is_dominated_by_embodied_candidate"
    )
    assert {
        agent.s.node(node)["attrs"]["identity"]
        for node in pareto_frontier(agent, profile)
    } == {"efficient", "conservative"}


def test_profile_rejects_missing_dimensions_instead_of_collapsing_them():
    agent = WorldAdapter(seeds=("embodied_pareto_profile",))
    owner = agent.s.add_node("EmbodiedEpisode", {})
    profile = install_pareto_profile(agent, owner, (
        {"name": "progress", "ordinal": 0, "direction": "maximize"},
        {"name": "energy", "ordinal": 1, "direction": "minimize"},
    ), context="incomplete_gate")
    with pytest.raises(ValueError, match="dimensions are incomplete"):
        publish_pareto_candidate(
            agent, profile, {"progress": 1.0}, identity="invalid"
        )


def test_pareto_profile_is_a_lightweight_first_class_cross_domain_seed():
    pareto = gen_embodied_pareto_profile_seed.manifest()
    assert pareto["depends_on"] == ["cognitive_pareto"]
    assert pareto["area"] == "compatibility"
    assert all(rule["area"] == "cognitive_pareto" for rule in pareto["rules"])

    assert "embodied_pareto_profile" in (
        gen_embodied_motor_priors_seed.manifest()["depends_on"]
    )
    assert "embodied_pareto_profile" in (
        gen_racing_cognition_seed.manifest()["depends_on"]
    )
    assert "embodied_pareto_profile" in (
        gen_embodied_motor_program_seed.manifest()["depends_on"]
    )
