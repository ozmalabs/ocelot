from __future__ import annotations

import json
from pathlib import Path

from scripts.gen_metacognitive_learning_seed import manifest


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "metacognitive_learning.json"


def _assert_integer_native(value):
    if isinstance(value, float):
        raise AssertionError(f"floating-point cognition value: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_integer_native(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _assert_integer_native(nested)


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _fixture(alternatives):
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("metacognitive_learning",))
    episode = agent.s.add_node("Node", {})
    plan = agent.s.add_node("LearningPlan", {"replan_count": 0})
    current_instance = agent.s.add_node("Node", {
        "status": "active", "attempt_count": 8,
        "success_count": 0, "failure_count": 8,
    })
    current_step = agent.s.add_node("LearningPlanStep", {
        "goal": "sterile_probe", "status": "active",
        "evidence_budget_units": 8, "evidence_spent_units": 8,
        "budget_success_baseline": 0, "context_evidence_units": 0,
        "successful_evidence_units": 0, "failed_evidence_units": 8,
    })
    _edge(agent, episode, "has_self_directed_learning_plan", plan)
    _edge(agent, plan, "has_learning_plan_step", current_step)
    _edge(agent, current_step, "plans_learning_capability", current_instance)
    _edge(agent, plan, "has_selected_learning_plan_step", current_step)
    _edge(agent, episode, "has_active_embodied_developmental_capability", current_instance)

    created = []
    for ordinal, row in enumerate(alternatives):
        instance = agent.s.add_node("Node", {
            "status": "available", "attempt_count": row["cost"],
            "success_count": row["yield"], "failure_count": row["failures"],
        })
        step = agent.s.add_node("LearningPlanStep", {
            "goal": f"alternative_{ordinal}", "status": "ready",
            "evidence_budget_units": 8,
            "evidence_spent_units": row["cost"],
            "budget_success_baseline": 0,
            "context_evidence_units": row["contexts"],
            "successful_evidence_units": row["yield"],
            "failed_evidence_units": row["failures"],
        })
        _edge(agent, plan, "has_learning_plan_step", step)
        _edge(agent, step, "plans_learning_capability", instance)
        created.append((step, instance))
    return agent, episode, plan, current_step, current_instance, created


def _run_reflection(agent, cycles=5):
    for _ in range(cycles):
        agent.tick()
        agent.dual_process_tick()


def test_seed_is_integer_native_and_domain_neutral():
    payload = manifest()
    _assert_integer_native(payload)
    encoded = json.dumps(payload)
    assert "has_embodied_developmental_context" not in encoded
    assert "reassess_after_embodied_developmental_capability" not in encoded
    assert "reassess_after_learning_capability" in encoded
    assert payload["depends_on"] == ["cognitive_pareto", "dual_process_core"]
    assert json.loads(SEED.read_text(encoding="utf-8")) == payload


def test_unique_pareto_counterexample_revises_plan_without_scalar_score():
    agent, _, plan, step, instance, alternatives = _fixture([{
        "yield": 3, "contexts": 2, "failures": 1, "cost": 4,
    }])

    _run_reflection(agent)

    revisions = agent.inner.neighbours(plan, "has_learning_plan_revision")
    assert len(revisions) == 1
    revision = revisions[0]
    assert agent.s.node(revision)["attrs"]["status"] == "enacted"
    assert agent.inner.neighbours(
        revision, "redirects_to_learning_plan_step"
    ) == [alternatives[0][0]]
    assert agent.s.node(step)["attrs"]["status"] == "meta_suspended"
    assert agent.s.node(instance)["attrs"]["status"] == "meta_suspended"
    assert agent.inner.neighbours(
        instance, "reassess_after_learning_capability"
    ) == [alternatives[0][1]]
    profiles = agent.inner.neighbours(plan, "has_learning_policy_pareto_profile")
    assert profiles
    assert agent.s.node(profiles[0])["attrs"]["scalarized"] == 0


