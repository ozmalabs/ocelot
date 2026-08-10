"""Behavioral gates for the M-by-N nested cognition/control fabric."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


def _fresh():
    return WorldAdapter(seeds=("capability_collapse",))


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def _outcome(agent, token):
    return agent.s.add_node("CapabilityOutcome", {
        "token": token,
        "outcome_kind": "task_invariant_basin",
    })


def _scope(agent, token):
    return agent.s.add_node("ControlAuthorityScope", {"scope_token": token})


def _scalar_program(agent, outcome, *, order=0, residual=0, boundary=1):
    program = agent.s.add_node("CapabilityProgram", {
        "order": order,
        "residual_quanta": residual,
        "capability_boundary_quanta": boundary,
        "baseline_capability_boundary_quanta": boundary,
        "required_practice_receipts": 1,
        "required_practice_contexts": 1,
        "maximum_practice_failures": 0,
        "consolidation_required": 0,
        "compiled_execution_failure_count": 0,
    })
    _edge(agent, program, "settles_to_capability_outcome", outcome)
    return program


def _channel(agent, token, observed, boundary, *, precision=10, demand=0,
             proactive_boundary=5):
    return agent.s.add_node("CapabilityResidualChannel", {
        "channel_token": token,
        "observed_quanta": observed,
        "boundary_quanta": boundary,
        "baseline_boundary_quanta": boundary,
        "precision_quanta": precision,
        "control_demand_quanta": demand,
        "proactive_boundary_quanta": proactive_boundary,
    })


def _channel_program(agent, default, channels, *, order=0, receipts=1,
                     consolidation=0):
    program = agent.s.add_node("CapabilityProgram", {
        "order": order,
        "residual_mode": "channels",
        "minimum_precision_quanta": 5,
        "capability_boundary_quanta": 0,
        "baseline_capability_boundary_quanta": 0,
        "required_practice_receipts": receipts,
        "required_practice_contexts": 1,
        "maximum_practice_failures": 0,
        "consolidation_required": consolidation,
        "compiled_execution_failure_count": 0,
    })
    _edge(agent, program, "holds_default_capability_outcome", default)
    for channel in channels:
        _edge(agent, program, "has_capability_residual_channel", channel)
    return program


def _state(agent, root, scope, epoch=1, *, continuous=False):
    attrs = {
        "stage": "settled" if continuous else "ready",
        "collapse_armed": 0 if continuous else 1,
        "request_epoch": 0 if continuous else epoch,
        "order_limit_enabled": 0,
        "maximum_order": 0,
        "outcome_verified": 0,
        "verification_status": "pending",
        "compiled_failure_processed_epoch": -1,
        "continuous_enabled": 1 if continuous else 0,
        "cycle_request_epoch": epoch if continuous else 0,
        "completed_cycle_epoch": 0,
    }
    state = agent.s.add_node("CapabilityCollapseState", attrs)
    context = agent.s.add_node("CapabilityContext", {
        "context_token": f"context_{epoch}_{state}",
    })
    _edge(agent, state, "has_root_capability_program", root)
    _edge(agent, state, "governs_control_authority_scope", scope)
    _edge(agent, state, "in_capability_context", context)
    return state


def test_local_default_keeps_running_when_typed_residual_goes_upward():
    agent = _fresh()
    finger = _scope(agent, "local_digit_group")
    hand = _scope(agent, "parent_hand")
    default = _outcome(agent, "local_hold")
    channel = _channel(agent, "contact_error", observed=8, boundary=3)
    program = _channel_program(agent, default, [channel])
    state = _state(agent, program, finger, continuous=True)
    _edge(agent, finger, "reports_capability_residual_to", hand)

    assert agent.tick() > 0

    attrs = agent.s.node(state)["attrs"]
    assert attrs["stage"] == "unresolved"
    assert attrs["completed_cycle_epoch"] == 1
    assert attrs["effective_outcome_provenance"] == "local_default"
    assert agent.s.neighbours(state, "effective_capability_outcome") == [default]
    reports = agent.s.neighbours(finger, "has_capability_residual_report")
    assert len(reports) == 1
    assert agent.s.neighbours(
        reports[0], "escalates_to_control_authority_scope",
    ) == [hand]
    assert agent.s.node(reports[0])["attrs"]["observed_quanta"] == 8


def test_proactive_demand_can_deepen_before_reactive_error():
    agent = _fresh()
    scope = _scope(agent, "proactive_scope")
    default = _outcome(agent, "continue_default")
    considered = _outcome(agent, "risk_aware_basin")
    # The observation is inside its reactive boundary, but expected consequence
    # has already pushed integer control demand outside the proactive boundary.
    channel = _channel(
        agent, "anticipated_consequence", observed=1, boundary=5,
        demand=9, proactive_boundary=4,
    )
    low = _channel_program(agent, default, [channel])
    high = _scalar_program(agent, considered, order=1)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)
    state = _state(agent, low, scope)

    assert agent.tick() > 0

    attrs = agent.s.node(state)["attrs"]
    assert attrs["achieved_order"] == 1
    assert attrs["cognitive_evaluations"] == 2
    assert agent.s.neighbours(state, "published_capability_outcome") == [considered]


def test_scoped_override_does_not_stop_local_cycle_and_expires():
    agent = _fresh()
    scope = _scope(agent, "local_scope")
    local = _outcome(agent, "local_basin")
    override = _outcome(agent, "parent_correction_basin")
    program = _scalar_program(agent, local)
    _edge(agent, program, "holds_default_capability_outcome", local)
    state = _state(agent, program, scope, continuous=True)

    assert agent.tick() > 0
    assert agent.s.neighbours(state, "effective_capability_outcome") == [local]

    lease = agent.s.add_node("CapabilityOverrideLease", {
        "active": 1,
        "valid_from_epoch": 2,
        "expires_after_epoch": 2,
    })
    _edge(agent, scope, "receives_capability_override_lease", lease)
    _edge(agent, lease, "overrides_with_capability_outcome", override)
    agent.s.set_attr(state, "cycle_request_epoch", 2)
    assert agent.tick() > 0
    attrs = agent.s.node(state)["attrs"]
    assert attrs["completed_cycle_epoch"] == 2
    assert attrs["cognitive_evaluations"] == 1
    assert attrs["effective_outcome_provenance"] == "scoped_override_lease"
    assert agent.s.neighbours(state, "effective_capability_outcome") == [override]

    agent.s.set_attr(state, "cycle_request_epoch", 3)
    assert agent.tick() > 0
    assert agent.s.node(lease)["attrs"]["status"] == "expired"
    assert agent.s.neighbours(state, "effective_capability_outcome") == [local]


def test_many_authority_scopes_cycle_independently_for_full_body_scale():
    agent = _fresh()
    states = []
    outcomes = []
    # More independent scopes than a simple humanoid limb inventory: enough for
    # fingers, toes, gaze, jaw, spine segments, limbs and whole-body auxiliaries.
    for ordinal in range(64):
        scope = _scope(agent, f"body_scope_{ordinal}")
        outcome = _outcome(agent, f"local_outcome_{ordinal}")
        program = _scalar_program(agent, outcome)
        _edge(agent, program, "holds_default_capability_outcome", outcome)
        state = _state(agent, program, scope, continuous=True)
        states.append(state)
        outcomes.append(outcome)

    assert agent.tick() > 0

    for state, outcome in zip(states, outcomes):
        assert agent.s.node(state)["attrs"]["completed_cycle_epoch"] == 1
        assert agent.s.neighbours(state, "effective_capability_outcome") == [outcome]

    # Only one local scheduler advances: no organism-wide barrier forces the
    # other 63 scopes to cycle with it.
    agent.s.set_attr(states[17], "cycle_request_epoch", 2)
    assert agent.tick() > 0
    assert agent.s.node(states[17])["attrs"]["completed_cycle_epoch"] == 2
    assert all(
        agent.s.node(state)["attrs"]["completed_cycle_epoch"] == 1
        for index, state in enumerate(states) if index != 17
    )


def test_observed_interference_discovers_joint_domain_for_combined_program():
    agent = _fresh()
    first = _scope(agent, "first_child")
    second = _scope(agent, "second_child")
    joint = _scope(agent, "learned_joint_domain")
    observation = agent.s.add_node("ControlCouplingObservation", {
        "interference_quanta": 7,
        "interference_boundary_quanta": 2,
        "precision_quanta": 9,
        "minimum_precision_quanta": 5,
        "processed": 0,
    })
    _edge(agent, observation, "first_control_authority_scope", first)
    _edge(agent, observation, "second_control_authority_scope", second)
    _edge(agent, observation, "recommends_joint_control_authority_scope", joint)

    assert agent.tick() > 0

    assert agent.s.neighbours(first, "requires_joint_settlement_with") == [second]
    assert agent.s.neighbours(second, "requires_joint_settlement_with") == [first]
    assert set(agent.s.neighbours(
        joint, "coordinates_child_control_authority_scope",
    )) == {first, second}
    residuals = agent.s.neighbours(joint, "has_capability_coupling_residual")
    assert len(residuals) == 1

    combined = _outcome(agent, "one_program_controlling_both_children")
    first_local = _outcome(agent, "first_local")
    second_local = _outcome(agent, "second_local")
    first_state = _state(
        agent, _scalar_program(agent, first_local), first, epoch=2,
    )
    second_state = _state(
        agent, _scalar_program(agent, second_local), second, epoch=2,
    )
    for scope in (first, second):
        lease = agent.s.add_node("CapabilityOverrideLease", {
            "active": 1,
            "valid_from_epoch": 2,
            "expires_after_epoch": 2,
        })
        _edge(agent, scope, "receives_capability_override_lease", lease)
        _edge(agent, lease, "overrides_with_capability_outcome", combined)

    assert agent.tick() > 0
    assert agent.s.neighbours(first_state, "effective_capability_outcome") == [combined]
    assert agent.s.neighbours(second_state, "effective_capability_outcome") == [combined]


def test_channel_practice_expands_only_evidenced_dimension_and_failure_revokes():
    agent = _fresh()
    scope = _scope(agent, "adaptive_scope")
    default = _outcome(agent, "default")
    practiced = _outcome(agent, "stable_task_basin")
    trained = _channel(agent, "trained_dimension", observed=8, boundary=3)
    untouched = _channel(agent, "already_safe_dimension", observed=1, boundary=4)
    low = _channel_program(agent, default, [trained, untouched], receipts=1)
    high = _scalar_program(agent, practiced, order=1)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)
    state = _state(agent, low, scope)

    assert agent.tick() > 0
    agent.s.set_attr(state, "outcome_verified", 1)
    agent.s.set_attr(state, "verification_status", "success")
    assert agent.tick() > 0

    assert agent.s.node(trained)["attrs"]["boundary_quanta"] == 8
    assert agent.s.node(untouched)["attrs"]["boundary_quanta"] == 4
    assert agent.s.neighbours(low, "compiles_capability_outcome") == [practiced]

    failed = _state(agent, low, scope, epoch=2)
    assert agent.tick() > 0
    assert agent.s.node(failed)["attrs"]["achieved_order"] == 0
    agent.s.set_attr(failed, "verification_status", "failure")
    assert agent.tick() > 0

    assert agent.s.neighbours(low, "compiles_capability_outcome") == []
    assert agent.s.node(trained)["attrs"]["boundary_quanta"] == 3
    assert agent.s.node(low)["attrs"]["learning_status"] == "revaluation_required"


def test_optional_consolidation_blocks_compilation_until_receipt():
    agent = _fresh()
    scope = _scope(agent, "consolidating_scope")
    default = _outcome(agent, "default")
    practiced = _outcome(agent, "consolidated_basin")
    channel = _channel(agent, "load", observed=6, boundary=2)
    low = _channel_program(
        agent, default, [channel], receipts=1, consolidation=1,
    )
    high = _scalar_program(agent, practiced, order=1)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)
    state = _state(agent, low, scope)

    assert agent.tick() > 0
    agent.s.set_attr(state, "outcome_verified", 1)
    agent.s.set_attr(state, "verification_status", "success")
    assert agent.tick() > 0
    assert agent.s.neighbours(low, "compiles_capability_outcome") == []
    assert agent.s.node(channel)["attrs"]["boundary_quanta"] == 2

    traces = agent.s.neighbours(low, "has_capability_channel_practice_trace")
    assert len(traces) == 1
    receipt = agent.s.add_node("CapabilityConsolidationReceipt", {
        "verified": 1,
        "consolidation_epoch": 2,
    })
    _edge(agent, traces[0], "has_capability_consolidation_receipt", receipt)
    assert agent.tick() > 0

    assert agent.s.neighbours(low, "compiles_capability_outcome") == [practiced]
    assert agent.s.node(channel)["attrs"]["boundary_quanta"] == 6
