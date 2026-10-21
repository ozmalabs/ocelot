"""Frozen E4 planner contract fixtures; native graph execution is added in E4.2."""
from __future__ import annotations

from dataclasses import dataclass
from collections import deque


@dataclass(frozen=True)
class Transition:
    source: str
    action: str
    target: str
    model_epoch: int = 1
    admissible: bool = True


def _reference_search(start, goal, transitions, *, model_epoch=1, depth_limit=8,
                      expansion_limit=256, funded=True):
    """Small contract oracle for the named cases, not a production planner."""
    if not funded:
        return {"status": "exhausted", "reason": "budget_denied", "paths": [], "expanded": 0}
    frontier = deque([(start, (), 0)])
    expanded = set()
    solutions = []
    while frontier and len(expanded) < min(expansion_limit, 256):
        state, path, depth = frontier.popleft()
        key = (state, model_epoch)
        if key in expanded:
            continue
        if state == goal:
            solutions.append(path)
            continue
        if depth >= min(depth_limit, 8):
            continue
        expanded.add(key)
        for transition in transitions:
            if (transition.source == state and transition.admissible
                    and transition.model_epoch == model_epoch):
                frontier.append((transition.target, path + (transition.action,), depth + 1))
    if solutions:
        return {"status": "solved", "paths": solutions, "expanded": len(expanded)}
    if not transitions:
        return {"status": "unknown", "reason": "missing_transition", "paths": [], "expanded": len(expanded)}
    return {"status": "exhausted", "reason": "frontier_closed", "paths": [], "expanded": len(expanded)}


def test_two_step_delayed_reward():
    transitions = [Transition("start", "tempting", "dead"),
                   Transition("start", "prepare", "middle"),
                   Transition("middle", "finish", "goal")]
    result = _reference_search("start", "goal", transitions)
    assert result["status"] == "solved"
    assert ("prepare", "finish") in result["paths"]
    assert ("tempting",) not in result["paths"]


def test_cycle_terminates():
    result = _reference_search("a", "goal", [Transition("a", "loop", "a")])
    assert result["status"] == "exhausted"
    assert result["expanded"] == 1


def test_missing_transition_unknown():
    result = _reference_search("start", "goal", [])
    assert result["status"] == "unknown"
    assert result["paths"] == []


def test_imagined_not_system_one():
    candidate = {"provenance_kind": "imagined", "observation_status": "not_observed",
                 "grounding_status": "ungrounded", "candidate_type": "ImaginedPlanCandidate"}
    assert candidate["provenance_kind"] != "observed"
    assert candidate["observation_status"] == "not_observed"
    assert candidate["grounding_status"] == "ungrounded"


def test_stale_model_replans():
    transitions = [Transition("start", "old", "goal", model_epoch=1)]
    result = _reference_search("start", "goal", transitions, model_epoch=2)
    assert result["status"] != "solved"
    assert result["paths"] == []


def test_frontier_bound():
    transitions = [Transition("s0", "next", "s1")]
    transitions.extend(Transition(f"s{i}", "next", f"s{i+1}") for i in range(1, 12))
    result = _reference_search("s0", "missing", transitions, depth_limit=99, expansion_limit=999)
    assert result["expanded"] <= 8


def test_every_expansion_funded():
    result = _reference_search("start", "goal", [Transition("start", "go", "goal")], funded=False)
    assert result["expanded"] == 0
    assert result["status"] == "exhausted"


def test_same_state_model_epoch_dedup():
    transitions = [Transition("a", "loop", "a", model_epoch=1),
                   Transition("a", "finish", "goal", model_epoch=2)]
    old = _reference_search("a", "goal", transitions, model_epoch=1)
    current = _reference_search("a", "goal", transitions, model_epoch=2)
    assert old["status"] != "solved"
    assert current["status"] == "solved"


