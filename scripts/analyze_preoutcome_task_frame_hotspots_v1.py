#!/usr/bin/env python3
"""Attribute pre-outcome held-topic access work to rules and source operations."""
from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "evaluation/reports/preoutcome_task_frame_capture_v1_20261005/capture.json.gz"
MANIFEST = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"
OUT = ROOT / "evaluation/reports/preoutcome_task_frame_hotspots_v1_analysis_20261005.json"
ANALYZER = Path(__file__).resolve()
LOCK_PATH = ROOT / "evaluation/substrate_capability/preoutcome_task_frame_capture_v1_20261005_lock.json"
NATIVE_PATH = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"

SEED_RULES = {
    "slang_variant_bind_denotes": "seeds/slang_lexicon.json",
    "curiosity_targets_ambivalent_nodes": "seeds/causal_attitude_networks.json",
    "gr_condition_lapse": "seeds/goal_residuals.json",
    "sd_decode": "seeds/shape_decode_loop.json",
    "sd_transform_decode": "seeds/shape_decode_loop.json",
    "sd_infer_dimension": "seeds/shape_decode_loop.json",
}
ENGINE_SOURCES = (
    "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/term.rs",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/graph_rules.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs",
)
PYTHON_SOURCES = ("substrate/world_adapter.py",)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


capture_bytes = CAPTURE.read_bytes()
capture_sha = hashlib.sha256(capture_bytes).hexdigest()
capture = json.loads(gzip.decompress(capture_bytes))
manifest = json.loads(MANIFEST.read_text())
locked_python = capture["locked_inputs"]["base_inputs"]["source_closure_sha256"]
source_hashes = {}
for rel in sorted(set(SEED_RULES.values()) | set(ENGINE_SOURCES) | set(PYTHON_SOURCES)):
    actual = digest(ROOT / rel)
    if rel in locked_python:
        locked = locked_python[rel]
        expected = locked.removeprefix("sha256:")
        source_hashes[rel] = {"actual_sha256": actual, "capture_locked_sha256": expected,
                              "matches_capture_lock": actual == expected}
    else:
        expected = manifest["files"].get(rel)
        source_hashes[rel] = {"actual_sha256": actual, "native_build_sha256": expected,
                              "matches_native_build": actual == expected}
capture_lock_file_matches_embedded = json.loads(LOCK_PATH.read_text()) == capture["locked_inputs"]
manifest_sha = digest(MANIFEST)
native_sha = digest(NATIVE_PATH)
build_manifest_matches_capture = manifest_sha == capture["locked_inputs"]["base_inputs"]["native_build_manifest_sha256"]
native_extension_matches_capture = native_sha == capture["locked_inputs"]["native_extension_sha256"].removeprefix("sha256:")

rule_definitions = {}
for name, rel in SEED_RULES.items():
    seed = json.loads((ROOT / rel).read_text())
    found = [rule for rule in seed.get("rules", []) if rule.get("name") == name]
    if len(found) != 1:
        raise SystemExit(f"expected one definition for {name} in {rel}, found {len(found)}")
    rule_definitions[name] = {
        "source": rel,
        "source_line": next(i for i, line in enumerate((ROOT / rel).read_text().splitlines(), 1)
                            if f'\"name\": \"{name}\"' in line),
        "source_sha256": source_hashes[rel]["actual_sha256"],
        "match_type": found[0].get("match_type"),
        "match": found[0].get("match"),
        "where_term_types": [],
        "effects": found[0].get("effects", []),
    }


def collect_term_types(obj, target):
    if isinstance(obj, dict):
        typ = obj.get("type")
        if typ:
            target.add(str(typ))
        for value in obj.values():
            collect_term_types(value, target)
    elif isinstance(obj, list):
        for value in obj:
            collect_term_types(value, target)


for name, rel in SEED_RULES.items():
    seed = json.loads((ROOT / rel).read_text())
    rule = next(rule for rule in seed["rules"] if rule.get("name") == name)
    terms = set()
    collect_term_types(rule.get("where"), terms)
    collect_term_types(rule.get("effects"), terms)
    rule_definitions[name]["where_term_types"] = sorted(terms)

