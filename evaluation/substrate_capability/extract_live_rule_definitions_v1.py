#!/usr/bin/env python3
"""Extract deduplicated, runtime-touched rule syntax from a locked capture."""
from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_3_workers_raw_20261005.json.gz"
SUMMARY = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_3_20261005.json"
ANALYSIS = ROOT / "evaluation/reports/live_frame_rule_scope_capture_v1_3_analysis_20261005.json"
OUT = ROOT / "evaluation/reports/live_rule_definitions_v1_20261005.json"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def term_rows(value: Any, path: str = ""):
    if isinstance(value, dict):
        if isinstance(value.get("type"), str):
            yield path or "$", value
        for key, child in value.items():
            yield from term_rows(child, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from term_rows(child, f"{path}[{index}]")


def compact_argument(value: Any) -> Any:
    if isinstance(value, dict):
        if isinstance(value.get("type"), str):
            kind = value["type"]
            for key in ("name", "key", "node_type", "edge_type", "any_type", "value"):
                if key in value and not isinstance(value[key], (dict, list)):
                    return {"type": kind, key: value[key]}
            return {"type": kind}
        return {key: compact_argument(item) for key, item in value.items()
                if not isinstance(item, (dict, list))}
    if isinstance(value, list):
        return [compact_argument(item) for item in value]
    return value


def main() -> None:
    raw_bytes = RAW.read_bytes()
    raw_payload = gzip.decompress(raw_bytes)
    raw_sha = sha_bytes(raw_payload)
    summary = json.loads(SUMMARY.read_text())
    analysis = json.loads(ANALYSIS.read_text())
    if raw_sha != summary["raw_uncompressed_sha256"]:
        raise SystemExit("raw capture hash does not match source-locked capture summary")
    if not all(summary["checks"].values()) or not all(analysis["checks"].values()):
        raise SystemExit("refusing to extract definitions from failed capture/analysis")
    raw = json.loads(raw_payload)
    selected: dict[int, dict] = {}
    definition_hashes: dict[int, set[str]] = {}
    touched: dict[int, Counter[str]] = {}
    for run in raw["runs"]:
        for request, snapshot in zip(run["capture"]["requests"], run["request_rule_snapshots"]):
            observed: Counter[int] = Counter()
            for access in request["access_rows"]:
                observed[int(access[0])] += int(access[6])
            rules = {int(rule["rule_uid"]): rule for rule in snapshot["after_rules"]}
            for uid in observed:
                rule = rules.get(uid)
                if rule is None:
                    raise SystemExit(f"runtime-touched rule {uid} has no post-request definition")
                encoded = json.dumps(rule, sort_keys=True, separators=(",", ":"), default=str)
                definition_hashes.setdefault(uid, set()).add(sha_bytes(encoded.encode()))
                selected.setdefault(uid, rule)
                touched.setdefault(uid, Counter())[str(request["prompt"])] += observed[uid]
    unstable = {uid: sorted(hashes) for uid, hashes in definition_hashes.items() if len(hashes) != 1}
    if unstable:
        raise SystemExit(f"runtime rule definitions vary across observed exports: {unstable}")
    expected = {int(row["rule_uid"]): row for row in analysis["runtime_rule_definition_activity"]}
    if set(expected) != set(selected):
        raise SystemExit("runtime-touched definition UID set differs from independent analysis")

    rows = []
    term_counts = Counter()
    for uid, rule in sorted(selected.items()):
        terms = []
        for path, term in term_rows([rule.get("where"), rule.get("effects")]):
            kind = term["type"]
            term_counts[kind] += 1
            args = {}
            for key in ("node", "source", "cell", "node_type", "edge_type", "any_type", "key", "name", "value"):
                if key in term:
                    args[key] = compact_argument(term[key])
            terms.append({"path": path, "type": kind, "arguments": args})
        rows.append({
            "rule_uid": uid, "name": rule.get("name"),
            "definition_sha256": next(iter(definition_hashes[uid])),
            "runtime_weighted_access_events_by_prompt": dict(sorted(touched[uid].items())),
            "match": rule.get("match"), "match_type": rule.get("match_type"),
            "terms": terms, "effects": rule.get("effects"),
        })
        analyzed = expected[uid]
        if dict(Counter(row["type"] for row in terms)) != analyzed["where_and_effect_term_counts"]:
            raise SystemExit(f"Term syntax count mismatch for RuleUID {uid}")
        if next(iter(definition_hashes[uid])) != analyzed["definition_sha256"]:
            raise SystemExit(f"definition hash mismatch for RuleUID {uid}")
    result = {
        "schema": "LiveRuntimeRuleDefinitionsV1",
        "run_id": "live-runtime-rule-definitions-v1-20261005",
        "raw_capture_path": str(RAW.relative_to(ROOT)),
        "raw_capture_sha256": sha_bytes(raw_bytes),
        "raw_uncompressed_sha256": raw_sha,
        "capture_summary_sha256": sha_bytes(SUMMARY.read_bytes()),
        "runtime_analysis_sha256": sha_bytes(ANALYSIS.read_bytes()),
        "summary": {
            "distinct_runtime_touched_rules": len(rows),
            "definitions_identical_across_observed_exports": not unstable,
            "matches_independent_runtime_analysis": True,
            "observed_rule_definition_hashes": {str(uid): next(iter(hashes)) for uid, hashes in sorted(definition_hashes.items())},
            "term_syntax_occurrences": dict(sorted(term_counts.items())),
        },
        "rules": rows,
        "claim_boundary": "Definitions are deduplicated from post-request snapshots only for rule IDs observed in runtime access traces. The trace establishes rule identity activity, not that every syntactic Term node executed or that all candidate, host, evaluator-helper, or scheduler dependencies are represented.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
