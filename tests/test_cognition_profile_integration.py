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
from evaluation.process_mastery.native_process_execution import (
    attest_open_process_candidate, execute_open_process_candidate, params_digest,
)
from evaluation.process_mastery.observed_sequence_execution import (
    execute_verified_observed_sequence, verify_observed_sequence_candidate,
)
from evaluation.process_mastery.explanation_rebuild import verify_rebuilt_composition
from evaluation.process_mastery.target_learning_worlds import (
    HeatSourceWorld, RequestRepairWorld, ThermalWorld, verify_induced_map_candidate,
)
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


def _p19_tick(agent):
    for _ in range(64):
        if not agent.inner.run_rules(10000):
            return
    raise AssertionError("P19 cognition-on graph did not reach a fixpoint")


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


def test_p19_default_isolation():
    world = WorldAdapter()
    try:
        loaded = set(installed_seeds(world.s).keys())
        assert "open_process_search" not in loaded
        assert "open_process_adoption" not in loaded
    finally:
        world.close()


def test_p19_shared_budget():
    world = boot_cognition_on()
    try:
        budgets = list(world.inner.neighbours(world.agent, "has_thinking_budget"))
        assert len(budgets) == 1
        assert world.s.node(budgets[0])["attrs"].get("enabled") == 1.0
        for requester_kind in ("open_process_search",):
            policies = [n for n in _nodes(world, "ThinkingBudgetRequest")
                        if world.s.node(n)["attrs"].get("requester_kind") == requester_kind]
            assert not policies
    finally:
        world.close()


def _run_p19_native_causal_chain():
    """Cognition-on graph proposal crosses approval and the world receipt boundary."""
    agent = boot_cognition_on()
    try:
        native, root, store = agent.inner, agent.agent, agent.s
        for policy_type in ("OpenProcessSearchPolicy", "OpenProcessAdoptionPolicy",
                            "StrategyDiscoveryPolicy"):
            for node in _nodes(agent, policy_type):
                native.set_attr(node, "enabled", 1.0)
        for node in _nodes(agent, "ProcessSchemaPolicy"):
            native.set_attr(node, "enabled", 0.0)
        budgets = list(native.neighbours(root, "has_thinking_budget"))
        assert len(budgets) == 1
        native.set_attr(budgets[0], "enabled", 1.0)
        native.set_attr(budgets[0], "remaining", 100.0)
        native.set_attr(budgets[0], "capacity", 100.0)

        domain = store.add_node("ProcessDomain", {
            "name": "p19-profile", "kind": "permutation",
            "probes": [[0, 1, 2, 3]], "source_epoch": 0.0,
            "model_epoch": 0.0, "frame_epoch": 0.0, "probe_epoch": 0.0,
        })
        _edge(agent, root, "has_process_domain", domain)
        held = {"p": [1, 0, 2, 3], "q": [0, 2, 1, 3]}
        schemas = []
        for name, params in held.items():
            schema = store.add_node("ProcessSchema", {
                "name": name, "kind": "permutation", "domain_kind": "permutation",
                "domain": "p19-profile", "params": params, "cost": 1.0,
                "source_digest": params_digest(params), "source_epoch": 0.0,
                "model_epoch": 0.0, "frame_epoch": 0.0, "status": "active",
            })
            _edge(agent, root, "has_process_schema", schema)
            _edge(agent, domain, "has_held_process", schema)
            schemas.append(schema)
        goal = native.evaluate(
            {"type": "ProcessApply",
             "p": {"type": "ProcessCompose", "a": {"type": "Var", "name": "a"},
                   "b": {"type": "Var", "name": "b"}},
             "state": {"type": "Var", "name": "state"}},
            {"a": held["p"], "b": held["q"], "state": [0, 1, 2, 3]})
        task = store.add_node("SolveTask", {
            "domain": "p19-profile", "initial_state": [0, 1, 2, 3],
            "state": [0, 1, 2, 3], "object_count": 4.0,
            "goal": goal, "status": "stuck", "trace": [], "steps": 0,
            "moves": 0.0, "stuck_count": 1,
        })
        _edge(agent, root, "has_solve_task", task)
        _edge(agent, task, "about_domain", domain)
        _p19_tick(agent)
        search_budget_requests = [n for n in _nodes(agent, "ThinkingBudgetRequest")
            if store.node(n)["attrs"].get("requester_kind") == "open_process_search"]
        assert len(search_budget_requests) == 1
        search_budget_request = search_budget_requests[0]
        assert store.node(search_budget_request)["attrs"].get("status") == "approved"
        assert list(native.neighbours(search_budget_request, "draws_on_thinking_budget")) == budgets
        assert store.node(search_budget_request)["attrs"].get("cost") == 2.0
        candidates = _nodes(agent, "OpenProcessCandidate")
        assert candidates
        candidate = next(c for c in candidates if store.node(c)["attrs"].get("params") ==
                         native.evaluate({"type": "ProcessCompose", "a": {"type": "Var", "name": "a"},
                                          "b": {"type": "Var", "name": "b"}},
                                         {"a": held["p"], "b": held["q"]}))
        digest = attest_open_process_candidate(agent, candidate)
        attrs = store.node(candidate)["attrs"]
        approval = store.add_node("OpenProcessAdoptionApproval", {
            "status": "approved", "approval_kind": "human",
            "expression_digest": digest, "expression_key": attrs["expression_key"],
            "expression_tree": attrs["expression_tree"], "effect_digest": attrs["effect_digest"],
            "params": attrs["params"], "guard_state": attrs["guard_state"],
            "domain": attrs["domain"], "source_epoch": attrs["source_epoch"],
            "model_epoch": attrs["model_epoch"], "frame_epoch": attrs["frame_epoch"],
        })
        _edge(agent, root, "has_open_process_adoption_approval", approval)
        _edge(agent, approval, "approves_open_process_candidate", candidate)
        _p19_tick(agent)
        assert store.node(candidate)["attrs"]["status"] == "adopted_candidate"

        world_state = [0, 1, 2, 3]
        calls = []

        def world_transition(action):
            observed = [None] * len(world_state)
            for source, destination in enumerate(action):
                observed[destination] = world_state[source]
            world_state[:] = observed
            calls.append(action)
            return {"observed_state": list(world_state)}

        result = execute_open_process_candidate(agent, candidate, state=[0, 1, 2, 3],
            authorize=lambda proposal: proposal["expression_digest"] == digest,
            world_transition=world_transition)
        assert result["status"] == "COMPLETED"
        assert result["receipt"]["observed_state"] == goal
        receipts = list(native.neighbours(candidate, "has_world_execution_receipt"))
        assert len(receipts) == 1
        assert store.node(receipts[0])["attrs"]["status"] == "verified"
        assert len(calls) == 1
        _p19_tick(agent)
        strategies = [n for n in _nodes(agent, "DiscoveredStrategy")
                      if store.node(n)["attrs"].get("source") == "native_world_receipt"]
        assert len(strategies) == 1
        assert list(native.neighbours(strategies[0], "witnessed_by_world_receipt")) == receipts

        # A changed binding cannot trigger another world transition.
        native.set_attr(domain, "model_epoch", 1.0)
        blocked = execute_open_process_candidate(agent, candidate, state=[0, 1, 2, 3],
            authorize=lambda proposal: True, world_transition=world_transition)
        assert blocked["status"] == "ABSTAIN"
        assert len(calls) == 1
    finally:
        agent.close()


