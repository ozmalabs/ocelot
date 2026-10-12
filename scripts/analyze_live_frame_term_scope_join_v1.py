#!/usr/bin/env python3
"""Join source Term-access classifications to runtime-touched rule definitions."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERM_INVENTORY = ROOT / "evaluation/reports/term_access_dependency_coverage_v1_1_20261003.json"
TERM_AUDITOR = ROOT / "scripts/audit_term_access_dependency_coverage_v1.py"
RUNTIME_SCOPES = ROOT / "evaluation/reports/live_frame_rule_scope_capture_v1_1_analysis_20261003.json"
OUT = ROOT / "evaluation/reports/live_frame_term_scope_join_v1_20261003.json"
SOURCE_PATHS = {
    "term_rs_sha256": "runners/dsl/src/term.rs",
    "rewrite_rs_sha256": "runners/dsl/src/rewrite.rs",
    "access_trace_rs_sha256": "runners/dsl/src/access_trace.rs",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    inventory = json.loads(TERM_INVENTORY.read_text())
    runtime = json.loads(RUNTIME_SCOPES.read_text())
    term_index = {row["variant"]: row for row in inventory["rows"]}
    if sha(TERM_AUDITOR) != inventory.get("audit_runner_sha256"):
        raise SystemExit("Term inventory generator changed since its source crosswalk")
    for input_key, relpath in SOURCE_PATHS.items():
        if sha(ROOT / relpath) != inventory["inputs"][input_key]:
            raise SystemExit(f"Term inventory source hash is stale: {relpath}")
    if not all(inventory["checks"].values()) or not all(runtime["checks"].values()):
        raise SystemExit("upstream source inventory or runtime scope analysis has failed checks")

    missing_variants: set[str] = set()
    rule_rows = []
    live_term_variants: dict[str, dict] = {}
    class_variant_sets: dict[str, set[str]] = defaultdict(set)
    class_rule_sets: dict[str, set[int]] = defaultdict(set)
    class_occurrences: Counter[str] = Counter()
    review_kind_variant_sets: dict[str, set[str]] = defaultdict(set)
    review_kind_occurrences: Counter[str] = Counter()
    per_rule_whole_population = []
    external_rule_ids = []
    for rule in runtime["runtime_rule_definition_activity"]:
        uid = int(rule["rule_uid"])
        classes: set[str] = set()
        review_kinds: set[str] = set()
        term_map = {}
        for variant, occurrences in rule["where_and_effect_term_counts"].items():
            source = term_index.get(variant)
            if source is None:
                missing_variants.add(variant)
                continue
            cls = str(source["access_class"])
            review = str(source.get("source_review_kind", "unknown"))
            classes.add(cls)
            review_kinds.add(review)
            class_variant_sets[cls].add(variant)
            class_rule_sets[cls].add(uid)
            class_occurrences[cls] += int(occurrences)
            review_kind_variant_sets[review].add(variant)
            review_kind_occurrences[review] += int(occurrences)
            live_term_variants.setdefault(variant, {
                "variant": variant,
                "access_class": cls,
                "source_review_kind": review,
                "source_review": source.get("source_review"),
                "external_dependency": source.get("external_dependency"),
                "direct_trace_event_codes": source.get("direct_trace_event_codes", []),
                "graph_helper_paths": source.get("graph_helper_paths", []),
                "trace_helper_paths": source.get("trace_helper_paths", []),
                "occurrences_across_runtime_definitions": 0,
                "runtime_rule_uids": set(),
            })
            live_term_variants[variant]["occurrences_across_runtime_definitions"] += int(occurrences)
            live_term_variants[variant]["runtime_rule_uids"].add(uid)
            term_map[variant] = {
                "occurrences": int(occurrences), "access_class": cls,
                "source_review_kind": review,
                "direct_trace_event_codes": source.get("direct_trace_event_codes", []),
                "external_dependency": source.get("external_dependency"),
            }
        if rule["whole_population_term_types"]:
            per_rule_whole_population.append({"rule_uid": uid, "name": rule["name"],
                                              "terms": rule["whole_population_term_types"]})
        if any(term_map[t]["external_dependency"] for t in term_map
               if term_map[t]["external_dependency"] is not None):
            external_rule_ids.append(uid)
        rule_rows.append({
            "rule_uid": uid, "name": rule["name"],
            "definition_sha256": rule["definition_sha256"],
            "weighted_access_events": rule["weighted_access_events"],
            "observed_event_kinds": rule["event_kinds"],
            "match_edge_types": rule["match_edge_types"],
            "attribute_keys_referenced_in_exported_terms": rule["attribute_keys_referenced_in_exported_terms"],
            "effect_kinds": rule["effect_kinds"],
            "term_access_classes": sorted(classes),
            "term_source_review_kinds": sorted(review_kinds),
            "terms": term_map,
        })

    for row in live_term_variants.values():
        row["runtime_rule_uids"] = sorted(row["runtime_rule_uids"])
        row["runtime_rule_count"] = len(row["runtime_rule_uids"])
    checks = {
        "all_upstream_checks_pass": True,
        "term_inventory_sources_match_current_files": True,
        "all_runtime_term_variants_have_source_rows": not missing_variants,
        "all_401_runtime_rule_definitions_joined": len(rule_rows) == 401,
        "runtime_weighted_access_total_reconciles": sum(row["weighted_access_events"] for row in rule_rows) == runtime["summary"]["weighted_access_events"],
    }
    classes = sorted(set(class_variant_sets) | set(class_rule_sets))
    summary = {
        "runtime_rule_definitions": len(rule_rows),
        "runtime_term_variants": len(live_term_variants),
        "runtime_term_occurrences_in_unique_rule_definitions": sum(class_occurrences.values()),
        "weighted_access_events": sum(row["weighted_access_events"] for row in rule_rows),
        "unmapped_runtime_term_variants": sorted(missing_variants),
        "term_access_classes": {
            cls: {"runtime_term_variant_count": len(class_variant_sets[cls]),
                  "runtime_rule_definition_count": len(class_rule_sets[cls]),
                  "term_occurrence_count": class_occurrences[cls]}
            for cls in classes
        },
        "runtime_term_variants_by_source_review_kind": {
            kind: {"variant_count": len(variants), "occurrence_count": review_kind_occurrences[kind]}
            for kind, variants in sorted(review_kind_variant_sets.items())
        },
        "runtime_rules_with_external_term_dependencies": len(external_rule_ids),
        "runtime_rules_with_whole_population_term_syntax": len(per_rule_whole_population),
        "whole_population_term_rule_uids_and_names": per_rule_whole_population,
    }
    result = {
        "schema_version": 1,
        "run_id": "live-frame-term-scope-join-v1-20261003",
        "term_inventory_path": str(TERM_INVENTORY.relative_to(ROOT)),
        "term_inventory_sha256": sha(TERM_INVENTORY),
        "term_inventory_runner_sha256": inventory["audit_runner_sha256"],
        "term_inventory_source_sha256": inventory["inputs"],
        "runtime_scope_analysis_path": str(RUNTIME_SCOPES.relative_to(ROOT)),
        "runtime_scope_analysis_sha256": sha(RUNTIME_SCOPES),
        "analysis_script_sha256": sha(Path(__file__).resolve()),
        "checks": checks, "summary": summary,
        "live_term_variant_crosswalk": [live_term_variants[k] for k in sorted(live_term_variants)],
        "runtime_rule_scope_crosswalk": rule_rows,
        "claim_boundary": "Term access classes are source-reviewed declarations and lexical helper findings, joined to syntactic Terms in runtime-traced rule definitions. They are not a complete call graph or proof each Term executed. Finite RuleKey resources can still scan graph-wide populations. This join does not model host, scheduler, rejected-candidate, or implicit evaluator dependencies and does not derive inference factor scopes/domains.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": checks,
                      "summary": {key: val for key, val in summary.items()
                                  if key != "whole_population_term_rule_uids_and_names"}}, indent=2))
    if not all(checks.values()):
        raise SystemExit("live Term-to-rule source crosswalk gate failed")


if __name__ == "__main__":
    main()
