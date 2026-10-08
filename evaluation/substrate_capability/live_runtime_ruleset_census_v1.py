#!/usr/bin/env python3
"""Profile the locked v1.6 live rule set and its store-attributed work."""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_mint_termination_fragment import analyze as check_finite_key  # noqa: E402

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_RUNTIME_RULESET_CENSUS_V1_PREREG_20261004.md"
RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_live_runtime_ruleset_census_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/live_runtime_ruleset_census_v1_lock_20261004.json"
RAW_IN = ROOT / "evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz"
LOCK_IN = ROOT / "evaluation/substrate_capability/live_runtime_closure_counters_v1_6_lock_20261004.json"
ANALYSIS_IN = ROOT / "evaluation/reports/live_runtime_closure_counters_v1_6_analysis_20261004.json"
CHECKER = ROOT / "scripts/analyze_mint_termination_fragment.py"
OUT = ROOT / "evaluation/reports/live_runtime_ruleset_census_v1_20261004.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_inputs() -> dict:
    return {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(RUNNER),
        "analyzer_sha256": sha(ANALYZER),
        "v1_6_capture_sha256": sha(RAW_IN),
        "v1_6_lock_sha256": sha(LOCK_IN),
        "v1_6_analysis_sha256": sha(ANALYSIS_IN),
        "finite_key_checker_sha256": sha(CHECKER),
    }