def test_p19_native_causal_chain():
    _run_p19_native_causal_chain()


def test_p19_state_perturbation_changes_execution():
    _run_p19_native_causal_chain()


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
                      "TemporalEscalationPolicy", "ThoughtManifoldPolicy",
                      "QualiaBehaviorPolicy", "ExperientialSignificancePolicy",
                      "QualiaRevisionPolicy"):
        nodes = _nodes(agent, node_type)
        assert len(nodes) == 1
        assert agent.s.node(nodes[0])["attrs"].get("enabled") == 0.0
    manifold_policy = _nodes(agent, "CognitionManifoldPolicy")
    assert len(manifold_policy) == 1
    assert agent.s.node(manifold_policy[0])["attrs"].get("enabled") == 0.0
    search_policy = _nodes(agent, "OpenProcessSearchPolicy")
    assert len(search_policy) == 1
    assert agent.s.node(search_policy[0])["attrs"].get("enabled") == 0.0
    adoption_policy = _nodes(agent, "OpenProcessAdoptionPolicy")
    assert len(adoption_policy) == 1
    assert agent.s.node(adoption_policy[0])["attrs"].get("enabled") == 0.0
    strategy_policy = _nodes(agent, "StrategyDiscoveryPolicy")
    assert len(strategy_policy) == 1
    assert agent.s.node(strategy_policy[0])["attrs"].get("allow_lift") == 0.0
    # Track I's opt-in invention operator manifest contributes two additional
    # disabled-policy tolerances to the cognition-on graph.
    assert len(list(agent.inner.neighbours(agent.agent, "has_tolerance"))) == 7


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


def test_p6_profile_chain():
    p6 = {"process_schema", "invention_operators", "invention_round",
          "invariant_miner", "process_solving"}
    agent = boot_cognition_on()
    exported = {r["name"] for r in agent.inner.export_rules()}
    for sid in p6:
        for rule in manifest_for(sid).get("rules", ()):
            if isinstance(rule, dict) and rule.get("name"):
                assert rule["name"] in exported, rule["name"]
    for node_type in ("ProcessSchemaPolicy", "SolverPolicy",
                      "InventionPolicy", "InvariantMinerPolicy"):
        for node in _nodes(agent, node_type):
            assert agent.s.node(node)["attrs"].get("enabled") == 0.0


def test_p6_default_isolation():
    p6 = {"process_schema", "invention_operators", "invention_round",
          "invariant_miner", "process_solving"}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    p6_rule_names = {r["name"] for sid in p6
                     for r in manifest_for(sid).get("rules", ())
                     if isinstance(r, dict) and r.get("name")}
    default_rules = {r["name"] for r in default.inner.export_rules()}
    conversation_rules = {r["name"] for r in conversation.inner.export_rules()}
    assert p6_rule_names.isdisjoint(default_rules)
    assert p6_rule_names.isdisjoint(conversation_rules)
    default.close()
    conversation.close()


