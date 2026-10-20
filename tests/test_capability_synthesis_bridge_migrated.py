"""Execution gates for capability_synthesis_bridge (P1.A1)."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "capability_synthesis_bridge.json"
GENERATOR = ROOT / "scripts" / "gen_capability_synthesis_bridge_seed.py"

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


def _fresh(*, enabled=0):
    agent = WorldAdapter(seeds=("capability_collapse", "capability_synthesis_bridge"))
    policies = agent.s.nodes("CapabilitySynthesisBridgePolicy")
    assert len(policies) == 1
    if enabled:
        agent.s.set_attr(policies[0], "enabled", 1)
    return agent


def _outcome(agent, token="opaque_combined_outcome"):
    return agent.s.add_node("CapabilityOutcome", {
        "token": token,
        "outcome_kind": "task_invariant_basin",
    })


def _scope(agent, token):
    return agent.s.add_node("ControlAuthorityScope", {"scope_token": token})


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


def _state(agent, root, epoch=1, *, scope=None, continuous=False):
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
        "context_epoch": epoch,
        "context_token": f"context_{epoch}_{state}",
    })
    _edge(agent, state, "has_root_capability_program", root)
    _edge(agent, state, "in_capability_context", context)
    if scope is not None:
        _edge(agent, state, "governs_control_authority_scope", scope)
    return state


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
    assert seed["id"] == "capability_synthesis_bridge"
    assert seed["self_load_only"] is True
    assert seed["depends_on"] == ["capability_collapse"]
    assert len(seed["rules"]) == 6
    _assert_no_float(seed)

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


def test_policy_disabled_is_byte_identical_no_request():
    agent = _fresh(enabled=0)
    program = _program(agent, 0, residual=8, boundary=2)
    state = _state(agent, program, 1)

    assert agent.tick() > 0

    attrs = agent.s.node(state)["attrs"]
    assert attrs["stage"] == "unresolved"
    assert attrs["synthesis_requested"] == 1
    assert agent.s.nodes("CapabilitySynthesisRequest") == []
    assert agent.s.nodes("SelfConcern") == []


def test_oneshot_request_files_concern_and_rearms_when_higher_program_supplied():
    agent = _fresh(enabled=1)
    low = _program(agent, 0, residual=8, boundary=2)
    state = _state(agent, low, 1)

    assert agent.tick() > 0

    reqs = agent.s.neighbours(state, "has_capability_synthesis_request")
    assert len(reqs) == 1
    req = reqs[0]
    req_attrs = agent.s.node(req)["attrs"]
    assert req_attrs["status"] == "open"
    assert req_attrs["reason"] == "unresolved_boundary"
    assert req_attrs["request_epoch"] == 1
    assert req_attrs["order"] == 0
    assert req_attrs["residual_quanta"] == 8
    assert req_attrs["boundary_quanta"] == 2
    assert agent.s.neighbours(req, "requests_higher_program_for") == [low]

    concerns = agent.s.nodes("SelfConcern")
    assert len(concerns) == 1
    sc_attrs = agent.s.node(concerns[0])["attrs"]
    assert sc_attrs["status"] == "noted"
    assert sc_attrs["source"] == "capability_collapse"
    assert sc_attrs["kind"] == "capability_synthesis"
    assert sc_attrs["content"] == "unresolved_boundary"
    assert agent.s.neighbours(concerns[0], "about_request") == [req]

    # Re-ticking without supplying a higher program never duplicates the request or concern.
    assert agent.tick() == 0
    assert len(agent.s.nodes("CapabilitySynthesisRequest")) == 1
    assert len(agent.s.nodes("SelfConcern")) == 1

    # Supply an order-1 program with an outcome and continuation edge.
    outcome = _outcome(agent, "synthesised_higher_basin")
    high = _program(agent, 1, residual=0, boundary=1)
    _edge(agent, high, "settles_to_capability_outcome", outcome)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)

    assert agent.tick() > 0

    assert _published(agent, state) == [outcome]
    state_attrs = agent.s.node(state)["attrs"]
    assert state_attrs["stage"] == "settled"
    assert state_attrs["achieved_order"] == 1
    assert state_attrs["request_epoch"] == 2

    req_attrs_after = agent.s.node(req)["attrs"]
    assert req_attrs_after["status"] == "resolved"
    assert req_attrs_after["resolved_order"] == 1


def test_continuous_channel_variant_rearms_via_cycle_request_epoch():
    agent = _fresh(enabled=1)
    scope = _scope(agent, "digit_group")
    default = _outcome(agent, "local_hold")
    channel = _channel(agent, "contact_error", observed=8, boundary=3)
    low = _channel_program(agent, default, [channel], order=0)
    state = _state(agent, low, epoch=1, scope=scope, continuous=True)

    assert agent.tick() > 0

    attrs = agent.s.node(state)["attrs"]
    assert attrs["stage"] == "unresolved"
    assert attrs["completed_cycle_epoch"] == 1
    assert agent.s.neighbours(state, "effective_capability_outcome") == [default]

    reqs = agent.s.neighbours(state, "has_capability_synthesis_request")
    assert len(reqs) == 1
    req = reqs[0]
    assert agent.s.node(req)["attrs"]["status"] == "open"
    assert agent.s.node(req)["attrs"]["reason"] == "unresolved_channel_envelope"

    higher_outcome = _outcome(agent, "higher_channel_basin")
    high = _program(agent, 1, residual=0, boundary=1)
    _edge(agent, high, "settles_to_capability_outcome", higher_outcome)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)

    assert agent.tick() > 0

    attrs_after = agent.s.node(state)["attrs"]
    assert attrs_after["stage"] == "settled"
    assert attrs_after["achieved_order"] == 1
    assert attrs_after["completed_cycle_epoch"] == 2
    assert agent.s.neighbours(state, "published_capability_outcome") == [higher_outcome]
    assert agent.s.neighbours(state, "effective_capability_outcome") == [higher_outcome]

    req_attrs = agent.s.node(req)["attrs"]
    assert req_attrs["status"] == "resolved"
    assert req_attrs["resolved_order"] == 1


def test_conflicting_override_leases_open_request_and_never_rearm():
    agent = _fresh(enabled=1)
    scope = _scope(agent, "contested_scope")
    local = _outcome(agent, "local_basin")
    override_a = _outcome(agent, "parent_a")
    override_b = _outcome(agent, "parent_b")
    low = _program(agent, 0, residual=0, boundary=2)
    _edge(agent, low, "settles_to_capability_outcome", local)
    _edge(agent, low, "holds_default_capability_outcome", local)
    state = _state(agent, low, epoch=1, scope=scope, continuous=False)

    for outcome in (override_a, override_b):
        lease = agent.s.add_node("CapabilityOverrideLease", {
            "active": 1,
            "valid_from_epoch": 1,
            "expires_after_epoch": 5,
        })
        _edge(agent, scope, "receives_capability_override_lease", lease)
        _edge(agent, lease, "overrides_with_capability_outcome", outcome)

    assert agent.tick() > 0

    reqs = agent.s.neighbours(state, "has_capability_synthesis_request")
    assert len(reqs) == 1
    req = reqs[0]
    req_attrs = agent.s.node(req)["attrs"]
    assert req_attrs["status"] == "open"
    assert req_attrs["reason"] == "conflicting_leases"

    concerns = agent.s.nodes("SelfConcern")
    assert len(concerns) == 1
    assert agent.s.node(concerns[0])["attrs"]["content"] == "conflicting_leases"

    # Even if a higher program is attached, conflicting_leases must never re-arm.
    high = _program(agent, 1, residual=0, boundary=1)
    _edge(agent, high, "settles_to_capability_outcome", override_a)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)

    assert agent.tick() == 0
    assert agent.s.node(req)["attrs"]["status"] == "open"
    assert agent.s.node(state)["attrs"]["request_epoch"] == 1


def test_ambiguous_continuations_mark_request_ambiguous_without_rearming():
    agent = _fresh(enabled=1)
    low = _program(agent, 0, residual=8, boundary=2)
    state = _state(agent, low, 1)

    assert agent.tick() > 0
    reqs = agent.s.neighbours(state, "has_capability_synthesis_request")
    assert len(reqs) == 1
    req = reqs[0]
    assert agent.s.node(req)["attrs"]["status"] == "open"

    high_a = _program(agent, 1, residual=0, boundary=1)
    high_b = _program(agent, 1, residual=0, boundary=1)
    _edge(agent, low, "continues_to_higher_order_capability_program", high_a)
    _edge(agent, low, "continues_to_higher_order_capability_program", high_b)

    assert agent.tick() > 0
    assert agent.s.node(req)["attrs"]["status"] == "ambiguous"
    assert agent.s.node(state)["attrs"]["stage"] == "unresolved"
    assert len(agent.s.nodes("CapabilitySynthesisRequest")) == 1
