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
from substrate.boot_profiles import (COGNITION_ON_SEEDS, boot_cognition_on,
                                     load_conversation_seed_profile)
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


def _p4_tick(agent):
    for _ in range(64):
        if not agent.inner.run_rules(10000):
            return
    raise AssertionError("P4 cognition-on graph did not reach a fixpoint")


def _p4_regular_window(agent, window_id="profile-denial", epoch=4.0):
    base = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
            ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]
    frames = [base]
    for ix in range(1, 5):
        frames.append([["cell", row[1] + ix, row[2], row[3]] for row in base])
    source = agent.s.add_node("Observation", {
        "key": f"source:{window_id}", "status": "decoded",
        "dim_checked": 1, "dim_explained": 0, "decoded_epoch": epoch,
    })
    _edge(agent, agent.agent, "observed", source)
    window = agent.s.add_node("TemporalSequenceWindow", {
        "window_id": window_id, "owner_id": "agent-root", "source_epoch": epoch,
        "first_event_id": f"event:{window_id}:0", "last_event_id": f"event:{window_id}:n",
        "frames": frames, "dim_types": ["pred", "coord:r", "coord:c", "val"],
        "regular_sampling": True, "status": "ready",
    })
    _edge(agent, agent.agent, "has_temporal_window", window)
    _edge(agent, window, "escalates_observation", source)
    return window, source


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
        ("has_cognition_planner_policy", "CognitionPlannerPolicy"),
        ("has_imagined_arbitration_policy", "ImaginedArbitrationPolicy"),
        ("has_decomposition_completion_policy", "DecompositionCompletionPolicy"),
        ("has_analog_imagery_policy", "AnalogImageryPolicy"),
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
    # P4 experimental adapters are cognition-on-only and remain inert by default.
    for node_type in ("QualiaShapeMintPolicy", "CognitionSignaturePolicy",
                      "SimilarityRecallPolicy", "CognitionAperturePolicy",
                      "TemporalEscalationPolicy", "ThoughtManifoldPolicy"):
        nodes = _nodes(agent, node_type)
        assert len(nodes) == 1
        assert agent.s.node(nodes[0])["attrs"].get("enabled") == 0.0
    manifold_policy = _nodes(agent, "CognitionManifoldPolicy")
    assert len(manifold_policy) == 1
    assert agent.s.node(manifold_policy[0])["attrs"].get("enabled") == 0.0
    assert len(list(agent.inner.neighbours(agent.agent, "has_tolerance"))) == 5


def test_p4_default_and_conversation_isolation():
    p4_only = {"qualia_shape_mint", "cognition_signature", "similarity_recall",
               "cognition_aperture", "temporal_escalation", "cognition_manifold",
               "thought_manifold"}
    default = WorldAdapter()
    assert p4_only.isdisjoint(installed_seeds(default.s))
    conversation = WorldAdapter(seeds=())
    report = load_conversation_seed_profile(conversation)
    assert report.get("failed") in (None, [])
    assert p4_only.isdisjoint(installed_seeds(conversation.s))
    default.close()
    conversation.close()


def test_p5_default_and_conversation_isolation():
    p5 = {"cognition_planner", "imagined_candidate_arbitration",
          "decomposition_completion", "analog_imagery"}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert p5.isdisjoint(installed_seeds(default.s))
    assert p5.isdisjoint(installed_seeds(conversation.s))
    default.close()
    conversation.close()


def test_p5_planner_arbitration_receipt_chain():
    from tests.test_cognition_multistep_planner_migrated import (
        _imagined_arbitration_case, _run_to_fixpoint,
    )
    agent = boot_cognition_on()
    for node_type in ("CognitionPlannerPolicy", "ImaginedArbitrationPolicy",
                      "DecompositionCompletionPolicy", "AnalogImageryPolicy"):
        enabled = [node for node in _nodes(agent, node_type)
                   if agent.s.node(node)["attrs"].get("enabled") == 1.0]
        assert enabled, f"cognition-on profile did not enable {node_type}"
    # Existing focused mechanism fixture supplies an exact two-step model;
    # this integration gate confirms the same planner/arbitration closure is
    # available in the cognition-on profile.
    adapter, request, context, _policy = _imagined_arbitration_case([
        ("s0", "prepare", "middle", 2), ("middle", "finish", "goal", 2),
    ])
    candidate = adapter.inner.neighbours(request, "has_imagined_plan_candidate")[0]
    revision = adapter.inner.neighbours(request, "has_system_two_decision_revision")[0]
    action_request = adapter.inner.neighbours(revision, "has_action_request")[0]
    attrs = adapter.s.node(action_request)["attrs"]
    adapter.inner.set_attr(action_request, "status", "emitted")
    adapter.inner.set_attr(action_request, "sink_receipt_id", "p5-profile-receipt")
    authorization = adapter.s.add_node("ActionAuthorization", {
        "status": "consumed", "request_id": attrs["request_id"],
        "source_epoch": attrs["source_epoch"], "action_key": attrs["action_key"],
    })
    adapter.inner.add_edge_unchecked(action_request, "has_action_authorization", authorization)
    observation = adapter.s.add_node("ImaginedActionObservation", {
        "status": "verified", "action_request_id": attrs["request_id"],
        "source_epoch": attrs["source_epoch"], "sink_receipt_id": "p5-profile-receipt",
        "observed_state_key": "middle",
    })
    adapter.inner.add_edge_unchecked(action_request, "has_action_observation", observation)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(candidate)["attrs"]["grounding_status"] == "grounded"
    assert adapter.s.node(context)["attrs"]["status"] == "committed"
    adapter.close()
    agent.close()


