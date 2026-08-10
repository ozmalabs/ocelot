"""Execution gates for the general order-N capability-collapse function."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "capability_collapse.json"
GENERATOR = ROOT / "scripts" / "gen_capability_collapse_seed.py"

for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _fresh():
    return WorldAdapter(seeds=("capability_collapse",))


def _outcome(agent, token="opaque_combined_outcome"):
    return agent.s.add_node("CapabilityOutcome", {
        "token": token,
        "outcome_kind": "task_invariant_basin",
    })


def _program(agent, order, residual, boundary, receipts=2):
    return agent.s.add_node("CapabilityProgram", {
        "order": order,
        "residual_quanta": residual,
        "capability_boundary_quanta": boundary,
        "baseline_capability_boundary_quanta": boundary,
        "required_practice_receipts": receipts,
        "required_practice_contexts": 1,
        "maximum_practice_failures": 0,
        "consolidation_required": 0,
        "compiled_execution_failure_count": 0,
    })


def _state(agent, root, epoch, *, limit_enabled=0, maximum_order=0):
    state = agent.s.add_node("CapabilityCollapseState", {
        "stage": "ready",
        "collapse_armed": 1,
        "request_epoch": epoch,
        "order_limit_enabled": limit_enabled,
        "maximum_order": maximum_order,
        "outcome_verified": 0,
    })
    _edge(agent, state, "has_root_capability_program", root)
    context = agent.s.add_node("CapabilityContext", {
        "context_epoch": epoch,
    })
    _edge(agent, state, "in_capability_context", context)
    return state


def _collapse(agent, root, epoch, **kwargs):
    state = _state(agent, root, epoch, **kwargs)
    assert agent.tick() > 0
    return state, agent.s.node(state)["attrs"]


def _published(agent, state):
    return agent.s.neighbours(state, "published_capability_outcome")


def _assert_no_float(value):
    if isinstance(value, float):
        raise AssertionError(f"floating-point cognition value: {value!r}")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_float(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_float(nested)


def test_seed_is_generated_integer_domain_neutral_graph_data():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    assert seed["id"] == "capability_collapse"
    assert seed["area"] == "general_cognition"
    assert seed["self_load_only"] is True
    assert seed["version"] == "2.0.0"
    assert len(seed["rules"]) == 43
    _assert_no_float(seed)

    serialized = json.dumps(seed).lower()
    assert "capabilityprogram" in serialized
    assert "continues_to_higher_order_capability_program" in serialized
    assert "compiles_capability_outcome" in serialized
    for domain_term in (
        "motor", "elbow", "wheel", "fovea", "doom", "language", "planner",
    ):
        assert domain_term not in serialized

    source = GENERATOR.read_text(encoding="utf-8")
    assert "float(" not in source
    assert "L(0.0)" not in source
    assert "L(1.0)" not in source


def test_generator_reproduces_committed_seed_exactly():
    before = SEED.read_bytes()
    subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert SEED.read_bytes() == before


def test_order_zero_settles_one_opaque_outcome_inside_boundary():
    agent = _fresh()
    outcome = _outcome(agent)
    program = _program(agent, 0, residual=3, boundary=3)
    _edge(agent, program, "settles_to_capability_outcome", outcome)

    state, attrs = _collapse(agent, program, 1)

    assert _published(agent, state) == [outcome]
    assert attrs["published_outcome_count"] == 1
    assert attrs["achieved_order"] == 0
    assert attrs["deepest_order"] == 0
    assert attrs["cognitive_evaluations"] == 1
    assert attrs["publication_provenance"] == "native_program"


def test_same_rule_recurses_through_arbitrary_held_order_chain():
    agent = _fresh()
    outcome = _outcome(agent, "order_five_result")
    programs = [
        _program(agent, order, residual=9 if order < 5 else 0, boundary=1)
        for order in range(6)
    ]
    for lower, higher in zip(programs, programs[1:]):
        _edge(agent, lower, "continues_to_higher_order_capability_program", higher)
    _edge(agent, programs[-1], "settles_to_capability_outcome", outcome)

    state, attrs = _collapse(agent, programs[0], 1)

    assert _published(agent, state) == [outcome]
    assert attrs["achieved_order"] == 5
    assert attrs["deepest_order"] == 5
    assert attrs["cognitive_evaluations"] == 6
    assert len(agent.s.neighbours(state, "has_capability_collapse_step")) == 5


def test_uncovered_surprise_requests_synthesis_without_a_fake_outcome():
    agent = _fresh()
    program = _program(agent, 0, residual=8, boundary=2)

    state, attrs = _collapse(agent, program, 1)

    assert _published(agent, state) == []
    assert attrs["status"] == "unresolved_boundary"
    assert attrs["synthesis_requested"] == 1
    assert attrs["published_outcome_count"] == 0


def test_deployment_order_limit_is_optional_not_architectural():
    agent = _fresh()
    outcome = _outcome(agent, "higher_result")
    low = _program(agent, 0, residual=9, boundary=1)
    high = _program(agent, 1, residual=0, boundary=1)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)
    _edge(agent, high, "settles_to_capability_outcome", outcome)

    limited, limited_attrs = _collapse(
        agent, low, 1, limit_enabled=1, maximum_order=0,
    )
    assert _published(agent, limited) == []
    assert limited_attrs["status"] == "configured_order_limit"
    assert limited_attrs["synthesis_requested"] == 0

    unlimited, unlimited_attrs = _collapse(
        agent, low, 2, limit_enabled=0, maximum_order=0,
    )
    assert _published(agent, unlimited) == [outcome]
    assert unlimited_attrs["achieved_order"] == 1


def test_verified_practice_compiles_deeper_outcome_basin_into_lower_order():
    agent = _fresh()
    outcome = _outcome(agent, "learned_compound_program")
    low = _program(agent, 0, residual=8, boundary=2, receipts=2)
    high = _program(agent, 1, residual=0, boundary=1, receipts=2)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)
    _edge(agent, high, "settles_to_capability_outcome", outcome)

    first, first_attrs = _collapse(agent, low, 1)
    assert first_attrs["achieved_order"] == 1
    # Selection alone is not practice. Physical/world verification is required.
    assert agent.tick() == 0
    assert agent.s.neighbours(low, "compiles_capability_outcome") == []
    agent.s.set_attr(first, "outcome_verified", 1)
    assert agent.tick() > 0
    assert agent.s.neighbours(low, "compiles_capability_outcome") == []

    second, second_attrs = _collapse(agent, low, 2)
    assert second_attrs["achieved_order"] == 1
    agent.s.set_attr(second, "outcome_verified", 1)
    assert agent.tick() > 0

    low_attrs = agent.s.node(low)["attrs"]
    assert agent.s.neighbours(low, "compiles_capability_outcome") == [outcome]
    assert low_attrs["capability_boundary_quanta"] == 8
    assert low_attrs["compiled_practice_receipts"] == 2
    assert low_attrs["learning_status"] == "muscle_memory_compiled"

    practiced, practiced_attrs = _collapse(agent, low, 3)
    assert _published(agent, practiced) == [outcome]
    assert practiced_attrs["achieved_order"] == 0
    assert practiced_attrs["deepest_order"] == 0
    assert practiced_attrs["cognitive_evaluations"] == 1
    assert practiced_attrs["publication_provenance"] == "compiled_practice"


def test_new_surprise_outside_practiced_boundary_re_escalates():
    agent = _fresh()
    outcome = _outcome(agent, "reusable_result")
    low = _program(agent, 0, residual=6, boundary=1, receipts=1)
    high = _program(agent, 1, residual=0, boundary=1, receipts=1)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)
    _edge(agent, high, "settles_to_capability_outcome", outcome)

    training, _ = _collapse(agent, low, 1)
    agent.s.set_attr(training, "outcome_verified", 1)
    assert agent.tick() > 0
    assert agent.s.node(low)["attrs"]["capability_boundary_quanta"] == 6

    agent.s.set_attr(low, "residual_quanta", 7)
    state, attrs = _collapse(agent, low, 2)
    assert _published(agent, state) == [outcome]
    assert attrs["achieved_order"] == 1
    assert attrs["deepest_order"] == 1


def test_simultaneous_verified_episodes_do_not_lose_practice_receipts():
    agent = _fresh()
    outcome = _outcome(agent, "concurrent_result")
    low = _program(agent, 0, residual=5, boundary=1, receipts=2)
    high = _program(agent, 1, residual=0, boundary=1, receipts=2)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)
    _edge(agent, high, "settles_to_capability_outcome", outcome)

    first = _state(agent, low, 1)
    second = _state(agent, low, 2)
    assert agent.tick() > 0
    agent.s.set_attr(first, "outcome_verified", 1)
    agent.s.set_attr(second, "outcome_verified", 1)

    assert agent.tick() > 0

    traces = agent.s.neighbours(low, "has_capability_practice_trace")
    assert len(traces) == 1
    assert agent.s.node(traces[0])["attrs"]["receipt_count"] == 2
    assert agent.s.neighbours(low, "compiles_capability_outcome") == [outcome]


def test_parallel_collapse_states_do_not_leak_programs_or_outcomes():
    agent = _fresh()
    left_outcome = _outcome(agent, "left")
    right_outcome = _outcome(agent, "right")
    left = _program(agent, 0, residual=0, boundary=1)
    right = _program(agent, 0, residual=0, boundary=1)
    _edge(agent, left, "settles_to_capability_outcome", left_outcome)
    _edge(agent, right, "settles_to_capability_outcome", right_outcome)
    left_state = _state(agent, left, 1)
    right_state = _state(agent, right, 1)

    assert agent.tick() > 0

    assert _published(agent, left_state) == [left_outcome]
    assert _published(agent, right_state) == [right_outcome]
