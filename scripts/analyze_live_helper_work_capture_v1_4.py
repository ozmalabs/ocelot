#!/usr/bin/env python3
"""Independently compare v1.3 post-request rule exports with v1 traces."""
from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_helper_work_capture_v1_4_workers_raw_20261005.json.gz"
SUMMARY = ROOT / "evaluation/reports/substrate_live_helper_work_capture_v1_4_20261005.json"
OUT = ROOT / "evaluation/reports/live_helper_work_capture_v1_4_analysis_20261005.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_gzip_json(path: Path) -> tuple[dict, str]:
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream), digest.hexdigest()


def walk_rule_terms(value):
    if isinstance(value, dict):
        if isinstance(value.get("type"), str):
            yield value
        for child in value.values():
            yield from walk_rule_terms(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_rule_terms(child)


def walk_types(value):
    for term in walk_rule_terms(value):
        yield term["type"]


def main() -> None:
    summary = json.loads(SUMMARY.read_text())
    if sha(RAW) != summary["raw_compressed_sha256"]:
        raise SystemExit("raw capture archive hash mismatch")
    raw, raw_digest = read_gzip_json(RAW)
    if raw_digest != summary["raw_uncompressed_sha256"]:
        raise SystemExit("decompressed capture payload hash mismatch")
    runs = {int(row["replicate"]): row for row in raw["runs"]}
    checks = {"archives_match_summaries": True}
    request_parity = True
    graph_parity = len({row["capture"].get("graph_semantic_sha256") for row in runs.values()}) == 1
    trace_by_prompt = {}
    full_resolution = True
    definition_hashes: dict[tuple[int, int], set[str]] = {}
    definition_records: dict[int, dict] = {}
    activity: dict[int, dict] = {}
    added = []
    all_new_uids = set()
    per_request = []
    for rep, run in sorted(runs.items()):
        for turn, (req, snapshot) in enumerate(zip(run["capture"]["requests"], run["request_rule_snapshots"])):
            signature = (req["access_rows"], req["work_rows"])
            if req["prompt"] in trace_by_prompt:
                request_parity &= signature == trace_by_prompt[req["prompt"]]
            else:
                trace_by_prompt[req["prompt"]] = signature
            before = {int(rule["rule_uid"]): rule for rule in snapshot["before_rules"]}
            after = {int(rule["rule_uid"]): rule for rule in snapshot["after_rules"]}
            observed = {int(row[0]) for row in req["access_rows"]}
            missing = sorted(observed - after.keys())
            full_resolution &= not missing
            added_uids = sorted(after.keys() - before.keys())
            added.append({"replicate": rep, "turn": turn, "uids": added_uids})
            all_new_uids.update(added_uids)
            per_request.append({"replicate": rep, "turn": turn, "prompt": req["prompt"],
                                "observed_rule_uids": len(observed), "mapped_rule_uids": len(observed & after.keys()),
                                "new_rule_uids_since_pre_request": added_uids, "unmapped_rule_uids": missing})
            access_weight_by_uid: Counter[int] = Counter()
            access_kinds_by_uid: dict[int, Counter[str]] = {}
            for access in req["access_rows"]:
                access_uid, access_kind, count = int(access[0]), str(access[1]), int(access[6])
                access_weight_by_uid[access_uid] += count
                access_kinds_by_uid.setdefault(access_uid, Counter())[access_kind] += count
            for uid in observed:
                rule = after.get(uid)
                if rule is None:
                    continue
                raw_json = json.dumps(rule, sort_keys=True, separators=(",", ":"), default=str)
                definition_hashes.setdefault((turn, uid), set()).add(hashlib.sha256(raw_json.encode()).hexdigest())
                row_weight = access_weight_by_uid[uid]
                if uid not in activity:
                    terms = list(walk_types([rule.get("where"), rule.get("effects")]))
                    term_types = Counter(terms)
                    whole_population = sorted({"NodesOfType", "NodesWhere", "ScalarAttrTriples", "Edges"} & set(term_types))
                    traversals = sorted({"EvalSubgraph", "ReachableFrom"} & set(term_types))
                    local_adjacency = sorted({"Neighbours", "InNeighbours", "MapNeighbours", "SlideNeighbours"} & set(term_types))
                    external_terms = sorted({"UseTool", "ReadFile", "ProgCallExtern"} & set(term_types))
                    attrs = sorted({str(term.get("key")) for term in
                                    walk_rule_terms([rule.get("where"), rule.get("effects")])
                                    if term.get("type") in {"Attr", "AttrByName"} and term.get("key") is not None})
                    matches = rule.get("match") or []
                    match_edge_types = sorted({str(edge[1]) for edge in matches
                                               if isinstance(edge, list) and len(edge) >= 3})
                    effect_kinds = sorted({str(effect[0]) for effect in rule.get("effects", [])
                                           if isinstance(effect, list) and effect})
                    activity[uid] = {
                        "rule_uid": uid, "name": rule.get("name"),
                        "definition_sha256": hashlib.sha256(raw_json.encode()).hexdigest(),
                        "weighted_access_events": 0, "event_kinds": Counter(),
                        "where_and_effect_term_counts": term_types,
                        "whole_population_term_types": whole_population,
                        "subgraph_or_reachability_term_types": traversals,
                        "local_adjacency_term_types": local_adjacency,
                        "external_boundary_term_types": external_terms,
                        "attribute_keys_referenced_in_exported_terms": attrs,
                        "match_edge_types": match_edge_types, "effect_kinds": effect_kinds,
                    }
                row = activity[uid]
                row["weighted_access_events"] += row_weight
                row["event_kinds"].update(access_kinds_by_uid[uid])
                if uid in added_uids:
                    definition_records[uid] = rule
    definitions_stable = all(len(hashes) == 1 for hashes in definition_hashes.values())
    activity_rows = []
    aggregate_terms: Counter[str] = Counter()
    for uid, row in sorted(activity.items()):
        aggregate_terms.update(row["where_and_effect_term_counts"])
        activity_rows.append({**row, "event_kinds": dict(sorted(row["event_kinds"].items())),
                              "where_and_effect_term_counts": dict(sorted(row["where_and_effect_term_counts"].items()))})
    late_rules = []
    access_by_uid: Counter[int] = Counter()
    helper_work: dict[str, Counter[str]] = {}
    helper_rule_work: dict[tuple[int, int], Counter[str]] = {}
    helper_subject_names = {
        1: "shape_decode", 2: "transform_decode", 3: "dim_infer",
        4: "gen_infer", 5: "time_infer", 6: "depth_infer",
        7: "blink_bridge", 8: "gap_abduce", 9: "gap_verify",
        10: "prog_eval_decode", 11: "join_render", 12: "ratio_induce",
        13: "support_infer",
    }
    helper_kinds = {
        "dynamic_helper_invocation", "helper_codebook_population_node",
        "helper_node_attribute_examined", "helper_codebook_part_parsed",
        "helper_relation_cue_population_node", "helper_search_candidate",
        "helper_candidate_part_scored", "helper_graph_term_node_decoded",
        "helper_render_rule_candidate", "helper_auxiliary_population_node",
    }
    for run in raw["runs"]:
        for request in run["capture"]["requests"]:
            for row in request["access_rows"]:
                access_by_uid[int(row[0])] += int(row[6])
            for row in request["work_rows"]:
                # Existing native API tuple: operation, rule UID, kind,
                # helper-family subject, work units.
                if len(row) != 5 or str(row[2]) not in helper_kinds:
                    continue
                rule_uid, kind = int(row[1]), str(row[2])
                helper_id = int(row[3]) if row[3] is not None else 0
                units = int(row[4])
                family = helper_subject_names.get(helper_id, f"unknown_{helper_id}")
                helper_work.setdefault(family, Counter())[kind] += units
                helper_rule_work.setdefault((rule_uid, helper_id), Counter())[kind] += units
    helper_invocations = sum(
        counts.get("dynamic_helper_invocation", 0)
        for counts in helper_work.values()
    )
    helper_detailed_units = sum(
        units for family, counts in helper_work.items()
        for kind, units in counts.items() if kind != "dynamic_helper_invocation"
    )
    helper_work_rows = [
        {"rule_uid": uid, "helper_id": helper_id,
         "helper": helper_subject_names.get(helper_id, f"unknown_{helper_id}"),
         "work": dict(sorted(counts.items()))}
        for (uid, helper_id), counts in sorted(helper_rule_work.items())
    ]
    for uid in sorted(definition_records):
        rule = definition_records[uid]
        types = Counter(walk_types([rule.get("where"), rule.get("effects")]))
        late_rules.append({
            "rule_uid": uid, "name": rule.get("name"),
            "weighted_access_events_across_workers": access_by_uid[uid],
            "match": rule.get("match"), "where_term_types": dict(sorted(types.items())),
            "effects": rule.get("effects"), "definition_sha256": hashlib.sha256(
                json.dumps(rule, sort_keys=True, separators=(",", ":"), default=str).encode()
            ).hexdigest(),
            "definition": rule,
        })
    checks.update({
        "all_runtime_uids_resolve_in_post_request_exports": full_resolution,
        "request_access_and_work_traces_reproduce_across_workers": request_parity,
        "final_graph_semantics_reproduce_across_workers": graph_parity,
        "mapped_definitions_stable_across_workers": definitions_stable,
        "all_late_added_uids_have_definitions": {r["rule_uid"] for r in late_rules} == all_new_uids,
        "worker_count_reproduces": len(runs) == 3,
        "six_requests_analyzed": len(per_request) == 6,
        "helper_invocations_captured": helper_invocations > 0,
        "helper_internal_work_captured": helper_detailed_units > 0,
    })
    result = {
        "schema_version": 1, "run_id": "live-helper-work-capture-v1.4-analysis-20261005",
        "raw_path": str(RAW.relative_to(ROOT)), "raw_archive_sha256": sha(RAW),
        "raw_uncompressed_sha256": raw_digest,
        "capture_summary_sha256": sha(SUMMARY),
        "analysis_script_sha256": sha(Path(__file__).resolve()),
        "checks": checks,
        "summary": {"request_records": len(per_request), "rule_definition_stability_groups": len(definition_hashes),
                    "late_rule_definitions": len(late_rules), "runtime_rule_uid_observations": sum(x["observed_rule_uids"] for x in per_request),
                    "runtime_rule_uid_mappings": sum(x["mapped_rule_uids"] for x in per_request),
                    "distinct_runtime_rule_definitions": len(activity_rows),
                    "whole_population_term_rules": sum(bool(row["whole_population_term_types"]) for row in activity_rows),
                    "subgraph_or_reachability_term_rules": sum(bool(row["subgraph_or_reachability_term_types"]) for row in activity_rows),
                    "local_adjacency_term_rules": sum(bool(row["local_adjacency_term_types"]) for row in activity_rows),
                    "external_boundary_term_rules": sum(bool(row["external_boundary_term_types"]) for row in activity_rows),
                    "weighted_access_events": sum(row["weighted_access_events"] for row in activity_rows),
                    "helper_invocations": helper_invocations,
                    "helper_internal_work_units": helper_detailed_units,
                    "helper_work_by_family": {family: dict(sorted(counts.items()))
                                              for family, counts in sorted(helper_work.items())},
                    "term_type_occurrences": dict(sorted(aggregate_terms.items()))},
        "helper_work_by_rule": helper_work_rows,
        "per_request_resolution": per_request, "new_rules_by_request": added,
        "runtime_rule_definition_activity": activity_rows,
        "late_minted_rule_definitions": late_rules,
        "interpretation_boundary": "Current-source repeated workers reproduce graph state and request traces. Exported rule syntax remains a candidate static scope rather than complete dependency or factor scope.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "summary": result["summary"],
                      "late_rule_names": [[row["rule_uid"], row["name"]] for row in late_rules]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("v1.4 helper-work analysis gate failed")


if __name__ == "__main__":
    main()