def test_incomparable_counterexamples_request_discrimination():
    agent, _, plan, step, _, _ = _fixture([
        {"yield": 3, "contexts": 1, "failures": 2, "cost": 4},
        {"yield": 2, "contexts": 3, "failures": 1, "cost": 4},
    ])

    _run_reflection(agent)

    residual = agent.inner.neighbours(step, "has_learning_plan_residual")[0]
    requests = agent.inner.neighbours(
        residual, "has_learning_policy_discrimination_request"
    )
    assert len(requests) == 1
    assert agent.s.node(requests[0])["attrs"]["candidate_count"] == 2
    assert agent.inner.neighbours(plan, "has_learning_plan_revision") == []
    assert agent.s.node(step)["attrs"]["status"] == "active"


def test_contextual_counterexample_hold_excludes_only_held_alternative():
    agent, _, plan, step, _, alternatives = _fixture([{
        "yield": 3, "contexts": 2, "failures": 1, "cost": 4,
    }])
    hold = agent.s.add_node("LearningPolicyCounterexampleHold", {
        "status": "active", "order_n": 2,
        "output_authority": 0, "integer_native": 1,
    })
    _edge(
        agent, alternatives[0][0],
        "has_learning_policy_counterexample_hold", hold,
    )

    _run_reflection(agent)
    assert agent.inner.neighbours(step, "has_learning_plan_residual") == []
    assert agent.inner.neighbours(plan, "has_learning_plan_revision") == []

    agent.inner.set_attr(hold, "status", "released")
    _run_reflection(agent)
    assert len(agent.inner.neighbours(plan, "has_learning_plan_revision")) == 1


def test_revision_reopens_only_after_new_target_success():
    agent, _, _, step, instance, alternatives = _fixture([{
        "yield": 3, "contexts": 2, "failures": 1, "cost": 4,
    }])
    _run_reflection(agent)
    target = alternatives[0][1]
    agent.inner.set_attr(target, "status", "mastered")

    agent.tick()
    assert agent.s.node(step)["attrs"]["status"] == "meta_suspended"
    assert agent.s.node(instance)["attrs"]["status"] == "meta_suspended"

    agent.inner.set_attr(target, "success_count", 4)
    agent.tick()
    assert agent.s.node(step)["attrs"]["status"] == "ready"
    assert agent.s.node(instance)["attrs"]["status"] == "available"


def test_failed_revision_lazily_materializes_next_meta_order():
    agent, _, plan, _, _, alternatives = _fixture([{
        "yield": 0, "contexts": 0, "failures": 8, "cost": 8,
    }])
    agent.tick()
    policies = agent.inner.neighbours(
        plan, "has_active_metacognitive_learning_policy"
    )
    assert len(policies) == 1
    policy = policies[0]
    revision = agent.s.add_node("LearningPlanRevision", {
        "status": "enacted", "order_n": 1,
    })
    _edge(agent, plan, "has_learning_plan_revision", revision)
    _edge(agent, revision, "redirects_to_learning_plan_step", alternatives[0][0])

    agent.tick()

    higher = agent.inner.neighbours(
        policy, "has_higher_order_metacognitive_policy"
    )
    assert len(higher) == 1
    assert agent.s.node(higher[0])["attrs"]["order_n"] == 2
    assert agent.inner.neighbours(
        plan, "has_active_metacognitive_learning_policy"
    ) == higher


