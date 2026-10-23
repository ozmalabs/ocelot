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

# These dimensions are named by the P22 improvement contract. Keep missing
# instruments visible instead of turning unavailable measurements into zero.
_CONTRACT_DIMENSIONS = (
    "training_data_bytes", "retrieval_work", "proposal_work",
    "verification_work", "model_refinement_work", "definition_decode_work",
    "approval_cost", "rollback_work", "wall_time_seconds",
    "native_rule_term_evaluations", "native_model_calls", "process_peak_rss_bytes",
)

# A rule contributes to at most one named operation class. These scopes count
# native term evaluations, not wall-clock or human effort. They are deliberately
# explicit so a new rule family cannot silently enter a cost category.
def _rule_work_class(rule_name: str | None) -> str | None:
    if not isinstance(rule_name, str):
        return None
    if rule_name.startswith(("episodic_retrieve_", "episodic_retrieval_")) or (
            rule_name.startswith("sl_") and "recall" in rule_name):
        return "retrieval_work"
    if rule_name.startswith(("cm_",)):
        return "model_refinement_work"
    if rule_name in {"sd_decode", "sd_redecode", "sd_transform_decode"}:
        return "definition_decode_work"
    if "rollback" in rule_name:
        return "rollback_work"
    if (rule_name.startswith(("iip_qualify_", "ops_mint_verified_",
                             "ops_test_candidate_composition_"))
            or "verify" in rule_name or "proof" in rule_name):
        return "verification_work"
    if rule_name.startswith(("ops_", "iip_propose_")):
        return "proposal_work"
    return None


def _classified_native_rule_work(native_rule_work: dict | None) -> dict:
    if native_rule_work is None:
        return {}
    totals = Counter()
    rule_counts = Counter()
    for row in native_rule_work.get("rules", []):
        if row.get("metric") != "term_evaluations":
            continue
        category = _rule_work_class(row.get("rule_name"))
        if category is not None:
            totals[category] += row["count"]
            rule_counts[category] += 1
    return {category: {"native_term_evaluations": totals[category],
                       "attributed_rule_count": rule_counts[category]}
            for category in sorted(set(totals) | set(rule_counts))}
def _finite_nonnegative(attrs: dict, key: str, *, kind: str, node_id) -> float:
    value = attrs.get(key, 0.0)
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0):
        raise ValueError(f"{kind} {node_id} has invalid {key}")
    return float(value)


