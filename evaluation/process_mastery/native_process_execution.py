"""Execute an expression selected by the cognition graph through native algebra."""
from __future__ import annotations

from typing import Callable, Any


def _attrs(agent, nid):
    return agent.s.node(nid)["attrs"]


def _children(agent, nid):
    children = agent.native.neighbours(nid, "expr_child")
    return sorted(children, key=lambda child: (agent.native.edge_attrs(nid, "expr_child", child) or {}).get("slot", 0))


def _compile(agent, nid, budget, max_nodes):
    budget["expression_visits"] += 1
    if budget["expression_visits"] > min(64, max_nodes):
        raise RuntimeError("expression traversal budget exceeded")
    attrs = _attrs(agent, nid)
    kind = attrs.get("kind")
    if kind == "input":
        if attrs.get("name") not in {"a", "b"}:
            raise RuntimeError("unsupported expression input")
        return {"type": "Var", "name": attrs["name"]}
    operator = attrs.get("operator")
    children = _children(agent, nid)
    if operator == "compose" and len(children) == 2:
        budget["compositions"] += 1
        return {"type": "ProcessCompose", "a": _compile(agent, children[0], budget, max_nodes),
                "b": _compile(agent, children[1], budget, max_nodes)}
    if operator == "commutator" and len(children) == 2:
        a, b = (_compile(agent, child, budget, max_nodes) for child in children)
        inv_a = {"type": "ProcessInverse", "a": a}
        inv_b = {"type": "ProcessInverse", "a": b}
        budget["compositions"] += 3
        return {"type": "ProcessCompose", "a": {"type": "ProcessCompose",
                "a": {"type": "ProcessCompose", "a": a, "b": b}, "b": inv_a}, "b": inv_b}
    raise RuntimeError("missing or unsupported operator expression")


def execute_selected(agent, request, *, a, b, state, authorize: Callable[[dict], bool],
                     world_transition: Callable[[Any], dict]) -> dict:
    """Evaluate a rule-selected request, authorize its proposal, and ingest receipt.

    The function never chooses an arm or constructs a process from task truth.
    The selected candidate and expression are resolved from the request's graph
    edges on every call so edits/deletion affect the next execution.
    """
    request_attrs = _attrs(agent, request)
    if request_attrs.get("status") != "funded" or request_attrs.get("selected_by") != "native_graph_rule":
        return {"status": "ABSTAIN", "reason": "request_not_graph_selected"}
    budget_requests = agent.native.neighbours(request, "has_execution_budget_request")
    if len(budget_requests) != 1:
        return {"status": "ABSTAIN", "reason": "missing_or_ambiguous_budget_request"}
    budget_attrs = _attrs(agent, budget_requests[0])
    if budget_attrs.get("status") != "approved" or budget_attrs.get("debited_epoch") is None:
        return {"status": "ABSTAIN", "reason": "execution_not_funded"}
    candidates = agent.native.neighbours(request, "selected_candidate")
    roots = [root for candidate in candidates
             for root in agent.native.neighbours(candidate, "has_expression_root")]
    if len(candidates) != 1 or len(roots) != 1:
        return {"status": "ABSTAIN", "reason": "missing_or_ambiguous_expression"}
    candidate = candidates[0]
    candidate_attrs = _attrs(agent, candidate)
    if candidate_attrs.get("status") != "promoted":
        return {"status": "ABSTAIN", "reason": "candidate_not_active"}
    source_epoch = candidate_attrs.get("source_epoch")
    if not isinstance(source_epoch, (int, float)) or request_attrs.get("source_epoch") != source_epoch:
        return {"status": "ABSTAIN", "reason": "stale_or_unversioned_expression"}
    meter = {"expression_visits": 0, "compositions": 0, "applications": 0, "failed_proposals": 0}
    try:
        expression_cap = candidate_attrs.get("expression_node_cap")
        if not isinstance(expression_cap, (int, float)) or expression_cap < 1:
            raise RuntimeError("missing expression node cap")
        expression = _compile(agent, roots[0], meter, int(expression_cap))
        # The expression owns the operation graph; source schema values are
        # resolved from the two graph-owned input nodes before native eval.
        process = agent.native.evaluate(expression, {"a": _attrs(agent, a).get("params"),
                                                     "b": _attrs(agent, b).get("params")})
        if process is None:
            raise RuntimeError("native expression evaluation returned no value")
        meter["applications"] += 1
        proposed = agent.native.evaluate({"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
                                          "state": {"type": "Var", "name": "state"}},
                                         {"p": process, "state": state})
        if proposed is None:
            raise RuntimeError("native process application returned no value")
    except RuntimeError as exc:
        meter["failed_proposals"] += 1
        return {"status": "ABSTAIN", "reason": str(exc), "meter": meter}
    proposal = {"request_id": request, "candidate_id": candidate,
                "expression_root": roots[0], "action": proposed,
                "source_epoch": source_epoch, "budget_request_id": budget_requests[0],
                "budget_debited_epoch": budget_attrs.get("debited_epoch")}
    if not authorize(proposal):
        meter["failed_proposals"] += 1
        return {"status": "DENIED", "proposal": proposal, "meter": meter}
    receipt = world_transition(proposed)
    if not isinstance(receipt, dict) or receipt.get("observed_state") is None:
        meter["failed_proposals"] += 1
        return {"status": "FAILED", "reason": "missing_world_receipt", "meter": meter}
    return {"status": "COMPLETED", "proposal": proposal, "receipt": receipt,
            "meter": meter}