def _graph_planner(transitions, *, enabled=True, remaining=16.0, depth_limit=8.0,
                   expansion_limit=256.0, maximum_path_arrivals=4096.0,
                   required_horizon=1.0):
    from substrate.world_adapter import WorldAdapter
    from scripts.gen_cognition_planner_seed import build_seed
    from scripts.gen_thinking_budget_seed import build as build_budget_seed

    adapter = WorldAdapter(seeds=())
    budget_summary = adapter.inner.load_seed_manifest(build_budget_seed(), adapter.agent)
    planner_summary = adapter.inner.load_seed_manifest(build_seed(), adapter.agent)
    assert budget_summary["rules_skipped"] == [], budget_summary
    assert planner_summary["rules_skipped"] == [], planner_summary
    policy = adapter.s.nodes("CognitionPlannerPolicy")[0]
    budget = adapter.s.nodes("ThinkingBudget")[0]
    adapter.inner.set_attr(policy, "enabled", 1.0 if enabled else 0.0)
    adapter.inner.set_attr(policy, "maximum_depth", 8.0)
    adapter.inner.set_attr(policy, "maximum_expansions", 256.0)
    adapter.inner.set_attr(policy, "maximum_path_arrivals", maximum_path_arrivals)
    adapter.inner.set_attr(policy, "current_model_epoch", 2.0)
    adapter.inner.set_attr(policy, "current_goal_epoch", 3.0)
    adapter.inner.set_attr(policy, "current_manifold_epoch", 5.0)
    adapter.inner.set_attr(policy, "current_model_id", "model-1")
    adapter.inner.set_attr(policy, "current_goal_id", "goal-1")
    adapter.inner.set_attr(policy, "current_manifold_id", "manifold-1")
    manifold_policy = adapter.s.add_node("CognitionManifoldPolicy", {
        "enabled": 1.0, "future_manifold_projection_budget": 16.0,
        "future_manifold_physical_horizon": required_horizon,
    })
    episode = adapter.s.add_node("CognitionManifoldEpisode", {
        "future_manifold_target": [[0.0] for _ in range(int(required_horizon))],
        "future_manifold_bounds": [[1.0] for _ in range(int(required_horizon))],
    })
    adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_manifold_policy", manifold_policy)
    adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_manifold_episode", episode)
    adapter.inner.set_attr(budget, "enabled", 1.0)
    adapter.inner.set_attr(budget, "remaining", remaining)
    adapter.inner.set_attr(budget, "capacity", remaining)
    mode = adapter.s.add_node("NetworkModeState", {"epoch": 4.0, "mode": "awake"})
    adapter.inner.add_edge_unchecked(adapter.agent, "has_network_mode_state", mode)
    start = adapter.s.add_node("CognitionPlanState", {
        "state_key": "s0", "owner_id": "owner-1", "model_id": "model-1", "model_epoch": 2.0,
        "goal_epoch": 3.0, "projection_version": 1.0, "uncertainty": 0.0,
    })
    goal = adapter.s.add_node("CognitionPlanState", {
        "state_key": "goal", "owner_id": "owner-1", "model_id": "model-1", "model_epoch": 2.0,
        "goal_id": "goal-1", "goal_epoch": 3.0,
        "projection_version": 1.0, "uncertainty": 0.0,
    })
    request = adapter.s.add_node("CognitionPlanRequest", {
        "request_id": "plan-1", "status": "pending", "source_epoch": 4.0,
        "owner_id": "owner-1", "start_state_id": "s0", "model_id": "model-1", "model_epoch": 2.0, "goal_id": "goal-1",
        "goal_epoch": 3.0, "manifold_id": "manifold-1", "manifold_epoch": 5.0,
        "required_horizon": required_horizon, "deadline_epoch": 10.0,
        "intervention_unit": "joule",
        "depth_limit": depth_limit, "expansion_limit": expansion_limit,
    })
    adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_plan_request", request)
    adapter.inner.add_edge_unchecked(request, "has_start_state", start)
    adapter.inner.add_edge_unchecked(request, "has_goal_state", goal)
    for index, item in enumerate(transitions):
        source, action, target, epoch = item
        state = adapter.s.add_node("CognitionPlanState", {
            "state_key": target, "model_id": "model-1", "model_epoch": float(epoch),
            "goal_epoch": 3.0, "projection_version": 1.0, "uncertainty": 0.1,
        })
        transition = adapter.s.add_node("CognitionPlanTransition", {
            "transition_id": f"t{index}", "source_state_key": source,
            "action_key": action, "model_id": "model-1", "model_epoch": float(epoch),
            "future_manifold_duration": 1.0,
            "future_manifold_times": [1.0],
            "future_manifold_values": [[0.0]],
            "future_manifold_widths": [[0.0]],
            "future_manifold_effort": [1.0],
            "intervention_unit": "joule",
        })
        receipt = adapter.s.add_node("CognitionManifoldFeasibilityReceipt", {
            "status": "verified", "verifier_kind": "native_future_manifold_projection",
            "model_id": "model-1", "model_epoch": float(epoch),
            "transition_id": f"t{index}", "projection_version": 1.0,
            "horizon": 2.0, "projection_loss": 0.0,
            "projection_information_loss": 0.0,
        })
        adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_plan_transition", transition)
        adapter.inner.add_edge_unchecked(transition, "has_successor_state", state)
        adapter.inner.add_edge_unchecked(transition, "has_feasibility_receipt", receipt)
        adapter.inner.add_edge_unchecked(state, "has_feasibility_receipt", receipt)
        if target == "goal":
            adapter.inner.add_edge_unchecked(goal, "has_feasibility_receipt", receipt)
    return adapter, request, budget


