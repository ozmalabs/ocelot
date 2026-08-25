from __future__ import annotations

import json
from pathlib import Path

import pytest

from domains.embodied_motor_hint_priors import seeded_motor_plan_hints
from domains.embodied_motor_shapes import motor_program_shape_signature
from scripts.harvest_humanoid_subprograms import harvest_libraries
from scripts.jabberwock_humanoid_walk import (
    _restore_motor_library,
    developmental_curriculum_contract,
)
from substrate.world_adapter import WorldAdapter


def _library(programs):
    return {
        "version": 4,
        "developmental_curriculum_contract": developmental_curriculum_contract(),
        "body_shapes": [{
            "attrs": {"name": "shape:a", "signature": [["body"]]},
            "programs": programs,
            "motor_transitions": [],
            "coordination_challenges": [],
            "residual_regimes": [],
        }],
    }


def _program(ordinal, tokens, *, progress=0.0):
    return {
        "attrs": {
            "ordinal": float(ordinal),
            "motor_task_context": "locomotion",
            "motor_task_phase": "preparation",
            "member_count": float(len(tokens)),
            "memory_eligible": 1.0,
            "receipt_learned": 1.0,
            "mean_directed_advance": progress,
        },
        "members": [
            {"token": token, "ordinal": float(index), "support_phase": 0.0}
            for index, token in enumerate(tokens)
        ],
    }


def _install_episode(agent, attrs=None):
    episode = agent.s.add_node("HumanoidEpisode", attrs or {})
    agent.inner.add_edge(agent.agent, "has_humanoid_episode", episode)
    return episode


def test_harvester_copies_structure_and_leaves_identity_to_shape_decode():
    base = _library([_program(4, ("a", "b"), progress=0.1)])
    source = _library([
        _program(99, ("a", "b"), progress=99.0),
        _program(4, ("b", "c"), progress=-5.0),
    ])
    merged, report = harvest_libraries(base, (("source.json", source),))
    programs = merged["body_shapes"][0]["programs"]
    assert len(programs) == 3
    assert report["imported_program_count"] == 2
    assert report["host_deduplication"] is False
    assert report["identity_owner"] == "graph_shape_decode"
    imported = programs[1]["attrs"]
    assert imported["ordinal"] == 5.0
    assert imported["source_program_ordinal"] == 99.0
    assert imported["harvested_subprogram"] == 1.0
    assert imported["mean_directed_advance"] == 99.0


