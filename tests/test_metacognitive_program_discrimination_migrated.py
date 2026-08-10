from __future__ import annotations

import json
from pathlib import Path

from scripts.gen_metacognitive_program_discrimination_seed import (
    manifest as discrimination_manifest,
)
from scripts.gen_threshold_classifier_seed import manifest as classifier_manifest
from tests.test_metacognitive_learning_migrated import _fixture, _run_reflection


ROOT = Path(__file__).resolve().parents[1]


def _assert_integer_native(value):
    if isinstance(value, float):
        raise AssertionError(f"floating-point cognition: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            _assert_integer_native(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _assert_integer_native(child)


def _load_faculty(agent):
    from substrate.seed_loader import manifest_for

    # The fixture already loaded metacognitive_learning. These are the two
    # remaining members of the declared dependency closure.
    for seed_id in (
        "threshold_classifier",
        "metacognitive_program_discrimination",
    ):
        agent.inner.load_seed_manifest(manifest_for(seed_id), agent.agent)


def test_learned_classifier_and_execution_seed_regenerate_integer_only():
    expected_classifier = json.loads((
        ROOT / "seeds" / "threshold_classifier.json"
    ).read_text(encoding="utf-8"))
    expected_discrimination = json.loads((
        ROOT / "seeds" / "metacognitive_program_discrimination.json"
    ).read_text(encoding="utf-8"))
    actual_classifier = classifier_manifest()
    actual_discrimination = discrimination_manifest()
    _assert_integer_native(actual_classifier)
    _assert_integer_native(actual_discrimination)
    assert actual_classifier == expected_classifier
    assert actual_discrimination == expected_discrimination


def test_persisted_program_is_executable_and_keeps_synthesis_provenance():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("threshold_classifier",))
    programs = agent.inner.neighbours(
        agent.agent, "holds_threshold_classifier"
    )
    assert len(programs) == 1
    attrs = agent.s.node(programs[0])["attrs"]
    assert attrs["learned"] == 1
    assert attrs["held_out_pass_count"] == attrs["held_out_count"] == 5
    assert attrs["tested_candidates"] > 0
    roots = agent.inner.neighbours(programs[0], "ir_subgraph")
    assert len(roots) == 1
    term = {
        "type": "ProgEval",
        "prog": {"type": "Var", "name": "program"},
        "env": {"type": "Var", "name": "inputs"},
        "oracles": None,
        "fuel": 10000,
        "field": "result",
    }
    assert agent.inner.evaluate(term, {
        "program": roots[0],
        "inputs": {
            "processed": 21, "progress": 2,
            "threshold": 10, "micros": 9,
        },
    }) == 9
    assert agent.inner.evaluate(term, {
        "program": roots[0],
        "inputs": {
            "processed": 20, "progress": 2,
            "threshold": 10, "micros": 9,
        },
    }) == 0


def test_graph_sweeps_classifier_and_redirects_to_unique_first_crossing():
    agent, _, plan, current_step, current_instance, alternatives = _fixture([
        {"yield": 3, "contexts": 1, "failures": 2, "cost": 4},
        {"yield": 2, "contexts": 3, "failures": 1, "cost": 5},
    ])
    _load_faculty(agent)

    _run_reflection(agent, cycles=8)

    residual = agent.inner.neighbours(
        current_step, "has_learning_plan_residual"
    )[0]
    request = agent.inner.neighbours(
        residual, "has_learning_policy_discrimination_request"
    )[0]
    request_attrs = agent.s.node(request)["attrs"]
    assert request_attrs["status"] == "resolved"
    # No configured ratio: the graph started at the identity boundary and
    # discovered that the first unique crossing was two.
    assert request_attrs["classifier_threshold"] == 2
    assert request_attrs["classifier_sweep_count"] == 2
    results = agent.inner.neighbours(request, "has_discrimination_result")
    assert len(results) == 1
    assert agent.s.node(results[0])["attrs"]["status"] == "resolved"

    revisions = agent.inner.neighbours(plan, "has_learning_plan_revision")
    assert len(revisions) == 1
    assert agent.inner.neighbours(
        revisions[0], "redirects_to_learning_plan_step"
    ) == [alternatives[0][0]]
    assert agent.inner.neighbours(
        revisions[0], "decided_by_discrimination_result"
    ) == results
    assert agent.s.node(current_step)["attrs"]["status"] == "meta_suspended"
    assert agent.s.node(current_instance)["attrs"]["status"] == "meta_suspended"