def _run_to_fixpoint(adapter):
    for _ in range(30):
        if not adapter.inner.run_rules(1000):
            return
    raise AssertionError("planner seed did not reach a fixpoint")


def test_planner_seed_reproduces_and_is_disabled_by_default():
    import json
    from scripts.gen_cognition_planner_seed import OUT, build_seed

    assert json.loads(OUT.read_text()) == build_seed()
    adapter, request, _budget = _graph_planner([], enabled=False)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "pending"


def test_graph_planner_materializes_and_funds_two_step_plan():
    adapter, request, budget = _graph_planner([
        ("s0", "prepare", "middle", 2),
        ("middle", "finish", "goal", 2),
    ], required_horizon=2.0)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "solved"
    assert adapter.s.node(request)["attrs"]["expanded_count"] == 2.0
    candidate = adapter.inner.neighbours(request, "has_imagined_plan_candidate")[0]
    attrs = adapter.s.node(candidate)["attrs"]
    assert attrs["provenance_kind"] == "imagined"
    assert attrs["observation_status"] == "not_observed"
    assert attrs["grounding_status"] == "ungrounded"
    assert adapter.s.node(budget)["attrs"]["remaining"] == 14.0
    frontiers = adapter.inner.neighbours(request, "has_frontier")
    expanded = [node for node in frontiers if adapter.s.node(node)["attrs"].get("status") == "expanded"]
    assert len(expanded) == 2
    for node in expanded:
        budget_requests = adapter.inner.neighbours(node, "has_expansion_budget_request")
        assert len(budget_requests) == 1
        budget_attrs = adapter.s.node(budget_requests[0])["attrs"]
        assert budget_attrs["status"] == "approved"
        assert budget_attrs["debited_epoch"] == 4.0
        assert adapter.s.node(node)["attrs"]["expanded_epoch"] == 4.0


def test_graph_planner_deduplicates_cycles_and_stale_transitions():
    adapter, request, _budget = _graph_planner([
        ("s0", "loop", "s0", 2),
        ("s0", "stale", "goal", 1),
    ])
    _run_to_fixpoint(adapter)
    frontiers = adapter.inner.neighbours(request, "has_frontier")
    assert len(frontiers) == 1
    assert adapter.s.node(request)["attrs"]["expanded_count"] == 1.0
    assert adapter.s.node(request)["attrs"]["status"] == "exhausted"


def test_graph_planner_does_not_expand_without_budget():
    adapter, request, budget = _graph_planner([("s0", "go", "goal", 2)], remaining=0.0)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["expanded_count"] == 0.0
    assert adapter.s.node(request)["attrs"]["status"] != "solved"
    assert adapter.s.node(budget)["attrs"]["remaining"] == 0.0