def term_features(term) -> tuple[str | None, dict[str, int]]:
    counts: collections.Counter[str] = collections.Counter()

    def visit(value):
        if isinstance(value, dict):
            kind = value.get("type")
            if isinstance(kind, str):
                counts[kind] += 1
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(term)
    root = term.get("type") if isinstance(term, dict) else None
    return root, dict(sorted(counts.items()))


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite an existing census artifact")
        LOCK.write_text(json.dumps({"schema": "LiveRuntimeRulesetCensusV1Lock", "locked_inputs": locked_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if sys.argv[1:]:
        raise SystemExit("usage: live_runtime_ruleset_census_v1.py [--lock]")
    locked = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock")
    analysis = json.loads(ANALYSIS_IN.read_text())
    if not analysis.get("passed"):
        raise SystemExit("v1.6 independent analysis must pass before census")
    with gzip.open(RAW_IN, "rt", encoding="utf-8") as stream:
        capture = json.load(stream)
    if not capture.get("source_stable") or not capture.get("all_checks_pass"):
        raise SystemExit("v1.6 capture integrity gates failed")
    matches = [r for r in capture["runs"] if r.get("replicate") == 0 and r.get("audit_mode") == "on"]
    if len(matches) != 1:
        raise SystemExit("fixed replicate 0/audit-on sample is not unique")
    run = matches[0]
    rules = run["native_exported_rules"]
    graph = run["full_graph"]
    node_ids = [str(node["id"]) for node in graph["nodes"]]
    graph_edges = [[str(edge["src"]), str(edge["type"]), str(edge["tgt"]), edge.get("attrs", {})] for edge in graph["edges"]]
    uids = [int(rule["rule_uid"]) for rule in rules]
    if len(uids) != len(set(uids)):
        raise SystemExit("duplicate baseline RuleUID")

    rules_out = []
    for local_i, rule in enumerate(rules):
        where = rule.get("where")
        effect_counts = collections.Counter(str(effect[0]) for effect in rule.get("effects", []) if isinstance(effect, list) and effect)
        root, condition_nodes = term_features(where)
        if where is not None:
            status, reasons = "outside_fragment_condition", ["where term is outside finite-key checker schema"]
        else:
            spec = {key: rule[key] for key in ("name", "match", "effects") if key in rule}
            verdict = check_finite_key([spec], node_ids, graph_edges)
            status, reasons = ("accepted", []) if verdict["accepted"] else ("rejected", verdict["reasons"])
        rules_out.append({
            "local_rule_index": local_i,
            "rule_uid": int(rule["rule_uid"]),
            "name": str(rule.get("name", "")),
            "batch": bool(rule.get("batch", False)),
            "match_arity": len(rule.get("match", [])),
            "where_root": root,
            "where_term_node_counts": condition_nodes,
            "effect_operation_counts": dict(sorted(effect_counts.items())),
            "finite_key_status": status,
            "finite_key_reasons": reasons,
            "work_by_prompt": {},
            "counter_identity_observed_by_prompt": {},
        })

    per_prompt = []
    primary_store_candidates: dict[str, dict[int, int]] = {}
    normalized_observations = []
    for observation in run["native_counter_observations"]:
        counters = observation["counter_rows"]
        metadata = {int(row[0]): {"name": str(row[2]), "arity": int(row[3]), "ambiguous": bool(row[4])} for row in counters["metadata"]}
        identities = {int(row[0]): (int(row[1]), int(row[2])) for row in counters["identities"]}
        if set(metadata) != set(identities):
            raise SystemExit("metadata and store-qualified identities do not align")
        prompt_candidates: collections.Counter[int] = collections.Counter()
        for audit_id, (store_id, local_i) in identities.items():
            if local_i < len(rules) and metadata[audit_id]["name"] == str(rules[local_i].get("name", "")) and metadata[audit_id]["arity"] == len(rules[local_i].get("match", [])):
                prompt_candidates[store_id] += 1
        if not prompt_candidates:
            raise SystemExit("no primary store crosswalk candidate for prompt")
        best = max(prompt_candidates.values())
        winners = [store_id for store_id, count in prompt_candidates.items() if count == best]
        if len(winners) != 1:
            raise SystemExit("primary-store crosswalk is not unique for prompt")
        primary_store = winners[0]
        primary_store_candidates[str(observation["prompt"])] = dict(sorted(prompt_candidates.items()))
        metrics = collections.defaultdict(collections.Counter)
        for audit_id, metric, count in counters["per_rule"]:
            audit_id = int(audit_id)
            if audit_id not in identities:
                raise SystemExit("per-rule counter has no source identity")
            store_id, local_i = identities[audit_id]
            metrics[(store_id, local_i)][str(metric)] += int(count)
        stores = collections.defaultdict(list)
        for audit_id, (store_id, local_i) in identities.items():
            stores[store_id].append({
                "audit_id": audit_id,
                "local_rule_index": local_i,
                "name": metadata[audit_id]["name"],
                "arity": metadata[audit_id]["arity"],
                "definition_available": local_i < len(rules) and metadata[audit_id]["name"] == str(rules[local_i].get("name", "")) and metadata[audit_id]["arity"] == len(rules[local_i].get("match", [])),
                "candidate_pairs": metrics[(store_id, local_i)]["candidate_pairs"],
                "candidate_tests": metrics[(store_id, local_i)]["candidate_tests"],
                "term_evaluations": metrics[(store_id, local_i)]["term_evaluations"],
            })
        if not stores:
            raise SystemExit("no observed store identities")
        matched_primary = sum(row["definition_available"] for row in stores[primary_store])
        if matched_primary > len(rules):
            raise SystemExit("primary-store definition crosswalk exceeds baseline definitions")
        if any(row["local_rule_index"] < len(rules) and not row["definition_available"] for row in stores[primary_store]):
            raise SystemExit("primary-store baseline identity metadata conflicts with exported definition")
        if len({row["local_rule_index"] for row in stores[primary_store] if row["definition_available"]}) != matched_primary:
            raise SystemExit("primary-store crosswalk maps multiple identities to one baseline index")
        for row in stores[primary_store]:
            if row["definition_available"]:
                rules_out[row["local_rule_index"]]["work_by_prompt"][observation["prompt"]] = {
                    key: row[key] for key in ("candidate_pairs", "candidate_tests", "term_evaluations")
                }
                rules_out[row["local_rule_index"]]["counter_identity_observed_by_prompt"][observation["prompt"]] = True
        global_counts = dict(counters["global"])
        category_counts = {"baseline_definitions": collections.Counter(), "primary_minted_no_body": collections.Counter(), "secondary_stores_no_body": collections.Counter()}
        for store_id, rows in stores.items():
            for row in rows:
                if store_id == primary_store and row["local_rule_index"] < len(rules):
                    category = "baseline_definitions"
                elif store_id == primary_store:
                    category = "primary_minted_no_body"
                else:
                    category = "secondary_stores_no_body"
                category_counts[category].update({k: row[k] for k in ("candidate_pairs", "candidate_tests", "term_evaluations")})
        direct_host = int(global_counts.get("term_evals_unattributed_host_api", 0))
        if sum(c["candidate_tests"] for c in category_counts.values()) != int(global_counts.get("cand_tested", -1)):
            raise SystemExit("store/source categories do not conserve candidate tests")
        if sum(c["candidate_pairs"] for c in category_counts.values()) != int(global_counts.get("cand_enum", -1)):
            raise SystemExit("store/source categories do not conserve candidate pairs")
        if sum(c["term_evaluations"] for c in category_counts.values()) + direct_host != int(global_counts.get("term_evals_total", -1)):
            raise SystemExit("store/source plus direct host do not conserve Term evaluations")
        per_prompt.append({
            "prompt": observation["prompt"],
            "primary_store_id": primary_store,
            "primary_definition_matches": matched_primary,
            "observed_store_count": len(stores),
            "global": {key: global_counts.get(key, 0) for key in ("cand_enum", "cand_tested", "term_evals_total", "term_evals_unattributed_host_api", "term_evals_unattributed_no_rule", "term_evals_unattributed_ambiguous")},
            "source_categories": {name: dict(sorted(counts.items())) for name, counts in category_counts.items()},
            "secondary_store_rows": [row for sid, rows in stores.items() if sid != primary_store for row in rows],
            "primary_post_boot_no_body_rows": [row for row in stores[primary_store] if row["local_rule_index"] >= len(rules)],
        })
        normalized_observations.append({"prompt": observation["prompt"], "primary_store_id": primary_store, "stores": stores})

    # Attach zero-work rows as explicit zeros so the baseline rule census is complete.
    for rule_row in rules_out:
        for observation in run["native_counter_observations"]:
            rule_row["work_by_prompt"].setdefault(observation["prompt"], {"candidate_pairs": 0, "candidate_tests": 0, "term_evaluations": 0})
            rule_row["counter_identity_observed_by_prompt"].setdefault(observation["prompt"], False)

    effect_totals = collections.Counter()
    where_root_totals = collections.Counter()
    status_totals = collections.Counter()
    batch_total = 0
    for row in rules_out:
        effect_totals.update(row["effect_operation_counts"])
        where_root_totals[str(row["where_root"])] += 1
        status_totals[row["finite_key_status"]] += 1
        batch_total += int(row["batch"])
    post_hash = locked_inputs()
    result = {
        "schema": "LiveRuntimeRulesetCensusV1",
        "locked_inputs": locked,
        "post_run_inputs": post_hash,
        "source_stable": locked == post_hash,
        "sample": {"replicate": 0, "audit_mode": "on", "baseline_rule_count": len(rules), "graph_nodes": len(node_ids), "graph_edges": len(graph_edges), "capture_run_id": capture.get("run_id")},
        "primary_store_rule_crosswalk_candidates": primary_store_candidates,
        "finite_key_status_counts": dict(sorted(status_totals.items())),
        "effect_operation_totals": dict(sorted(effect_totals.items())),
        "condition_root_counts": dict(sorted(where_root_totals.items())),
        "batch_rule_count": batch_total,
        "per_prompt": per_prompt,
        "rules": rules_out,
        "all_checks_pass": False,
    }
    result["all_checks_pass"] = result["source_stable"] and len(rules_out) == 2357 and len(per_prompt) == 2 and sum(status_totals.values()) == len(rules_out)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": result["all_checks_pass"], "baseline_rules": len(rules_out), "finite_key_status_counts": result["finite_key_status_counts"], "primary_stores": result["primary_store_rule_crosswalk_candidates"], "profile": OUT.relative_to(ROOT).as_posix()}, sort_keys=True))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