def test_graph_shape_decode_collapses_harvested_program_identity():
    try:
        agent = WorldAdapter(seeds=("humanoid_adaptation",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    library = _library([
        _program(0, ("a", "b"), progress=0.1),
        _program(1, ("a", "b"), progress=99.0),
    ])
    _install_episode(agent, {"body_shape_initialized": 1.0})
    _restore_motor_library(agent, library)
    agent.tick()
    shape = agent.inner.neighbours(
        agent.agent, "has_humanoid_body_shape_library"
    )[0]
    assert len(agent.inner.neighbours(
        shape, "stores_humanoid_motor_program"
    )) == 1
    duplicates = agent.inner.neighbours(
        shape, "stores_duplicate_humanoid_motor_program"
    )
    assert len(duplicates) == 1
    assert len(agent.inner.neighbours(
        duplicates[0], "is_shape_duplicate_of_humanoid_program"
    )) == 1


def test_transition_chains_become_output_null_plan_hints():
    base = _library([])
    source = _library([
        _program(3, ("a", "b")),
        _program(4, ("c", "d")),
    ])
    source["body_shapes"][0]["motor_transitions"] = [{"attrs": {
        "ordinal": 0.0,
        "motor_task_context": "locomotion",
        "from_program_ordinal": 3.0,
        "next_program_ordinal": 4.0,
        "from_task_phase": "stance",
        "next_task_phase": "swing",
    }}]
    merged, report = harvest_libraries(base, (("source.json", source),))
    harvested = [
        row for row in merged["plan_hints"]
        if row["attrs"]["provenance"] == "source.json"
    ]
    assert report["imported_plan_hint_count"] == 1
    assert harvested[0]["attrs"]["output_authority"] == 0.0
    assert len(harvested[0]["stages"]) == 2
    assert all(
        stage["attrs"]["output_authority"] == 0.0
        for stage in harvested[0]["stages"]
    )
    assert harvested[0]["stages"][0]["attrs"]["signature"] == (
        motor_program_shape_signature(
            source["body_shapes"][0]["programs"][0]["attrs"],
            source["body_shapes"][0]["programs"][0]["members"],
        )
    )


def test_seeded_priors_are_constraints_not_commands():
    hints = seeded_motor_plan_hints()
    names = {row["attrs"]["name"] for row in hints}
    assert "prior:maneuver:forward_roll" in names
    assert "prior:maneuver:dynamic_high_alpha_cobra" in names
    assert all(row["attrs"]["output_authority"] == 0.0 for row in hints)
    assert all(
        stage["attrs"]["output_authority"] == 0.0
        for row in hints
        for stage in row["stages"]
    )
    encoded = json.dumps(hints)
    assert "torque" not in encoded
    assert "selected_token" not in encoded


def test_graph_plan_hint_recruits_search_index_without_releasing_action():
    try:
        agent = WorldAdapter(seeds=("humanoid_adaptation",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    integration_sets = agent.inner.neighbours(
        agent.agent, "has_embodied_integration_task_set"
    )
    assert integration_sets
    program_row = _program(0, ("a", "b"))
    signature = motor_program_shape_signature(
        program_row["attrs"], program_row["members"]
    )
    library = {
        "version": 5,
        "developmental_curriculum_contract": developmental_curriculum_contract(),
        "body_shapes": [],
        "plan_hints": [{
            "attrs": {
                "name": "hint:test:locomotion",
                "signature": (("motor_task", "locomotion"),),
                "output_authority": 0.0,
            },
            "stages": [{"attrs": {
                "name": "hint:test:locomotion:stage:0",
                "signature": (("concept", "abstract_propulsion"),),
                "routing_signature": (
                    ("motor_task_context", "locomotion"),
                    ("motor_task_phase", "preparation"),
                ),
                "output_authority": 0.0,
                "ordinal": 0.0,
            }}],
        }],
    }
    episode = _install_episode(agent, {
        "motor_plan_query_signature": (("motor_task", "locomotion"),),
        "motor_plan_hint_count": 0.0,
        "motor_plan_hint_escalation_count": 0.0,
        "motor_plan_basin_seed_count": 0.0,
        "state_seq": 1.0,
        "action_ready": 0.0,
    })
    restored = _restore_motor_library(agent, library)
    assert restored["plan_hint_count"] == 1
    program = agent.s.add_node("HumanoidMotorProgram", {
        "name": "program:test:grounded",
        "signature": signature,
        "motor_task_context": "locomotion",
        "motor_task_phase": "preparation",
        "status": "grounded",
    })
    agent.inner.add_edge(episode, "has_humanoid_motor_program", program)
    work_bound = len(agent.inner.neighbours(
        agent.agent, "has_embodied_motor_plan_hint_library"
    )) + len(agent.inner.neighbours(
        agent.agent, "has_embodied_motor_routing_shape"
    )) + len(agent.inner.neighbours(
        agent.agent, "has_embodied_motor_consequence_routing_shape"
    ))
    for _ in range(work_bound):
        agent.tick()
        if program in agent.inner.neighbours(
            episode, "has_humanoid_motor_program_search_index"
        ):
            break
    considered = agent.inner.neighbours(
        episode, "considers_humanoid_motor_plan_hint"
    )
    assert "hint:test:locomotion" in {
        agent.s.node(hint)["attrs"]["name"] for hint in considered
    }
    assert program in agent.inner.neighbours(
        episode, "has_humanoid_motor_program_search_index"
    )
    assert program in agent.inner.neighbours(
        episode, "has_humanoid_motor_program_basin_seed"
    )
    assert agent.s.node(episode)["attrs"][
        "motor_plan_hint_escalation_count"
    ] == 1.0
    assert agent.s.node(episode)["attrs"]["action_ready"] == 0.0


def test_graph_recruits_plan_hints_for_the_active_task_context():
    try:
        agent = WorldAdapter(seeds=("humanoid_adaptation",))
    except RuntimeError as exc:
        pytest.skip(f"native substrate unavailable: {exc}")
    library = {
        "version": 5,
        "developmental_curriculum_contract": developmental_curriculum_contract(),
        "body_shapes": [],
        "plan_hints": [
            {
                "attrs": {
                    "name": f"hint:test:{context}",
                    "signature": (("motor_task", context),),
                    "output_authority": 0.0,
                },
                "stages": [],
            }
            for context in ("locomotion", "self_takeoff")
        ],
    }
    locomotion_signature = (("motor_task", "locomotion"),)
    takeoff_signature = (("motor_task", "self_takeoff"),)
    episode = _install_episode(agent, {
        "motor_plan_query_signature": locomotion_signature,
        "motor_plan_active_query_context": "locomotion",
        "motor_plan_locomotion_query_signature": locomotion_signature,
        "motor_plan_self_takeoff_query_signature": takeoff_signature,
        "self_takeoff_drive_active": 0.0,
        "motor_plan_hint_count": 0.0,
        "motor_plan_hint_escalation_count": 0.0,
        "motor_plan_basin_seed_count": 0.0,
        "state_seq": 1.0,
        "action_ready": 0.0,
    })
    _restore_motor_library(agent, library)

    agent.tick()
    considered = agent.inner.neighbours(
        episode, "considers_humanoid_motor_plan_hint"
    )
    test_names = {
        agent.s.node(hint)["attrs"]["name"]
        for hint in considered
        if agent.s.node(hint)["attrs"]["name"].startswith("hint:test:")
    }
    assert test_names == {"hint:test:locomotion"}

    agent.inner.set_attr(episode, "self_takeoff_drive_active", 1.0)
    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["motor_plan_active_query_context"] == "self_takeoff"
    assert attrs["motor_plan_query_signature"] == takeoff_signature
    considered = agent.inner.neighbours(
        episode, "considers_humanoid_motor_plan_hint"
    )
    test_names = {
        agent.s.node(hint)["attrs"]["name"]
        for hint in considered
        if agent.s.node(hint)["attrs"]["name"].startswith("hint:test:")
    }
    assert test_names == {"hint:test:locomotion", "hint:test:self_takeoff"}
    assert attrs["action_ready"] == 0.0


def test_plan_hint_rules_have_no_actuator_release_effects():
    seed = json.loads((
        Path(__file__).resolve().parents[1] / "seeds" / "humanoid_adaptation.json"
    ).read_text(encoding="utf-8"))
    rules = {
        row["name"]: row
        for row in seed["rules"]
        if "motor_plan_hint" in row["name"]
    }
    assert set(rules) == {
        "ha_consider_shape_matched_motor_plan_hint",
        "ha_bind_motor_plan_hint_stage_search_basin",
        "ha_route_abstract_motor_plan_hint_stage_basin",
    }
    encoded = json.dumps(rules)
    indexed_routing = json.dumps({
        name: rule
        for name, rule in rules.items()
        if name != "ha_consider_shape_matched_motor_plan_hint"
    })
    assert "ShapeDecode" not in indexed_routing
    assert "realizes_embodied_motor_routing_shape" in indexed_routing
    assert "source_program_ordinal" in indexed_routing
    assert "SystemTwoEscalation" not in encoded
    for forbidden in (
        "selected_token",
        "enacts_humanoid_motor_program",
        '"action_ready"',
        "has_ready_humanoid_motor_program",
    ):
        assert forbidden not in encoded