def test_graph_planner_missing_transition_is_unknown():
    adapter, request, _budget = _graph_planner([])
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "unknown"
    assert adapter.s.node(request)["attrs"]["terminal_reason"] == "missing_transition"


def test_graph_planner_depth_bound_is_terminal():
    adapter, request, _budget = _graph_planner([
        ("s0", "one", "middle", 2),
        ("middle", "two", "goal", 2),
    ], depth_limit=1.0)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "exhausted"
    assert adapter.s.node(request)["attrs"]["expanded_count"] == 1.0
    assert not adapter.inner.neighbours(request, "has_imagined_plan_candidate")


def test_graph_planner_preserves_two_goal_paths_but_counts_unique_expansions():
    adapter, request, budget = _graph_planner([
        ("s0", "left", "left", 2),
        ("s0", "right", "right", 2),
        ("left", "finish_left", "goal", 2),
        ("right", "finish_right", "goal", 2),
    ], required_horizon=2.0)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "solved"
    assert adapter.s.node(request)["attrs"]["expanded_count"] == 3.0
    candidates = adapter.inner.neighbours(request, "has_imagined_plan_candidate")
    assert len(candidates) == 2
    assert all(adapter.s.node(candidate)["attrs"]["provenance_kind"] == "imagined"
               for candidate in candidates)
    assert adapter.s.node(budget)["attrs"]["remaining"] == 13.0


def test_graph_planner_preserves_alternate_paths_through_shared_intermediate():
    adapter, request, budget = _graph_planner([
        ("s0", "left", "left", 2),
        ("s0", "right", "right", 2),
        ("left", "merge_left", "shared", 2),
        ("right", "merge_right", "shared", 2),
        ("shared", "finish", "goal", 2),
    ], required_horizon=3.0)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "solved"
    assert adapter.s.node(request)["attrs"]["expanded_count"] == 4.0
    candidates = adapter.inner.neighbours(request, "has_imagined_plan_candidate")
    assert len(candidates) == 2

    def candidate_actions(candidate):
        arrival = adapter.inner.neighbours(candidate, "has_terminal_path_arrival")[0]
        actions = []
        while adapter.s.node(arrival)["attrs"].get("path_kind") != "origin":
            actions.append(adapter.s.node(arrival)["attrs"]["action_key"])
            arrival = adapter.inner.neighbours(arrival, "parent_path_arrival")[0]
        return tuple(reversed(actions))

    assert {candidate_actions(candidate) for candidate in candidates} == {
        ("left", "merge_left", "finish"),
        ("right", "merge_right", "finish"),
    }

    frontiers = adapter.inner.neighbours(request, "has_frontier")
    shared = [node for node in frontiers if adapter.s.node(node)["attrs"].get("state_key") == "shared"]
    assert len(shared) == 1
    parents = adapter.inner.neighbours(shared[0], "has_parent_frontier")
    assert {adapter.s.node(parent)["attrs"]["state_key"] for parent in parents} == {"left", "right"}
    incoming = adapter.inner.neighbours(shared[0], "uses_transition")
    assert {adapter.s.node(transition)["attrs"]["action_key"] for transition in incoming} == {
        "merge_left", "merge_right"
    }
    arrivals = adapter.inner.neighbours(shared[0], "has_path_arrival")
    paired_arrivals = {
        (adapter.s.node(adapter.inner.neighbours(arrival, "from_frontier")[0])["attrs"]["state_key"],
         adapter.s.node(adapter.inner.neighbours(arrival, "via_transition")[0])["attrs"]["action_key"],
         adapter.s.node(adapter.inner.neighbours(arrival, "to_frontier")[0])["attrs"]["state_key"])
        for arrival in arrivals
    }
    assert paired_arrivals == {
        ("left", "merge_left", "shared"),
        ("right", "merge_right", "shared"),
    }
    assert {adapter.s.node(adapter.inner.neighbours(arrival, "parent_path_arrival")[0])["attrs"]["action_key"]
            for arrival in arrivals} == {"left", "right"}
    for parent in parents:
        earlier = adapter.inner.neighbours(parent, "has_parent_frontier")
        assert len(earlier) == 1
        assert adapter.s.node(earlier[0])["attrs"]["state_key"] == "s0"
    goal_frontier = [node for node in frontiers if adapter.s.node(node)["attrs"].get("state_key") == "goal"]
    assert len(goal_frontier) == 1
    assert [adapter.s.node(node)["attrs"]["state_key"] for node in adapter.inner.neighbours(
        goal_frontier[0], "has_parent_frontier")] == ["shared"]
    assert [adapter.s.node(node)["attrs"]["action_key"] for node in adapter.inner.neighbours(
        goal_frontier[0], "uses_transition")] == ["finish"]
    assert adapter.s.node(budget)["attrs"]["remaining"] == 12.0


