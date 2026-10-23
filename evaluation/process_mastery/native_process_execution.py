"""Execute an expression selected by the cognition graph through native algebra."""
from __future__ import annotations

import hashlib
import json
from typing import Callable, Any


def _attrs(agent, nid):
    return agent.s.node(nid)["attrs"]


def _native(agent):
    native = getattr(agent, "native", None) or getattr(agent, "inner", None)
    if native is None:
        raise TypeError("agent must expose a native substrate handle")
    return native


def params_digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    default=str).encode()).hexdigest()


def open_process_candidate_digest(agent, candidate) -> str:
    """Hash graph-authored expression data and exact supporting evidence.

    The candidate label is deliberately excluded. Parent schemas come from
    derivation-attempt edges, so the digest covers the expression, parameters,
    finite effect, observed guard, subgoal, parent source digests, domain and
    evidence epochs.
    """
    attrs = _attrs(agent, candidate)
    native = _native(agent)
    attempts = native.neighbours(candidate, "derived_from_attempt")
    if len(attempts) != 1:
        raise ValueError("candidate must have exactly one derivation attempt")
    # Recursive search attempts extend an earlier graph-authored expression.
    # Walk the complete attempt ancestry so a digest binds every held process
    # source used by the tree, not only the last operand attached to the leaf.
    parent_nodes = {}
    parent_candidates = {}
    pending, visited = list(attempts), set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        for node in native.neighbours(current, "uses_parent_process"):
            parent_nodes[node] = _attrs(agent, node)
        for node in native.neighbours(current, "extends_candidate"):
            parent_candidates[node] = _attrs(agent, node)
        pending.extend(native.neighbours(current, "extends_search_attempt"))
    parents = sorted(({
        "name": parent.get("name"),
        "source_digest": parent.get("source_digest"),
        "params": parent.get("params"),
        "source_epoch": parent.get("source_epoch"),
    } for parent in parent_nodes.values()),
        key=lambda parent: json.dumps(parent, sort_keys=True, separators=(",", ":")))
    payload = {
        "schema": "open_process_expression_v1",
        "expression_key": attrs.get("expression_key"),
        "expression_tree": attrs.get("expression_tree"),
        "params": attrs.get("params"),
        "effect_digest": attrs.get("effect_digest"),
        "guard_state": attrs.get("guard_state"),
        "subgoal_state": attrs.get("subgoal_state"),
        "domain": attrs.get("domain"), "kind": attrs.get("kind"),
        "source_epoch": attrs.get("source_epoch"),
        "model_epoch": attrs.get("model_epoch"),
        "frame_epoch": attrs.get("frame_epoch"), "parents": parents,
    }
    if parent_candidates:
        candidate_sources = []
        for parent_id, parent in parent_candidates.items():
            receipts = native.neighbours(parent_id, "has_expression_digest_receipt")
            if (parent.get("expression_digest_status") != "verified"
                    or len(receipts) != 1
                    or _attrs(agent, receipts[0]).get("status") != "verified"
                    or _attrs(agent, receipts[0]).get("expression_digest")
                       != parent.get("expression_digest")):
                raise ValueError("parent candidate lacks one matching digest receipt")
            candidate_sources.append({
                "expression_digest": parent.get("expression_digest"),
                "domain": parent.get("domain"),
                "source_epoch": parent.get("source_epoch"),
                "model_epoch": parent.get("model_epoch"),
                "frame_epoch": parent.get("frame_epoch"),
            })
        payload["parent_candidates"] = sorted(candidate_sources,
            key=lambda parent: json.dumps(parent, sort_keys=True,
                                          separators=(",", ":")))
    return params_digest(payload)


def attest_open_process_candidate(agent, candidate) -> str:
    """Persist a verifier-side digest receipt for a graph-minted candidate."""
    digest = open_process_candidate_digest(agent, candidate)
    attrs = _attrs(agent, candidate)
    existing = _native(agent).neighbours(candidate, "has_expression_digest_receipt")
    if existing:
        if (len(existing) == 1
                and _attrs(agent, existing[0]).get("status") == "verified"
                and _attrs(agent, existing[0]).get("expression_digest") == digest):
            return digest
        raise ValueError("candidate already has a conflicting expression digest receipt")
    agent.s.set_attr(candidate, "expression_digest", digest)
    agent.s.set_attr(candidate, "expression_digest_status", "verified")
    receipt = agent.s.add_node("OpenProcessDigestReceipt", {
        "status": "verified", "candidate_id": candidate,
        "expression_digest": digest, "effect_digest": attrs.get("effect_digest"),
        "domain": attrs.get("domain"),
    })
    _native(agent).add_edge(candidate, "has_expression_digest_receipt", receipt, {})
    return digest


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