class NativeRuleWorkCapture:
    """Isolated-process opt-in per-rule native work attribution.

    The underlying audit counters are process-global, so capture refuses to
    start if another audit mode or accumulated rows are present. The P22
    development CLI uses one graph per worker process, making rule-index
    attribution unambiguous.
    """

    def __init__(self, native):
        self.native = native
        self.active = False

    def start(self):
        mode = self.native.scale_audit_mode_snapshot()
        if any(mode):
            raise RuntimeError("native scale audit must be disabled before P22 capture")
        if (self.native.scale_audit_per_rule_snapshot()
                or self.native.scale_audit_rule_identity_snapshot()):
            raise RuntimeError("native scale audit rows must be empty before P22 capture")
        self.native.scale_audit_reset()
        self.native.scale_audit_per_rule_reset()
        self.native.scale_audit_set_enabled(True)
        self.native.scale_audit_set_per_rule_enabled(True)
        self.active = True
        return self

    def snapshot(self) -> dict:
        """Read cumulative per-rule work without ending the active capture."""
        if not self.active:
            raise RuntimeError("native rule-work capture is not active")
        counters = self.native.scale_audit_per_rule_snapshot()
        metadata = self.native.scale_audit_rule_metadata_snapshot()
        identities = self.native.scale_audit_rule_identity_snapshot()
        store_ids = {store_id for _audit_id, store_id, _local_index in identities}
        if len(store_ids) > 1:
            raise RuntimeError("P22 rule-work capture spans multiple native graph stores")
        name_by_audit = {audit_id: (name, ambiguous)
            for audit_id, _symbol, name, _arity, ambiguous in metadata}
        identity_by_audit = {audit_id: (store_id, local_index)
            for audit_id, store_id, local_index in identities}
        rows = []
        unresolved_indices = set()
        for audit_rule_id, metric, count in counters:
            identity = identity_by_audit.get(audit_rule_id)
            metadata_row = name_by_audit.get(audit_rule_id)
            if (identity is None or metadata_row is None or metadata_row[1]
                    or identity[0] not in store_ids):
                unresolved_indices.add(int(audit_rule_id))
                rule_index = (int(identity[1]) if identity is not None else None)
                rule_name = None
            else:
                rule_index = int(identity[1])
                rule_name = metadata_row[0]
            rows.append({"rule_index": rule_index,
                "rule_audit_id": int(audit_rule_id), "rule_name": rule_name,
                "metric": metric, "count": int(count)})
        rows.sort(key=lambda row: (row["rule_index"] is None,
            row["rule_index"] if row["rule_index"] is not None else -1,
            row["metric"], row["rule_audit_id"]))
        totals = {}
        for row in rows:
            totals[row["metric"]] = totals.get(row["metric"], 0) + row["count"]
        payload = {"schema": "p22_native_rule_work_v2",
            "store_instance_id": next(iter(store_ids)) if store_ids else None,
            "rules": rows, "rule_identity_coverage": (
                "COMPLETE" if not unresolved_indices else "PARTIAL"),
            "unresolved_rule_indices": sorted(unresolved_indices),
            "totals_by_metric": dict(sorted(totals.items()))}
        payload["snapshot_sha256"] = hashlib.sha256(json.dumps(payload,
            sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return payload

    def finish(self) -> dict:
        if not self.active:
            raise RuntimeError("native rule-work capture is not active")
        try:
            return self.snapshot()
        finally:
            self.close()

    def close(self):
        if self.active:
            self.native.scale_audit_set_enabled(False)
            self.native.scale_audit_set_per_rule_enabled(False)
            self.native.scale_audit_reset()
            self.native.scale_audit_per_rule_reset()
            self.active = False


def native_rule_work_digest_valid(value: dict) -> bool:
    if (not isinstance(value, dict) or value.get("schema") not in {
            "p22_native_rule_work_v1", "p22_native_rule_work_v2",
            "p22_native_rule_work_v3"}):
        return False
    recorded = value.get("snapshot_sha256")
    payload = {key: item for key, item in value.items() if key != "snapshot_sha256"}
    if (not isinstance(recorded, str) or hashlib.sha256(json.dumps(payload,
            sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
            != recorded):
        return False
    if value.get("schema") != "p22_native_rule_work_v3":
        return True
    capture_ids = value.get("capture_ids")
    store_ids = value.get("store_instance_ids")
    rows = value.get("rules")
    totals = value.get("totals_by_metric")
    if (not isinstance(capture_ids, list) or not isinstance(store_ids, list)
            or not isinstance(rows, list) or not isinstance(totals, dict)):
        return False
    if (any(not isinstance(item, str) or not item for item in capture_ids)
            or len(capture_ids) != len(set(capture_ids))
            or any(isinstance(item, bool) or not isinstance(item, int) for item in store_ids)
            or len(store_ids) != len(set(store_ids))):
        return False
    if (not isinstance(value.get("unresolved_rule_ids"), list)
            or value.get("rule_identity_coverage") not in {"COMPLETE", "PARTIAL"}
            or (value.get("rule_identity_coverage") == "COMPLETE"
                and value["unresolved_rule_ids"])):
        return False
    recomputed = Counter()
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            return False
        capture_id, store_id = row.get("capture_id"), row.get("store_instance_id")
        if (capture_id not in capture_ids
                or (store_id is not None and (isinstance(store_id, bool)
                    or not isinstance(store_id, int) or store_id not in store_ids))
                or isinstance(row.get("count"), bool)
                or not isinstance(row.get("count"), int) or row["count"] < 0
                or not isinstance(row.get("metric"), str)
                or isinstance(row.get("rule_audit_id"), bool)
                or not isinstance(row.get("rule_audit_id"), int)):
            return False
        identity = (capture_id, store_id, row["rule_audit_id"], row["metric"])
        if identity in seen:
            return False
        seen.add(identity)
        recomputed[row["metric"]] += row["count"]
    return dict(sorted(recomputed.items())) == totals


def merge_native_rule_work_snapshots(cumulative: dict, increment: dict) -> dict:
    """Merge cumulative per-rule counters across restored native graph stores.

    Each input is digest-checked before rows are namespaced by the originating
    store. This lets a later process resume a graph checkpoint without losing
    prior rule work or conflating process-local audit IDs.
    """
    inputs = (cumulative, increment)
    if any(not native_rule_work_digest_valid(value) for value in inputs):
        raise ValueError("cannot merge a malformed native rule-work snapshot")
    rows = []
    unresolved = []
    store_ids = set()
    capture_ids = set()
    complete = True
    for value in inputs:
        schema = value["schema"]
        complete = complete and value.get("rule_identity_coverage") == "COMPLETE"
        input_capture_ids = (value.get("capture_ids", [])
            if schema == "p22_native_rule_work_v3"
            else [value["snapshot_sha256"]])
        if set(input_capture_ids).intersection(capture_ids):
            raise ValueError("native rule-work merge would double-count a captured snapshot")
        capture_ids.update(input_capture_ids)
        if schema == "p22_native_rule_work_v3":
            source_ids = value.get("store_instance_ids", [])
            for store_id in source_ids:
                store_ids.add(int(store_id))
            rows.extend(dict(row) for row in value.get("rules", []))
            unresolved.extend(value.get("unresolved_rule_ids", []))
            continue
        store_id = value.get("store_instance_id")
        capture_id = value["snapshot_sha256"]
        if store_id is not None:
            store_ids.add(int(store_id))
        for row in value.get("rules", []):
            audit_id = row.get("rule_audit_id", row.get("rule_index"))
            if audit_id is None:
                complete = False
                audit_id = -1
            rows.append({**row, "store_instance_id": store_id,
                         "capture_id": capture_id,
                         "rule_audit_id": int(audit_id)})
        unresolved.extend({"store_instance_id": store_id,
                           "rule_audit_id": int(rule_id)}
                          for rule_id in value.get("unresolved_rule_indices", []))
    rows.sort(key=lambda row: (
        row.get("store_instance_id") is None,
        row.get("store_instance_id") if row.get("store_instance_id") is not None else -1,
        row.get("capture_id", ""),
        row.get("rule_index") is None,
        row.get("rule_index") if row.get("rule_index") is not None else -1,
        row["metric"], row["rule_audit_id"]))
    totals = Counter()
    for row in rows:
        if (isinstance(row.get("count"), bool)
                or not isinstance(row.get("count"), int) or row["count"] < 0
                or not isinstance(row.get("metric"), str)
                or isinstance(row.get("rule_audit_id"), bool)
                or not isinstance(row.get("rule_audit_id"), int)):
            raise ValueError("cannot merge malformed native rule-work rows")
        totals[row["metric"]] += row["count"]
    payload = {"schema": "p22_native_rule_work_v3",
        "store_instance_id": None,
        "store_instance_ids": sorted(store_ids),
        "capture_ids": sorted(capture_ids),
        "rules": rows,
        "rule_identity_coverage": "COMPLETE" if complete and not unresolved else "PARTIAL",
        "unresolved_rule_ids": unresolved,
        "totals_by_metric": dict(sorted(totals.items()))}
    payload["snapshot_sha256"] = hashlib.sha256(json.dumps(payload,
        sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return payload


def snapshot_native_resources(agent, *, runtime_counters: dict | None = None,
                              native_rule_work: dict | None = None) -> dict:
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
    measured_runtime = None
    if runtime_counters is not None:
        if not isinstance(runtime_counters, dict):
            raise TypeError("runtime counters must be a mapping")
        measured_runtime = {}
        for key in ("native_rule_steps", "native_model_calls"):
            value = runtime_counters.get(key)
            if (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ValueError(f"runtime counter {key} must be a nonnegative integer")
            measured_runtime[key] = value
        for key in ("search_attempts_reserved", "process_peak_rss_bytes",
                    "native_candidate_validation_evaluations"):
            if key not in runtime_counters:
                continue
            value = runtime_counters[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"runtime counter {key} must be a nonnegative integer")
            measured_runtime[key] = value
        if "wall_time_seconds" in runtime_counters:
            value = runtime_counters["wall_time_seconds"]
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or value < 0):
                raise ValueError("runtime counter wall_time_seconds must be finite and nonnegative")
            measured_runtime["wall_time_seconds"] = float(value)

    measured_rule_work = None
    if native_rule_work is not None:
        if not native_rule_work_digest_valid(native_rule_work):
            raise ValueError("native rule-work snapshot digest does not verify")
        totals = native_rule_work.get("totals_by_metric")
        if not isinstance(totals, dict) or any(
                not isinstance(key, str) or isinstance(value, bool)
                or not isinstance(value, int) or value < 0
                for key, value in totals.items()):
            raise ValueError("native rule-work totals are malformed")
        measured_rule_work = native_rule_work

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
    budget_by_requester = Counter()
    status_rows = []
    training_records = []
    approval_review_seconds = []
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
        if kind == "OpenProcessAdoptionApproval":
            review_seconds = attrs.get("human_review_seconds")
            review_source = attrs.get("human_review_cost_source")
            if review_seconds is not None and (
                    isinstance(review_seconds, bool)
                    or not isinstance(review_seconds, (int, float))
                    or not math.isfinite(review_seconds) or review_seconds < 0):
                raise ValueError("human review seconds must be finite and nonnegative")
            approval_review_seconds.append(
                float(review_seconds) if review_source == "reviewer_self_report"
                and review_seconds is not None else None)
        if kind == "ProcessCurriculumEvidence" and attrs.get("split") == "training":
            cumulative["training_evidence_exposures"] += 1
            training_records.append({"node_id": str(node_id), "type": kind,
                                    "attrs": attrs})
        if kind == "ProcessCurriculumOutcome" and attrs.get("split") == "training":
            cumulative["training_outcomes"] += 1
            training_records.append({"node_id": str(node_id), "type": kind,
                                    "attrs": attrs})
        if kind == "ThinkingBudgetRequest":
            request_cost = _finite_nonnegative(attrs, "cost", kind=kind, node_id=node_id)
            cumulative["budget_requested"] += request_cost
            requester = attrs.get("requester_kind")
            if isinstance(requester, str) and requester:
                budget_by_requester[requester] += request_cost
            if attrs.get("status") == "approved":
                cumulative["budget_approved"] += _finite_nonnegative(
                    attrs, "cost", kind=kind, node_id=node_id)
            if attrs.get("status") == "denied":
                cumulative["budget_denied_cost"] += _finite_nonnegative(
                    attrs, "cost", kind=kind, node_id=node_id)
        if kind == "SolveTask":
            if (attrs.get("split") == "training"
                    and attrs.get("evaluation_only") != 1.0):
                cumulative["training_task_exposures"] += 1
                training_records.append({"node_id": str(node_id), "type": kind,
                                        "attrs": attrs})
            cumulative["native_solver_steps"] += _finite_nonnegative(
                attrs, "steps", kind=kind, node_id=node_id)
            cumulative["native_solver_primitive_work"] += _finite_nonnegative(
                attrs, "moves", kind=kind, node_id=node_id)
        if kind == "OpenProcessSearchAttempt":
            cumulative["search_declared_primitive_work"] += _finite_nonnegative(
                attrs, "work_cost", kind=kind, node_id=node_id)
        nodes.append(str(node_id))

    # Use the runtime's canonical persistence representation for the byte
    # denominator. The prior node-by-node sum omitted every edge and therefore
    # understated the graph footprint, especially for rule-heavy arms.
    graph_dict = native.graph_to_dict()
    serialized_bytes = len(json.dumps(graph_dict, sort_keys=True,
        separators=(",", ":"), default=str).encode("utf-8"))
    graph_edges = store.edge_count()
    graph_bytes_native = native.memory_total_bytes()
    training_data_bytes = len(json.dumps(training_records, sort_keys=True,
        separators=(",", ":"), default=str).encode("utf-8"))
    if not approval_review_seconds:
        approval_cost = 0.0
        approval_coverage = {"status": "MEASURED",
            "scope": "native graph contains zero candidate approval records",
            "source": "p22_native_resource_snapshot_v1.node_counts.OpenProcessAdoptionApproval"}
    elif all(value is not None for value in approval_review_seconds):
        approval_cost = sum(approval_review_seconds)
        approval_coverage = {"status": "MEASURED",
            "scope": "sum of reviewer-reported candidate review durations in seconds",
            "source": "OpenProcessAdoptionApproval.human_review_seconds; reviewer_self_report"}
    else:
        approval_cost = float(len(approval_review_seconds))
        approval_coverage = {"status": "PARTIAL_EVENT_COUNT",
            "scope": "approval events counted; one or more review durations are unavailable",
            "source": "p22_native_resource_snapshot_v1.resource_event_counts.approval_events"}
    coverage = {
        "training_data_bytes": {"status": "MEASURED_NODE_PAYLOAD_BYTES",
            "scope": "canonical training evidence, task, and outcome node records; edges excluded"},
        "native_model_calls": {"status": "MEASURED" if measured_runtime is not None
            else "UNAVAILABLE", "scope": "caller-supplied runtime counter"},
        "process_peak_rss_bytes": {"status": "MEASURED" if measured_runtime is not None
            and "process_peak_rss_bytes" in measured_runtime else "UNAVAILABLE",
            "scope": "isolated process peak RSS counter"},
        "wall_time_seconds": {"status": "MEASURED" if measured_runtime is not None
            and "wall_time_seconds" in measured_runtime else "UNAVAILABLE",
            "scope": "isolated probe elapsed time from perf_counter"},
        "proposal_work": {"status": "PARTIAL_EVENT_COUNT",
            "scope": "search attempts and proposal records counted; no operation-cost counter"},
        "verification_work": {"status": "PARTIAL_EVENT_COUNT",
            "scope": "candidate validation evaluations and qualifications counted; no operation-cost counter"},
        "approval_cost": approval_coverage,
    }
    for dimension in _CONTRACT_DIMENSIONS:
        coverage.setdefault(dimension, {"status": "UNAVAILABLE",
            "scope": "no direct instrument in this snapshot"})
    if measured_rule_work is not None:
        coverage["native_rule_term_evaluations"] = {
            "status": "MEASURED", "scope": "native per-rule term-evaluation counter"}
        class_status = ("MEASURED" if measured_rule_work.get(
            "rule_identity_coverage") == "COMPLETE" else "PARTIAL_RULE_IDENTITY")
        for dimension in ("retrieval_work", "proposal_work", "verification_work",
                          "model_refinement_work", "definition_decode_work",
                          "rollback_work"):
            coverage[dimension] = {"status": class_status,
                "scope": "term evaluations for explicitly classified native rule names"}

    statuses = [{"type": kind, "status": status, "count": count}
                for (kind, status), count in sorted(status_counts.items())]
    payload = {
        "schema": "p22_native_resource_snapshot_v1",
        "node_ids": sorted(nodes),
        "graph_node_count": len(nodes),
        "graph_edge_count": graph_edges,
        "node_counts": dict(sorted(node_counts.items())),
        "status_counts": statuses,
        "status_records": sorted(status_rows,
                                  key=lambda row: (row["type"], row["node_id"])),
        "resource_counts": {name: selected_counts.get(name, 0)
                            for name in sorted(set(_RESOURCE_KINDS.values()))},
        "cumulative_resources": {name: float(value) for name, value
                                  in sorted(cumulative.items())},
        "budget_request_cost_by_requester": dict(sorted(
            (name, float(value)) for name, value in budget_by_requester.items())),
        "resource_event_counts": {
            "proposal_events": selected_counts.get("search_attempts", 0)
                + selected_counts.get("improvement_proposals", 0),
            "qualification_events": selected_counts.get("qualifications", 0),
            "candidate_validation_evaluations": (measured_runtime or {}).get(
                "native_candidate_validation_evaluations"),
            "approval_events": selected_counts.get("candidate_approval_events", 0),
        },
        "approval_cost_seconds": approval_cost,
        "training_data_bytes": training_data_bytes,
        "resource_measurement_coverage": coverage,
        "runtime_counters": measured_runtime,
        "native_rule_work": measured_rule_work,
        "native_rule_work_by_class": _classified_native_rule_work(measured_rule_work),
        "thinking_budget_capacity": float(capacity),
        "thinking_budget_remaining": float(remaining),
        "thinking_budget_spent": float(capacity - remaining),
        "serialized_graph_bytes": serialized_bytes,
        "native_graph_memory_bytes": int(graph_bytes_native),
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
    runtime_dimensions = ["native_rule_steps", "native_model_calls"]
    if any("search_attempts_reserved" in (snapshot.get("runtime_counters") or {})
           for snapshot in snapshots.values()):
        runtime_dimensions.append("search_attempts_reserved")
    if any("process_peak_rss_bytes" in (snapshot.get("runtime_counters") or {})
           for snapshot in snapshots.values()):
        runtime_dimensions.append("process_peak_rss_bytes")
    if any("wall_time_seconds" in (snapshot.get("runtime_counters") or {})
           for snapshot in snapshots.values()):
        runtime_dimensions.append("wall_time_seconds")
    if any("native_candidate_validation_evaluations" in
           (snapshot.get("runtime_counters") or {}) for snapshot in snapshots.values()):
        runtime_dimensions.append("native_candidate_validation_evaluations")
    rule_work_values = [snapshot.get("native_rule_work") for snapshot in snapshots.values()]
    has_rule_work = any(value is not None for value in rule_work_values)
    rule_work_complete = all(value is not None for value in rule_work_values)
    rule_metrics = sorted({metric for value in rule_work_values if value is not None
        for metric in value.get("totals_by_metric", {})})
    for arm, snapshot in snapshots.items():
        if snapshot.get("schema") != "p22_native_resource_snapshot_v1":
            raise ValueError(f"{arm} has an unsupported resource snapshot")
        if not resource_snapshot_digest_valid(snapshot):
            raise ValueError(f"{arm} resource snapshot digest does not verify")
        counts = snapshot.get("resource_counts", {})
        vectors[arm] = {
            **{key: counts.get(key, 0) for key in required},
            "thinking_budget_spent": snapshot["thinking_budget_spent"],
            "graph_node_count": snapshot["graph_node_count"],
            "graph_edge_count": snapshot["graph_edge_count"],
            "serialized_graph_bytes": snapshot["serialized_graph_bytes"],
            "native_graph_memory_bytes": snapshot["native_graph_memory_bytes"],
            "training_data_bytes": snapshot.get("training_data_bytes"),
            **{f"event:{key}": value for key, value in
               snapshot.get("resource_event_counts", {}).items()},
            **{f"budget_requester:{key}": value for key, value in
               snapshot.get("budget_request_cost_by_requester", {}).items()},
            **{key: snapshot.get("cumulative_resources", {}).get(key, 0.0)
               for key in cumulative_dimensions},
            **{key: (snapshot.get("runtime_counters") or {}).get(key)
               for key in runtime_dimensions},
            **{f"native_rule_work:{metric}": (
                   snapshot.get("native_rule_work", {}).get("totals_by_metric", {}).get(
                       metric, 0) if snapshot.get("native_rule_work") is not None else None)
               for metric in rule_metrics},
        }
        rule_work = snapshot.get("native_rule_work")
        if rule_work is not None and not native_rule_work_digest_valid(rule_work):
            raise ValueError(f"{arm} native rule-work snapshot digest does not verify")
    common = set.intersection(*(set(vector) for vector in vectors.values()))
    matched = {key: (None not in {vector[key] for vector in vectors.values()}
                     and len({vector[key] for vector in vectors.values()}) == 1)
               for key in sorted(common)}
    unavailable = sorted(key for key in common
        if any(vector[key] is None for vector in vectors.values()))
    measurement_gaps = sorted({dimension for snapshot in snapshots.values()
        for dimension, detail in snapshot.get("resource_measurement_coverage", {}).items()
        if detail.get("status") not in {"MEASURED", "MEASURED_NODE_PAYLOAD_BYTES"}})
    return {"arms": vectors, "matched": matched,
            "all_resource_dimensions_match": all(matched.values()) and
                (not has_rule_work or rule_work_complete),
            "native_rule_work_complete": rule_work_complete,
            "all_contract_dimensions_measured": not measurement_gaps,
            "contract_measurement_gaps": measurement_gaps,
            "unavailable_dimensions": unavailable,
            "failure_statuses_retained": True}


def analyzer_resource_record(snapshot: dict, *, cumulative_primitive_work: int,
                             wall_time_seconds: float | None = None) -> dict:
    """Map a verified native snapshot to P22 analyzer values and evidence.

    Missing instrumentation remains ``None``/``UNAVAILABLE``; event counts
    cannot stand in for operation cost. ``cumulative_primitive_work`` must
    come from the digest-bound checkpoint lineage, while wall time is measured
    by the isolated worker outside this snapshot.
    """
    if snapshot.get("schema") != "p22_native_resource_snapshot_v1":
        raise ValueError("unsupported P22 resource snapshot")
    if not resource_snapshot_digest_valid(snapshot):
        raise ValueError("P22 resource snapshot digest does not verify")
    if (isinstance(cumulative_primitive_work, bool)
            or not isinstance(cumulative_primitive_work, int)
            or cumulative_primitive_work < 0):
        raise ValueError("cumulative primitive work must be a nonnegative integer")
    if wall_time_seconds is not None and (
            isinstance(wall_time_seconds, bool)
            or not isinstance(wall_time_seconds, (int, float))
            or not math.isfinite(wall_time_seconds) or wall_time_seconds < 0):
        raise ValueError("wall time must be finite and nonnegative")

    cumulative = snapshot.get("cumulative_resources", {})
    runtime = snapshot.get("runtime_counters") or {}
    counts = snapshot.get("resource_counts", {})
    coverage = snapshot.get("resource_measurement_coverage", {})
    exposures = (cumulative.get("training_evidence_exposures", 0)
        + cumulative.get("training_task_exposures", 0)
        + cumulative.get("training_outcomes", 0))
    primitive = (cumulative.get("native_solver_primitive_work", 0)
        + cumulative.get("search_declared_primitive_work", 0))
    if cumulative_primitive_work < primitive:
        raise ValueError("checkpoint cumulative primitive work is below measured snapshot work")
    events = snapshot.get("resource_event_counts", {})
    # Derive from the digest-bound rule rows so older v2 development snapshots
    # remain auditable without rewriting their raw bytes.
    class_work = snapshot.get("native_rule_work_by_class")
    if class_work is None:
        class_work = _classified_native_rule_work(snapshot.get("native_rule_work"))
    class_work_complete = ((snapshot.get("native_rule_work") or {}).get(
        "rule_identity_coverage") == "COMPLETE")
    direct = {
        "primitive_work": primitive,
        "cumulative_primitive_work": cumulative_primitive_work,
        "native_rule_term_evaluations": (runtime.get("native_rule_term_evaluations")
            if runtime.get("native_rule_term_evaluations") is not None else
            (snapshot.get("native_rule_work") or {}).get("totals_by_metric", {}).get(
                "term_evaluations")),
        "native_rule_steps": runtime.get("native_rule_steps"),
        "native_model_calls": runtime.get("native_model_calls"),
        "search_attempts": counts.get("search_attempts", 0),
        "training_data_exposures": exposures,
        "training_data_bytes": snapshot.get("training_data_bytes"),
        "thinking_budget_spent": snapshot.get("thinking_budget_spent"),
        "serialized_graph_bytes": snapshot.get("serialized_graph_bytes"),
        "native_graph_memory_bytes": snapshot.get("native_graph_memory_bytes"),
        "process_peak_rss_bytes": runtime.get("process_peak_rss_bytes"),
        "wall_time_seconds": (wall_time_seconds if wall_time_seconds is not None
            else runtime.get("wall_time_seconds")),
    }
    classified = {
        name: (class_work.get(name, {}).get("native_term_evaluations", 0)
            if class_work_complete else None)
        for name in ("retrieval_work", "proposal_work", "verification_work",
                     "model_refinement_work", "definition_decode_work",
                     "rollback_work")}
    approval_measurement = coverage.get("approval_cost", {})
    approval_cost = snapshot.get("approval_cost_seconds")
    approval_status = approval_measurement.get("status")
    if approval_status != "MEASURED":
        approval_cost = events.get("approval_events", 0)
    values = {**direct, **classified, "approval_cost": approval_cost}
    measurements = {}
    for name, value in direct.items():
        source = {
            "primitive_work": "p22_native_resource_snapshot_v1.cumulative_resources",
            "cumulative_primitive_work": "p22_native_checkpoint_v1.cumulative_primitive_work",
            "native_rule_term_evaluations": "p22_native_resource_snapshot_v1.native_rule_work.totals_by_metric.term_evaluations",
            "native_rule_steps": "p22_native_resource_snapshot_v1.runtime_counters.native_rule_steps",
            "native_model_calls": "p22_native_resource_snapshot_v1.runtime_counters.native_model_calls",
            "search_attempts": "p22_native_resource_snapshot_v1.resource_counts.search_attempts",
            "training_data_exposures": "p22_native_resource_snapshot_v1.cumulative_resources.training_exposures",
            "training_data_bytes": "p22_native_resource_snapshot_v1.training_data_bytes",
            "thinking_budget_spent": "p22_native_resource_snapshot_v1.thinking_budget_spent",
            "serialized_graph_bytes": "p22_native_resource_snapshot_v1.serialized_graph_bytes",
            "native_graph_memory_bytes": "p22_native_resource_snapshot_v1.native_graph_memory_bytes",
            "process_peak_rss_bytes": "p22_native_resource_snapshot_v1.runtime_counters.process_peak_rss_bytes",
            "wall_time_seconds": ("p22_isolated_worker.perf_counter"
                if wall_time_seconds is not None else
                "p22_native_resource_snapshot_v1.runtime_counters.wall_time_seconds"),
        }[name]
        status = ("MEASURED_NODE_PAYLOAD_BYTES" if name == "training_data_bytes"
            else "MEASURED") if value is not None else "UNAVAILABLE"
        measurements[name] = {"status": status, "source": source}
    for name in classified:
        measurements[name] = {
            "status": "MEASURED" if values[name] is not None else "UNAVAILABLE",
            "source": ("p22_native_resource_snapshot_v1.native_rule_work_by_class"
                "[native_term_evaluations; complete rule identity coverage]")}
    measurements["approval_cost"] = {
        "status": approval_status or "UNAVAILABLE",
        "source": approval_measurement.get("source",
            "p22_native_resource_snapshot_v1.resource_event_counts.approval_events")}
    # Preserve the snapshot's own declarations; it may be newer than this
    # adapter and should never have a weaker coverage result.
    for name, detail in coverage.items():
        if (name in measurements and name not in {
                "wall_time_seconds", "cumulative_primitive_work"}
                and not (class_work_complete and name in classified)
                and detail.get("status") == "UNAVAILABLE"):
            measurements[name] = {"status": "UNAVAILABLE",
                                  "source": detail.get("scope", "unavailable")}
    return {"resources": values, "resource_measurements": measurements,
            "resource_snapshot_sha256": snapshot["snapshot_sha256"]}


def resource_snapshot_digest_valid(snapshot: dict) -> bool:
    if not isinstance(snapshot, dict):
        return False
    recorded_digest = snapshot.get("snapshot_sha256")
    payload = {key: value for key, value in snapshot.items()
               if key != "snapshot_sha256"}
    actual_digest = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    return recorded_digest == actual_digest
