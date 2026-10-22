"""Bounded graph-native primitive-search adapter for finite PMB worlds."""
from __future__ import annotations

import json
from typing import Any

from scripts.gen_cognition_planner_seed import build_seed as planner_seed
from scripts.gen_thinking_budget_seed import build as budget_seed
from substrate.world_adapter import WorldAdapter


def _run_to_fixpoint(adapter):
    for ticks in range(1, 31):
        if adapter.inner.run_rules(1_000) == 0:
            return ticks
    raise RuntimeError("native primitive planner did not reach a fixpoint")


def search_and_execute(task: dict[str, Any], *, world, remaining: float = 100_000.0):
    """Search the complete supplied finite model and execute one world receipt.

    Python encodes world states/transitions as graph data and transports the
    selected first action to the world adapter. Search, frontier expansion,
    goal matching and path selection run through the native graph rules.
    """
    adapter = WorldAdapter(seeds=())
    budget_load = adapter.inner.load_seed_manifest(budget_seed(), adapter.agent)
    planner_load = adapter.inner.load_seed_manifest(planner_seed(), adapter.agent)
    if budget_load["rules_skipped"] or planner_load["rules_skipped"]:
        raise RuntimeError("native primitive-search seed load incomplete")
    policy = adapter.s.nodes("CognitionPlannerPolicy")[0]
    budget = adapter.s.nodes("ThinkingBudget")[0]
    for key, value in {"enabled": 1.0, "maximum_depth": 8.0,
                       "maximum_expansions": 256.0,
                       "maximum_path_arrivals": 4096.0,
                       "current_model_epoch": 2.0,
                       "current_goal_epoch": 3.0,
                       "current_manifold_epoch": 5.0,
                       "current_model_id": "p16-model",
                       "current_goal_id": "p16-goal",
                       "current_manifold_id": "p16-manifold"}.items():
        adapter.inner.set_attr(policy, key, value)
    for key, value in {"enabled": 1.0, "remaining": remaining,
                       "capacity": remaining, "capacity_ceiling": remaining,
                       "refill_per_epoch": 0.0, "last_refill_epoch": -1000.0}.items():
        adapter.inner.set_attr(budget, key, value)
    manifold_policy = adapter.s.add_node("CognitionManifoldPolicy", {
        "enabled": 1.0, "future_manifold_projection_budget": 16.0,
        "future_manifold_physical_horizon": 1.0})
    episode = adapter.s.add_node("CognitionManifoldEpisode", {
        "future_manifold_target": [[0.0]], "future_manifold_bounds": [[1.0]]})
    adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_manifold_policy", manifold_policy)
    adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_manifold_episode", episode)
    mode = adapter.s.add_node("NetworkModeState", {"epoch": 4.0, "mode": "awake"})
    adapter.inner.add_edge_unchecked(adapter.agent, "has_network_mode_state", mode)

    start_key, goal_key = "s0", "goal"
    start = adapter.s.add_node("CognitionPlanState", {
        "state_key": start_key, "owner_id": "p16-owner", "model_id": "p16-model",
        "model_epoch": 2.0, "projection_version": 1.0, "uncertainty": 0.0})
    goal = adapter.s.add_node("CognitionPlanState", {
        "state_key": goal_key, "owner_id": "p16-owner", "model_id": "p16-model",
        "model_epoch": 2.0, "goal_id": "p16-goal", "goal_epoch": 3.0,
        "projection_version": 1.0, "uncertainty": 0.0})
    request = adapter.s.add_node("CognitionPlanRequest", {
        "request_id": f"p16-{task['family']}-{task['seed']}", "status": "pending",
        "source_epoch": 4.0, "owner_id": "p16-owner", "start_state_id": start_key,
        "model_id": "p16-model", "model_epoch": 2.0, "model_complete": 1.0,
        "goal_id": "p16-goal", "goal_epoch": 3.0, "manifold_id": "p16-manifold",
        "manifold_epoch": 5.0, "required_horizon": 1.0, "deadline_epoch": 10.0,
        "intervention_unit": "action", "depth_limit": 1.0, "expansion_limit": 256.0,
        "world_access": {"initial_state": list(task["initial_state"]),
                         "goal_state": list(task["goal_state"]),
                         "primitive_affordances": task["primitive_affordances"],
                         "legal_actions_by_state": task["legal_actions_by_state"]}})
    adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_plan_request", request)
    adapter.inner.add_edge_unchecked(request, "has_start_state", start)
    adapter.inner.add_edge_unchecked(request, "has_goal_state", goal)

    initial_state = tuple(task["initial_state"])
    goal_state = tuple(task["goal_state"])
    # Start and goal are distinct graph roles even when their world values
    # coincide. Preserve both keys so native search can take an identity
    # transition and produce a normal terminal path/receipt.
    state_key = {initial_state: start_key}
    if goal_state != initial_state:
        state_key[goal_state] = goal_key
    for source, action, target in task["transition_model"]:
        source_state = tuple(map(int, source.split(",")))
        target_state = tuple(map(int, target.split(",")))
        if source_state not in state_key:
            state_key[source_state] = "p16-state-" + ",".join(map(str, source_state))
        if target_state not in state_key:
            state_key[target_state] = "p16-state-" + ",".join(map(str, target_state))
        transition_id = f"{source}|{action}|{target}"
        transition_source_key = start_key if source_state == initial_state else state_key[source_state]
        transition_target_key = goal_key if target_state == goal_state else state_key[target_state]
        transition = adapter.s.add_node("CognitionPlanTransition", {
            "transition_id": transition_id, "source_state_key": transition_source_key,
            "action_key": action, "model_id": "p16-model", "model_epoch": 2.0,
            "future_manifold_duration": 1.0, "future_manifold_times": [1.0],
            "future_manifold_values": [[0.0]], "future_manifold_widths": [[0.0]],
            "future_manifold_effort": [1.0], "intervention_unit": "action"})
        successor = adapter.s.add_node("CognitionPlanState", {
            "state_key": transition_target_key, "model_id": "p16-model",
            "model_epoch": 2.0, "goal_epoch": 3.0, "projection_version": 1.0,
            "uncertainty": 0.1})
        receipt = adapter.s.add_node("CognitionManifoldFeasibilityReceipt", {
            "status": "verified", "verifier_kind": "native_future_manifold_projection",
            "model_id": "p16-model", "model_epoch": 2.0,
            "transition_id": transition_id, "projection_version": 1.0,
            "horizon": 2.0, "projection_loss": 0.0,
            "projection_information_loss": 0.0})
        adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_plan_transition", transition)
        adapter.inner.add_edge_unchecked(transition, "has_successor_state", successor)
        adapter.inner.add_edge_unchecked(transition, "has_feasibility_receipt", receipt)
        adapter.inner.add_edge_unchecked(successor, "has_feasibility_receipt", receipt)
        if transition_target_key == goal_key:
            adapter.inner.add_edge_unchecked(goal, "has_feasibility_receipt", receipt)

    before_nodes = len(adapter.s.nodes())
    ticks = _run_to_fixpoint(adapter)
    request_attrs = adapter.s.node(request)["attrs"]
    if request_attrs.get("status") != "solved":
        return {"status": "FAILED", "planner_status": request_attrs.get("status"),
                "reason": request_attrs.get("terminal_reason"), "ticks": ticks,
                "expanded": request_attrs.get("expanded_count", 0),
                "graph_nodes": len(adapter.s.nodes()), "actions": 0}
    candidates = adapter.inner.neighbours(request, "has_imagined_plan_candidate")
    if len(candidates) != 1:
        raise RuntimeError(f"expected one graph-selected plan, found {len(candidates)}")
    arrivals = adapter.inner.neighbours(candidates[0], "has_terminal_path_arrival")
    if len(arrivals) != 1:
        raise RuntimeError(f"expected one terminal path, found {len(arrivals)}")
    transition = adapter.inner.neighbours(arrivals[0], "via_transition")
    if len(transition) != 1:
        raise RuntimeError("terminal path has no unique native transition")
    action = adapter.s.node(transition[0])["attrs"]["action_key"]
    receipt = world.transition(world.state, action)
    if not world.verify_receipt(receipt):
        raise RuntimeError("external primitive-search receipt failed verification")
    return {"status": "COMPLETED", "planner_status": "solved", "action": action,
            "receipt": receipt, "ticks": ticks,
            "expanded": request_attrs.get("expanded_count", 0),
            "graph_nodes": len(adapter.s.nodes()), "actions": 1,
            "remaining_budget": adapter.s.node(budget)["attrs"].get("remaining"),
            "graph_nodes_added": len(adapter.s.nodes()) - before_nodes,
            "plan_candidate": adapter.s.node(candidates[0])["attrs"]}