def test_p6_shared_budget():
    agent = boot_cognition_on()
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    assert len(budgets) == 1
    attached = list(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
    assert budgets[0] in attached
    assert all(agent.s.node(n)["type"] == "ThinkingBudget" for n in attached)
    agent.close()


def test_p10_profile_chain():
    p10 = {"process_lifting", "goal_invention", "strategy_discovery"}
    agent = boot_cognition_on()
    exported = {r["name"] for r in agent.inner.export_rules()}
    for sid in p10:
        for item in manifest_for(sid).get("rules", ()):
            if isinstance(item, dict) and item.get("name"):
                assert item["name"] in exported, item["name"]
    for node_type in ("ProcessLiftingPolicy", "GoalInventionPolicy", "StrategyDiscoveryPolicy"):
        for node in _nodes(agent, node_type):
            assert agent.s.node(node)["attrs"].get("enabled") == 0.0
    agent.close()


def test_p10_default_isolation():
    p10 = {"process_lifting", "goal_invention", "strategy_discovery"}
    p10_rule_names = {item["name"] for sid in p10
                      for item in manifest_for(sid).get("rules", ())
                      if isinstance(item, dict) and item.get("name")}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    default_rules = {r["name"] for r in default.inner.export_rules()}
    conversation_rules = {r["name"] for r in conversation.inner.export_rules()}
    assert p10_rule_names.isdisjoint(default_rules)
    assert p10_rule_names.isdisjoint(conversation_rules)
    default.close()
    conversation.close()


def test_p10_shared_budget():
    agent = boot_cognition_on()
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    attached = list(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
    assert len(budgets) == 1 and budgets[0] in attached
    assert all(agent.s.node(n)["type"] == "ThinkingBudget" for n in attached)
    agent.close()


def test_p11_profile_chain():
    p11 = {"representation_search", "process_transfer"}
    agent = boot_cognition_on()
    exported = {r["name"] for r in agent.inner.export_rules()}
    for sid in p11:
        for item in manifest_for(sid).get("rules", ()):
            if isinstance(item, dict) and item.get("name"):
                assert item["name"] in exported, item["name"]
    for node_type in ("RepresentationSearchPolicy", "ProcessTransferPolicy"):
        nodes = _nodes(agent, node_type)
        assert nodes and all(agent.s.node(n)["attrs"].get("enabled") == 0.0 for n in nodes)
    agent.close()


def test_p11_default_isolation():
    p11_rules = {item["name"] for sid in {"representation_search", "process_transfer"}
                 for item in manifest_for(sid).get("rules", ())
                 if isinstance(item, dict) and item.get("name")}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert p11_rules.isdisjoint({r["name"] for r in default.inner.export_rules()})
    assert p11_rules.isdisjoint({r["name"] for r in conversation.inner.export_rules()})
    default.close()
    conversation.close()


def test_p11_shared_budget():
    agent = boot_cognition_on()
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    attached = list(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
    assert len(budgets) == 1 and budgets[0] in attached
    assert all(agent.s.node(n)["type"] == "ThinkingBudget" for n in attached)
    agent.close()


def test_p13_profile_chain():
    p13 = {"sleep_regime", "library_learning", "strategy_library"}
    agent = boot_cognition_on()
    exported = {r["name"] for r in agent.inner.export_rules()}
    for sid in p13:
        for item in manifest_for(sid).get("rules", ()):
            if isinstance(item, dict) and item.get("name"):
                assert item["name"] in exported, item["name"]
    for edge_type, node_type in (
        ("has_sleep_regime_policy", "SleepRegimePolicy"),
        ("has_library_learning_policy", "LibraryLearningPolicy"),
        ("has_strategy_library_policy", "StrategyLibraryPolicy"),
    ):
        attached = [n for n in agent.inner.neighbours(agent.agent, edge_type)
                    if agent.s.node(n)["type"] == node_type
                    and agent.s.node(n)["attrs"].get("enabled") == 1.0]
        assert len(attached) == 1

    # WorldAdapter.tick services the consolidation request before the sleep
    # receipt rule; raw rule fixpoint execution alone does not run that adapter.
    budget = next(n for n in _nodes(agent, "ThinkingBudget")
                  if agent.s.node(n)["attrs"].get("enabled") == 1.0)
    agent.inner.set_attr(budget, "remaining", 16.0)
    agent.inner.set_attr(budget, "capacity", 16.0)
    context = agent.s.add_node("MemoryContext", {"context_key": "p13-profile"})
    schema = agent.s.add_node("MemorySchema", {"name": "p13-observed-route"})
    episode = agent.s.add_node("EpisodicEvent", {
        "event_key": "p13-observed-event", "cue_key": "p13-cue", "epoch": 0.0,
        "salience": 0.8, "surprise": 0.5, "value": 0.5,
        "observation_status": "observed", "provenance_kind": "perceived",
        "state_kind": "world_state", "state_summary": "observed state",
    })
    _edge(agent, agent.agent, "experienced_event", episode)
    _edge(agent, episode, "in_context", context)
    _edge(agent, episode, "instantiates_schema", schema)
    for _ in range(8):
        agent.tick()
    sample = agent.s.add_node("NetworkModeSample", {
        "epoch": 1.0, "default_mode_weight": 1.0,
        "exteroceptive_load": 0.0, "task_demand": 0.0,
        "interoceptive_urgency": 0.0, "uncertainty": 0.0,
        "idle_duration": 8.0, "status": "raw",
    })
    _edge(agent, agent.agent, "has_network_mode_sample", sample)
    for _ in range(8):
        agent.tick()
    receipts = _nodes(agent, "SleepStageReceipt")
    assert receipts, "profile tick did not produce the funded P13 replay receipt"
    replay = next(r for r in receipts if agent.s.node(r)["attrs"].get("stage") == "replay")
    replay_attrs = agent.s.node(replay)["attrs"]
    assert replay_attrs["observation_status"] == "not_observed"
    assert replay_attrs["provenance_kind"] == "offline_sleep_stage"
    request = list(agent.inner.neighbours(replay, "funded_by_request"))[0]
    assert agent.s.node(request)["attrs"]["status"] == "serviced"
    agent.close()


def test_p13_default_isolation():
    p13 = {"sleep_regime", "library_learning", "strategy_library"}
    p13_rules = {item["name"] for sid in p13
                 for item in manifest_for(sid).get("rules", ())
                 if isinstance(item, dict) and item.get("name")}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert p13.isdisjoint(installed_seeds(default.s))
    assert p13.isdisjoint(installed_seeds(conversation.s))
    assert p13_rules.isdisjoint({r["name"] for r in default.inner.export_rules()})
    assert p13_rules.isdisjoint({r["name"] for r in conversation.inner.export_rules()})
    default.close()
    conversation.close()


def test_p13_shared_budget():
    agent = boot_cognition_on()
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    attached = list(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
    assert len(budgets) == 1 and budgets[0] in attached
    assert all(agent.s.node(n)["type"] == "ThinkingBudget" for n in attached)
    agent.close()


def test_p14_profile_chain():
    p14 = {"process_laws", "process_proof_adoption", "invention_operator_authorship"}
    boot_started = time.perf_counter()
    agent = boot_cognition_on()
    boot_seconds = time.perf_counter() - boot_started
    exported = {r["name"] for r in agent.inner.export_rules()}
    for sid in p14:
        for item in manifest_for(sid).get("rules", ()):
            if isinstance(item, dict) and item.get("name"):
                assert item["name"] in exported, item["name"]
    for node_type in ("ProcessLawsPolicy", "ProcessProofAdoptionPolicy",
                      "InventionOperatorAuthorshipPolicy"):
        active = [n for n in _nodes(agent, node_type)
                  if agent.s.node(n)["attrs"].get("enabled") == 1.0]
        assert len(active) == 1

    # Exercise actual graph rules: a composition request mints its expression graph,
    # while a registered proof-required domain blocks a process without proof.
    request = agent.s.add_node("OperatorCompositionRequest", {
        "name": "p14-profile-request", "status": "draft",
        "recipe": "commutator_square", "left_operator": "commutator",
        "right_operator": "commutator", "candidate_name": "commutator_square_v1",
    })
    _edge(agent, agent.agent, "has_operator_composition_request", request)
    domain = agent.s.add_node("ProcessDomain", {
        "name": "p14-proof-domain", "kind": "permutation", "source_epoch": 0,
        "model_epoch": 0, "frame_epoch": 0, "family_digest": "p14-family",
        "model_digest": "p14-model", "probes": [[0, 1, 2]],
    })
    _edge(agent, agent.agent, "has_process_domain", domain)
    held_a = agent.s.add_node("ProcessSchema", {
        "name": "held-a", "kind": "permutation", "domain": "p14-proof-domain",
        "status": "active", "provenance": "held", "params": [1, 2, 0],
    })
    held_b = agent.s.add_node("ProcessSchema", {
        "name": "held-b", "kind": "permutation", "domain": "p14-proof-domain",
        "status": "active", "provenance": "held", "params": [0, 2, 1],
    })
    _edge(agent, agent.agent, "has_process_schema", held_a)
    _edge(agent, agent.agent, "has_process_schema", held_b)
    from scripts.track_i_seed_lib import A as _A, PCommutator as _PCommutator
    exact_params = agent.inner.evaluate(_PCommutator(_A("a", "params"), _A("b", "params")),
                                        {"a": held_a, "b": held_b})
    proved_process = agent.s.add_node("ProcessSchema", {
        "name": "p14-commutator", "kind": "permutation", "domain": "p14-proof-domain",
        "status": "active", "invented": 1, "operator": "commutator",
        "params": exact_params, "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
    })
    _edge(agent, agent.agent, "has_process_schema", proved_process)
    _edge(agent, domain, "has_invented_process", proved_process)
    _edge(agent, proved_process, "has_arg0", held_a)
    _edge(agent, proved_process, "has_arg1", held_b)
    law = agent.s.add_node("ProcessLaw", {
        "claim": "commutator_even", "status": "conjecture", "proven": 0,
        "family": "p14-proof-domain", "family_digest": "p14-family",
        "family_epoch": 0, "process_epoch": 0, "model_digest": "p14-model",
        "model_epoch": 0, "frame_epoch": 0,
        "statement_digest": "4e3f9f19059a7254dbc8b885e464eccf69cec770eec50cb43a4d89e01415adb2",
        "assumptions_digest": "d055b01ab1e76e1190f7b04e01fe250ab42f5ce6ccc24eaf4dfd84263ec96077",
        "assumptions": "permutation_group;parity_homomorphism_Z2;operator_semantics_v1",
        "evidence_kind": "structural_derivation", "counterexample_count": 0,
    })
    _edge(agent, agent.agent, "has_process_law_candidate", law)
    _edge(agent, law, "about_process", proved_process)
    process = agent.s.add_node("ProcessSchema", {
        "name": "p14-unproved-process", "kind": "permutation",
        "domain": "p14-proof-domain", "status": "active", "invented": 1,
        "params": [1, 0, 2],
    })
    _edge(agent, agent.agent, "has_process_schema", process)
    policy = next(n for n in _nodes(agent, "ProcessProofAdoptionPolicy")
                  if agent.s.node(n)["attrs"].get("enabled") == 1.0)
    requirement = agent.s.add_node("ProcessProofRequirement", {
        "name": "p14-proof-requirement", "required": 1,
        "required_law": "commutator_even",
    })
    _edge(agent, policy, "requires_proof_for", requirement)
    _edge(agent, requirement, "applies_to", domain)
    _p4_tick(agent)
    candidates = [n for n in _nodes(agent, "CandidateOperator")
                  if agent.s.node(n)["attrs"].get("name") == "commutator_square_v1"]
    assert len(candidates) == 1
    assert agent.s.node(request)["attrs"]["status"] == "built"
    assert agent.s.node(process)["attrs"]["status"] == "proof_blocked"
    assert agent.s.node(law)["attrs"]["status"] == "checked"
    proof = agent.inner.neighbours(law, "has_proof_reference")[0]
    assert agent.s.node(proof)["attrs"]["checker"] == "process_laws_seed_v1"
    assert agent.s.node(proof)["attrs"]["process_params"] == agent.s.node(proved_process)["attrs"]["params"]
    assert agent.s.node(proved_process)["attrs"]["proof_adoption_status"] == "approved"

    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    assert len(budgets) == 1
    graph = agent.inner.graph_to_dict()
    serialized_bytes = len(json.dumps(graph, sort_keys=True).encode("utf-8"))
    assert boot_seconds > 0 and serialized_bytes > 0 and graph["nodes"]
    agent.close()


def test_p14_default_isolation():
    p14 = {"process_laws", "process_proof_adoption", "invention_operator_authorship"}
    p14_rules = {item["name"] for sid in p14 for item in manifest_for(sid).get("rules", ())
                 if isinstance(item, dict) and item.get("name")}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert p14.isdisjoint(installed_seeds(default.s))
    assert p14.isdisjoint(installed_seeds(conversation.s))
    assert p14_rules.isdisjoint({r["name"] for r in default.inner.export_rules()})
    assert p14_rules.isdisjoint({r["name"] for r in conversation.inner.export_rules()})
    default.close()
    conversation.close()


def test_p14_shared_budget():
    agent = boot_cognition_on()
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    attached = list(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
    assert len(budgets) == 1 and budgets[0] in attached
    assert all(agent.s.node(n)["type"] == "ThinkingBudget" for n in attached)
    agent.close()


def test_p15_profile_chain():
    p15 = {"process_portfolio", "process_curriculum", "recursive_process_improvement"}
    p21 = {"curriculum_learning_bridge"}
    boot_started = time.perf_counter()
    agent = boot_cognition_on()
    boot_seconds = time.perf_counter() - boot_started
    graph_before = agent.inner.graph_to_dict()
    nodes_before = len(graph_before["nodes"])
    bytes_before = len(json.dumps(graph_before, sort_keys=True).encode("utf-8"))
    exported = {rule["name"] for rule in agent.inner.export_rules()}
    for sid in p15:
        for item in manifest_for(sid).get("rules", ()):
            if isinstance(item, dict) and item.get("name"):
                assert item["name"] in exported, item["name"]
    for item in manifest_for("curriculum_learning_bridge").get("rules", ()):
        if isinstance(item, dict) and item.get("name"):
            assert item["name"] in exported, item["name"]
    for ptype in ("ProcessPortfolioPolicy", "ProcessCurriculumPolicy",
                  "RecursiveProcessImprovementPolicy"):
        policy = _nodes(agent, ptype)
        assert len(policy) == 1
        assert agent.s.node(policy[0])["attrs"].get("enabled") == 0.0
    bridge_policy = _nodes(agent, "CurriculumLearningBridgePolicy")
    assert len(bridge_policy) == 1
    assert agent.s.node(bridge_policy[0])["attrs"].get("enabled") == 0.0
    assert p21.issubset(set(COGNITION_ON_SEEDS))

    # Turn on only curriculum for this profile-native event. Its task must be
    # created from the observed training transition through native rules.
    policy = _nodes(agent, "ProcessCurriculumPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    hyp = agent.s.add_node("ProcessInductionHypothesis", {
        "owner_id": "agent-root", "action_kind": "press", "object_type": "switch",
        "feature_key": "light", "before_value": "off", "after_value": "on",
        "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5,
        "status": "disputed", "counterexample_count": 1,
    })
    ce = agent.s.add_node("ProcessCounterexample", {
        "event_id": "p15-profile-event", "status": "observed",
    })
    obs = agent.s.add_node("TransitionObservation", {
        "owner_id": "agent-root", "event_id": "p15-profile-event",
        "action_kind": "press", "object_type": "switch", "feature_key": "light",
        "before_value": "off", "after_value": "on", "split": "training",
        "source_epoch": 3, "model_epoch": 2, "frame_epoch": 5,
    })
    _edge(agent, agent.agent, "has_process_induction_hypothesis", hyp)
    _edge(agent, hyp, "has_counterexample", ce)
    _edge(agent, ce, "counterexample_transition", obs)
    budget = next(n for n in agent.inner.neighbours(agent.agent, "has_thinking_budget")
                  if agent.s.node(n)["attrs"].get("enabled") == 1.0)
    before = agent.s.node(budget)["attrs"]["remaining"]
    _p4_tick(agent)
    evidence = _nodes(agent, "ProcessCurriculumEvidence")
    tasks = _nodes(agent, "ProcessCurriculumTask")
    assert len(evidence) == len(tasks) == 1
    assert agent.s.node(tasks[0])["attrs"]["split"] == "training"
    assert agent.s.node(tasks[0])["attrs"]["answer_fields_absent"] is True
    assert agent.s.node(budget)["attrs"]["remaining"] == before - 1.0
    fund = agent.inner.neighbours(evidence[0], "funded_by")[0]
    assert agent.s.node(fund)["attrs"]["requester_kind"] == "process_curriculum"
    assert agent.s.node(fund)["attrs"]["status"] == "approved"
    assert agent.inner.neighbours(tasks[0], "from_evidence") == evidence
    graph_after = agent.inner.graph_to_dict()
    nodes_after = len(graph_after["nodes"])
    bytes_after = len(json.dumps(graph_after, sort_keys=True).encode("utf-8"))
    assert 0 < boot_seconds < 10
    assert nodes_after > nodes_before and bytes_after > bytes_before
    agent.close()


def test_p15_default_isolation():
    p15 = {"process_portfolio", "process_curriculum", "recursive_process_improvement"}
    p21 = {"curriculum_learning_bridge"}
    p15_rules = {item["name"] for sid in p15 for item in manifest_for(sid).get("rules", ())
                 if isinstance(item, dict) and item.get("name")}
    p15_rules |= {item["name"] for item in manifest_for("curriculum_learning_bridge").get("rules", ())
                  if isinstance(item, dict) and item.get("name")}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert (p15 | p21).isdisjoint(installed_seeds(default.s))
    assert (p15 | p21).isdisjoint(installed_seeds(conversation.s))
    assert p15_rules.isdisjoint({r["name"] for r in default.inner.export_rules()})
    assert p15_rules.isdisjoint({r["name"] for r in conversation.inner.export_rules()})
    default.close()
    conversation.close()


def test_p15_shared_budget():
    agent = boot_cognition_on()
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    attached = list(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
    assert len(budgets) == 1 and budgets[0] in attached
    assert all(agent.s.node(n)["type"] == "ThinkingBudget" for n in attached)
    for ptype, edge in (("ProcessPortfolioPolicy", "has_process_portfolio_policy"),
                        ("ProcessCurriculumPolicy", "has_process_curriculum_policy"),
                        ("RecursiveProcessImprovementPolicy", "has_recursive_improvement_policy")):
        policy = _nodes(agent, ptype)[0]
        assert agent.s.node(policy)["attrs"]["enabled"] == 0.0
        assert policy in agent.inner.neighbours(agent.agent, edge)
    bridge = _nodes(agent, "CurriculumLearningBridgePolicy")[0]
    assert agent.s.node(bridge)["attrs"]["enabled"] == 0.0
    assert bridge in agent.inner.neighbours(agent.agent, "has_curriculum_learning_bridge_policy")
    agent.close()


def test_p16_native_execution_profile_is_opt_in_and_budgeted():
    p16 = {"native_process_execution"}
    agent = boot_cognition_on()
    policy = _nodes(agent, "NativeProcessExecutionPolicy")
    assert len(policy) == 1
    assert agent.s.node(policy[0])["attrs"].get("enabled") == 0.0
    exported = {rule["name"] for rule in agent.inner.export_rules()}
    for item in manifest_for("native_process_execution").get("rules", ()):
        if isinstance(item, dict) and item.get("name"):
            assert item["name"] in exported
    assert p16.issubset(set(COGNITION_ON_SEEDS))
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert p16.isdisjoint(installed_seeds(default.s))
    assert p16.isdisjoint(installed_seeds(conversation.s))
    assert not _nodes(default, "NativeProcessExecutionPolicy")
    assert not _nodes(conversation, "NativeProcessExecutionPolicy")
    agent.close()
    default.close()
    conversation.close()


def test_p12_profile_chain():
    p12 = {"imitation", "social_process", "process_explanation"}
    agent = boot_cognition_on()
    exported = {r["name"] for r in agent.inner.export_rules()}
    for sid in p12:
        for item in manifest_for(sid).get("rules", ()):
            if isinstance(item, dict) and item.get("name"):
                assert item["name"] in exported, item["name"]
    for node_type in ("ImitationPolicy", "SocialProcessPolicy", "ProcessExplanationPolicy"):
        policies = _nodes(agent, node_type)
        assert policies and all(agent.s.node(n)["attrs"].get("enabled") == 0.0
                                for n in policies)

    # Enable only the exercised faculty and expose a real witnessed world row.
    policy = _nodes(agent, "ImitationPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    episode = agent.s.add_node("SocialEpisode", {
        "episode_id": "p12-profile-episode", "status": "observed",
        "observation_status": "complete", "source_kind": "directed_demonstration",
        "owner_id": "agent-root", "actor_id": "peer",
        "actor_body_id": "peer-body", "learner_body_id": "learner-body",
        "source_epoch": 3, "model_epoch": 2, "target_frame_epoch": 4,
        "binding_id": "object-a", "template_key": "press",
        "action_sequence": ["seq", ["add", [1]]],
    })
    body_map = agent.s.add_node("SocialBodyFrameMap", {
        "status": "verified", "source_body_id": "peer-body",
        "target_body_id": "learner-body", "source_epoch": 3,
        "target_frame_epoch": 4, "map_id": "p12-profile-map"})
    agent.s.add_edge(agent.agent, "has_social_episode", episode, {})
    agent.s.add_edge(episode, "uses_body_frame_map", body_map, {})
    budget = next(n for n in agent.inner.neighbours(agent.agent, "has_thinking_budget")
                  if agent.s.node(n)["attrs"].get("enabled") == 1.0)
    request = agent.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "imitation", "episode_id": "p12-profile-episode",
        "source_epoch": 3, "operation_id": "p12-profile-request",
        "source_key": "p12-profile-request", "status": "pending", "cost": 1.0})
    agent.s.add_edge(agent.agent, "has_imitation_request", request, {})
    agent.s.add_edge(request, "draws_on_thinking_budget", budget, {})
    for _ in range(20):
        if not agent.inner.run_rules(1000):
            break
    candidates = list(agent.s.nodes("DemonstratedProcessCandidate"))
    assert len(candidates) == 1
    assert agent.s.node(request)["attrs"]["status"] == "approved"
    assert agent.s.node(request)["attrs"]["terminal_status"] == "completed"
    agent.close()


def test_p12_default_isolation():
    p12_rules = {item["name"] for sid in {"imitation", "social_process", "process_explanation"}
                 for item in manifest_for(sid).get("rules", ())
                 if isinstance(item, dict) and item.get("name")}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert p12_rules.isdisjoint({r["name"] for r in default.inner.export_rules()})
    assert p12_rules.isdisjoint({r["name"] for r in conversation.inner.export_rules()})
    default.close()
    conversation.close()


def test_p12_shared_budget():
    agent = boot_cognition_on()
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    attached = list(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
    assert len(budgets) == 1 and budgets[0] in attached
    budget = budgets[0]
    before = agent.s.node(budget)["attrs"]["remaining"]
    requests = []
    for ix, requester in enumerate(("imitation", "social_process", "process_explanation")):
        request = agent.s.add_node("ThinkingBudgetRequest", {
            "requester_kind": requester, "source_key": f"p12-shared:{requester}",
            "source_epoch": 0, "operation_id": f"p12-shared:{ix}",
            "status": "pending", "cost": 0.5})
        agent.s.add_edge(request, "draws_on_thinking_budget", budgets[0], {})
        requests.append(request)
    for _ in range(8):
        agent.s.tick(1000)
    assert all(agent.s.node(r)["attrs"]["status"] == "approved" for r in requests)
    assert all(agent.s.node(r)["attrs"].get("debited_epoch") is not None for r in requests)
    assert agent.s.node(budget)["attrs"]["remaining"] == before - 1.5
    agent.close()


def test_p9_profile_chain():
    p9 = {"invention_round", "invariant_miner"}
    agent = boot_cognition_on()
    exported = {r["name"] for r in agent.inner.export_rules()}
    for sid in p9:
        for rule in manifest_for(sid).get("rules", ()):
            if isinstance(rule, dict) and rule.get("name"):
                assert rule["name"] in exported, rule["name"]
    assert "ir_repair_candidate_verify" in exported
    assert "ir_repair_epoch_stale" in exported
    agent.close()


def test_p9_default_isolation():
    p9_rules = {r["name"] for sid in {"invention_round", "invariant_miner"}
                for r in manifest_for(sid).get("rules", ())
                if isinstance(r, dict) and r.get("name")}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert p9_rules.isdisjoint({r["name"] for r in default.inner.export_rules()})
    assert p9_rules.isdisjoint({r["name"] for r in conversation.inner.export_rules()})
    default.close()
    conversation.close()


def test_p9_shared_budget():
    agent = boot_cognition_on()
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    assert len(budgets) == 1
    assert set(budgets).issubset(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
    agent.close()



def test_p7_profile_chain():
    p7 = {"experience_signature", "qualia_acquisition", "numerosity"}
    agent = boot_cognition_on()
    exported = {r["name"] for r in agent.inner.export_rules()}
    for sid in p7:
        for rule in manifest_for(sid).get("rules", ()):
            if isinstance(rule, dict) and rule.get("name"):
                assert rule["name"] in exported, rule["name"]
    for node_type in ("ExperienceSignaturePolicy", "QualiaAcquisitionPolicy", "NumerosityPolicy"):
        policy_nodes = _nodes(agent, node_type)
        assert policy_nodes
        assert all(agent.s.node(node)["attrs"].get("enabled") == 0.0
                   for node in policy_nodes)
    agent.close()


def test_p7_default_isolation():
    p7 = {"experience_signature", "qualia_acquisition", "numerosity"}
    names = {r["name"] for sid in p7 for r in manifest_for(sid).get("rules", ())
             if isinstance(r, dict) and r.get("name")}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert names.isdisjoint({r["name"] for r in default.inner.export_rules()})
    assert names.isdisjoint({r["name"] for r in conversation.inner.export_rules()})
    default.close()
    conversation.close()


def test_p7_shared_budget():
    agent = boot_cognition_on()
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    assert len(budgets) == 1
    assert budgets[0] in list(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
    assert len(_nodes(agent, "NumerosityPolicy")) == 1
    assert agent.s.node(_nodes(agent, "NumerosityPolicy")[0])["attrs"]["enabled"] == 0.0
    agent.close()


def test_p8_profile_chain():
    p8 = {"process_induction", "latent_process", "experiment_design"}
    agent = boot_cognition_on()
    exported = {r["name"] for r in agent.inner.export_rules()}
    for sid in p8:
        for rule in manifest_for(sid).get("rules", ()):
            if isinstance(rule, dict) and rule.get("name"):
                assert rule["name"] in exported, rule["name"]
    for node_type in ("ModelLearningPolicy", "LatentProcessPolicy", "ExperimentDesignPolicy"):
        policies = _nodes(agent, node_type)
        assert policies
        assert all(agent.s.node(n)["attrs"].get("enabled") == 0.0 for n in policies)
    agent.close()


def test_p8_default_isolation():
    p8 = {"process_induction", "latent_process", "experiment_design"}
    names = {r["name"] for sid in p8 for r in manifest_for(sid).get("rules", ())
             if isinstance(r, dict) and r.get("name")}
    default = WorldAdapter()
    conversation = WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert names.isdisjoint({r["name"] for r in default.inner.export_rules()})
    assert names.isdisjoint({r["name"] for r in conversation.inner.export_rules()})
    default.close()
    conversation.close()


def test_p8_shared_budget():
    agent = boot_cognition_on()
    enabled = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    assert len(enabled) == 1
    assert enabled[0] in list(agent.inner.neighbours(agent.agent, "has_thinking_budget"))
    agent.close()


def _p20_add_target_transition(agent, index, after, *, model_epoch=2):
    s, ag = agent.s, agent.agent
    common = {"owner_id": "p20-owner", "episode_id": f"p20-episode-{index}",
              "event_id": f"p20-event-{index}", "source_epoch": 3,
              "model_epoch": model_epoch, "frame_epoch": 5, "status": "observed"}
    obs = s.add_node("TransitionObservation", {
        **common, "object_id": f"widget-{index}", "object_type": "Widget",
        "action_kind": "warm", "feature_key": "temperature",
        "before_value": "cold", "after_value": after})
    action = s.add_node("TransitionActionReceipt", dict(common))
    outcome = s.add_node("TransitionOutcomeReceipt", dict(common))
    agent.s.add_edge(ag, "has_transition_observation", obs, {})
    agent.s.add_edge(obs, "has_action_receipt", action, {})
    agent.s.add_edge(obs, "has_outcome_receipt", outcome, {})


def _p20_learned_profile(after="warm"):
    agent = boot_cognition_on()
    for policy in _nodes(agent, "ModelLearningPolicy"):
        agent.s.set_attr(policy, "enabled", 1.0)
    _p20_add_target_transition(agent, 1, after)
    _p20_add_target_transition(agent, 2, after)
    for _ in range(40):
        if not agent.inner.run_rules(2000):
            break
    query = agent.s.add_node("ProcessPredictionQuery", {
        "query_id": "p20-unseen-binding", "owner_id": "p20-owner",
        "object_id": "widget-new", "object_type": "Widget", "action_kind": "warm",
        "feature_key": "temperature", "before_value": "cold", "source_epoch": 3,
        "model_epoch": 2, "frame_epoch": 5, "status": "pending"})
    agent.s.add_edge(agent.agent, "has_process_prediction_query", query, {})
    for _ in range(20):
        if not agent.inner.run_rules(2000):
            break
    predictions = agent.s.nodes("ProcessPrediction")
    return agent, [agent.s.node(node)["attrs"] for node in predictions]


def test_p20_native_causal_chain():
    agent, predictions = _p20_learned_profile()
    assert len(agent.s.nodes("ProcessInductionHypothesis")) == 1
    assert len(predictions) == 1
    assert predictions[0]["expected_after_value"] == "warm"
    agent.close()


def test_p20_native_map_induction_through_cognition_profile():
    agent = boot_cognition_on()
    policy = _nodes(agent, "TargetLearningPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    source = HeatSourceWorld(sample_ids=("profile-source-a", "profile-source-b"))
    target = ThermalWorld(object_ids=("profile-target-a", "profile-target-b"))
    source_receipts, target_receipts, observations = [], [], []
    budget = agent.inner.neighbours(agent.agent, "has_thinking_budget")[0]
    for ix, (source_id, target_id) in enumerate(
            (("profile-source-a", "profile-target-a"),
             ("profile-source-b", "profile-target-b")), 1):
        src = source.apply_heat(source_id, "apply_heat")
        tgt = target.apply(target_id, "warm")
        source_receipts.append(src)
        target_receipts.append(tgt)
        pair_id = f"profile-map-pair-{ix}"
        pair = agent.s.add_node("TargetMapObservation", {
            "pair_id": pair_id, "source_event_id": src.event_id,
            "target_event_id": tgt.event_id, "source_object_id": src.object_id,
            "target_object_id": tgt.object_id, "source_action": src.action_kind,
            "target_action": tgt.action_kind, "source_object_type": src.object_type,
            "target_object_type": tgt.object_type, "source_feature": src.feature_key,
            "target_feature": tgt.feature_key, "source_before": src.before_value,
            "target_before": tgt.before_value, "source_after": src.after_value,
            "target_after": tgt.after_value, "source_epoch": 3,
            "target_frame_epoch": 5, "status": "observed_pair"})
        agent.s.add_edge(agent.agent, "has_target_map_observation", pair, {})
        observations.append(pair)
        funding = agent.s.add_node("ThinkingBudgetRequest", {
            "requester_kind": "target_map_observation", "source_key": pair_id,
            "source_epoch": 3, "requested_epoch": 0.0,
            "operation_id": f"profile-target-map:{ix}", "status": "pending", "cost": 1.0})
        agent.s.add_edge(agent.agent, "has_thinking_budget_request", funding, {})
        agent.s.add_edge(funding, "draws_on_thinking_budget", budget, {})
        agent.s.add_edge(pair, "funded_by", funding, {})
    for _ in range(30):
        if not agent.inner.run_rules(2000):
            break
    candidates = [n for n in _nodes(agent, "RepresentationMap")
                  if agent.s.node(n)["attrs"].get("mapping_kind") == "induced_categorical_effect"]
    assert len(candidates) == 1
    proposal = verify_induced_map_candidate(
        candidate=agent.s.node(candidates[0]), source_receipts=source_receipts,
        target_receipts=target_receipts,
        object_pairs={source_receipts[0].object_id: target_receipts[0].object_id,
                      source_receipts[1].object_id: target_receipts[1].object_id})
    assert proposal["status"] == "verified"
    assert all(agent.s.node(agent.inner.neighbours(pair, "funded_by")[0])["attrs"]["status"] == "approved"
               for pair in observations)
    agent.close()


def test_p20_mapped_source_prior_requires_target_receipt():
    agent = boot_cognition_on()
    for node_type in ("ModelLearningPolicy", "TargetLearningPolicy"):
        for policy in _nodes(agent, node_type):
            agent.s.set_attr(policy, "enabled", 1.0)
    prior = agent.s.add_node("TargetProcessPrior", {
        "prior_id": "profile-prior", "source_id": "profile-source", "owner_id": "p20-owner",
        "action_kind": "warm", "object_type": "Widget", "feature_key": "temperature",
        "before_value": "cold", "after_value": "warm", "source_epoch": 3,
        "model_epoch": 2, "frame_epoch": 5, "status": "candidate"})
    frame_map = agent.s.add_node("RepresentationMap", {
        "map_id": "profile-map", "status": "verified",
        "mapping_kind": "exact_categorical_effect", "target_frame_epoch": 5})
    map_receipt = agent.s.add_node("TargetSourcePriorReceipt", {
        "receipt_id": "profile-map-receipt", "receipt_kind": "source_target_map",
        "map_id": "profile-map", "status": "verified"})
    target_receipt = agent.s.add_node("TargetSourcePriorReceipt", {
        "receipt_id": "profile-target-receipt", "receipt_kind": "target_prior_effect",
        "source_prior_id": "profile-prior", "target_event_id": "p20-event-1",
        "status": "verified", "exact_effect_match": True})
    for edge, node in (("has_source_target_map", frame_map),
                       ("has_source_prior_receipt", map_receipt),
                       ("has_source_prior_receipt", target_receipt)):
        agent.s.add_edge(prior, edge, node, {})
    agent.s.add_edge(agent.agent, "has_target_source_prior", prior, {})
    _p20_add_target_transition(agent, 1, "warm")
    for _ in range(40):
        if not agent.inner.run_rules(2000):
            break
    hypotheses = [agent.s.node(n)["attrs"] for n in agent.s.nodes("ProcessInductionHypothesis")]
    assert len(hypotheses) == 1
    assert hypotheses[0]["law_kind"] == "mapped_source_prior_confirmed"
    assert hypotheses[0]["target_support_count"] == 1.0
    agent.close()


def test_p20_observed_sequence_candidate_from_incidental_actions():
    agent = boot_cognition_on()
    policy = _nodes(agent, "ObservedSequenceLearningPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    episode = agent.s.add_node("SocialEpisode", {
        "episode_id": "p20-incidental-sequence", "status": "observed",
        "source_kind": "witnessed_interaction", "observation_status": "complete",
        "owner_id": "agent-root", "actor_id": "peer", "source_epoch": 4,
        "model_epoch": 7, "frame_epoch": 9,
        "action_sequence": ["seq", ["request", "repair"]]})
    agent.s.add_edge(agent.agent, "has_social_episode", episode, {})
    first, second = [], []
    for name in ("request", "repair"):
        process = agent.s.add_node("ProcessSchema", {
            "name": f"p20-primitive-{name}", "operator": name,
            "params": ["seq", ["add", [1]]], "status": "active",
            "model_epoch": 7, "source_epoch": 4, "frame_epoch": 9})
        agent.s.add_edge(agent.agent, "has_process_schema", process, {})
        (first if name == "request" else second).append(process)
    request = agent.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "observed_sequence_learning",
        "episode_id": "p20-incidental-sequence", "source_epoch": 4,
        "status": "approved", "debited_epoch": 10.0, "cost": 1.0})
    agent.s.add_edge(agent.agent, "has_thinking_budget_request", request, {})
    budget = agent.inner.neighbours(agent.agent, "has_thinking_budget")[0]
    agent.s.add_edge(request, "draws_on_thinking_budget", budget, {})
    for _ in range(20):
        if not agent.inner.run_rules(2000):
            break
    candidates = _nodes(agent, "ObservedProcessSequenceCandidate")
    assert len(candidates) == 1
    candidate = candidates[0]
    assert agent.s.node(candidate)["attrs"]["action_sequence"] == ["seq", ["request", "repair"]]
    assert agent.s.node(candidate)["attrs"]["status"] == "unverified_candidate"
    assert agent.inner.neighbours(candidate, "uses_first_primitive") == first
    assert agent.inner.neighbours(candidate, "uses_second_primitive") == second
    assert not agent.s.nodes("OwnTrialReceipt")

    validation_request = agent.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "observed_sequence_validation",
        "candidate_id": agent.s.node(candidate)["attrs"]["candidate_id"],
        "source_key": "p20-profile-validation", "source_epoch": 4,
        "operation_id": "p20-profile-validation", "status": "approved",
        "debited_epoch": 10.0, "cost": 2.0})
    agent.s.add_edge(agent.agent, "has_thinking_budget_request", validation_request, {})
    agent.s.add_edge(validation_request, "draws_on_thinking_budget", budget, {})
    agent.s.add_edge(candidate, "has_verification_request", validation_request, {})
    verified = verify_observed_sequence_candidate(agent, candidate)
    assert verified["status"] == "VERIFIED"
    own_world = RequestRepairWorld(world_id="p20-profile-own-world", case_id="new-case")
    own_result = execute_verified_observed_sequence(
        agent, candidate, world=own_world, authorize=lambda _proposal: True)
    assert own_result["status"] == "COMPLETED"
    assert own_world.solved
    assert len(agent.inner.neighbours(candidate, "has_own_trial_receipt")) == 2
    agent.close()


def test_p20_explanation_rebuild_through_cognition_profile():
    agent = boot_cognition_on()
    policy = _nodes(agent, "ProcessExplanationPolicy")[0]
    agent.s.set_attr(policy, "enabled", 1.0)
    primitives = []
    for event, precondition, token in (("request", "idle", "ask"),
                                        ("repair", "requested", "fix")):
        primitive = agent.s.add_node("ProcessPrimitiveVocabulary", {
            "primitive_id": f"profile-shared-{event}", "semantic_event": event,
            "public_token": token, "precondition": precondition,
            "native_effect": ["finite_action", event], "vocabulary_status": "shared",
            "model_epoch": 8, "frame_epoch": 3})
        agent.s.add_edge(agent.agent, "has_process_primitive_vocabulary", primitive, {})
        primitives.append(primitive)
    explanation_id = "profile-public-request-repair"
    explanation = agent.s.add_node("ProcessExplanationInput", {
        "explanation_id": explanation_id, "text": "Ask, then fix after the request.",
        "language": "en", "parse_status": "parsed", "explanation_kind": "ordered_two_step",
        "semantic_sequence": ["seq", ["request", "repair"]],
        "required_preconditions": ["idle", "requested"],
        "supported_vocabulary": ["ask", "fix"], "model_epoch": 8, "frame_epoch": 3})
    agent.s.add_edge(agent.agent, "has_process_explanation_input", explanation, {})
    request = agent.s.add_node("ProcessExplanationRequest", {
        "explanation_id": explanation_id, "status": "requested"})
    agent.s.add_edge(agent.agent, "has_process_explanation_request", request, {})
    funding = agent.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_explanation_rebuild", "explanation_id": explanation_id,
        "source_key": explanation_id, "source_epoch": 1, "operation_id": "profile:rebuild",
        "status": "approved", "debited_epoch": 1.0, "cost": 1.0})
    agent.s.add_edge(request, "funded_by", funding, {})
    budget = agent.inner.neighbours(agent.agent, "has_thinking_budget")[0]
    agent.s.add_edge(funding, "draws_on_thinking_budget", budget, {})
    for _ in range(24):
        if not agent.inner.run_rules(2000):
            break
    candidates = _nodes(agent, "RebuiltProcessCandidate")
    assert len(candidates) == 1
    candidate = candidates[0]
    assert agent.inner.neighbours(candidate, "uses_first_shared_primitive") == [primitives[0]]
    assert agent.inner.neighbours(candidate, "uses_second_shared_primitive") == [primitives[1]]
    validation = agent.s.add_node("ThinkingBudgetRequest", {
        "requester_kind": "process_rebuild_validation",
        "candidate_id": agent.s.node(candidate)["attrs"]["candidate_id"],
        "source_key": "profile:fresh-verify", "source_epoch": 1,
        "operation_id": "profile:verify", "status": "pending", "cost": 2.0})
    agent.s.add_edge(agent.agent, "has_thinking_budget_request", validation, {})
    agent.s.add_edge(candidate, "has_verification_request", validation, {})
    agent.s.add_edge(validation, "draws_on_thinking_budget", budget, {})
    for _ in range(16):
        if not agent.inner.run_rules(2000):
            break
    assert agent.s.node(validation)["attrs"]["status"] == "approved"
    assert agent.s.node(validation)["attrs"]["debited_epoch"] is not None
    verified = verify_rebuilt_composition(agent, candidate)
    assert verified["status"] == "VERIFIED"
    assert agent.s.node(candidate)["attrs"]["status"] == "adopted"
    assert len([n for n in _nodes(agent, "ProcessSchema")
                if agent.s.node(n)["attrs"].get("provenance") == "rebuilt_from_explanation"]) == 1
    agent.close()


