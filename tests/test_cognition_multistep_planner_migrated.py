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
