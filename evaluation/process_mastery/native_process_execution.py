"""Execute an expression selected by the cognition graph through native algebra."""
from __future__ import annotations

import hashlib
import json
from typing import Callable, Any


def _attrs(agent, nid):
    return agent.s.node(nid)["attrs"]


def params_digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    default=str).encode()).hexdigest()


def _children(agent, nid):
    children = agent.native.neighbours(nid, "expr_child")
    return sorted(children, key=lambda child: (agent.native.edge_attrs(nid, "expr_child", child) or {}).get("slot", 0))


def _expression_graph(agent, root, limit):
    """Validate and meter the graph witness; native_term performs evaluation."""
    nodes = []
    stack = [root]
    while stack:
        current = stack.pop()
        if len(nodes) >= min(64, limit):
            raise RuntimeError("expression traversal budget exceeded")
        attrs = _attrs(agent, current)
        kind = attrs.get("kind")
        if kind == "input" and attrs.get("name") in {"a", "b"}:
            signature = ("input", attrs["name"])
            children = _children(agent, current)
            if children:
                raise RuntimeError("input expression has children")
        elif kind == "operator" and attrs.get("operator") in {"compose", "commutator"}:
            signature = ("operator", attrs["operator"])
            children = _children(agent, current)
            if len(children) != 2:
                raise RuntimeError("operator expression has incomplete children")
            stack.extend(reversed(children))
        else:
            raise RuntimeError("missing or unsupported operator expression")
        nodes.append(signature)
    return nodes


def _term_compositions(term):
    if isinstance(term, list):
        return sum(_term_compositions(item) for item in term)
    if not isinstance(term, dict):
        return 0
    return int(term.get("type") in {"ProcessCompose", "ProcessInverse"}) + sum(
        _term_compositions(value) for key, value in term.items() if key != "type")


def execute_selected(agent, request, *, state, authorize: Callable[[dict], bool],
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
    inputs_a = agent.native.neighbours(request, "uses_process_input_a")
    inputs_b = agent.native.neighbours(request, "uses_process_input_b")
    roots = [root for candidate in candidates
             for root in agent.native.neighbours(candidate, "has_expression_root")]
    if (len(candidates) != 1 or len(roots) != 1
            or len(inputs_a) != 1 or len(inputs_b) != 1):
        return {"status": "ABSTAIN", "reason": "missing_or_ambiguous_source_or_expression"}
    candidate = candidates[0]
    candidate_attrs = _attrs(agent, candidate)
    if candidate_attrs.get("status") != "promoted":
        return {"status": "ABSTAIN", "reason": "candidate_not_active"}
    source_epoch = candidate_attrs.get("source_epoch")
    if not isinstance(source_epoch, (int, float)) or request_attrs.get("source_epoch") != source_epoch:
        return {"status": "ABSTAIN", "reason": "stale_or_unversioned_expression"}
    a, b = inputs_a[0], inputs_b[0]
    task_ids = agent.native.neighbours(request, "for_solve_task")
    if len(task_ids) != 1:
        return {"status": "ABSTAIN", "reason": "missing_or_ambiguous_task"}
    task_attrs = _attrs(agent, task_ids[0])
    source_attrs = (_attrs(agent, a), _attrs(agent, b))
    if any(source.get("status") != "active" for source in source_attrs):
        return {"status": "ABSTAIN", "reason": "inactive_process_source"}
    if any(source.get("owner_agent") != agent.ag for source in source_attrs):
        return {"status": "ABSTAIN", "reason": "foreign_process_source"}
    if any(source.get("domain") != task_attrs.get("domain") for source in source_attrs):
        return {"status": "ABSTAIN", "reason": "cross_domain_process_source"}
    if (request_attrs.get("input_a_epoch") != source_attrs[0].get("source_epoch")
            or request_attrs.get("input_b_epoch") != source_attrs[1].get("source_epoch")):
        return {"status": "ABSTAIN", "reason": "stale_process_source"}
    if any("params" not in source for source in source_attrs):
        return {"status": "ABSTAIN", "reason": "missing_process_source_value"}
    input_digests = [params_digest(source.get("params")) for source in source_attrs]
    if (request_attrs.get("input_a_digest") != input_digests[0]
            or request_attrs.get("input_b_digest") != input_digests[1]
            or source_attrs[0].get("source_digest") != input_digests[0]
            or source_attrs[1].get("source_digest") != input_digests[1]):
        return {"status": "ABSTAIN", "reason": "stale_or_unversioned_process_source_digest"}
    meter = {"expression_visits": 0, "compositions": 0, "applications": 0, "failed_proposals": 0}
    try:
        expression_cap = candidate_attrs.get("expression_node_cap")
        if not isinstance(expression_cap, (int, float)) or expression_cap < 1:
            raise RuntimeError("missing expression node cap")
        expression_nodes = _expression_graph(agent, roots[0], int(expression_cap))
        expression = _attrs(agent, roots[0]).get("native_term")
        if not isinstance(expression, dict) or expression.get("type") != "ProcessCompose":
            raise RuntimeError("missing native expression term")
        actual_term_digest = hashlib.sha256(json.dumps(expression, sort_keys=True,
            separators=(",", ":"), default=str).encode()).hexdigest()
        if _attrs(agent, roots[0]).get("native_term_digest") != actual_term_digest:
            raise RuntimeError("native expression digest mismatch")
        graph_digest = hashlib.sha256(json.dumps(expression_nodes,
            separators=(",", ":")).encode()).hexdigest()
        if _attrs(agent, roots[0]).get("expression_graph_digest") != graph_digest:
            raise RuntimeError("expression graph digest mismatch")
        meter["expression_visits"] = len(expression_nodes)
        meter["compositions"] = _term_compositions(expression)
        # The expression's inputs come only from the source nodes bound to the
        # graph-selected request. No host-selected process values enter eval.
        process = agent.native.evaluate(expression, {"a": source_attrs[0]["params"],
                                                     "b": source_attrs[1]["params"]})
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
                "input_source_ids": [a, b], "input_source_epochs": [
                    source_attrs[0].get("source_epoch"), source_attrs[1].get("source_epoch")],
                "input_source_digests": input_digests,
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
