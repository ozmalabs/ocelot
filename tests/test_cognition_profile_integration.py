"""Integration and profile gates for boot_cognition_on (P1.H8.2, P1.H8.3, P1.H8.4)."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

pytest.importorskip("substrate_rs")

from substrate.boot_core import installed_seeds
from substrate.boot_profiles import COGNITION_ON_SEEDS, boot_cognition_on
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter
from tests.test_geninfer_grain_migrated import BLOCK, DT3, JIT, _rot


def _edge(agent, src, edge_type, tgt):
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _nodes(agent, node_type):
    return [
        nid for nid in agent.s.nodes()
        if agent.s.node(nid)["type"] == node_type
    ]


def test_default_world_adapter_loads_none_of_cognition_on_seeds():
    """Phase 1 gate: a default WorldAdapter() boot loads none of the new seeds."""
    default_agent = WorldAdapter()
    loaded_ids = set(installed_seeds(default_agent.s).keys())
    for sid in COGNITION_ON_SEEDS:
        assert sid not in loaded_ids, f"Default boot unexpectedly loaded {sid}"

    exported_rule_names = {
        r["name"] for r in default_agent.inner.export_rules()
    }
    for sid in (
        "capability_synthesis_bridge",
        "decomposition_consumer",
        "impasse_simulation_bridge",
        "consolidation_scheduler",
        "staleness_decay",
        "demotion_hierarchy",
        "core_emotions",
        "arousal_window_coreg",
        "capability_collapse",
        "extended_thinking",
        "inference_ladder_record",
    ):
        manifest = manifest_for(sid)
        for rule in manifest.get("rules", ()):
            if isinstance(rule, dict) and "match" in rule and rule.get("name"):
                assert rule["name"] not in exported_rule_names, (
                    f"Default boot unexpectedly installed rule {rule['name']!r} from {sid}"
                )


def test_cognition_on_profile_boots_and_attaches_enabled_params():
    """P1.H8.2 & P1.H8.3: boot_cognition_on() installs all COGNITION_ON_SEEDS rules
    and attaches every opt-in params/policy node with enabled == 1 from agent_root.
    """
    t0 = time.perf_counter()
    agent = boot_cognition_on()
    boot_elapsed = time.perf_counter() - t0
    assert boot_elapsed < 10.0, f"boot_cognition_on() took {boot_elapsed:.2f}s"

    exported_rule_names = {
        r["name"] for r in agent.inner.export_rules()
    }
    for sid in COGNITION_ON_SEEDS:
        manifest = manifest_for(sid)
        for rule in manifest.get("rules", ()):
            if isinstance(rule, dict) and "match" in rule and rule.get("name"):
                assert rule["name"] in exported_rule_names, (
                    f"Missing rule {rule['name']!r} from {sid} in boot_cognition_on()"
                )

    expected_edges_and_types = [
        ("has_held_decay_params", "HeldDecayParams"),
        ("has_hier_tier_params", "HeldTierParams"),
        ("has_emotion_params", "HeldEmotionParams"),
        ("has_window", "WindowOfTolerance"),
        ("has_capability_synthesis_bridge_policy", "CapabilitySynthesisBridgePolicy"),
        ("has_decomposition_consumer_policy", "DecompositionConsumerPolicy"),
        ("has_impasse_simulation_policy", "ImpasseSimulationPolicy"),
        ("has_consolidation_scheduler_policy", "ConsolidationSchedulerPolicy"),
        ("has_thinking_budget", "ThinkingBudget"),
        ("has_extended_thinking_policy", "ExtendedThinkingPolicy"),
    ]
    for edge_type, node_type in expected_edges_and_types:
        targets = list(agent.inner.neighbours(agent.agent, edge_type))
        matching = [
            nid for nid in targets
            if agent.s.node(nid)["type"] == node_type
            and agent.s.node(nid)["attrs"].get("enabled") == 1
        ]
        assert len(matching) >= 1, (
            f"Expected enabled {node_type} reachable via {edge_type} from agent_root"
        )
    assert len(list(agent.inner.neighbours(agent.agent, "has_tolerance"))) == 5


def test_cognition_on_runs_a_funded_dim_grain_episode():
    agent = boot_cognition_on()
    mode = _nodes(agent, "NetworkModeState")[0]
    budget = next(n for n in agent.inner.neighbours(agent.agent, "has_thinking_budget")
                  if agent.s.node(n)["attrs"].get("enabled") == 1.0)
    policy = next(n for n in agent.inner.neighbours(agent.agent, "has_extended_thinking_policy")
                  if agent.s.node(n)["attrs"].get("enabled") == 1.0)
    agent.s.set_attr(mode, "epoch", 1.0)
    agent.s.set_attr(agent.agent, "codebook_epoch", 0.0)
    agent.s.set_attr(budget, "remaining", 8.0)
    agent.s.set_attr(budget, "last_refill_epoch", 1.0)
    agent.s.add_node("ShapeSignature", {
        "name": "profile_block", "signature": json.dumps(BLOCK), "kind": "faculty",
        "faculty": "profile_block", "dim_types": DT3,
    })
    signature = _rot(JIT)
    obs = agent.s.add_node("Observation", {
        "signature": signature, "key": ["profile-grain"], "status": "decoded",
        "residual": signature, "decoded_epoch": 0.0, "dim_types": DT3,
    })
    _edge(agent, agent.agent, "observed", obs)
    agent.inner.run_rules()
    attrs = agent.s.node(obs)["attrs"]
    assert attrs["status"] == "recognized_transformed"
    assert attrs["accepted_at_relaxed"] == "dim_grain_ladder"
    assert agent.s.node(budget)["attrs"]["remaining"] == pytest.approx(7.0)
    assert len(_nodes(agent, "ExtendedThinkingEpisode")) == 1


def test_cognition_on_single_agent_end_to_end_four_rule_chains():
    """P1.H8.4: On a single boot_cognition_on() agent, run all four P1 rule chains:
      (A4) dual-process tie -> world-model simulation -> ImaginedCandidate;
      (A1) unresolved capability collapse -> synthesis request -> higher program settles;
      (A2) order-3 impasse -> partitioned child axes + child_mean_saturation rollup;
      (B1) idle NetworkModeSample epochs -> offline MemoryCycles, ReplayTraces, SemanticSupport.
    """
    agent = boot_cognition_on()

    # ------------------------------------------------------------------
    # Chain 1 (A4): Dual-process tie -> ImaginedCandidate
    # ------------------------------------------------------------------
    mode = _nodes(agent, "NetworkModeState")[0]
    agent.s.set_attr(mode, "epoch", 1.0)

    obs = agent.s.add_node("WorldModelObservation", {
        "belief_status": "new",
        "prediction_comparison_status": "uncompared",
        "provenance_kind": "perceived",
        "state_kind": "corridor",
        "state_summary": "door ahead, cover on the left",
        "epoch": 1.0,
        "confidence": 0.9,
        "uncertainty": 0.1,
    })
    _edge(agent, agent.agent, "has_world_model_observation", obs)
    agent.dual_process_tick()

    for act_kind, rank in (("forward", 1.0), ("turn_left", 2.0)):
        wm_act = agent.s.add_node("WorldModelAction", {
            "action_kind": act_kind,
            "branch_rank": rank,
        })
        _edge(agent, agent.agent, "has_world_model_action", wm_act)

    for rank, source, action, successor, observation, outcome, value in (
        (1, "corridor", "forward", "junction", "junction_visible", "progress", 0.7),
        (2, "corridor", "turn_left", "corridor", "left_wall_visible", "safe_reorientation", 0.2),
        (3, "junction", "forward", "exit", "exit_visible", "goal_progress", 1.0),
        (4, "junction", "turn_left", "corridor", "side_route_visible", "safe_reorientation", 0.4),
    ):
        tr = agent.s.add_node("TransitionHypothesis", {
            "source_state_kind": source,
            "action_kind": action,
            "successor_state_kind": successor,
            "successor_summary": f"{action} predicts {successor}",
            "predicted_observation_kind": observation,
            "predicted_observation_value": value,
            "predicted_outcome_kind": outcome,
            "predicted_outcome_value": value,
            "confidence": 0.8,
            "uncertainty": 0.2,
            "model_rank": float(rank),
            "revision_count": 0.0,
        })
        _edge(agent, agent.agent, "has_transition_hypothesis", tr)
        feat = agent.s.add_node("TransitionFeature", {
            "feature_key": f"affordance:{action}",
            "feature_value": successor,
            "confidence": 0.9,
        })
        _edge(agent, tr, "predicts_feature", feat)

    dp_ctx = agent.s.add_node("DualProcessContext", {
        "status": "pending",
        "epoch": 1,
        "prediction_error": 0.0,
        "novelty": 0.0,
        "uncertainty": 0.0,
        "system_two_expected_utility": 0.0,
        "system_two_reliability": 0.0,
        "system_two_latency": 0.0,
        "system_two_effort": 0.0,
    })
    _edge(agent, agent.agent, "has_dual_process_context", dp_ctx)
    for _ in range(2):
        cand = agent.s.add_node("SystemOneCandidate", {
            "status": "ready",
            "epoch": 1,
            "default_value": 1.0,
            "urgency": 0.0,
            "valence": 0.0,
            "residual": 0.0,
            "grounded": 1,
            "reliability": 1.0,
            "learned_default": 0,
            "consolidation_strength": 0.0,
            "accumulated_evidence": 0.0,
            "evidence_increment": 0.0,
            "experience_count": 0,
            "eligibility_trace": 1.0,
            "predicted_value": 0.0,
        })
        _edge(agent, dp_ctx, "has_system_one_candidate", cand)

    agent.dual_process_tick()

    escalations = list(agent.inner.neighbours(dp_ctx, "has_system_two_escalation"))
    assert len(escalations) == 1
    imagined = list(agent.inner.neighbours(escalations[0], "has_imagined_candidate"))
    assert len(imagined) == 1
    assert agent.s.node(imagined[0])["attrs"]["root_action_kind"] == "forward"

    # ------------------------------------------------------------------
    # Chain 2 (A1): Unresolved capability collapse -> request -> settles
    # ------------------------------------------------------------------
    low = agent.s.add_node("CapabilityProgram", {
        "order": 0,
        "residual_quanta": 8,
        "capability_boundary_quanta": 2,
        "baseline_capability_boundary_quanta": 2,
        "required_practice_receipts": 2,
        "required_practice_contexts": 1,
        "maximum_practice_failures": 0,
        "consolidation_required": 0,
        "compiled_execution_failure_count": 0,
    })
    cc_state = agent.s.add_node("CapabilityCollapseState", {
        "stage": "ready",
        "collapse_armed": 1,
        "request_epoch": 1,
        "order_limit_enabled": 0,
        "maximum_order": 0,
        "outcome_verified": 0,
        "verification_status": "pending",
        "compiled_failure_processed_epoch": -1,
        "continuous_enabled": 0,
        "cycle_request_epoch": 0,
        "completed_cycle_epoch": 0,
    })
    cc_ctx = agent.s.add_node("CapabilityContext", {
        "context_epoch": 1,
        "context_token": "cognition_on_ctx_1",
    })
    _edge(agent, cc_state, "has_root_capability_program", low)
    _edge(agent, cc_state, "in_capability_context", cc_ctx)

    agent.tick()
    reqs = list(agent.inner.neighbours(cc_state, "has_capability_synthesis_request"))
    assert len(reqs) == 1
    req = reqs[0]
    assert agent.s.node(req)["attrs"]["status"] == "open"

    outcome = agent.s.add_node("CapabilityOutcome", {
        "token": "synthesised_higher_basin",
        "outcome_kind": "task_invariant_basin",
    })
    high = agent.s.add_node("CapabilityProgram", {
        "order": 1,
        "residual_quanta": 0,
        "capability_boundary_quanta": 1,
        "baseline_capability_boundary_quanta": 1,
        "required_practice_receipts": 2,
        "required_practice_contexts": 1,
        "maximum_practice_failures": 0,
        "consolidation_required": 0,
        "compiled_execution_failure_count": 0,
    })
    _edge(agent, high, "settles_to_capability_outcome", outcome)
    _edge(agent, low, "continues_to_higher_order_capability_program", high)

    agent.tick()
    assert agent.s.node(cc_state)["attrs"]["stage"] == "settled"
    assert agent.s.node(cc_state)["attrs"]["achieved_order"] == 1
    assert agent.s.node(req)["attrs"]["status"] == "resolved"
    assert list(agent.inner.neighbours(cc_state, "published_capability_outcome")) == [outcome]

    # ------------------------------------------------------------------
    # Chain 3 (A2): Order-3 impasse -> partitioned child axes
    # ------------------------------------------------------------------
    ax = agent.s.add_node("CapabilityAxis", {
        "is_axis": 1.0,
        "saturation": 0.2,
        "shortfall": 0.7,
        "mf_stall": 0,
        "capability_keys": ["alpha", "beta"],
    })
    for key_name in ("alpha", "beta"):
        ck = agent.s.add_node("CapKey", {"name": key_name})
        _edge(agent, ax, "requires_key", ck)
    imp = agent.s.add_node("Impasse", {
        "order": 3,
        "acted_order": 3,
        "kind": "escalation",
        "resolved": False,
    })
    _edge(agent, imp, "about_axis", ax)
    _edge(agent, imp, "needs_decomposition", ax)

    agent.tick()
    children = list(agent.inner.neighbours(ax, "decomposes_into"))
    assert len(children) == 2
    assert agent.s.node(imp)["attrs"]["dc_handled"] == 1
    assert agent.s.node(imp)["attrs"]["dc_outcome"] == "partitioned"

    agent.s.set_attr(children[0], "saturation", 0.8)
    agent.s.set_attr(children[1], "saturation", 0.4)
    agent.tick()
    assert agent.s.node(ax)["attrs"]["child_mean_saturation"] == pytest.approx(0.6)

    # ------------------------------------------------------------------
    # Chain 4 (B1): Idle epochs -> offline replay & SemanticSupport
    # ------------------------------------------------------------------
    for idx, (ev_key, cue_key, schema_name) in enumerate([
        ("ev_a", "cue_a", "schema_alpha"),
        ("ev_b", "cue_b", "schema_beta"),
    ]):
        m_ctx = agent.s.add_node("MemoryContext", {"context_key": f"room_{idx}"})
        m_schema = agent.s.add_node("MemorySchema", {"name": schema_name})
        ev = agent.s.add_node("EpisodicEvent", {
            "event_key": ev_key,
            "cue_key": cue_key,
            "epoch": 1.0,
            "salience": 0.7,
            "surprise": 0.8,
            "value": 0.6,
            "observation_status": "observed",
            "provenance_kind": "perceived",
            "state_kind": "world_state",
            "state_summary": "experienced world state",
        })
        _edge(agent, agent.agent, "experienced_event", ev)
        _edge(agent, ev, "in_context", m_ctx)
        _edge(agent, ev, "instantiates_schema", m_schema)

    agent.tick()
    assert len(_nodes(agent, "Episode")) == 2

    for epoch in range(2, 14):
        sample = agent.s.add_node("NetworkModeSample", {
            "epoch": float(epoch),
            "exteroceptive_load": 0.0,
            "task_demand": 0.0,
            "interoceptive_urgency": 0.0,
            "uncertainty": 0.0,
            "idle_duration": 8.0,
            "status": "raw",
        })
        _edge(agent, agent.agent, "has_network_mode_sample", sample)
        agent.tick()

    assert len(list(agent.inner.neighbours(agent.agent, "has_memory_clock"))) == 1
    supports = _nodes(agent, "SemanticSupport")
    assert len(supports) >= 1
    assert sum(agent.s.node(s)["attrs"]["support_count"] for s in supports) >= 2.0


def test_cognition_on_64_epoch_system_two_requests_bounded_by_funded_total():
    """P2.A5.5: Over a 64-epoch run on boot_cognition_on(), total System-2 requests
    drawn against ThinkingBudget are <= the funded total (initial capacity + 64 * refill_per_epoch)."""
    agent = boot_cognition_on()
    enabled_budgets = [
        nid
        for nid in agent.inner.neighbours(agent.agent, "has_thinking_budget")
        if agent.s.node(nid)["attrs"].get("enabled") == 1.0
    ]
    assert len(enabled_budgets) == 1
    budget = enabled_budgets[0]

    # Set tight budget parameters so a 64-epoch stream exercises both refilling and denials
    agent.s.set_attr(budget, "capacity", 8.0)
    agent.s.set_attr(budget, "remaining", 8.0)
    agent.s.set_attr(budget, "refill_per_epoch", 1.0)
    agent.s.set_attr(budget, "last_refill_epoch", 0.0)

    isb_policies = [
        nid
        for nid in agent.inner.neighbours(agent.agent, "has_impasse_simulation_policy")
        if agent.s.node(nid)["attrs"].get("enabled") == 1.0
    ]
    csch_policies = [
        nid
        for nid in agent.inner.neighbours(agent.agent, "has_consolidation_scheduler_policy")
        if agent.s.node(nid)["attrs"].get("enabled") == 1.0
    ]
    agent.s.set_attr(isb_policies[0], "cost", 2.0)
    agent.s.set_attr(csch_policies[0], "cost", 2.0)
    agent.s.set_attr(csch_policies[0], "cooldown_epochs", 1.0)

    m_ctx = agent.s.add_node("MemoryContext", {"context_key": "room_budget"})
    m_schema = agent.s.add_node("MemorySchema", {"name": "schema_budget"})
    ev = agent.s.add_node(
        "EpisodicEvent",
        {
            "event_key": "ev_budget",
            "cue_key": "cue_budget",
            "epoch": 1.0,
            "salience": 0.7,
            "surprise": 0.8,
            "value": 0.6,
            "observation_status": "observed",
            "provenance_kind": "perceived",
            "state_kind": "world_state",
            "state_summary": "experienced world state",
        },
    )
    _edge(agent, agent.agent, "experienced_event", ev)
    _edge(agent, ev, "in_context", m_ctx)
    _edge(agent, ev, "instantiates_schema", m_schema)

    total_mints = 0
    prev_cycle_ids: set[int] = set()
    for epoch in range(1, 65):
        sample = agent.s.add_node(
            "NetworkModeSample",
            {
                "epoch": float(epoch),
                "exteroceptive_load": 0.0,
                "task_demand": 0.0,
                "interoceptive_urgency": 0.0,
                "uncertainty": 0.0,
                "idle_duration": 8.0,
                "status": "raw",
            },
        )
        _edge(agent, agent.agent, "has_network_mode_sample", sample)
        agent.tick()
        cur_cycle_ids = set(_nodes(agent, "MemoryCycle"))
        new_cycles = cur_cycle_ids - prev_cycle_ids
        total_mints += len(new_cycles)
        prev_cycle_ids = cur_cycle_ids

    # Initial remaining = 8.0, 64 epochs * refill_per_epoch (1.0) = 64.0 -> max funded spend = 72.0.
    # At cost = 2.0 per request, at most 36 requests can be funded across 64 epochs.
    funded_total_requests = (8.0 + 64.0 * 1.0) / 2.0
    assert 1 <= total_mints <= funded_total_requests
    assert len(_nodes(agent, "ThinkingBudgetDenial")) >= 1

