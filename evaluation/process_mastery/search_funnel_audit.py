"""External, read-only P22 search funnel accounting (P23.03)."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/research/engine_substrate/COGNITION_SEARCH_DIAGNOSIS_CONTRACT.md"
TABLE_HEADER = "| Path | SHA-256 | Class | Status | Branch disposition | Parent artifact | Training draws |"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inventory() -> list[dict]:
    text = CONTRACT.read_text()
    table = text.split(TABLE_HEADER, 1)[1]
    rows = []
    for line in table.splitlines():
        match = re.fullmatch(
            r"\| `([^`]+)` \| `([0-9a-f]{64})` \| ([^|]+) \| ([^|]+) \| ([^|]+) \| (—|`[^`]+`) \| ([^|]+) \|",
            line,
        )
        if match:
            path, digest, kind, status, disposition, parent, _draws = match.groups()
            if kind == "branch":
                rows.append({"path": path, "sha256": digest,
                    "status": status.strip(), "disposition": disposition.strip(),
                    "parent": parent.strip("`") if parent != "—" else None})
    return rows


def _records(snapshot: dict, node_type: str) -> dict[str, str]:
    return {row["node_id"]: str(row.get("status", ""))
        for row in snapshot.get("status_records", [])
        if row.get("type") == node_type}


def _parent_snapshot(record: dict) -> tuple[dict, dict]:
    parent = record.get("parent_checkpoint") or {}
    raw = parent.get("resource_snapshot_json")
    if raw:
        return parent, json.loads(raw)
    return parent, {"status_records": [], "node_counts": {}, "runtime_counters": {},
        "graph_node_count": 0, "graph_edge_count": 0}


def _effect_signature(candidate: dict) -> str | None:
    receipts = candidate.get("qualification_inputs", {}).get("digest_receipts", [])
    effects = [receipt.get("effect_digest") for receipt in receipts
               if receipt.get("status") == "verified"]
    if not effects:
        return None
    return json.dumps(effects[0], sort_keys=True, separators=(",", ":"))


def _effect_values(signature: str | None):
    if signature is None:
        return None
    try:
        value = json.loads(signature)
        if len(value) == 1 and isinstance(value[0], list):
            value = value[0]
        return tuple(value)
    except (TypeError, ValueError):
        return None


def _known_parent_effects(parent: dict) -> set[tuple]:
    graph_json = parent.get("native_graph_snapshot_json")
    if not graph_json:
        return set()
    graph = json.loads(graph_json)
    known = set()
    for node in graph.get("nodes", []):
        typ, attrs = node.get("type"), node.get("attrs", {})
        if typ not in {"ProcessSchema", "OpenProcessCandidate"}:
            continue
        if attrs.get("domain") not in {"p22-development-d4", "p22-development-loopover"}:
            continue
        is_active = typ == "ProcessSchema" and attrs.get("status") == "active"
        is_adopted = (typ == "OpenProcessCandidate"
            and attrs.get("status") == "adopted_candidate"
            and attrs.get("adoption_status") == "approved")
        if not (is_active or is_adopted):
            continue
        params = attrs.get("params", {})
        if isinstance(params, dict) and set(params) == {"__list__"}:
            params = params["__list__"]
        if isinstance(params, list):
            known.add(tuple(params))
        effect = attrs.get("effect_digest") or attrs.get("adopted_effect_digest")
        if isinstance(effect, dict) and set(effect) == {"__list__"}:
            effect = effect["__list__"]
        if isinstance(effect, list) and effect:
            first = effect[0]
            if isinstance(first, dict) and set(first) == {"__list__"}:
                first = first["__list__"]
            if isinstance(first, list):
                known.add(tuple(first))
    return known


def _parent_candidate_effects(parent: dict) -> set[tuple]:
    graph_json = parent.get("native_graph_snapshot_json")
    if not graph_json:
        return set()
    graph = json.loads(graph_json)
    effects = set()
    for node in graph.get("nodes", []):
        attrs = node.get("attrs", {})
        if node.get("type") != "OpenProcessCandidate":
            continue
        raw = attrs.get("effect_digest") or attrs.get("adopted_effect_digest")
        if isinstance(raw, dict) and set(raw) == {"__list__"}:
            raw = raw["__list__"]
        if isinstance(raw, list) and raw:
            value = raw[0]
            if isinstance(value, dict) and set(value) == {"__list__"}:
                value = value["__list__"]
            if isinstance(value, list):
                effects.add(tuple(value))
    return effects


def audit_branch(path: Path, *, expected_sha256: str | None = None,
                 disposition: str = "unique branch") -> dict:
    """Compare one restored graph to its embedded parent; never sum ancestors."""
    path = path.resolve()
    raw_sha = _sha256(path)
    if expected_sha256 and raw_sha != expected_sha256:
        raise ValueError(f"artifact digest mismatch: {path}")
    record = json.loads(path.read_text())
    if disposition.startswith("interrupted;"):
        return {"artifact_path": str(path.relative_to(ROOT)),
            "artifact_sha256": raw_sha, "status": record.get("status"),
            "branch_disposition": disposition,
            "attempts": {"completed": 0, "credit": 0,
                "reason": "invalid/interrupted allocation has no completed graph"},
            "independent_work_credit": 0}

    current = record.get("resource_snapshot", {})
    parent, prior = _parent_snapshot(record)
    parent_id = parent.get("checkpoint_id")
    parent_digest = parent.get("checkpoint_digest")
    current_attempts = _records(current, "OpenProcessSearchAttempt")
    prior_attempts = _records(prior, "OpenProcessSearchAttempt")
    new_attempt_ids = set(current_attempts) - set(prior_attempts)
    cumulative_count = int(current.get("node_counts", {}).get(
        "OpenProcessSearchAttempt", 0))
    inherited_count = int(prior.get("node_counts", {}).get(
        "OpenProcessSearchAttempt", 0))
    increment = cumulative_count - inherited_count
    if increment != len(new_attempt_ids) or increment < 0:
        raise ValueError(f"attempt inventory does not conserve branch work: {path}")
    attempt_status_counts = Counter(current_attempts[item] for item in new_attempt_ids)
    if sum(attempt_status_counts.values()) != increment:
        raise ValueError(f"attempt statuses do not conserve branch work: {path}")

    new_ids = {}
    for node_type in ("OpenProcessSearchRequest", "OpenProcessCandidate",
            "IndependentImprovementProposal", "IndependentImprovementQualification",
            "OpenProcessAdoptionApproval", "OpenProcessWorldReceipt"):
        new_ids[node_type] = set(_records(current, node_type)) - set(_records(prior, node_type))

    candidate_rows = {row["candidate_id"]: row for row in record.get("candidates", [])}
    new_candidate_rows = [candidate_rows[item] for item in sorted(new_ids[
        "OpenProcessCandidate"]) if item in candidate_rows]
    verified_expressions = {row.get("expression_digest") for row in new_candidate_rows
        if row.get("expression_digest") and any(
            receipt.get("status") == "verified"
            for receipt in row.get("qualification_inputs", {}).get("digest_receipts", []))}
    parent_effects = _known_parent_effects(parent)
    existing_effects = _parent_candidate_effects(parent)
    signatures = []
    duplicates = []
    held_or_identity = []
    useful_effects = set()
    for row in new_candidate_rows:
        signature = _effect_signature(row)
        effect = _effect_values(signature)
        signatures.append(signature)
        if effect is None:
            continue
        identity = tuple(range(len(effect)))
        if effect == identity or effect in parent_effects:
            held_or_identity.append(row["candidate_id"])
        elif effect in existing_effects:
            duplicates.append(row["candidate_id"])
        else:
            useful_effects.add(effect)
        existing_effects.add(effect)

    trial_map = record.get("candidate_independent_goal_trials", {})
    trial_rows = []
    for candidate_id in sorted(new_ids["OpenProcessCandidate"]):
        value = candidate_rows.get(candidate_id, {}).get("independent_goal_trials", [])
        if isinstance(value, dict):
            value = [row for rows in value.values() for row in rows]
        if isinstance(value, list):
            trial_rows.extend(row for row in value if isinstance(row, dict))
    trial_ids = {row.get("attempt_id") for row in trial_rows if row.get("attempt_id")}
    trial_statuses = Counter(str(row.get("status", "unknown")) for row in trial_rows)

    request_attempts = sum(int(row.get("attempt_count", 0))
                           for row in record.get("search_requests", []))
    if request_attempts != cumulative_count:
        raise ValueError(f"request attempt receipts do not equal graph counter: {path}")
    request_budget_rows = [{"request_id": row.get("request_id"),
        "task_keys": row.get("task_keys", []),
        "attempts_used": int(row.get("attempt_count", 0)),
        "attempt_ceiling": int(row.get("max_attempts", 0)),
        "remaining_headroom": max(0, int(row.get("max_attempts", 0))
                                   - int(row.get("attempt_count", 0)))}
        for row in record.get("search_requests", [])]
    request_ceilings = [row["attempt_ceiling"] for row in request_budget_rows]
    global_ceiling = int(record.get("global_attempt_ceiling", 0))
    runtime, parent_runtime = current.get("runtime_counters", {}), prior.get("runtime_counters", {})
    wall_increment = max(0.0, float(runtime.get("wall_time_seconds", 0.0))
                         - float(parent_runtime.get("wall_time_seconds", 0.0)))
    peak_rss_increment = max(0, int(runtime.get("process_peak_rss_bytes", 0))
                            - int(parent_runtime.get("process_peak_rss_bytes", 0)))
    node_increment = int(current.get("graph_node_count", 0)) - int(prior.get("graph_node_count", 0))
    edge_increment = int(current.get("graph_edge_count", 0)) - int(prior.get("graph_edge_count", 0))

    rejection_rows = []
    qualification_by_candidate = {row["candidate_id"]: row
        for row in record.get("candidates", [])}
    for row in new_candidate_rows:
        effect = _effect_values(_effect_signature(row))
        if effect is None:
            reason = "expression_effect_receipt_missing"
            predicate = "candidate_expression_attestation"
        elif effect == tuple(range(len(effect))):
            reason = "identity_effect_excluded"
            predicate = "iip_novel_effect_guard.identity_effect"
        elif effect in parent_effects:
            reason = "effect_matches_active_or_adopted_parent"
            predicate = "iip_novel_effect_guard.active_or_adopted_effect"
        elif row["candidate_id"] in duplicates:
            reason = "effect_repeats_prior_candidate"
            predicate = "unique_effect_deduplication"
        else:
            trials_for_candidate = trial_map.get(row["candidate_id"], [])
            if isinstance(trials_for_candidate, dict):
                trials_for_candidate = [v for values in trials_for_candidate.values() for v in values]
            reason = ("no_independent_goal_trials" if not trials_for_candidate
                      else "no_qualifying_independent_goal_composition_observed")
            predicate = "iip_qualify_after_independent_goal_composition"
        row_summary = qualification_by_candidate[row["candidate_id"]]
        rejection_rows.append({"candidate_id": row["candidate_id"],
            "expression_digest": row_summary.get("expression_digest"),
            "effect": effect, "source_attempt_ids": [attempt
                for proposal in row_summary.get("proposals", [])
                for attempt in proposal.get("source_attempt_ids", [])],
            "qualification_count": int(row_summary.get("qualification_count", 0)),
            "predicate": predicate, "reason": reason,
            "parent_checkpoint_id": parent_id,
            "parent_checkpoint_digest": parent_digest})

    attempts_without_candidate_link = max(0, increment - len({attempt
        for row in new_candidate_rows for proposal in row.get("proposals", [])
        for attempt in proposal.get("source_attempt_ids", []) if attempt in new_attempt_ids}))
    unique_syntax_count = len(verified_expressions)
    unique_effect_count = len({signature for signature in signatures if signature is not None})
    useful_count = len(useful_effects)
    return {"artifact_path": str(path.relative_to(ROOT)),
        "artifact_sha256": raw_sha, "status": record.get("status"),
        "family": record.get("family"), "generation": record.get("parent_checkpoint", {}).get("generation"),
        "branch_disposition": disposition,
        "parent_checkpoint_id": parent_id, "parent_checkpoint_digest": parent_digest,
        "cumulative_graph_attempts": cumulative_count,
        "inherited_graph_attempts": inherited_count,
        "attempts": {"new": increment,
            "by_status": dict(sorted(attempt_status_counts.items())),
            "status_count_conserved": sum(attempt_status_counts.values()) == increment,
            "unlinked_from_candidate_summary": attempts_without_candidate_link,
            "expression_detail_coverage": "PARTIAL_CANDIDATE_BEARING_ATTEMPTS_ONLY"},
        "funnel": {"attempts_new": increment,
            "verified_candidate_expressions_observed": unique_syntax_count,
            "unique_candidate_effects_observed": unique_effect_count,
            "new_legal_unique_effects": useful_count,
            "new_candidate_nodes": len(new_ids["OpenProcessCandidate"]),
            "new_independent_goal_trials": len(trial_ids),
            "independent_trial_statuses": dict(sorted(trial_statuses.items())),
            "new_qualifications": len(new_ids["IndependentImprovementQualification"]),
            "new_approvals": len(new_ids["OpenProcessAdoptionApproval"]),
            "new_world_receipts": len(new_ids["OpenProcessWorldReceipt"]),
            "attempt_to_expression_gap_is_uninstrumented": attempts_without_candidate_link},
        "candidate_effect_duplicates": duplicates,
        "candidate_effects_excluded_as_identity_or_parent_held": held_or_identity,
        "candidate_rejections": rejection_rows,
        "request_attempt_total_cumulative": request_attempts,
        "request_attempt_ceiling_each": request_ceilings,
        "request_budget_rows": request_budget_rows,
        "request_attempt_headroom_total": sum(row["remaining_headroom"]
                                               for row in request_budget_rows),
        "global_attempt_ceiling": global_ceiling,
        "global_attempt_headroom": max(0, global_ceiling - cumulative_count),
        "candidate_transfer_depth": record.get("candidate_transfer_depth"),
        "independent_trial_budget": "not a search-attempt ceiling; report observed trials separately",
        "resources": {"wall_time_seconds_increment": wall_increment,
            "peak_rss_bytes_increment": peak_rss_increment,
            "graph_nodes_increment": node_increment,
            "graph_edges_increment": edge_increment,
            "per_useful_effect": ({"wall_time_seconds": wall_increment / useful_count,
                "peak_rss_bytes": peak_rss_increment / useful_count,
                "graph_nodes": node_increment / useful_count,
                "graph_edges": edge_increment / useful_count} if useful_count else None)},
        "heldout_accessed": False, "agent_graph_mutated": False}


def run_inventory_audit() -> dict:
    rows = _inventory()
    branches = []
    for row in rows:
        branches.append(audit_branch(ROOT / row["path"],
            expected_sha256=row["sha256"], disposition=row["disposition"]))
    credited = sum(row.get("independent_work_credit", row.get("attempts", {}).get("new", 0))
                   for row in branches if row["branch_disposition"] != "duplicate/replay")
    source_paths = [ROOT / path for path in (
        "evaluation/process_mastery/p22_resource_accounting.py",
        "evaluation/process_mastery/p22_development.py",
        "evaluation/process_mastery/linear_p22_v1.py",
        "scripts/gen_open_process_search_seed.py",
        "scripts/gen_independent_improvement_seed.py",
        "seeds/open_process_search.json",
        "seeds/independent_improvement.json",
        "docs/research/engine_substrate/COGNITION_SEARCH_DIAGNOSIS_CONTRACT.md")]
    return {"schema": "p23_search_funnel_audit_v1",
        "scope": "hash_bound_archived_development_branches_only",
        "branch_count": len(branches),
        "cumulative_development_attempts_across_distinct_restorations": credited,
        "branch_records": branches,
        "heldout_accessed": False, "agent_graph_mutated": False,
        "source_hashes": {str(path.relative_to(ROOT)): _sha256(path)
                          for path in source_paths},
        "contract_sha256": _sha256(CONTRACT),
        "analyzer_sha256": _sha256(Path(__file__).resolve())}


if __name__ == "__main__":
    print(json.dumps(run_inventory_audit(), indent=2, sort_keys=True))
