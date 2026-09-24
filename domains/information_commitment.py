"""Validated bridge from future-manifold evidence to graph selection."""
from __future__ import annotations

from collections.abc import Mapping
import json

from domains.future_option_risk import FutureManifold, ManifoldProjection, evaluate_future_manifold

_METRICS = ("expected_information_gain", "delay_cost", "opportunity_cost",
            "decision_relevance", "refinement_cost", "expected_goal_work",
            "resource_cost")


def _resolve(agent):
    substrate = getattr(agent, "s", agent)
    return substrate, getattr(agent, "inner", getattr(substrate, "_inner", substrate))


def _ensure_loaded(agent):
    substrate, native = _resolve(agent)
    try:
        if "ic_gate_manifold_projection" in {r.get("name") for r in native.export_rules()}:
            return
    except Exception:
        pass
    from substrate.seed_loader import manifest_for
    root = getattr(agent, "agent", None)
    if root is None:
        roots = list(substrate.nodes("Agent"))
        root = roots[0] if roots else substrate.add_node("Agent", {"role": "commitment_root"})
    for seed in ("cognitive_areas", "information_commitment"):
        native.load_seed_manifest(manifest_for(seed), root)


def _edge(native, src, typ, tgt):
    try:
        native.add_edge(src, typ, tgt)
    except (TypeError, AttributeError):
        native.add_edge_unchecked(src, typ, tgt)


def _candidate(substrate, native, context, kind, attrs, manifold):
    if not isinstance(attrs, Mapping):
        raise ValueError(f"{kind} must be a mapping")
    values = {key: float(attrs.get(key, 0.0)) for key in _METRICS}
    assessment = evaluate_future_manifold(manifold, attrs["projection"])
    projection = assessment.projection
    values.update({"name": str(attrs.get("name", kind)), "decision_kind": kind,
                   "hard_veto": float(attrs.get("hard_veto", 0.0)),
                   "requires_approval": float(attrs.get("requires_approval", 0.0)),
                   "action_count": 0.0, "intervention_magnitude": 0.0,
                   "decision_ordinal": {"wait": 0.0, "refine": 1.0, "commit": 2.0}[kind],
                   "chosen": 0.0, "net_value": 0.0})
    node = substrate.add_node("CommitOption", values)
    _edge(native, context, "has_candidate", node)
    values["action_count"] = float(projection.action_count)
    values["intervention_magnitude"] = projection.intervention_magnitude
    substrate.set_attr(node, "action_count", values["action_count"])
    substrate.set_attr(node, "intervention_magnitude", values["intervention_magnitude"])
    audit = assessment.as_mapping()
    pnode = substrate.add_node("ManifoldProjection", {
        "manifold_id": projection.manifold_id, "projection_horizon": projection.projection_horizon,
        "minimum_retained_width": assessment.minimum_retained_width,
        "maximum_information_loss": assessment.maximum_information_loss,
        "maximum_escape_width": assessment.maximum_escape_width,
        "has_escape_residual": 1.0 if any(s.cells or s.links for s in assessment.escape_tube) else 0.0,
        "assessment_reason": assessment.reason,
        "assessment_allowed": 1.0 if assessment.allowed else 0.0,
        "retained_tube_json": json.dumps(audit["retained_tube"], sort_keys=True, separators=(",", ":")),
        "lost_tube_json": json.dumps(audit["lost_tube"], sort_keys=True, separators=(",", ":")),
        "escape_tube_json": json.dumps(audit["escape_tube"], sort_keys=True, separators=(",", ":")),
        "validated": 1.0})
    _edge(native, node, "has_manifold_projection", pnode)
    return node


def assess(agent, *, manifold, commit, wait, refine, approver=None, retain_trace=True):
    if not isinstance(manifold, Mapping):
        raise ValueError("manifold must be a mapping")
    checked = FutureManifold.from_mapping(manifold)
    for name, candidate in (("commit", commit), ("wait", wait), ("refine", refine)):
        if not isinstance(candidate, Mapping) or not isinstance(candidate.get("projection"), Mapping):
            raise ValueError(f"{name} requires a projection mapping")
    _ensure_loaded(agent)
    substrate, native = _resolve(agent)
    context = substrate.add_node("DecisionContext", {"status": "open", "decided": 0.0,
        "decision": "", "manifold_id": checked.manifold_id,
        "required_horizon": checked.required_horizon,
        "minimum_width": checked.minimum_width,
        "maximum_information_loss": checked.maximum_information_loss})
    nodes = {kind: _candidate(substrate, native, context, kind, attrs, checked)
             for kind, attrs in (("wait", wait), ("refine", refine), ("commit", commit))}
    native_steps = native.run_rules()
    decisions = list(native.neighbours(context, "has_commit_decision"))
    if not decisions:
        return {"decision": None, "authorized": False, "reason": "no_unique_decision",
                "context": context, "candidate": None, "record": None}
    record = decisions[0]
    selected = list(native.neighbours(record, "selected"))
    candidate = selected[0] if selected else None
    decision = substrate.node(record)["attrs"].get("decision_kind")
    receipt = substrate.add_node("NativeInformationCommitmentReceipt", {
        "schema": "native_information_commitment_receipt.v1",
        "cluster": "information_commitment.native_decision_settlement",
        "provenance": "native_rule_readback:information_commitment",
        "native_rule": "ic_gate_manifold_projection",
        "native_steps": int(native_steps),
        "decision": decision,
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })
    native.add_edge_unchecked(
        context, "has_native_information_commitment_receipt", receipt)
    requires = bool(candidate and substrate.node(candidate)["attrs"].get("requires_approval"))
    authorized = decision != "commit" or not requires or bool(approver)
    native.set_attr(record, "status", "authorized" if authorized else "awaiting_approval")
    if approver: native.set_attr(record, "approver", str(approver))
    if candidate: native.set_attr(candidate, "authorized", 1.0 if authorized else 0.0)
    result = {"decision": decision, "authorized": authorized,
            "reason": "graph_resolved" if authorized else "external_approval_required",
            "context": context, "candidate": candidate, "record": record,
            "alternatives": nodes}
    if not retain_trace:
        for node in (*nodes.values(), context):
            if native.has_node(node):
                native.remove_node(node)
        result["context"] = None
        result["candidate"] = None
        result["alternatives"] = {}
    return result