def test_output_null_revision_memory_survives_motor_library_round_trip():
    from scripts.jabberwock_humanoid_walk import (
        MOTOR_LIBRARY_VERSION,
        _motor_library_snapshot,
        _restore_motor_library,
    )
    from substrate.world_adapter import WorldAdapter

    source = WorldAdapter(seeds=("embodied_development",))
    target = WorldAdapter(seeds=("embodied_development",))
    memory = source.s.add_node("MetacognitiveLearningRevisionMemory", {
        "signature": (("link_count", 8), ("terminal_count", 4)),
        "suspended_goal": "orientation_change",
        "redirect_goal": "supported_posture_control",
        "suspended_capability": "side_lying_transition",
        "redirect_capability": "prone_support",
        "order_n": 2,
        "status": "retained",
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(
        source, source.agent,
        "has_metacognitive_learning_revision_memory", memory,
    )
    counterexample = source.s.add_node(
        "MetacognitiveLearningCounterexampleMemory", {
            "signature": (("link_count", 8), ("terminal_count", 4)),
            "source_capability": "supine_prone_rolling",
            "source_goal": "rolling",
            "failed_redirect_capability": "prone_reach_and_pivot",
            "failed_redirect_goal": "supported_translation",
            "order_n": 2,
            "mastery_context_member_count": 1,
            "status": "retained",
            "output_authority": 0,
            "integer_native": 1,
        },
    )
    member = source.s.add_node(
        "MetacognitiveCounterexampleContextMember", {
            "capability_name": "prone_forelimb_support",
            "goal": "support_discovery",
            "status": "mastered",
            "output_authority": 0,
            "integer_native": 1,
        },
    )
    _edge(
        source, source.agent,
        "has_metacognitive_learning_counterexample_memory", counterexample,
    )
    _edge(
        source, counterexample,
        "has_metacognitive_counterexample_context_member", member,
    )

    snapshot = json.loads(json.dumps(_motor_library_snapshot(source)))
    assert snapshot["version"] == MOTOR_LIBRARY_VERSION
    assert len(snapshot["metacognitive_learning_revisions"]) == 1
    assert len(snapshot["metacognitive_learning_counterexamples"]) == 1
    restored = _restore_motor_library(target, snapshot)
    assert restored["metacognitive_revision_count"] == 1
    memories = target.inner.neighbours(
        target.agent, "has_metacognitive_learning_revision_memory"
    )
    attrs = target.s.node(memories[0])["attrs"]
    assert attrs["order_n"] == 2
    assert attrs["output_authority"] == 0
    assert attrs["integer_native"] == 1
    assert restored["metacognitive_counterexample_count"] == 1
    assert restored["metacognitive_counterexample_context_count"] == 1
    restored_counterexamples = target.inner.neighbours(
        target.agent, "has_metacognitive_learning_counterexample_memory"
    )
    assert len(restored_counterexamples) == 1
    restored_members = target.inner.neighbours(
        restored_counterexamples[0],
        "has_metacognitive_counterexample_context_member",
    )
    assert len(restored_members) == 1
    assert target.s.node(restored_members[0])["attrs"][
        "capability_name"
    ] == "prone_forelimb_support"


def test_exact_body_revision_memory_warm_starts_plan_allocation_not_output():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    signature = (("link_count", 8), ("terminal_count", 4))
    memory = agent.s.add_node("MetacognitiveLearningRevisionMemory", {
        "signature": signature,
        "suspended_goal": "rolling",
        "redirect_goal": "support_discovery",
        "suspended_capability": "supine_prone_rolling",
        "redirect_capability": "prone_forelimb_support",
        "order_n": 2,
        "status": "retained",
        "output_authority": 0,
        "integer_native": 1,
    })
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "body_capability_signature": signature,
        "development_evidence_window": 4,
        "development_learning_active": 1,
        "latest_development_receipt_seq": 0,
        "integer_native": 1,
        "output_authority": 0,
    })
    _edge(
        agent, agent.agent,
        "has_metacognitive_learning_revision_memory", memory,
    )
    _edge(
        agent, agent.agent,
        "has_embodied_development_episode", episode,
    )

    agent.tick()

    instances = agent.inner.neighbours(
        episode, "has_embodied_developmental_capability"
    )
    rolling = [
        node for node in instances
        if agent.s.node(node)["attrs"].get("goal") == "rolling"
    ]
    assert len(rolling) == 1
    assert agent.s.node(rolling[0])["attrs"]["status"] == "meta_suspended"
    redirect = agent.inner.neighbours(
        rolling[0], "reassess_after_learning_capability"
    )
    assert len(redirect) == 1
    assert agent.s.node(redirect[0])["attrs"]["goal"] == "support_discovery"
    plans = agent.inner.neighbours(
        episode, "has_self_directed_learning_plan"
    )
    revisions = agent.inner.neighbours(
        plans[0], "has_learning_plan_revision"
    )
    assert len(revisions) == 1
    revision_attrs = agent.s.node(revisions[0])["attrs"]
    assert revision_attrs["status"] == "enacted"
    assert revision_attrs["redirect_success_baseline"] == 0
    policies = agent.inner.neighbours(
        plans[0], "has_active_metacognitive_learning_policy"
    )
    assert agent.s.node(policies[0])["attrs"]["order_n"] == 2
    assert agent.s.node(memory)["attrs"]["output_authority"] == 0