def test_held_program_classifies_live_learning_effort_and_clears_on_catchup():
    from domains import faculty_autogenesis
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("metacognitive_program_discrimination",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 4,
    })
    plan = agent.s.add_node("LearningPlan", {})
    step = agent.s.add_node("LearningPlanStep", {})
    instance = agent.s.add_node("Node", {
        "attempt_count": 5,
        "success_count": 1,
        "classifier_effort_excess": 0,
    })
    _edge = agent.inner.add_edge_unchecked
    _edge(agent.agent, "has_embodied_development_episode", episode, {})
    _edge(episode, "has_self_directed_learning_plan", plan, {})
    _edge(plan, "has_selected_learning_plan_step", step, {})
    _edge(step, "plans_learning_capability", instance, {})

    agent.tick()
    faculty_autogenesis.pump(agent)

    assert agent.s.node(instance)["attrs"]["classifier_effort_excess"] == 1
    assessments = agent.inner.neighbours(
        step, "has_learning_classifier_assessment"
    )
    assert len(assessments) == 1
    assert agent.s.node(assessments[0])["attrs"] == {
        "status": "excess",
        "kind": "effort_exceeds_causal_yield_window",
        "processed_units": 5,
        "progress_units": 1,
        "threshold_units": 4,
        "output_authority": 0,
        "integer_native": 1,
    }
    assert len(agent.inner.neighbours(
        assessments[0], "executed_classifier"
    )) == 1

    agent.inner.set_attr(instance, "success_count", 2)
    agent.tick()
    assert agent.s.node(instance)["attrs"]["classifier_effort_excess"] == 0
    statuses = {
        agent.s.node(node)["attrs"]["status"]
        for node in agent.inner.neighbours(
            step, "has_learning_classifier_assessment"
        )
    }
    assert statuses == {"excess", "recovered"}


def test_equal_first_crossing_is_retained_not_broken_by_order():
    agent, _, plan, current_step, _, _ = _fixture([
        {"yield": 3, "contexts": 1, "failures": 2, "cost": 4},
        {"yield": 2, "contexts": 3, "failures": 1, "cost": 4},
    ])
    _load_faculty(agent)

    _run_reflection(agent, cycles=8)

    residual = agent.inner.neighbours(
        current_step, "has_learning_plan_residual"
    )[0]
    request = agent.inner.neighbours(
        residual, "has_learning_policy_discrimination_request"
    )[0]
    assert agent.s.node(request)["attrs"]["status"] == "needs_more_evidence"
    results = agent.inner.neighbours(request, "has_discrimination_result")
    assert len(results) == 1
    attrs = agent.s.node(results[0])["attrs"]
    assert attrs["status"] == "underdetermined"
    assert attrs["candidate_count"] == 2
    assert agent.inner.neighbours(plan, "has_learning_plan_revision") == []


def test_embodied_development_boots_with_learned_discriminator_in_graph():
    from domains import faculty_autogenesis
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    assert agent.inner.neighbours(agent.agent, "holds_faculty") == []
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 4,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "has_embodied_development_episode", episode
    )
    agent.tick()
    faculty_autogenesis.pump(agent)
    held = agent.inner.neighbours(agent.agent, "holds_faculty")
    assert len(held) == 1
    assert agent.s.node(held[0])["attrs"]["self_authored"] == 1
    names = {rule["name"] for rule in agent.inner.export_rules()}
    assert "mpd_sweep_boundary_until_a_policy_first_crosses" in names
    assert "mpd_redirect_plan_at_unique_learned_classifier_crossing" in names