def execute_open_process_candidate(agent, candidate, *, state,
                                   authorize: Callable[[dict], bool],
                                   world_transition: Callable[[Any], dict]) -> dict:
    """Execute an adopted P19 candidate after rechecking its exact live binding.

    Search candidates are non-actionable until the graph adoption gate has
    consumed an exact, candidate-linked human approval. The host only validates
    graph data, applies the stored process through the native evaluator, and
    records the world receipt; it does not choose or rebuild an expression.
    """
    attrs = _attrs(agent, candidate)
    native = _native(agent)
    if attrs.get("status") != "adopted_candidate" or attrs.get("adoption_status") != "approved":
        return {"status": "ABSTAIN", "reason": "candidate_not_adopted"}
    digest_receipts = native.neighbours(candidate, "has_expression_digest_receipt")
    if (len(digest_receipts) != 1
            or _attrs(agent, digest_receipts[0]).get("status") != "verified"
            or _attrs(agent, digest_receipts[0]).get("expression_digest") != attrs.get("expression_digest")):
        return {"status": "ABSTAIN", "reason": "missing_or_ambiguous_expression_digest_receipt"}
    approvals = native.neighbours(candidate, "approved_by_open_process_adoption")
    if len(approvals) != 1:
        return {"status": "ABSTAIN", "reason": "missing_or_ambiguous_adoption_approval"}
    approval = _attrs(agent, approvals[0])
    if approval.get("status") != "consumed" or approval.get("approval_kind") != "human":
        return {"status": "ABSTAIN", "reason": "adoption_approval_not_consumed"}
    if any(approval.get(key) != attrs.get(key) for key in (
            "expression_digest", "expression_key", "expression_tree", "effect_digest", "params",
            "guard_state", "domain", "source_epoch", "model_epoch", "frame_epoch")):
        return {"status": "ABSTAIN", "reason": "adoption_approval_binding_changed"}
    if (attrs.get("expression_digest") != attrs.get("adopted_expression_digest")
            or attrs.get("expression_key") != attrs.get("adopted_expression_key")
            or attrs.get("expression_tree") != attrs.get("adopted_expression_tree")
            or attrs.get("effect_digest") != attrs.get("adopted_effect_digest")
            or attrs.get("params") != attrs.get("adopted_params")
            or attrs.get("guard_state") != attrs.get("adopted_guard_state")):
        return {"status": "ABSTAIN", "reason": "adopted_expression_binding_changed"}
    domains = [nid for nid in agent.s.nodes("ProcessDomain")
               if _attrs(agent, nid).get("name") == attrs.get("domain")]
    if len(domains) != 1:
        return {"status": "ABSTAIN", "reason": "missing_or_ambiguous_process_domain"}
    domain = _attrs(agent, domains[0])
    epochs = ("source_epoch", "model_epoch", "frame_epoch")
    if any(attrs.get(key) != attrs.get("adopted_" + key)
           or domain.get(key) != attrs.get("adopted_" + key) for key in epochs):
        agent.s.set_attr(candidate, "status", "invalidated")
        agent.s.set_attr(candidate, "adoption_status", "invalidated")
        agent.s.set_attr(candidate, "invalidation_reason", "domain_epoch_changed")
        return {"status": "ABSTAIN", "reason": "adopted_domain_epoch_changed"}
    if state != attrs.get("guard_state"):
        return {"status": "ABSTAIN", "reason": "candidate_guard_not_satisfied"}
    probes = domain.get("probes")
    actual_effect = native.evaluate(
        {"type": "EffectFingerprint", "p": {"type": "Var", "name": "p"},
         "probes": {"type": "Var", "name": "probes"}},
        {"p": attrs.get("params"), "probes": probes})
    actual_expression_digest = open_process_candidate_digest(agent, candidate)
    if (actual_effect != attrs.get("effect_digest")
            or actual_expression_digest != attrs.get("expression_digest")):
        agent.s.set_attr(candidate, "status", "invalidated")
        agent.s.set_attr(candidate, "adoption_status", "invalidated")
        agent.s.set_attr(candidate, "invalidation_reason", "native_effect_digest_changed")
        return {"status": "ABSTAIN", "reason": "native_effect_digest_changed"}
    predicted = native.evaluate(
        {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
         "state": {"type": "Var", "name": "state"}},
        {"p": attrs.get("params"), "state": state})
    if predicted is None:
        return {"status": "ABSTAIN", "reason": "native_process_precondition_failed"}
    proposal = {"candidate_id": candidate, "expression_digest": attrs["expression_digest"],
                "domain": attrs["domain"], "state": state, "action": attrs["params"],
                "predicted_state": predicted,
                "params_digest": params_digest(attrs["params"]),
                "adoption_approval_id": approvals[0]}
    if not authorize(proposal):
        return {"status": "DENIED", "proposal": proposal}
    world_receipt = world_transition(attrs["params"])
    if not isinstance(world_receipt, dict) or world_receipt.get("observed_state") is None:
        return {"status": "FAILED", "reason": "missing_world_receipt", "proposal": proposal}
    observed = world_receipt["observed_state"]
    result = "verified" if observed == predicted else "contradicted"
    receipt = agent.s.add_node("OpenProcessWorldReceipt", {
        "status": result, "candidate_id": candidate,
        "expression_digest": attrs["expression_digest"],
        "effect_digest": actual_effect, "params_digest": proposal["params_digest"],
        "domain": attrs["domain"], "source_epoch": domain.get("source_epoch"),
        "model_epoch": domain.get("model_epoch"), "frame_epoch": domain.get("frame_epoch"),
        "requested_state": state, "predicted_state": predicted,
        "observed_state": observed,
    })
    native.add_edge(candidate, "has_world_execution_receipt", receipt, {})
    process_nodes = native.neighbours(candidate, "adopted_as_process")
    attempts = native.neighbours(candidate, "derived_from_attempt")
    tasks = [task for attempt in attempts
             for task in native.neighbours(attempt, "about_task")]
    if result == "verified" and len(process_nodes) == 1 and len(tasks) == 1:
        process = process_nodes[0]
        process_attrs = _attrs(agent, process)
        if process_attrs.get("params") == attrs.get("params"):
            agent.s.set_attr(process, "status", "active")
            agent.s.set_attr(process, "source_digest", params_digest(attrs.get("params")))
            agent.s.set_attr(process, "fingerprint_checked", 1)
            agent.s.set_attr(process, "dedup_checked", 1)
            agent.s.set_attr(process, "indexed", 1)
            agent.s.set_attr(process, "verification_receipt", "native_world_receipt")
            task = tasks[0]
            task_attrs = _attrs(agent, task)
            native.add_edge(task, "has_open_process_world_receipt", receipt, {})
            native.add_edge(task, "uses_approved_open_process_candidate", candidate, {})
            agent.s.set_attr(task, "state", observed)
            agent.s.set_attr(task, "trace", list(task_attrs.get("trace") or []) + [process])
            agent.s.set_attr(task, "steps", int(task_attrs.get("steps", 0)) + 1)
            agent.s.set_attr(task, "moves", float(task_attrs.get("moves", 0.0)) +
                             float(process_attrs.get("cost", 1.0)))
            agent.s.set_attr(task, "status", "solved" if observed == task_attrs.get("goal") else "active")
    elif result != "verified":
        agent.s.set_attr(candidate, "status", "invalidated")
        agent.s.set_attr(candidate, "adoption_status", "invalidated")
        for process in process_nodes:
            agent.s.set_attr(process, "status", "proof_blocked")
    if result != "verified":
        return {"status": "FAILED", "reason": "world_result_contradicts_native_prediction",
                "proposal": proposal, "receipt": world_receipt, "evidence_node": receipt}
    return {"status": "COMPLETED", "proposal": proposal,
            "receipt": world_receipt, "evidence_node": receipt}