def test_same_goal_capabilities_consolidate_by_identity_without_recreation():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    signature = (("link_count", 8), ("terminal_count", 4))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "body_capability_signature": signature,
        "development_evidence_window": 4,
        "development_learning_active": 0,
        "latest_development_receipt_seq": 0,
        "integer_native": 1,
        "output_authority": 0,
    })
    motor_episode = agent.s.add_node("HumanoidEpisode", {
        "library_consolidation_requested": 0,
        "integer_native": 1,
    })
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    _edge(agent, agent.agent, "has_humanoid_episode", motor_episode)
    _edge(
        agent, motor_episode, "projects_embodied_development", episode
    )
    agent.tick()
    instances = agent.inner.neighbours(
        episode, "has_embodied_developmental_capability"
    )
    by_name = {
        agent.s.node(instance)["attrs"]["name"]: instance
        for instance in instances
    }
    prone = by_name["prone_forelimb_support"]
    quadruped = by_name["quadruped_support"]
    agent.inner.set_attr(prone, "status", "mastered")
    agent.inner.set_attr(prone, "attempt_count", 9)
    agent.inner.set_attr(quadruped, "status", "available")
    agent.inner.set_attr(quadruped, "attempt_count", 12)
    agent.inner.set_attr(quadruped, "success_count", 6)
    agent.inner.set_attr(quadruped, "failure_count", 6)
    memory = agent.s.add_node("EmbodiedDevelopmentalExperienceMemory", {
        "name": "developmental_experience:quadruped_support:test",
        "signature": signature,
        "capability_name": "quadruped_support",
        "goal": "support_discovery",
        "evidence_kind": "support_gain",
        "status": "available",
        "attempt_count": 6,
        "success_count": 3,
        "failure_count": 3,
        "retention_pending": 0,
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(
        agent, agent.agent,
        "has_embodied_developmental_experience_memory", memory,
    )
    agent.inner.set_attr(
        motor_episode, "library_consolidation_requested", 1
    )

    agent.tick()
    assert agent.tick() == 0

    memories = [
        node for node in agent.inner.neighbours(
            agent.agent, "has_embodied_developmental_experience_memory"
        )
        if agent.s.node(node)["attrs"].get("capability_name")
        == "quadruped_support"
        and agent.s.node(node)["attrs"].get("status") != "superseded"
    ]
    assert memories == [memory]
    attrs = agent.s.node(memory)["attrs"]
    assert attrs["attempt_count"] == 12
    assert attrs["success_count"] == 6


def test_failed_revision_hold_is_released_when_mastery_frontier_changes():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    signature = (("link_count", 8), ("terminal_count", 4))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "body_capability_signature": signature,
        "development_evidence_window": 4,
        "development_learning_active": 1,
        "latest_development_receipt_seq": 0,
        "integer_native": 1,
        "output_authority": 0,
    })
    _edge(
        agent, agent.agent,
        "has_embodied_development_episode", episode,
    )
    agent.tick()
    plan = agent.inner.neighbours(
        episode, "has_self_directed_learning_plan"
    )[0]
    selected = agent.inner.neighbours(
        plan, "has_selected_learning_plan_step"
    )[0]
    steps = agent.inner.neighbours(plan, "has_learning_plan_step")
    failed = next(step for step in steps if step != selected)
    memory = agent.s.add_node(
        "MetacognitiveLearningCounterexampleMemory", {
            "signature": signature,
            "source_capability": agent.s.node(selected)["attrs"]["name"],
            "source_goal": agent.s.node(selected)["attrs"]["goal"],
            "failed_redirect_capability": agent.s.node(failed)["attrs"]["name"],
            "failed_redirect_goal": agent.s.node(failed)["attrs"]["goal"],
            "order_n": 2,
            "mastery_context_member_count": 0,
            "status": "retained",
            "output_authority": 0,
            "integer_native": 1,
        },
    )
    _edge(
        agent, agent.agent,
        "has_metacognitive_learning_counterexample_memory", memory,
    )

    agent.tick()
    holds = agent.inner.neighbours(
        failed, "has_learning_policy_counterexample_hold"
    )
    assert len(holds) == 1
    assert agent.s.node(holds[0])["attrs"]["status"] == "active"

    capability = agent.inner.neighbours(
        selected, "plans_learning_capability"
    )[0]
    agent.inner.set_attr(capability, "status", "mastered")
    agent.tick()
    assert agent.s.node(holds[0])["attrs"]["status"] == "released"


