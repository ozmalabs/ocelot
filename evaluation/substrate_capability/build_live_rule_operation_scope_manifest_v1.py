#!/usr/bin/env python3
"""Build a conservative operation-scope manifest from the live source join."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOIN = ROOT / "evaluation/reports/live_frame_term_scope_join_v1_1_20261005.json"
DEFINITIONS = ROOT / "evaluation/reports/live_rule_definitions_v1_20261005.json"
TERM_INVENTORY = ROOT / "evaluation/reports/term_access_dependency_coverage_v1_2_20261005.json"
HELPER_AUDIT = ROOT / "evaluation/reports/live_dynamic_helper_scope_audit_v1_20261005.json"
OUT = ROOT / "evaluation/reports/live_rule_operation_scope_manifest_v1_20261005.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    joined = json.loads(JOIN.read_text())
    definitions = json.loads(DEFINITIONS.read_text())
    inventory_data = json.loads(TERM_INVENTORY.read_text())
    helper_audit = json.loads(HELPER_AUDIT.read_text())
    if not all(joined["checks"].values()):
        raise SystemExit("refusing to build manifest from a failed source/runtime join")
    if not definitions["summary"]["definitions_identical_across_observed_exports"]:
        raise SystemExit("refusing to use unstable exported runtime rule definitions")
    if not all(helper_audit["checks"].values()):
        raise SystemExit("refusing to build manifest from failed helper scope audit")
    helper_by_variant = {
        row["term_variant"]: audit
        for audit in helper_audit["audits"]
        for row in audit["term_variants"]
    }
    term_inventory = {row["variant"]: row for row in inventory_data["rows"]}
    definition_by_uid = {int(row["rule_uid"]): row for row in definitions["rules"]}
    join_by_uid = {int(row["rule_uid"]): row for row in joined["runtime_rule_scope_crosswalk"]}
    definition_hashes_match_join = (
        set(definition_by_uid) == set(join_by_uid)
        and all(definition_by_uid[uid]["definition_sha256"] == row["definition_sha256"]
                for uid, row in join_by_uid.items())
    )
    if not definition_hashes_match_join:
        raise SystemExit("exact raw definitions do not hash-match the joined runtime rules")
    whole_population_by_uid = {
        int(row["rule_uid"]): row["terms"]
        for row in joined["summary"]["whole_population_term_rule_uids_and_names"]
    }
    rows = []
    broad_reasons: Counter[str] = Counter()
    term_class_counts: Counter[str] = Counter()
    operation_counts: Counter[str] = Counter()
    match_binding_counts: Counter[str] = Counter()
    exact_syntax_rows_checked = 0
    exact_access_weights_reconciled = True
    for rule in joined["runtime_rule_scope_crosswalk"]:
        exact = definition_by_uid.get(int(rule["rule_uid"]))
        if exact is None or exact["definition_sha256"] != rule["definition_sha256"]:
            raise SystemExit(f"exact exported syntax missing or hash mismatch for RuleUID {rule['rule_uid']}")
        operations = []
        reasons: set[str] = set()
        match_variables = {str(value) for edge in (exact.get("match") or [])
                           if isinstance(edge, list) for value in (edge[0], edge[2])
                           if isinstance(value, str)}
        exact_terms = exact["terms"]
        exact_counts = Counter(row["type"] for row in exact_terms)
        joined_counts = {variant: int(data["occurrences"]) for variant, data in rule["terms"].items()}
        if dict(exact_counts) != joined_counts:
            raise SystemExit(f"exact Term syntax does not reconcile for RuleUID {rule['rule_uid']}")
        exact_syntax_rows_checked += sum(exact_counts.values())
        exact_access_weights_reconciled &= sum(exact["runtime_weighted_access_events_by_prompt"].values()) == int(rule["weighted_access_events"])
        for variant, occurrence in sorted(rule["terms"].items()):
            inventory = term_inventory[variant]
            access_class = occurrence["access_class"]
            review = occurrence["source_review_kind"]
            term_class_counts[access_class] += int(occurrence["occurrences"])
            rows_of_type = [row for row in exact_terms if row["type"] == variant]
            for syntax in rows_of_type:
                operation_counts[variant] += 1
                args = syntax["arguments"]
                node_ref = args.get("node", args.get("source", args.get("cell")))
                var_name = node_ref.get("name") if isinstance(node_ref, dict) and node_ref.get("type") == "Var" else None
                if var_name is not None:
                    binding = "match_bound" if var_name in match_variables else "term_bound_or_unresolved"
                elif node_ref is not None:
                    binding = "non_variable_or_unresolved"
                else:
                    binding = "not_applicable"
                match_binding_counts[binding] += 1

                if variant == "NodesOfType":
                    scope = "whole current population of the explicit node type"
                    reasons.add("whole_population_enumeration")
                elif variant in {"Neighbours", "InNeighbours", "MapNeighbours", "SlideNeighbours"}:
                    edge_type = args.get("edge_type")
                    any_type = args.get("any_type") is True or edge_type in (None, "any", "*")
                    scope = ("one-hop wildcard adjacency at the recorded anchor; degree and crossings unbounded"
                             if any_type else f"one-hop adjacency at the recorded anchor for edge type {edge_type!r}; degree and crossings unbounded")
                    if any_type:
                        reasons.add("wildcard_adjacency")
                    else:
                        reasons.add("unbounded_degree_or_cross_frame_adjacency")
                elif variant == "ReachableFrom":
                    edge_type = args.get("edge_type")
                    scope = f"transitive reachability over edge type {edge_type!r}; reachable region may be graph-wide"
                    reasons.add("transitive_reachability")
                elif variant in {"Attr", "AttrByName"}:
                    scope = f"finite attribute key {args.get('key')!r} at node expression {node_ref!r}"
                    if binding != "match_bound":
                        reasons.add("attribute_anchor_binding_not_proven_by_match")
                elif variant == "TypeOf":
                    scope = f"node-type read at node expression {node_ref!r}; source audit conservatively marks reads_any"
                    reasons.add("source_conservative_reads_any")
                elif review == "dynamic_helper":
                    helper_audit_row = helper_by_variant.get(variant)
                    scope = (f"source-audited helper scope: {helper_audit_row['scope_class']}"
                             if helper_audit_row else "dynamic helper path has no scope audit")
                    reasons.add("dynamic_helper_scope_or_cost_not_fully_measured")
                elif inventory.get("direct_term_graph_access"):
                    scope = "source-declared graph access; see exact syntax arguments and helper references"
                    reasons.add("graph_access_operation_scope_requires_review")
                else:
                    # Generic child fallback variants compose over child Terms;
                    # the recursive syntax rows above carry their graph accesses.
                    scope = "compositional operator; inherits child Term dependencies"
                operations.append({
                    "path": syntax["path"], "variant": variant,
                    "arguments": args,
                    "source_access_class": access_class,
                    "source_review_kind": review,
                    "source_review": inventory.get("source_review"),
                    "direct_graph_access": inventory.get("direct_term_graph_access", False),
                    "evaluator_helpers": inventory.get("evaluator_helpers", []),
                    "graph_helper_paths": inventory.get("graph_helper_paths", []),
                    "trace_helper_paths": inventory.get("trace_helper_paths", []),
                    "direct_trace_event_codes": inventory.get("direct_trace_event_codes", []),
                    "external_dependency": inventory.get("external_dependency"),
                    "anchor_binding_assessment": binding,
                    "scope_interpretation": scope,
                    "helper_scope_audit_family": next((audit["family"] for audit in helper_audit["audits"]
                                                        if any(item["term_variant"] == variant for item in audit["term_variants"])), None),
                })

        whole_population = whole_population_by_uid.get(int(rule["rule_uid"]), [])
        if whole_population:
            reasons.add("whole_population_term_syntax")
        kinds = {op["variant"] for op in operations}
        if whole_population:
            known_scope = "whole_population_scan_present"
        elif kinds & {"ReachableFrom", "EvalSubgraph"}:
            known_scope = "potentially_graph_wide_transitive_or_subgraph"
        elif "TypeOf" in kinds or any(op["source_review_kind"] == "dynamic_helper" for op in operations):
            known_scope = "potentially_graph_wide_or_dynamic"
        elif kinds & {"Neighbours", "InNeighbours", "MapNeighbours", "SlideNeighbours"}:
            known_scope = "anchored_adjacency_with_unbounded_degree"
        else:
            known_scope = "finite_key_or_inherited_scope_candidate"
        reasons.add("candidate_matcher_host_scheduler_and_rejected_work_not_in_term_manifest")
        reasons.add("syntactic_term_presence_does_not_prove_term_execution")
        for reason in reasons:
            broad_reasons[reason] += 1
        rows.append({
            "rule_uid": rule["rule_uid"],
            "name": rule["name"],
            "definition_sha256": rule["definition_sha256"],
            "exact_definition_source": definitions["raw_capture_path"],
            "weighted_access_events": rule["weighted_access_events"],
            "observed_event_kinds": rule["observed_event_kinds"],
            "match_edge_types_observed_in_definition": rule["match_edge_types"],
            "attribute_keys_observed_in_terms": rule["attribute_keys_referenced_in_exported_terms"],
            "effect_kinds_observed_in_definition": rule["effect_kinds"],
            "term_access_classes": rule["term_access_classes"],
            "match_variables": sorted(match_variables),
            "match": exact.get("match"),
            "whole_population_syntax_flags": whole_population,
            "known_scope_summary": known_scope,
            "locality_proven": False,
            "locality_blockers": sorted(reasons),
            "operations": operations,
        })

    result = {
        "schema": "LiveRuleOperationScopeManifestV1",
        "run_id": "live-rule-operation-scope-manifest-v1-20261005",
        "input_path": str(JOIN.relative_to(ROOT)),
        "input_sha256": digest(JOIN),
        "definitions_path": str(DEFINITIONS.relative_to(ROOT)),
        "definitions_sha256": digest(DEFINITIONS),
        "helper_audit_path": str(HELPER_AUDIT.relative_to(ROOT)),
        "helper_audit_sha256": digest(HELPER_AUDIT),
        "term_inventory_path": str(TERM_INVENTORY.relative_to(ROOT)),
        "term_inventory_sha256": digest(TERM_INVENTORY),
        "builder_sha256": digest(Path(__file__).resolve()),
        "source_inventory_sha256": joined["term_inventory_sha256"],
        "runtime_analysis_sha256": joined["runtime_scope_analysis_sha256"],
        "summary": {
            "runtime_rule_definitions": len(rows),
            "rules_marked_locality_proven": sum(row["locality_proven"] for row in rows),
            "rules_with_whole_population_syntax": sum(bool(row["whole_population_syntax_flags"]) for row in rows),
            "rule_count_by_known_scope_summary": dict(Counter(row["known_scope_summary"] for row in rows)),
            "term_occurrences_by_access_class": dict(term_class_counts),
            "operation_occurrences_by_term_variant": dict(operation_counts),
            "anchor_binding_assessments": dict(match_binding_counts),
            "rule_count_by_locality_blocker": dict(sorted(broad_reasons.items())),
            "weighted_access_events": sum(row["weighted_access_events"] for row in rows),
        },
        "checks": {
            "upstream_join_checks_pass": all(joined["checks"].values()),
            "dynamic_helper_audit_passes": all(helper_audit["checks"].values()),
            "definition_set_matches_join": len(rows) == len(definition_by_uid) == 401,
            "all_definition_hashes_match_join": definition_hashes_match_join,
            "per_rule_term_syntax_reconciles": exact_syntax_rows_checked == sum(
                int(value["occurrences"]) for rule in joined["runtime_rule_scope_crosswalk"]
                for value in rule["terms"].values()),
            "per_rule_runtime_access_weights_reconcile": exact_access_weights_reconciled,
        },
        "rules": rows,
        "claim_boundary": "This manifest joins exact exported syntax for runtime-touched rule definitions to source-reviewed Term access declarations. It records concrete Term arguments, match-variable names, direct graph-access declarations, and helper paths. Anchor binding remains conservative where iterator/binding semantics are not represented. Dynamic helper footprints, matcher candidate enumeration, host/scheduler work, and rejected-candidate evaluations remain outside this Term manifest. Term syntax does not prove execution; no rule is classified as proven local. This is not a factor-scope, treewidth, exact-inference, or natural-prevalence result.",
    }
    result["checks"]["all_checks_pass"] = all(result["checks"].values())
    if not result["checks"]["all_checks_pass"]:
        raise SystemExit(f"manifest reconciliation failed: {result['checks']}")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "summary": result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
