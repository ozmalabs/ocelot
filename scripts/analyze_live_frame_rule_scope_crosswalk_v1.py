#!/usr/bin/env python3
"""Crosswalk live traced RuleUIDs to exported rule match/where/effect shapes."""
from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_workers_raw_20261003.json.gz"
CAPTURE = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_20261003.json"
OUT = ROOT / "evaluation/reports/live_frame_rule_scope_crosswalk_v1_20261003.json"
POPULATION_TERMS = {"NodesOfType", "NodesWhere", "ScalarAttrTriples", "Edges"}
TRAVERSAL_TERMS = {"EvalSubgraph", "ReachableFrom"}
ADJACENCY_TERMS = {"Neighbours", "InNeighbours", "MapNeighbours", "SlideNeighbours"}
EXTERNAL_TERMS = {"UseTool", "ReadFile", "ProgCallExtern"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(value):
    if isinstance(value, dict):
        if isinstance(value.get("type"), str):
            yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def main() -> None:
    summary = json.loads(CAPTURE.read_text())
    if sha(RAW) != summary["raw_compressed_sha256"]:
        raise SystemExit("capture archive SHA-256 mismatch")
    with gzip.open(RAW, "rb") as stream:
        raw_digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            raw_digest.update(block)
    if raw_digest.hexdigest() != summary["raw_sha256"]:
        raise SystemExit("decompressed capture SHA-256 mismatch")
    with gzip.open(RAW, "rt", encoding="utf-8") as stream:
        raw = json.load(stream)
    run = next(row for row in raw["runs"] if "native_exported_rules" in row)
    rules = {int(rule["rule_uid"]): rule for rule in run["native_exported_rules"]}

    weights: Counter[int] = Counter()
    by_kind: dict[int, Counter[str]] = {}
    prompt_uids: dict[str, set[int]] = {}
    for worker in raw["runs"]:
        for request in worker["requests"]:
            key = str(request["prompt"])
            prompt_uids.setdefault(key, set())
            for row in request["access_rows"]:
                uid, kind, count = int(row[0]), str(row[1]), int(row[6])
                prompt_uids[key].add(uid)
                weights[uid] += count
                by_kind.setdefault(uid, Counter())[kind] += count

    activity = []
    missing = []
    population_rule_uids = []
    traversal_rule_uids = []
    adjacency_rule_uids = []
    external_rule_uids = []
    global_attr_keys: Counter[str] = Counter()
    term_counts: Counter[str] = Counter()
    for uid in sorted(weights):
        rule = rules.get(uid)
        if rule is None:
            missing.append({"rule_uid": uid, "weighted_access_events": weights[uid],
                            "event_kinds": dict(sorted(by_kind[uid].items()))})
            continue
        terms = list(walk(rule.get("where"))) + list(walk(rule.get("effects")))
        term_types = Counter(term["type"] for term in terms)
        term_counts.update(term_types)
        population = sorted(POPULATION_TERMS & set(term_types))
        traversal = sorted(TRAVERSAL_TERMS & set(term_types))
        adjacency = sorted(ADJACENCY_TERMS & set(term_types))
        external = sorted(EXTERNAL_TERMS & set(term_types))
        if population:
            population_rule_uids.append(uid)
        if traversal:
            traversal_rule_uids.append(uid)
        if adjacency:
            adjacency_rule_uids.append(uid)
        if external:
            external_rule_uids.append(uid)
        attrs = sorted({str(term.get("key")) for term in terms
                        if term.get("type") in {"Attr", "AttrByName"} and term.get("key") is not None})
        global_attr_keys.update(attrs)
        matches = rule.get("match") or []
        match_edges = []
        if isinstance(matches, list):
            for edge in matches:
                if isinstance(edge, list) and len(edge) >= 3:
                    match_edges.append(str(edge[1]))
        effect_kinds = sorted({str(effect[0]) for effect in rule.get("effects", [])
                               if isinstance(effect, list) and effect})
        activity.append({
            "rule_uid": uid, "name": rule.get("name"),
            "weighted_access_events": weights[uid],
            "event_kinds": dict(sorted(by_kind[uid].items())),
            "match_edge_types": sorted(set(match_edges)),
            "where_and_effect_term_counts": dict(sorted(term_types.items())),
            "attribute_keys_referenced_in_exported_terms": attrs,
            "effect_kinds": effect_kinds,
            "whole_population_term_types": population,
            "subgraph_or_reachability_term_types": traversal,
            "local_adjacency_term_types": adjacency,
            "external_boundary_term_types": external,
        })

    all_uids = set(weights)
    checks = {
        "capture_hashes_match": True,
        "all_captured_rule_uids_accounted_for": len(activity) + len(missing) == len(all_uids),
        "prompt_uids_accounted_for": len(prompt_uids) == 2,
        "six_late_minted_uids_retained_as_unmapped": len(missing) == 6,
    }
    result = {
        "schema_version": 1,
        "run_id": "live-frame-rule-scope-crosswalk-v1-20261003",
        "capture_summary_path": str(CAPTURE.relative_to(ROOT)),
        "capture_summary_sha256": sha(CAPTURE),
        "raw_archive_path": str(RAW.relative_to(ROOT)),
        "raw_archive_sha256": sha(RAW),
        "raw_uncompressed_sha256": raw_digest.hexdigest(),
        "analysis_script_sha256": sha(Path(__file__).resolve()),
        "native_rule_export_replicate": run["replicate"],
        "checks": checks,
        "summary": {
            "distinct_traced_rule_uids": len(all_uids),
            "exported_rule_definitions": len(activity),
            "traced_uids_missing_from_pre_request_export": len(missing),
            "export_mapped_rules_with_whole_population_terms": len(population_rule_uids),
            "export_mapped_rules_with_subgraph_or_reachability_terms": len(traversal_rule_uids),
            "export_mapped_rules_with_local_adjacency_terms": len(adjacency_rule_uids),
            "export_mapped_rules_with_external_boundary_terms": len(external_rule_uids),
            "weighted_access_events_mapped_to_exported_rules": sum(r["weighted_access_events"] for r in activity),
            "weighted_access_events_on_unmapped_rules": sum(r["weighted_access_events"] for r in missing),
            "term_types_in_active_exported_rules": dict(sorted(term_counts.items())),
            "attribute_keys_referenced_in_active_exported_rules": dict(sorted(global_attr_keys.items())),
            "prompt_rule_uid_counts": {prompt: len(ids) for prompt, ids in sorted(prompt_uids.items())},
        },
        "unmapped_rule_uids": missing,
        "active_exported_rule_activity": activity,
        "claim_boundary": "The rule export was captured before the first conversation. Six runtime UIDs first observed during the request are not in that export, so no static definition is inferred for them. Exported match edges and Term AST shapes are source/engine representations, not a complete dependency scope or factorization proof. Attribute references and broad Terms are candidate access classes; dynamic values, callbacks, failed matches, and uninstrumented reads remain unresolved.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "summary": {key: value for key, value in result["summary"].items()
                                  if key not in {"term_types_in_active_exported_rules",
                                                 "attribute_keys_referenced_in_active_exported_rules"}},
                      "unmapped_rule_uids": missing}, indent=2))
    if not all(checks.values()):
        raise SystemExit("live frame rule-scope crosswalk gate failed")


if __name__ == "__main__":
    main()