def test_p5_stop_at_native_sink():
    from tests.test_response_inhibition_migrated import _native_graph, _request, _tick
    substrate, agent = _native_graph(enabled=True)
    request, authorization, stop = _request(substrate, agent)
    _tick(substrate)
    assert substrate.node(request)["attrs"]["status"] == "withheld"
    assert substrate.node(authorization)["attrs"]["status"] == "revoked"
    assert substrate.node(stop)["attrs"]["status"] == "withheld"


def test_p4_budget_shared():
    agent = boot_cognition_on()
    budgets = [node for node in agent.inner.neighbours(agent.agent, "has_thinking_budget")
               if agent.s.node(node)["type"] == "ThinkingBudget"
               and agent.s.node(node)["attrs"].get("enabled") == 1.0]
    assert len(budgets) == 1
    budget = budgets[0]
    agent.s.set_attr(budget, "enabled", 1.0)
    agent.s.set_attr(budget, "remaining", 1.0)
    agent.s.set_attr(budget, "refill_per_epoch", 0.0)
    agent.s.set_attr(budget, "last_refill_epoch", 4.0)
    mode = _nodes(agent, "NetworkModeState")[0]
    agent.s.set_attr(mode, "epoch", 4.0)

    # A P4 Observer question consumes one unit from the profile's shared node.
    policy = _nodes(agent, "CognitionAperturePolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    observer = agent.s.add_node("Observer", {
        "name": "profile-shared-budget", "resolves": ["pred"], "ap_full": ["pred"],
        "ap_scope_n": 0.0, "ap_gen": 0.0, "ap_chosen_dwell": 1.0,
        "ap_question_after": 1.0,
    })
    aperture = agent.s.add_node("Aperture", {"name": "chosen", "resolves": []})
    _edge(agent, observer, "chose_aperture", aperture)
    source = agent.s.add_node("CognitionApertureSource", {
        "adapter_id": "reading", "source_key": "shared-budget-source",
        "owner_id": "profile-shared-budget", "frame_id": "frame:shared",
        "source_epoch": 4.0, "value_kind": "integer", "value": 1,
        "missing": False, "tolerance": 0, "authority": "chosen",
        "voi_status": "positive", "voi_evidence_id": "voi:shared",
        "dimension_id": "observer:reading",
    })
    _edge(agent, agent.agent, "has_cognition_aperture_source", source)
    _edge(agent, source, "applies_to_observer", observer)
    _p4_tick(agent)
    aperture_requests = [node for node in _nodes(agent, "ThinkingBudgetRequest")
                         if agent.s.node(node)["attrs"].get("requester_kind")
                         == "cognition_aperture_probe"]
    assert len(aperture_requests) == 1
    assert _nodes(agent, "ThinkingBudgetDenial") == []
    assert agent.s.node(budget)["attrs"]["remaining"] == pytest.approx(0.0)
    assert list(agent.inner.neighbours(aperture_requests[0], "draws_on_thinking_budget")) == [budget]

    # Temporal escalation is then denied against that same exhausted budget.
    temporal_policy = _nodes(agent, "TemporalEscalationPolicy")[0]
    agent.s.set_attr(temporal_policy, "enabled", 1.0)
    window, _source = _p4_regular_window(agent, epoch=4.0)
    _p4_tick(agent)
    temporal_requests = [node for node in _nodes(agent, "ThinkingBudgetRequest")
                         if agent.s.node(node)["attrs"].get("requester_kind")
                         == "temporal_escalation"]
    assert len(temporal_requests) == 1
    assert agent.s.node(temporal_requests[0])["attrs"]["status"] == "denied"
    assert list(agent.inner.neighbours(temporal_requests[0], "draws_on_thinking_budget")) == [budget]
    assert agent.s.node(window)["attrs"]["status"] != "time_inferred"
    agent.close()