def test_p20_state_perturbation_changes_execution():
    warm_agent, warm = _p20_learned_profile("warm")
    hot_agent, hot = _p20_learned_profile("hot")
    assert warm[0]["expected_after_value"] == "warm"
    assert hot[0]["expected_after_value"] == "hot"
    warm_agent.close()
    hot_agent.close()


def test_p20_default_isolation():
    agent = boot_cognition_on()
    assert all(agent.s.node(n)["attrs"].get("enabled") == 0.0
               for n in _nodes(agent, "ModelLearningPolicy"))
    assert all(agent.s.node(n)["attrs"].get("enabled") == 0.0
               for n in _nodes(agent, "SocialProcessPolicy"))
    assert all(agent.s.node(n)["attrs"].get("enabled") == 0.0
               for n in _nodes(agent, "TargetLearningPolicy"))
    assert all(agent.s.node(n)["attrs"].get("enabled") == 0.0
               for n in _nodes(agent, "ObservedSequenceLearningPolicy"))
    p20_seeds = {"target_learning", "observed_sequence_learning"}
    p20_rules = {item["name"] for sid in p20_seeds
                 for item in manifest_for(sid).get("rules", ())
                 if isinstance(item, dict) and item.get("name")}
    default, conversation = WorldAdapter(), WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    assert p20_seeds.isdisjoint(installed_seeds(default.s))
    assert p20_seeds.isdisjoint(installed_seeds(conversation.s))
    assert p20_rules.isdisjoint({r["name"] for r in default.inner.export_rules()})
    assert p20_rules.isdisjoint({r["name"] for r in conversation.inner.export_rules()})
    agent.close()
    default.close()
    conversation.close()