def test_graph_planner_path_arrival_limit_closes_without_partial_candidates():
    adapter, request, budget = _graph_planner(
        [("s0", "finish", "goal", 2)], maximum_path_arrivals=1.0,
    )
    _run_to_fixpoint(adapter)
    attrs = adapter.s.node(request)["attrs"]
    assert attrs["status"] == "exhausted"
    assert attrs["terminal_reason"] == "path_arrival_limit"
    assert attrs["expanded_count"] == 0.0
    assert adapter.inner.neighbours(request, "has_imagined_plan_candidate") == []
    assert adapter.s.node(budget)["attrs"]["remaining"] == 16.0


def test_graph_planner_expansion_limit_is_terminal():
    transitions = [(f"s{i}", f"a{i}", f"s{i+1}", 2) for i in range(6)]
    adapter, request, _budget = _graph_planner(transitions, expansion_limit=2.0)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "exhausted"
    assert adapter.s.node(request)["attrs"]["expanded_count"] == 2.0
    assert adapter.s.node(request)["attrs"]["terminal_reason"] == "frontier_closed"


def test_graph_planner_hard_depth_cap_is_eight():
    transitions = [(f"s{i}", f"a{i}", f"s{i+1}", 2) for i in range(12)]
    adapter, request, _budget = _graph_planner(
        transitions, depth_limit=50.0, expansion_limit=999.0)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["expanded_count"] == 8.0
    frontiers = adapter.inner.neighbours(request, "has_frontier")
    assert max(adapter.s.node(node)["attrs"]["depth"] for node in frontiers) == 8.0
    assert adapter.s.node(request)["attrs"]["status"] == "exhausted"


def test_graph_planner_rejects_stale_model_snapshot():
    adapter, request, _budget = _graph_planner([("s0", "go", "goal", 2)])
    policy = adapter.s.nodes("CognitionPlannerPolicy")[0]
    adapter.inner.set_attr(policy, "current_model_epoch", 3.0)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "model_stale"
    assert not adapter.inner.neighbours(request, "has_frontier")


def test_graph_planner_rejects_mismatched_owner_or_start_identity():
    adapter, request, _budget = _graph_planner([("s0", "go", "goal", 2)])
    start = adapter.inner.neighbours(request, "has_start_state")[0]
    adapter.inner.set_attr(start, "owner_id", "different-owner")
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "model_stale"
    assert adapter.s.node(request)["attrs"]["terminal_reason"] == "planning_epoch_changed"
    assert not adapter.inner.neighbours(request, "has_frontier")