def test_p4_profile_chain():
    agent = boot_cognition_on()
    mode = _nodes(agent, "NetworkModeState")[0]
    agent.s.set_attr(mode, "epoch", 4.0)
    budget = next(node for node in agent.inner.neighbours(agent.agent, "has_thinking_budget")
                  if agent.s.node(node)["type"] == "ThinkingBudget"
                  and agent.s.node(node)["attrs"].get("enabled") == 1.0)
    for node_type in ("QualiaShapeMintPolicy", "CognitionSignaturePolicy",
                      "SimilarityRecallPolicy"):
        policy = _nodes(agent, node_type)[0]
        agent.s.set_attr(policy, "enabled", 1.0)
    agent.s.set_attr(budget, "enabled", 1.0)
    agent.s.set_attr(budget, "remaining", 8.0)
    agent.s.set_attr(budget, "refill_per_epoch", 0.0)
    agent.s.set_attr(budget, "last_refill_epoch", 4.0)

    observation = agent.s.add_node("Observation", {
        "key": "p4-profile-chain", "status": "decoded", "outcome_status": "verified",
        "outcome_id": "p4-profile-chain-outcome", "coordinate": [0, 1, 5, 14],
        "order": 2, "owner_id": "profile-owner", "frame_id": "profile-frame",
        "source_epoch": 4.0, "decoded_epoch": 4.0, "valence": 1.0,
        "reading": "profile-verified-reading",
    })
    _edge(agent, agent.agent, "observed", observation)
    _p4_tick(agent)

    shapes = _nodes(agent, "QualiaShape")
    assert len(shapes) == 1
    assert agent.s.node(shapes[0])["attrs"]["evidence_status"] == "verified"
    descriptors = [node for node in _nodes(agent, "CognitionSignatureDescriptor")
                   if agent.s.node(node)["attrs"].get("source_id") == "qualia_shape"
                   and agent.s.node(node)["attrs"].get("status") == "current"]
    assert descriptors
    results = [node for node in _nodes(agent, "SimilarityRecallResult")
               if agent.s.node(node)["attrs"].get("observation_key") == '"p4-profile-chain"']
    assert len(results) == 1
    result_attrs = agent.s.node(results[0])["attrs"]
    assert result_attrs["status"] == "accepted_verified_exact"
    assert list(agent.inner.neighbours(results[0], "verified_signature"))
    receipts = [node for node in _nodes(agent, "CognitionSignatureVerificationReceipt")
                if agent.s.node(node)["attrs"].get("verifier_kind")
                == "verified_shape_outcome"]
    assert receipts

    # Feed a measured numeric GWM transition through the native manifold path.
    manifold_policy = _nodes(agent, "CognitionManifoldPolicy")[0]
    episode = _nodes(agent, "CognitionManifoldEpisode")[0]
    agent.s.set_attr(manifold_policy, "enabled", 1.0)
    agent.s.set_attr(manifold_policy, "future_manifold_projection_budget", 2.0)
    agent.s.set_attr(manifold_policy, "future_manifold_physical_horizon", 2.0)
    agent.s.set_attr(episode, "future_manifold_target", [[1.0], [2.0]])
    agent.s.set_attr(episode, "future_manifold_bounds", [[0.0], [0.0]])
    request = agent.s.add_node("SimulationRequest", {"status": "completed", "horizon": 2.0})
    trajectory = agent.s.add_node("PredictionTrajectory", {})
    state = agent.s.add_node("PredictedBeliefState", {"uncertainty": 0.0})
    transition = agent.s.add_node("TransitionHypothesis", {
        "future_manifold_supported": True, "transition_id": "profile-transition",
        "model_id": "profile-model", "model_epoch": 4,
        "future_manifold_values": [[1.0], [2.0]], "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]], "future_manifold_effort": [0.0, 0.0],
    })
    for src, edge, tgt in ((agent.agent, "has_simulation_request", request),
                           (request, "has_prediction_trajectory", trajectory),
                           (trajectory, "has_predicted_belief_state", state),
                           (state, "generated_by_transition", transition)):
        _edge(agent, src, edge, tgt)
    _p4_tick(agent)
    candidates = _nodes(agent, "CognitionManifoldCandidate")
    assert len(candidates) == 1
    assert agent.s.node(candidates[0])["attrs"]["projection_resolved"] == 1.0
    assert len(_nodes(agent, "CognitionManifoldFeasibilityReceipt")) == 1

    # The same profile denies a sealed temporal rung after the shared budget is exhausted.
    temporal_policy = _nodes(agent, "TemporalEscalationPolicy")[0]
    agent.s.set_attr(temporal_policy, "enabled", 1.0)
    agent.s.set_attr(budget, "remaining", 0.0)
    window, source = _p4_regular_window(agent, window_id="profile-chain-denied", epoch=4.0)
    _p4_tick(agent)
    temporal_requests = [node for node in _nodes(agent, "ThinkingBudgetRequest")
                         if agent.s.node(node)["attrs"].get("requester_kind")
                         == "temporal_escalation"]
    assert len(temporal_requests) == 1
    assert agent.s.node(temporal_requests[0])["attrs"]["status"] == "denied"
    assert agent.s.node(window)["attrs"]["status"] != "time_inferred"
    assert agent.s.node(source)["attrs"].get("dim_explained") == 0
    agent.close()


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