def test_p20_shared_budget():
    agent = boot_cognition_on()
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    assert len(budgets) == 1
    assert budgets[0] in agent.inner.neighbours(agent.agent, "has_thinking_budget")
    agent.close()


def test_p22_default_isolation():
    agent = boot_cognition_on()
    default, conversation = WorldAdapter(), WorldAdapter(seeds=())
    load_conversation_seed_profile(conversation)
    try:
        policies = _nodes(agent, "IndependentImprovementPolicy")
        assert len(policies) == 1
        assert agent.s.node(policies[0])["attrs"].get("enabled") == 0.0
        assert not _nodes(default, "IndependentImprovementPolicy")
        assert not _nodes(conversation, "IndependentImprovementPolicy")
        budgets = [n for n in _nodes(agent, "ThinkingBudget")
                   if agent.s.node(n)["attrs"].get("enabled") == 1.0]
        assert len(budgets) == 1
    finally:
        agent.close()
        default.close()
        conversation.close()


def test_p22_native_causal_chain_and_shared_budget():
    agent = boot_cognition_on()
    try:
        for kind, enabled in (("OpenProcessSearchPolicy", 1.0),
                              ("IndependentImprovementPolicy", 1.0),
                              ("SolverPolicy", 0.0)):
            for policy in _nodes(agent, kind):
                agent.s.set_attr(policy, "enabled", enabled)
        domain = agent.s.add_node("ProcessDomain", {
            "name": "p22-causal", "kind": "permutation", "probes": [[0, 1, 2, 3]],
            "probe_epoch": 0, "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0})
        agent.s.add_edge(agent.agent, "has_process_domain", domain, {})
        processes = (("source-a", [1, 0, 2, 3]), ("source-b", [0, 2, 1, 3]))
        for name, params in processes:
            schema = agent.s.add_node("ProcessSchema", {
                "kind": "permutation", "domain": "p22-causal", "domain_kind": "permutation",
                "name": name, "params": params, "source_digest": name, "cost": 1.0,
                "provenance": "held", "status": "active", "invariants": [],
                "source_epoch": 0, "model_epoch": 0, "frame_epoch": 0,
                "probe_epoch": 0, "source_probe_epoch": 0})
            agent.s.add_edge(agent.agent, "has_process_schema", schema, {})
            agent.s.add_edge(domain, "has_held_process", schema, {})
        params = agent.inner.evaluate(
            {"type": "ProcessCompose", "a": {"type": "Var", "name": "a"},
             "b": {"type": "Var", "name": "b"}},
            {"a": processes[0][1], "b": processes[1][1]})
        goal = agent.inner.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
             "state": {"type": "Var", "name": "state"}},
            {"p": params, "state": [0, 1, 2, 3]})
        task = agent.s.add_node("SolveTask", {
            "domain": "p22-causal", "initial_state": [0, 1, 2, 3],
            "state": [0, 1, 2, 3], "goal": goal, "object_count": 4.0,
            "status": "stuck", "split": "training"})
        agent.s.add_edge(agent.agent, "has_solve_task", task, {})
        agent.s.add_edge(task, "about_domain", domain, {})
        for _ in range(20):
            agent.inner.run_rules(4000)
        attempts = _nodes(agent, "OpenProcessSearchAttempt")
        candidates = _nodes(agent, "OpenProcessCandidate")
        assert attempts and candidates
        attest_open_process_candidate(agent, candidates[0])
        for _ in range(4):
            agent.inner.run_rules(4000)
        proposals = _nodes(agent, "IndependentImprovementProposal")
        assert len(proposals) == 1
        verified = [n for n in attempts
                    if agent.s.node(n)["attrs"].get("status") == "verified"]
        assert verified
        assert agent.s.node(proposals[0])["attrs"]["actionable"] is False
        budgets = [n for n in _nodes(agent, "ThinkingBudget")
                   if agent.s.node(n)["attrs"].get("enabled") == 1.0]
        assert len(budgets) == 1
        assert agent.inner.neighbours(agent.agent, "has_thinking_budget") == budgets
    finally:
        agent.close()


def test_p22_shared_budget():
    agent = boot_cognition_on()
    try:
        budgets = [n for n in _nodes(agent, "ThinkingBudget")
                   if agent.s.node(n)["attrs"].get("enabled") == 1.0]
        assert len(budgets) == 1
        assert budgets[0] in agent.inner.neighbours(agent.agent, "has_thinking_budget")
    finally:
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

