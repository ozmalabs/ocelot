#!/usr/bin/env python3
"""Independent event-identity vs static-key analysis for CAN trace v1."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_can_runtime_access_trace_v1_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_can_runtime_access_trace_v1_analysis_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(RAW.read_text())
    groups = []
    all_valid = True
    for cell in raw["cells"]:
        traced = cell["traced"]
        rules = {int(row["rule_uid"]): row for row in traced["static_rules"]}
        observed_uids = {int(row["rule_uid"]) for row in traced["event_rows"]}
        observed_rules = observed_uids & set(rules)

        static_pairs = set()
        wildcard_pairs = set()
        for writer_uid in observed_rules:
            writer = rules[writer_uid]
            for reader_uid in observed_rules:
                reader = rules[reader_uid]
                if set(writer["writes"]) & set(reader["reads"]):
                    static_pairs.add((writer_uid, reader_uid))
                if writer["writes_any"] or reader["reads_any"]:
                    wildcard_pairs.add((writer_uid, reader_uid))
        static_pairs |= wildcard_pairs

        concrete_writes: dict[tuple, set[int]] = {}
        concrete_reads: dict[tuple, set[int]] = {}
        for row in traced["event_rows"]:
            uid, kind = int(row["rule_uid"]), row["kind"]
            if kind == "effect_attr_write":
                key = ("attr", row["node"], row["resource"])
                concrete_writes.setdefault(key, set()).add(uid)
            elif kind in ("effect_edge_upsert", "effect_edge_delete", "effect_replace_edge"):
                key = ("edge", row["node"], row["resource"], row["peer"])
                concrete_writes.setdefault(key, set()).add(uid)
            elif kind in ("term_attr_read", "jit_attr_read"):
                key = ("attr", row["node"], row["resource"])
                concrete_reads.setdefault(key, set()).add(uid)
            elif kind in ("pattern_edge", "term_edge_read"):
                key = ("edge", row["node"], row["resource"], row["peer"])
                concrete_reads.setdefault(key, set()).add(uid)

        dynamic_pairs = set()
        for key, writers in concrete_writes.items():
            for reader_uid in concrete_reads.get(key, set()):
                for writer_uid in writers:
                    dynamic_pairs.add((writer_uid, reader_uid))

        unexplained_dynamic = sorted(
            [list(pair) for pair in dynamic_pairs - static_pairs]
        )
        trace_counts = Counter()
        for event in traced["event_rows"]:
            trace_counts[(int(event["rule_uid"]), event["kind"])] += int(event["count"])
        coverage_rows = []
        for uid in sorted(observed_rules):
            metrics = {key: int(value) for key, value in
                       traced["per_rule_scale_audit_counters"].get(str(uid), {}).items()}
            rule = rules[uid]
            counts = {
                "pattern_edge_events": trace_counts[(uid, "pattern_edge")],
                "leaf_visits_times_pattern_edges": metrics.get("binding_leaves", 0) * int(rule["match_edge_count"]),
                "term_attr_read_events": trace_counts[(uid, "term_attr_read")],
                "term_attr_evaluations": metrics.get("Attr", 0),
                "effect_attr_write_events": trace_counts[(uid, "effect_attr_write")],
                "effect_attr_write_attempts": metrics.get("effect_attr_set_attempts", 0),
                "effect_edge_upsert_events": trace_counts[(uid, "effect_edge_upsert")],
                "effect_edge_insert_attempts": metrics.get("effect_edge_insert_attempts", 0),
            }
            coverage_rows.append({"rule_uid": uid, "rule_name": rule["rule_name"],
                                  "counts": counts,
                                  "pattern_edge_accounting_exact": counts["pattern_edge_events"] == counts["leaf_visits_times_pattern_edges"],
                                  "attr_read_accounting_exact": counts["term_attr_read_events"] == counts["term_attr_evaluations"],
                                  "attr_write_accounting_exact": counts["effect_attr_write_events"] == counts["effect_attr_write_attempts"],
                                  "edge_upsert_accounting_exact": counts["effect_edge_upsert_events"] == counts["effect_edge_insert_attempts"]})
        coverage_exact = all(
            row[key] for row in coverage_rows for key in (
                "pattern_edge_accounting_exact", "attr_read_accounting_exact",
                "attr_write_accounting_exact", "edge_upsert_accounting_exact")
        )
        if unexplained_dynamic or traced["static_resource_mismatches"]:
            all_valid = False
        groups.append({
            "n": cell["n"], "topology": cell["topology"], "mode": cell["mode"],
            "replicate": cell["replicate"],
            "observed_rule_count": len(observed_rules),
            "static_key_possible_dependency_pairs_among_observed_rules": len(static_pairs),
            "concrete_identity_dependency_pairs_observed": len(dynamic_pairs),
            "static_pairs_without_observed_concrete_overlap": len(static_pairs - dynamic_pairs),
            "observed_dynamic_pairs_not_in_static_projection": unexplained_dynamic,
            "trace_resource_key_mismatches": traced["static_resource_mismatches"],
            "instrumented_site_counter_conservation": coverage_rows,
            "instrumented_site_counter_conservation_exact": coverage_exact,
            "identity_refinement_ratio_static_over_dynamic": (
                len(static_pairs) / len(dynamic_pairs) if dynamic_pairs else None
            ),
        })
    report = {
        "schema_version": 1,
        "raw_sha256": sha(RAW),
        "analysis_method": (
            "Within each paired CAN cell, intersect static native read/write keys among rules with observed events; "
            "separately intersect concrete attr(node,key) and matched-edge(src,type,tgt) identities in the trace. "
            "This observed overlap relation is descriptive, not a complete dynamic dependency relation."
        ),
        "all_observed_event_keys_agree_with_static_and_dynamic_pairs_are_subset": all_valid,
        "all_traced_site_counters_conserve": all(
            group["instrumented_site_counter_conservation_exact"] for group in groups
        ),
        "groups": groups,
        "claim_boundary": (
            "Finite partial traces on eight small CAN cells cannot prove dependency absence or frame safety. "
            "The identity-overlap ratio is not treewidth and does not include untraced JIT/aggregate/type accesses."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_valid": all_valid, "groups": len(groups),
                      "output": str(OUT)}, indent=2))
    if not all_valid:
        raise SystemExit("CAN trace analysis found unexplained events")


if __name__ == "__main__":
    main()
