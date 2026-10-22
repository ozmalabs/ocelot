"""Read-only cumulative resource snapshots for P22 native graph runs."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import math


_RESOURCE_KINDS = {
    "OpenProcessSearchAttempt": "search_attempts",
    "OpenProcessSearchRequest": "search_requests",
    "IndependentImprovementProposal": "improvement_proposals",
    "IndependentImprovementQualification": "qualifications",
    "OpenProcessAdoptionApproval": "candidate_approval_events",
    "OpenProcessWorldReceipt": "world_receipts",
    "SolveTask": "solve_tasks",
    "ProcessCurriculumTask": "curriculum_tasks",
    "ThinkingBudgetDenial": "budget_denials",
}
def _finite_nonnegative(attrs: dict, key: str, *, kind: str, node_id) -> float:
    value = attrs.get(key, 0.0)
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0):
        raise ValueError(f"{kind} {node_id} has invalid {key}")
    return float(value)


def snapshot_native_resources(agent) -> dict:
    """Measure cumulative graph and shared-budget usage without filtering outcomes.

    `serialized_graph_bytes` is the canonical JSON size of the graph readback;
    it is not a claim about native allocator or resident-memory use. Search
    attempts and all node statuses are counted, including rejected, failed,
    pending, and timed-out records when present.
    """
    store = getattr(agent, "s", None)
    native = getattr(agent, "inner", None) or getattr(agent, "native", None)
    root = getattr(agent, "agent", None) or getattr(agent, "ag", None)
    if store is None or native is None or root is None:
        raise TypeError("agent must expose native graph store and root")

    budget_ids = native.neighbours(root, "has_thinking_budget")
    budgets = [store.node(node)["attrs"] for node in budget_ids
               if store.node(node)["attrs"].get("enabled") == 1.0]
    if len(budgets) != 1:
        raise ValueError("resource accounting requires exactly one enabled shared ThinkingBudget")
    capacity = budgets[0].get("capacity")
    remaining = budgets[0].get("remaining")
    if (isinstance(capacity, bool) or not isinstance(capacity, (int, float))
            or isinstance(remaining, bool) or not isinstance(remaining, (int, float))
            or not math.isfinite(capacity) or not math.isfinite(remaining)
            or capacity < 0 or remaining < 0 or remaining > capacity):
        raise ValueError("shared ThinkingBudget has invalid capacity or remaining value")

    nodes = []
    node_counts = Counter()
    status_counts = Counter()
    selected_counts = Counter()
    cumulative = Counter()
    status_rows = []
    serialized_bytes = 0
    for node_id in store.nodes():
        record = store.node(node_id)
        kind = record.get("type", "<missing>")
        attrs = record.get("attrs", {})
        if not isinstance(attrs, dict):
            raise ValueError("native graph node has malformed attrs")
        status = attrs.get("status")
        node_counts[kind] += 1
        if status is not None:
            status_counts[(kind, str(status))] += 1
            status_rows.append({"node_id": str(node_id), "type": kind,
                                "status": str(status)})
        if kind in _RESOURCE_KINDS:
            selected_counts[_RESOURCE_KINDS[kind]] += 1
        if kind == "ProcessCurriculumEvidence" and attrs.get("split") == "training":
            cumulative["training_evidence_exposures"] += 1
        if kind == "ProcessCurriculumOutcome" and attrs.get("split") == "training":
            cumulative["training_outcomes"] += 1
        if kind == "ThinkingBudgetRequest":
            cumulative["budget_requested"] += _finite_nonnegative(
                attrs, "cost", kind=kind, node_id=node_id)
            if attrs.get("status") == "approved":
                cumulative["budget_approved"] += _finite_nonnegative(
                    attrs, "cost", kind=kind, node_id=node_id)
            if attrs.get("status") == "denied":
                cumulative["budget_denied_cost"] += _finite_nonnegative(
                    attrs, "cost", kind=kind, node_id=node_id)
        if kind == "SolveTask":
            if attrs.get("split") == "training":
                cumulative["training_task_exposures"] += 1
            cumulative["native_solver_steps"] += _finite_nonnegative(
                attrs, "steps", kind=kind, node_id=node_id)
            cumulative["native_solver_primitive_work"] += _finite_nonnegative(
                attrs, "moves", kind=kind, node_id=node_id)
        if kind == "OpenProcessSearchAttempt":
            cumulative["search_declared_primitive_work"] += _finite_nonnegative(
                attrs, "work_cost", kind=kind, node_id=node_id)
        encoded = json.dumps({"id": str(node_id), "node": record}, sort_keys=True,
                             separators=(",", ":"), default=str).encode("utf-8")
        serialized_bytes += len(encoded)
        nodes.append(str(node_id))

    statuses = [{"type": kind, "status": status, "count": count}
                for (kind, status), count in sorted(status_counts.items())]
    payload = {
        "schema": "p22_native_resource_snapshot_v1",
        "node_ids": sorted(nodes),
        "node_counts": dict(sorted(node_counts.items())),
        "status_counts": statuses,
        "status_records": sorted(status_rows,
                                  key=lambda row: (row["type"], row["node_id"])),
        "resource_counts": {name: selected_counts.get(name, 0)
                            for name in sorted(set(_RESOURCE_KINDS.values()))},
        "cumulative_resources": {name: float(value) for name, value
                                  in sorted(cumulative.items())},
        "thinking_budget_capacity": float(capacity),
        "thinking_budget_remaining": float(remaining),
        "thinking_budget_spent": float(capacity - remaining),
        "serialized_graph_bytes": serialized_bytes,
    }
    payload["snapshot_sha256"] = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return payload


def compare_resource_snapshots(snapshots: dict[str, dict]) -> dict:
    """Report exact resource matching for named arms without dropping failures."""
    if len(snapshots) < 2 or any(not arm for arm in snapshots):
        raise ValueError("at least two named arm snapshots are required")
    required = ("search_attempts", "improvement_proposals", "qualifications",
                "candidate_approval_events", "world_receipts", "solve_tasks",
                "curriculum_tasks", "budget_denials")
    cumulative_dimensions = (
        "training_evidence_exposures", "training_task_exposures",
        "training_outcomes", "budget_requested",
        "budget_approved", "budget_denied_cost", "native_solver_steps",
        "native_solver_primitive_work", "search_declared_primitive_work")
    vectors = {}
    for arm, snapshot in snapshots.items():
        if snapshot.get("schema") != "p22_native_resource_snapshot_v1":
            raise ValueError(f"{arm} has an unsupported resource snapshot")
        if not resource_snapshot_digest_valid(snapshot):
            raise ValueError(f"{arm} resource snapshot digest does not verify")
        counts = snapshot.get("resource_counts", {})
        vectors[arm] = {
            **{key: counts.get(key, 0) for key in required},
            "thinking_budget_spent": snapshot["thinking_budget_spent"],
            "serialized_graph_bytes": snapshot["serialized_graph_bytes"],
            **{key: snapshot.get("cumulative_resources", {}).get(key, 0.0)
               for key in cumulative_dimensions},
        }
    common = set.intersection(*(set(vector) for vector in vectors.values()))
    matched = {key: len({vector[key] for vector in vectors.values()}) == 1
               for key in sorted(common)}
    return {"arms": vectors, "matched": matched,
            "all_resource_dimensions_match": all(matched.values()),
            "failure_statuses_retained": True}


def resource_snapshot_digest_valid(snapshot: dict) -> bool:
    if not isinstance(snapshot, dict):
        return False
    recorded_digest = snapshot.get("snapshot_sha256")
    payload = {key: value for key, value in snapshot.items()
               if key != "snapshot_sha256"}
    actual_digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    return recorded_digest == actual_digest