def test_graph_planner_cancels_stale_snapshot_before_state_adaptation():
    from scripts.gen_cognition_planner_seed import build_seed
    from scripts.gen_thinking_budget_seed import build as build_budget_seed
    from substrate.world_adapter import WorldAdapter

    adapter = WorldAdapter(seeds=())
    for manifest in (build_budget_seed(), build_seed()):
        assert adapter.inner.load_seed_manifest(manifest, adapter.agent)["rules_skipped"] == []
    policy = adapter.s.nodes("CognitionPlannerPolicy")[0]
    for key, value in {
        "enabled": 1.0, "current_model_epoch": 2.0, "current_goal_epoch": 3.0,
        "current_manifold_epoch": 5.0, "current_model_id": "model-1",
        "current_goal_id": "goal-1", "current_manifold_id": "manifold-1",
    }.items():
        adapter.inner.set_attr(policy, key, value)
    mode = adapter.s.add_node("NetworkModeState", {"epoch": 4.0, "mode": "awake"})
    adapter.inner.add_edge_unchecked(adapter.agent, "has_network_mode_state", mode)
    request = adapter.s.add_node("CognitionPlanRequest", {
        "request_id": "stale-before-adaptation", "status": "pending", "source_epoch": 4.0,
        "owner_id": "owner-1", "model_id": "model-1", "model_epoch": 1.0,
        "goal_id": "goal-1", "goal_epoch": 3.0,
        "manifold_id": "manifold-1", "manifold_epoch": 5.0,
        "deadline_epoch": 10.0,
    })
    adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_plan_request", request)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "model_stale"
    assert not adapter.inner.neighbours(request, "has_start_state")
    assert not adapter.inner.neighbours(request, "has_frontier")


def test_graph_planner_does_not_solve_without_projection_feasibility():
    adapter, request, _budget = _graph_planner([("s0", "go", "goal", 2)])
    goal = adapter.inner.neighbours(request, "has_goal_state")[0]
    receipt = adapter.inner.neighbours(goal, "has_feasibility_receipt")[0]
    adapter.inner.set_attr(receipt, "status", "unresolved")
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "unknown"
    assert not adapter.inner.neighbours(request, "has_imagined_plan_candidate")


def test_graph_planner_rejects_invalid_native_feasibility_receipt():
    adapter, request, _budget = _graph_planner([("s0", "go", "goal", 2)])
    transition = adapter.inner.neighbours(adapter.agent, "has_cognition_plan_transition")[0]
    receipt = adapter.inner.neighbours(transition, "has_feasibility_receipt")[0]
    adapter.inner.set_attr(receipt, "projection_information_loss", 0.25)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(request)["attrs"]["status"] == "unknown"
    assert not adapter.inner.neighbours(request, "has_imagined_plan_candidate")


def test_graph_planner_cancels_expired_request():
    adapter, request, _budget = _graph_planner([("s0", "go", "goal", 2)])
    mode = adapter.inner.neighbours(adapter.agent, "has_network_mode_state")[0]
    adapter.inner.set_attr(mode, "epoch", 11.0)
    _run_to_fixpoint(adapter)
    attrs = adapter.s.node(request)["attrs"]
    assert attrs["status"] == "exhausted"
    assert attrs["terminal_reason"] == "deadline_exceeded"
    assert not adapter.inner.neighbours(request, "has_imagined_plan_candidate")




def test_graph_planner_propagates_deadline_and_blocks_late_budget_debit():
    adapter, request, budget = _graph_planner([], remaining=4.0)
    frontier = adapter.s.add_node("CognitionPlanFrontier", {
        "status": "ready", "state_key": "s0", "source_epoch": 4.0,
        "model_epoch": 2.0, "goal_epoch": 3.0, "manifold_epoch": 5.0,
        "depth": 0.0, "rank": 0.0,
    })
    adapter.inner.add_edge_unchecked(request, "has_frontier", frontier)
    budget_request = adapter.s.add_node("ThinkingBudgetRequest", {
        "status": "pending", "requester_kind": "cognition_planner",
        "request_id": "plan-1:s0", "cost": 1.0, "source_epoch": 4.0,
        "deadline_epoch": 10.0,
    })
    adapter.inner.add_edge_unchecked(frontier, "has_expansion_budget_request", budget_request)
    adapter.inner.add_edge_unchecked(budget_request, "draws_on_thinking_budget", budget)
    mode = adapter.inner.neighbours(adapter.agent, "has_network_mode_state")[0]
    adapter.inner.set_attr(mode, "epoch", 11.0)
    _run_to_fixpoint(adapter)
    assert adapter.s.node(budget_request)["attrs"]["status"] == "canceled"
    assert adapter.s.node(budget)["attrs"]["remaining"] == 4.0



