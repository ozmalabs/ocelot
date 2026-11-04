"""Explicit native policy conditions for the P22 matched-arm study."""
from __future__ import annotations

import math


_ARM_SWITCHES = {
    "unchanged": {"curriculum": False, "invention": False},
    "adaptive_only": {"curriculum": True, "invention": False},
    "invention_only": {"curriculum": False, "invention": True},
    "full": {"curriculum": True, "invention": True},
}

_POLICY_GROUPS = {
    "curriculum": ("ProcessCurriculumPolicy",
                   "IndependentImprovementCurriculumBridgePolicy"),
    "invention": ("OpenProcessSearchPolicy", "IndependentImprovementPolicy",
                  "OpenProcessAdoptionPolicy"),
}
_P21_ONLY_POLICIES = ("CurriculumLearningBridgePolicy",)
_COMMON_ANCESTOR_POLICIES = ("ProcessSchemaPolicy", "SolverPolicy")


def configure_p22_arm(agent, arm: str, *, budget_capacity: float) -> dict:
    """Set one P22 condition on a fresh cognition-on graph.

    This function configures policy availability only. It does not select a
    task, candidate, expression, action, approval, or outcome for the agent.
    Callers must use a fresh graph per arm so state cannot leak between arms.
    """
    if arm not in _ARM_SWITCHES:
        raise ValueError(f"unknown P22 arm: {arm}")
    if (isinstance(budget_capacity, bool)
            or not isinstance(budget_capacity, (int, float))
            or not math.isfinite(budget_capacity) or budget_capacity <= 0):
        raise ValueError("P22 shared budget capacity must be finite and positive")
    store = getattr(agent, "s", None)
    native = getattr(agent, "inner", None) or getattr(agent, "native", None)
    root = getattr(agent, "agent", None) or getattr(agent, "ag", None)
    if store is None or native is None or root is None:
        raise TypeError("P22 arm setup requires a native cognition-on agent")

    switches = _ARM_SWITCHES[arm]
    policy_state = {}
    for kind in _COMMON_ANCESTOR_POLICIES:
        nodes = store.nodes(kind)
        if len(nodes) != 1:
            raise RuntimeError(f"P22 profile must contain exactly one {kind}")
        store.set_attr(nodes[0], "enabled", 1.0)
        policy_state[kind] = {"node_id": str(nodes[0]), "enabled": True}
    for group, kinds in _POLICY_GROUPS.items():
        for kind in kinds:
            nodes = store.nodes(kind)
            if len(nodes) != 1:
                raise RuntimeError(f"P22 profile must contain exactly one {kind}")
            enabled = float(switches[group])
            store.set_attr(nodes[0], "enabled", enabled)
            if group == "curriculum" and enabled:
                store.set_attr(nodes[0], "selector_mode", "residual")
            policy_state[kind] = {"node_id": str(nodes[0]), "enabled": bool(enabled)}

    for kind in _P21_ONLY_POLICIES:
        nodes = store.nodes(kind)
        if len(nodes) != 1:
            raise RuntimeError(f"P22 profile must contain exactly one {kind}")
        store.set_attr(nodes[0], "enabled", 0.0)
        policy_state[kind] = {"node_id": str(nodes[0]), "enabled": False}

    budgets = list(native.neighbours(root, "has_thinking_budget"))
    enabled_budgets = [node for node in budgets
        if store.node(node)["attrs"].get("enabled") == 1.0]
    if len(enabled_budgets) != 1:
        raise RuntimeError("P22 arm requires exactly one enabled shared ThinkingBudget")
    budget = enabled_budgets[0]
    attrs = store.node(budget)["attrs"]
    ceiling = attrs.get("capacity_ceiling")
    if (isinstance(ceiling, bool) or not isinstance(ceiling, (int, float))
            or budget_capacity > ceiling):
        raise ValueError("P22 budget capacity exceeds native ThinkingBudget ceiling")
    for key, value in (("capacity", float(budget_capacity)),
                       ("remaining", float(budget_capacity)),
                       ("refill_per_epoch", 0.0),
                       ("last_refill_epoch", -1_000.0)):
        store.set_attr(budget, key, value)
    return {"arm": arm, "policy_state": policy_state,
            "budget_node_id": str(budget),
            "budget_capacity": float(budget_capacity),
            "budget_remaining": float(budget_capacity),
            "shared_budget_count": 1}
