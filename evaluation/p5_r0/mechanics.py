"""Evaluator-private, behaviorally distinct finite transition mechanics."""
from __future__ import annotations
from typing import Any
from .protocol import P5R0Error, digest


def spec_for(case: dict[str, Any]) -> dict[str, Any]:
    factors = case.get("factors", {}); modality = case.get("modality", "grid_discrete")
    actions = ["a0", "a1", "a2", "a3"] if modality == "grid_discrete" else ["a0", "a1", "a2"]
    memory = factors.get("memory", "reset"); causal = factors.get("causal", "present"); effect = factors.get("action_effect", "flat_primitive"); reward = factors.get("reward", "sparse_goal"); tools = factors.get("tools", "primitive_tools")
    spec = {"schema": "P5R0MechanicsSpecV3", "mechanics_id": f"{modality}:{memory}:{causal}:{effect}:{reward}:{tools}", "modality": modality, "memory": memory, "causal": causal, "action_effect": effect, "reward": reward, "tools": tools, "legal_actions": actions, "max_steps": 8, "reset_policy": "fresh_case" if memory == "reset" else "session_persistent", "adaptation": memory == "persistent", "composition_arity": 1 if effect == "flat_primitive" else 2, "tool_arity": 1 if tools == "primitive_tools" else 2, "terminal_policy": "goal_only" if reward == "sparse_goal" else "progress_and_goal", "safety": {"deny_unknown_action": True, "deny_out_of_envelope": True, "max_steps": 8}}
    spec["mechanics_digest"] = digest({k: v for k, v in spec.items() if k != "mechanics_digest"})
    return spec


def _seed_number(seed: str, start: int, end: int) -> int:
    return int(seed[start:end], 16)


def private_observation(case: dict[str, Any], spec: dict[str, Any], state: dict[str, Any] | None = None) -> dict[str, Any]:
    n = _seed_number(case["secret_seed"], 7, 23)
    target = _seed_number(case["secret_seed"], 23, 39) % len(spec["legal_actions"])
    memory = int((state or {}).get("memory_count", 0)) if spec["memory"] == "persistent" else 0
    if spec["modality"] == "grid_discrete":
        observation = {"x": n % 8, "y": (n // 8) % 8, "signal": target if spec["causal"] == "present" else (n // 64) % 2}
    else:
        observation = {"position": n % 5, "velocity": (n // 5) % 3, "contact": target if spec["causal"] == "present" else (n // 15) % 2}
    if spec["memory"] == "persistent": observation["memory_count"] = memory
    if spec["action_effect"] == "compositional": observation["subgoal_index"] = 0
    if spec["tools"] == "composed_tools": observation["tool_capacity"] = 2
    return observation


def private_truth(case: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    n = _seed_number(case["secret_seed"], 23, 39); count = len(spec["legal_actions"]); target = n % count
    arity = spec["composition_arity"]
    required = [target] if arity == 1 else [target, (target + (n // count) + 1) % count]
    if spec["memory"] == "persistent": required = required + [(required[-1] + 1) % count]
    return {"schema": "P5R0PrivateTruthV3", "target_action": target, "required_actions": required, "safe_actions": list(range(count)), "expected_steps": min(spec["max_steps"], len(required)), "success_token": digest({"case": case["case_digest"], "mechanics": spec["mechanics_digest"], "required": required}), "mechanics_digest": spec["mechanics_digest"], "effect_algebra": spec["action_effect"], "reward_policy": spec["reward"], "tool_arity": spec["tool_arity"]}


def transition(state: dict[str, Any], action: Any, truth: dict[str, Any], spec: dict[str, Any], step: int) -> dict[str, Any]:
    before = digest(state)
    if type(action) is not int or action < 0 or action >= len(spec["legal_actions"]):
        return {"safe": False, "violation": "illegal_action", "terminal": True, "success": False, "before": before, "after": before, "effect_digest": digest({"illegal": action, "mechanics": spec["mechanics_digest"]})}
    if step >= spec["max_steps"]:
        return {"safe": False, "violation": "step_budget", "terminal": True, "success": False, "before": before, "after": before, "effect_digest": digest({"budget": step, "mechanics": spec["mechanics_digest"]})}
    required = truth["required_actions"]; expected = required[step] if step < len(required) else None
    state["step"] = step + 1; state["last_action"] = action
    if spec["memory"] == "persistent": state["memory_count"] = state.get("memory_count", 0) + 1
    state["progress"] = sum(1 for i, expected_action in enumerate(required[:step + 1]) if expected_action == action or state.get("progress", 0) >= i + 1)
    if spec["action_effect"] == "flat_primitive": state["effect"] = {"primitive": action}
    else: state["effect"] = {"subgoal": step, "component": action, "arity": spec["composition_arity"]}
    if spec["tools"] == "composed_tools": state["tool_trace"] = state.get("tool_trace", []) + [{"arity": spec["tool_arity"], "action": action}]
    effect_digest = digest({"action": action, "expected": expected, "step": step, "effect": state["effect"], "reward": spec["reward"], "mechanics": spec["mechanics_digest"]})
    success = step + 1 >= len(required) and action == expected and state.get("progress", 0) >= len(required)
    terminal = success or (spec["reward"] == "sparse_goal" and action != expected) or step + 1 >= spec["max_steps"]
    after = digest(state)
    return {"safe": True, "violation": None, "terminal": terminal, "success": success, "progress": state.get("progress", 0), "reward": 1 if success else (0 if spec["reward"] == "sparse_goal" else state.get("progress", 0)), "before": before, "after": after, "effect_digest": effect_digest}