def test_failed_revision_consolidates_relational_mastery_context():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    signature = (("link_count", 8), ("terminal_count", 4))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "body_capability_signature": signature,
        "development_evidence_window": 4,
        "development_learning_active": 1,
        "latest_development_receipt_seq": 0,
        "integer_native": 1,
        "output_authority": 0,
    })
    motor_episode = agent.s.add_node("HumanoidEpisode", {
        "library_consolidation_requested": 0,
        "integer_native": 1,
    })
    _edge(agent, agent.agent, "has_embodied_development_episode", episode)
    _edge(agent, agent.agent, "has_humanoid_episode", motor_episode)
    _edge(
        agent, motor_episode, "projects_embodied_development", episode
    )
    agent.tick()
    plan = agent.inner.neighbours(
        episode, "has_self_directed_learning_plan"
    )[0]
    steps = agent.inner.neighbours(plan, "has_learning_plan_step")
    source = agent.inner.neighbours(
        plan, "has_selected_learning_plan_step"
    )[0]
    failed = next(step for step in steps if step != source)
    mastered_step = next(
        step for step in steps if step not in (source, failed)
    )
    mastered_instance = agent.inner.neighbours(
        mastered_step, "plans_learning_capability"
    )[0]
    agent.inner.set_attr(mastered_instance, "status", "mastered")
    revision = agent.s.add_node("LearningPlanRevision", {
        "kind": "redirect_to_productive_learning_frontier",
        "status": "counterexample_observed",
        "order_n": 2,
        "output_authority": 0,
        "integer_native": 1,
    })
    _edge(agent, plan, "has_learning_plan_revision", revision)
    _edge(agent, revision, "revises_learning_plan_step", source)
    _edge(agent, revision, "redirects_to_learning_plan_step", failed)
    agent.inner.set_attr(
        motor_episode, "library_consolidation_requested", 1
    )

    agent.tick()

    memories = agent.inner.neighbours(
        agent.agent, "has_metacognitive_learning_counterexample_memory"
    )
    assert len(memories) == 1
    attrs = agent.s.node(memories[0])["attrs"]
    assert attrs["source_capability"] == agent.s.node(source)["attrs"]["name"]
    assert attrs["failed_redirect_capability"] == agent.s.node(failed)["attrs"]["name"]
    assert attrs["mastery_context_member_count"] == 1
    members = agent.inner.neighbours(
        memories[0], "has_metacognitive_counterexample_context_member"
    )
    assert len(members) == 1
    assert agent.s.node(members[0])["attrs"]["capability_name"] == (
        agent.s.node(mastered_step)["attrs"]["name"]
    )