def test_graph_planner_accepts_native_p4_projection_receipt():
    from scripts.gen_cognition_manifold_seed import build_seed as build_manifold_seed
    from scripts.gen_cognition_planner_seed import build_seed as build_planner_seed
    from scripts.gen_thinking_budget_seed import build as build_budget_seed
    from substrate.world_adapter import WorldAdapter
    from tests.test_generative_world_model_migrated import _model_fixture, _nodes, _perceive

    adapter = WorldAdapter(seeds=("default_mode_core", "generative_world_model"))
    for manifest in (build_budget_seed(), build_manifold_seed()):
        summary = adapter.inner.load_seed_manifest(manifest, adapter.agent)
        assert summary["rules_skipped"] == [], summary

    _, belief = _perceive(adapter, epoch=1)
    manifold_policy = adapter.s.nodes("CognitionManifoldPolicy")[0]
    episode = adapter.s.nodes("CognitionManifoldEpisode")[0]
    budget = adapter.s.nodes("ThinkingBudget")[0]
    mode = adapter.inner.neighbours(adapter.agent, "has_network_mode_state")[0]
    for node, values in (
        (manifold_policy, {"enabled": 1.0, "future_manifold_projection_budget": 2.0,
                           "future_manifold_physical_horizon": 2.0}),
        (episode, {"future_manifold_target": [[1.0], [2.0]],
                   "future_manifold_bounds": [[0.0], [0.0]]}),
        (budget, {"enabled": 1.0, "remaining": 10.0, "capacity": 10.0,
                  "refill_per_epoch": 0.0, "last_refill_epoch": 1.0}),
    ):
        for key, value in values.items():
            adapter.inner.set_attr(node, key, value)

    sim_request, _clock, model_transitions = _model_fixture(
        adapter, belief, epoch=1, deadline=5, budget=6)
    adapter.inner.set_attr(sim_request, "maximum_branching", 1.0)
    adapter.inner.set_attr(sim_request, "horizon", 2.0)
    model_transition = model_transitions[0]
    for key, value in {
        "future_manifold_supported": True, "transition_id": "gwm-native-transition",
        "model_id": "model-1", "model_epoch": 2.0,
        "future_manifold_values": [[1.0], [2.0]],
        "future_manifold_times": [1, 2],
        "future_manifold_widths": [[0.0], [0.0]],
        "future_manifold_effort": [0.0, 0.0],
        "future_manifold_duration": 2.0, "intervention_unit": "joule",
    }.items():
        adapter.inner.set_attr(model_transition, key, value)

    for _ in range(30):
        if not adapter.inner.run_rules(10000):
            break
    else:
        raise AssertionError("GWM and native P4 projector did not reach a fixpoint")
    p4_candidates = [node for node in _nodes(adapter, "CognitionManifoldCandidate")
                     if adapter.s.node(node)["attrs"].get("status") == "audited"]
    assert p4_candidates
    p4_candidate = next(node for node in p4_candidates
                        if model_transition in adapter.inner.neighbours(node, "projects_transition"))
    receipt = adapter.inner.neighbours(p4_candidate, "has_feasibility_receipt")[0]
    receipt_attrs = adapter.s.node(receipt)["attrs"]
    assert receipt_attrs["status"] == "verified"
    assert receipt_attrs["verifier_kind"] == "native_future_manifold_projection"
    assert model_transition in adapter.inner.neighbours(receipt, "verifies_transition")

    summary = adapter.inner.load_seed_manifest(build_planner_seed(), adapter.agent)
    assert summary["rules_skipped"] == [], summary
    policy = adapter.s.nodes("CognitionPlannerPolicy")[0]
    for key, value in {
        "enabled": 1.0, "maximum_depth": 8.0, "maximum_expansions": 256.0,
        "current_model_epoch": 2.0, "current_goal_epoch": 3.0,
        "current_manifold_epoch": 5.0, "current_model_id": "model-1",
        "current_goal_id": "goal-1", "current_manifold_id": "manifold-1",
    }.items():
        adapter.inner.set_attr(policy, key, value)

    model_goal = adapter.inner.neighbours(p4_candidate, "projects_predicted_state")[0]
    request = adapter.s.add_node("CognitionPlanRequest", {
        "request_id": "native-p4-plan", "status": "pending",
        "source_epoch": float(adapter.s.node(mode)["attrs"]["epoch"]),
        "owner_id": "owner-1", "model_id": "model-1", "model_epoch": 2.0,
        "goal_id": "goal-1", "goal_epoch": 3.0,
        "manifold_id": "manifold-1", "manifold_epoch": 5.0,
        "required_horizon": 2.0, "deadline_epoch": 5.0,
        "intervention_unit": "joule",
        "depth_limit": 8.0, "expansion_limit": 256.0,
    })
    adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_plan_request", request)
    adapter.inner.add_edge_unchecked(request, "has_model_start_state", belief)
    adapter.inner.add_edge_unchecked(request, "has_model_goal_state", model_goal)
    for _ in range(30):
        if not adapter.inner.run_rules(10000):
            break
    else:
        raise AssertionError("planner did not reach a fixpoint after native P4 projection")

    start = adapter.inner.neighbours(request, "has_start_state")[0]
    goal = adapter.inner.neighbours(request, "has_goal_state")[0]
    assert belief in adapter.inner.neighbours(start, "represents_model_state")
    assert model_goal in adapter.inner.neighbours(goal, "represents_model_state")
    adapted = [node for node in adapter.inner.neighbours(adapter.agent, "has_cognition_plan_transition")
               if adapter.s.node(node)["attrs"].get("transition_id") == receipt_attrs["transition_id"]]
    assert adapted
    assert receipt in adapter.inner.neighbours(adapted[0], "has_feasibility_receipt")
    assert adapter.s.node(adapted[0])["attrs"]["action_key"] == adapter.s.node(
        model_transition)["attrs"]["action_kind"]
    assert adapter.s.node(adapted[0])["attrs"]["source_state_key"] == adapter.s.node(
        start)["attrs"]["state_key"]
    assert adapter.s.node(adapted[0])["attrs"]["uncertainty"] == adapter.s.node(
        model_goal)["attrs"]["uncertainty"]

    assert adapter.s.node(request)["attrs"]["status"] == "solved"
    candidates = adapter.inner.neighbours(request, "has_imagined_plan_candidate")
    assert len(candidates) == 1
    assert adapter.s.node(candidates[0])["attrs"]["provenance_kind"] == "imagined"
    assert adapter.s.node(budget)["attrs"]["remaining"] == 9.0

    unprojected_goal = adapter.s.add_node("PredictedBeliefState", {
        "state_kind": "unprojected_goal", "uncertainty": 0.2,
    })
    unbound = adapter.s.add_node("CognitionPlanRequest", {
        "request_id": "native-p4-plan-unprojected", "status": "pending",
        "source_epoch": float(adapter.s.node(mode)["attrs"]["epoch"]),
        "owner_id": "owner-1", "model_id": "model-1", "model_epoch": 2.0,
        "goal_id": "goal-1", "goal_epoch": 3.0,
        "manifold_id": "manifold-1", "manifold_epoch": 5.0,
        "required_horizon": 2.0, "deadline_epoch": 5.0,
    })
    adapter.inner.add_edge_unchecked(adapter.agent, "has_cognition_plan_request", unbound)
    adapter.inner.add_edge_unchecked(unbound, "has_model_start_state", belief)
    adapter.inner.add_edge_unchecked(unbound, "has_model_goal_state", unprojected_goal)
    for _ in range(30):
        if not adapter.inner.run_rules(10000):
            break
    else:
        raise AssertionError("planner did not close an unprojected exact-goal request")
    assert adapter.s.node(unbound)["attrs"]["status"] == "unknown"
    assert adapter.s.node(unbound)["attrs"]["terminal_reason"] == "missing_model_state_or_goal_projection"
    assert not adapter.inner.neighbours(unbound, "has_frontier")