turn_rows = []
replication_checks = {}
for turn_index, turn0 in enumerate(capture["runs"][0]["turns"]):
    prompt = turn0["prompt"]
    signatures = []
    by_rule = Counter()
    by_rule_kind = defaultdict(Counter)
    by_rule_resource = defaultdict(Counter)
    outside_total = 0
    all_rule_total = 0
    for run in capture["runs"]:
        turn = run["turns"][turn_index]
        signature = Counter()
        for event in turn["postcheckpoint_rule_access"]["events"]:
            key = (event["rule_uid"], event["rule_name"], event["kind"], event["resource"],
                   tuple(event["scope_roles"]))
            signature[key] += event["count"]
            all_rule_total += event["count"]
            if "outside_cut" in event["scope_roles"]:
                outside_total += event["count"]
                name = event["rule_name"]
                by_rule[name] += event["count"]
                by_rule_kind[name][event["kind"]] += event["count"]
                by_rule_resource[name][(event["kind"], event["resource"])] += event["count"]
        signatures.append(signature)
    replication_checks[prompt] = all(sig == signatures[0] for sig in signatures[1:])
    # Counts are replicated three times. Per-turn values below use one worker.
    scale = len(capture["runs"])
    top_rules = []
    for name, weighted_count in by_rule.most_common(10):
        top_rules.append({
            "rule_name": name,
            "outside_cut_access_count_per_worker": weighted_count // scale,
            "share_of_outside_cut_accesses": round(weighted_count / scale / (outside_total / scale), 6),
            "operation_counts_per_worker": {k: v // scale for k, v in sorted(by_rule_kind[name].items())},
            "resource_counts_per_worker": [
                {"kind": kind, "resource": resource, "count": count // scale}
                for (kind, resource), count in by_rule_resource[name].most_common(10)],
            "source_definition": rule_definitions.get(name),
        })
    rule_summaries = {}
    for name in SEED_RULES:
        if name in by_rule:
            rule_summaries[name] = {
                "outside_cut_access_count_per_worker": by_rule[name] // scale,
                "operation_counts_per_worker": {k: v // scale for k, v in sorted(by_rule_kind[name].items())},
                "resource_counts_per_worker": [
                    {"kind": kind, "resource": resource, "count": count // scale}
                    for (kind, resource), count in by_rule_resource[name].most_common(12)],
            }
    turn_rows.append({
        "prompt": prompt,
        "outside_cut_access_count_per_worker": outside_total // scale,
        "all_rule_access_count_per_worker": all_rule_total // scale,
        "outside_cut_rule_count": len(by_rule),
        "top_rules": top_rules,
        "audited_rules": rule_summaries,
    })

first = turn_rows[0]
first_slang = first["audited_rules"]["slang_variant_bind_denotes"]
later_slang = [row["audited_rules"].get("slang_variant_bind_denotes", {}) for row in turn_rows[1:]]
curiosity = [row["audited_rules"].get("curiosity_targets_ambivalent_nodes", {}) for row in turn_rows]
residual = [row["audited_rules"].get("gr_condition_lapse", {}) for row in turn_rows]
slang_type_reads = first_slang["operation_counts_per_worker"].get("effect_type_candidate_read", 0)
slang_pattern_matches = first_slang["operation_counts_per_worker"].get("pattern_edge", 0)
first_three_total = sum(first["audited_rules"][name]["outside_cut_access_count_per_worker"]
                        for name in ("slang_variant_bind_denotes", "curiosity_targets_ambivalent_nodes", "gr_condition_lapse"))
first_shape_total = sum(first["audited_rules"][name]["outside_cut_access_count_per_worker"]
                        for name in ("sd_decode", "sd_transform_decode", "sd_infer_dimension"))

result = {
    "schema_version": 1,
    "capture_path": str(CAPTURE.relative_to(ROOT)),
    "capture_sha256": capture_sha,
    "capture_lock_path": str(LOCK_PATH.relative_to(ROOT)),
    "capture_lock_sha256": digest(LOCK_PATH),
    "capture_lock_file_matches_embedded": capture_lock_file_matches_embedded,
    "capture_commit": capture["locked_inputs"]["base_inputs"]["commit"],
    "native_extension_sha256": capture["locked_inputs"]["native_extension_sha256"],
    "native_build_manifest_sha256": manifest_sha,
    "native_build_manifest_matches_capture": build_manifest_matches_capture,
    "native_extension_matches_capture": native_extension_matches_capture,
    "analyzer_sha256": digest(ANALYZER),
    "source_hashes": source_hashes,
    "all_static_sources_match_capture_or_native_build": all(
        row.get("matches_capture_lock", row.get("matches_native_build", False))
        for row in source_hashes.values()),
    "per_prompt_worker_trace_profiles_repeat": all(replication_checks.values()),
    "replication_checks": replication_checks,
    "per_turn": turn_rows,
    "hotspot_findings": {
        "first_turn_top_three_named_rules_access_count": first_three_total,
        "first_turn_shape_decode_family_access_count": first_shape_total,
        "first_turn_slang_node_dedup_candidate_reads": slang_type_reads,
        "first_turn_slang_rule_match_edges": slang_pattern_matches,
        "slang_candidates_per_rule_match": (slang_type_reads // slang_pattern_matches
                                               if slang_pattern_matches else None),
        "later_turn_slang_outside_access_counts": [
            row.get("outside_cut_access_count_per_worker", 0) for row in later_slang],
        "curiosity_rule_outside_access_counts": [
            row.get("outside_cut_access_count_per_worker", 0) for row in curiosity],
        "goal_residual_lapse_outside_access_counts": [
            row.get("outside_cut_access_count_per_worker", 0) for row in residual],
    },
    "limitations": [
        "Access-event counts are mechanism work counters, not elapsed time or CPU cost.",
        "Events outside the declared ingress cut may be background supervision or shared global state; they are not thereby necessary task dependencies.",
        "The trace covers native rule accesses after the checkpoint, not every host-side read or operation.",
        "The seven prompts are one authored task family and three worker replicates, not a natural-task sample.",
    ],
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"analysis": str(OUT.relative_to(ROOT)),
                  "source_hashes_match": result["all_static_sources_match_capture_or_native_build"],
                  "lock_and_native_artifacts_match": (capture_lock_file_matches_embedded
                      and build_manifest_matches_capture and native_extension_matches_capture),
                  "worker_profiles_repeat": result["per_prompt_worker_trace_profiles_repeat"],
                  "first_turn_top_three": first_three_total,
                  "later_slang_scan_counts": result["hotspot_findings"]["later_turn_slang_outside_access_counts"],
                  "curiosity_counts": result["hotspot_findings"]["curiosity_rule_outside_access_counts"],
                  "gr_condition_lapse_counts": result["hotspot_findings"]["goal_residual_lapse_outside_access_counts"]}, indent=2))
