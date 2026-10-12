#!/usr/bin/env python3
"""Compare baseline global pair marking with request-scoped cue counting."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_episodic_cue_index_variant_v3_20260925.json"
SIZES = (6, 24, 78, 192)
REPEATS = 2
PAIR_RULE = "episodic_mark_overlapping_cues_for_conservative_completion"
RETRIEVE_RULE = "episodic_retrieve_best_partial_cue"


def cue_count_term():
    return {"type": "Count", "source": {
        "type": "Filter",
        "source": {"type": "Neighbours", "node": {"type": "Var", "name": "agent"},
                    "edge_type": "recorded_episode"},
        "var_name": "counted_episode",
        "predicate": {"type": "Eq",
                      "a": {"type": "Attr", "node": {"type": "Var", "name": "counted_episode"}, "key": "cue_key"},
                      "b": {"type": "Attr", "node": {"type": "Var", "name": "request"}, "key": "cue_key"}}
    }}


def install_variant(variant):
    import substrate.boot_core as boot_core_module
    from substrate.seed_loader import manifest_for as original_manifest_for

    def manifest_for_variant(seed_id):
        manifest = original_manifest_for(seed_id)
        if seed_id != "episodic_working_memory_core" or variant != "request_count":
            return manifest
        manifest = copy.deepcopy(manifest)
        manifest["rules"] = [r for r in manifest["rules"] if r["name"] != PAIR_RULE]
        retrieve = next(r for r in manifest["rules"] if r["name"] == RETRIEVE_RULE)
        count = cue_count_term()
        ambiguous = {"type": "Gt", "a": count, "b": {"type": "Lit", "value": 1.0}}
        recall = next(e for e in retrieve["effects"] if e[0] == "add_node" and e[1] == "recall")
        recall[3]["confidence"] = {"__term__": {
            "type": "IfThenElse", "cond": ambiguous,
            "then": {"type": "Lit", "value": 0.5},
            "other": {"type": "Attr", "node": {"type": "Var", "name": "episode"},
                      "key": "completion_confidence_cap"},
        }}
        recall[3]["uncertainty"] = {"__term__": {
            "type": "Minus", "a": {"type": "Lit", "value": 1.0},
            "b": {"type": "IfThenElse", "cond": ambiguous,
                 "then": {"type": "Lit", "value": 0.5},
                 "other": {"type": "Attr", "node": {"type": "Var", "name": "episode"},
                           "key": "completion_confidence_cap"}},
        }}
        return manifest

    boot_core_module.manifest_for = manifest_for_variant


def edge(agent, src, rel, tgt):
    agent.inner.add_edge_unchecked(src, rel, tgt, {})


def make_specs(n, workload):
    if workload == "unique":
        return [{"i": i, "cue": f"variant-cue-{i}", "summary": f"variant-route-{i}-north",
                 "salience": 0.8, "surprise": 0.7, "value": 0.9} for i in range(n)]
    rows = [{"i": 0, "cue": "variant-cue-collision", "summary": "collision-target-north",
             "salience": 0.9, "surprise": 0.8, "value": 0.9},
            {"i": 1, "cue": "variant-cue-collision", "summary": "collision-alternative-south",
             "salience": 0.1, "surprise": 0.1, "value": 0.1}]
    rows.extend({"i": i, "cue": f"variant-cue-{i}", "summary": f"variant-route-{i}-north",
                 "salience": 0.8, "surprise": 0.7, "value": 0.9} for i in range(2, n))
    return rows


def writer(variant, workload, n, path):
    install_variant(variant)
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("episodic_working_memory_core",))
    for x in make_specs(n, workload):
        ctx = agent.s.add_node("MemoryContext", {"context_key": f"variant-context-{x['i']}"})
        schema = agent.s.add_node("MemorySchema", {"name": "route_state"})
        event = agent.s.add_node("EpisodicEvent", {
            "event_key": f"variant-event-{x['i']}", "cue_key": x["cue"],
            "epoch": 1.0, "salience": x["salience"], "surprise": x["surprise"], "value": x["value"],
            "observation_status": "observed", "provenance_kind": "perceived",
            "state_kind": "route", "state_summary": x["summary"],
        })
        edge(agent, agent.agent, "experienced_event", event)
        edge(agent, event, "in_context", ctx)
        edge(agent, event, "instantiates_schema", schema)
    t0 = time.perf_counter_ns(); closure_progress = int(agent.tick()); closure_ns = time.perf_counter_ns() - t0
    episode_count = sum(1 for node in agent.s.nodes() if agent.s.node(node)["type"] == "Episode")
    agent.save(path)
    row = {"pid": os.getpid(), "variant": variant, "workload": workload, "n": n,
           "episode_count": episode_count, "closure_progress": closure_progress,
           "closure_ns": closure_ns, "checkpoint_bytes": Path(path).stat().st_size,
           "node_count": agent.s.node_count(), "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           "rule_names": [str(x[1]) for x in agent.inner.rule_access_sets()]}
    agent.close(); print(json.dumps(row, sort_keys=True))


def reader(variant, workload, n, path, audit):
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter.load(path)
    cue = (f"variant-cue-{n//2}" if workload == "unique" else "variant-cue-collision")
    expected = (f"variant-route-{n//2}-north" if workload == "unique" else "collision-target-north")
    request = agent.s.add_node("MemoryRetrievalRequest", {"status": "pending", "cue_key": cue, "epoch": 4.0})
    edge(agent, agent.agent, "has_memory_retrieval_request", request)
    agent.inner.scale_audit_set_enabled(False); agent.inner.scale_audit_set_per_rule_enabled(False)
    agent.inner.scale_audit_reset(); agent.inner.scale_audit_per_rule_reset()
    if audit:
        agent.inner.scale_audit_set_enabled(True); agent.inner.scale_audit_set_per_rule_enabled(True)
    t0 = time.perf_counter_ns(); progress = int(agent.tick()); tick_ns = time.perf_counter_ns() - t0
    candidates = list(agent.inner.neighbours(request, "has_recall_candidate"))
    row = {"pid": os.getpid(), "variant": variant, "workload": workload, "n": n, "audit": audit,
           "tick_ns": tick_ns, "progress": progress, "candidate_count": len(candidates),
           "expected_summary": expected, "state_summary": None, "status": None, "confidence": None,
           "uncertainty": None, "provenance_kind": None, "observation_status": None}
    if len(candidates) == 1:
        ca = agent.s.node(candidates[0])["attrs"]
        ev = list(agent.inner.neighbours(candidates[0], "reconstructs_event"))
        ea = agent.s.node(ev[0])["attrs"] if len(ev) == 1 else {}
        row.update({"state_summary": ea.get("state_summary"), "status": ca.get("status"),
                    "confidence": ca.get("confidence"), "uncertainty": ca.get("uncertainty"),
                    "provenance_kind": ca.get("provenance_kind"),
                    "observation_status": ca.get("observation_status")})
    collision_eps = [node for node in agent.s.nodes() if agent.s.node(node)["type"] == "Episode" and
                     agent.s.node(node)["attrs"].get("cue_key") == cue]
    row["cue_episode_attrs"] = [{"completion_confidence_cap": agent.s.node(ep)["attrs"].get("completion_confidence_cap"),
                                 "separation_status": agent.s.node(ep)["attrs"].get("separation_status")}
                                for ep in collision_eps]
    names = [str(x[1]) for x in agent.inner.rule_access_sets()]
    row["pair_rule_active"] = PAIR_RULE in names
    row["memory_rule_count"] = sum("episodic_" in x for x in names)
    if audit:
        row["global_counters"] = dict(agent.inner.scale_audit_snapshot())
        index_to_name = {int(x[0]): str(x[1]) for x in agent.inner.rule_access_sets()}
        row["per_rule_counters"] = [{"rule_name": index_to_name.get(int(i), str(i)),
                                      "metric": str(metric), "count": int(count)}
                                     for i, metric, count in agent.inner.scale_audit_per_rule_snapshot()]
    else:
        row["global_counters"] = None; row["per_rule_counters"] = None
    agent.inner.scale_audit_set_per_rule_enabled(False); agent.inner.scale_audit_set_enabled(False)
    row["rss_peak_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    try:
        agent.close(); row["close_status"] = "closed"
    except Exception as exc:
        row["close_status"] = "error"; row["close_exception_type"] = type(exc).__name__
    print(json.dumps(row, sort_keys=True))


def main():
    if len(sys.argv) == 6 and sys.argv[1] == "--write":
        writer(sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]); return
    if len(sys.argv) == 7 and sys.argv[1] == "--read":
        reader(sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[6], sys.argv[5] == "audit"); return
    env = dict(os.environ); env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    runs = []
    with tempfile.TemporaryDirectory(prefix="episodic-cue-variant-") as td:
        for workload in ("unique", "collision"):
            for n in SIZES:
                for rep in range(REPEATS):
                    for variant in ("baseline", "request_count"):
                        path = Path(td) / f"{workload}-n{n}-r{rep}-{variant}.json"
                        wp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--write", variant,
                                             workload, str(n), str(path)], cwd=ROOT, env=env, text=True,
                                            capture_output=True, check=True)
                        w = json.loads(wp.stdout.strip()); arms = {}
                        for arm in ("control", "audit"):
                            rp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--read", variant,
                                                 workload, str(n), arm, str(path)], cwd=ROOT, env=env,
                                                text=True, capture_output=True, check=True)
                            arms[arm] = json.loads(rp.stdout.strip())
                        runs.append({"workload": workload, "n": n, "replicate": rep,
                                     "variant": variant, "writer": w, "readers": arms})
    checks = {
        "complete_preregistered_grid": len(runs) == 2 * len(SIZES) * REPEATS * 2,
        "all_processes_distinct_within_each_run": all(len({r["writer"]["pid"], r["readers"]["control"]["pid"],
                                                            r["readers"]["audit"]["pid"]}) == 3 for r in runs),
        "writers_bind_declared_episode_count": all(r["writer"]["episode_count"] == r["n"] for r in runs),
        "all_control_and_audit_readers_return_exact_answer": all(
            all(r["readers"][a]["candidate_count"] == 1 and
                r["readers"][a]["state_summary"] == r["readers"][a]["expected_summary"] and
                r["readers"][a]["status"] == "recalled" and
                r["readers"][a]["provenance_kind"] == "recalled" and
                r["readers"][a]["observation_status"] == "not_observed"
                for a in ("control", "audit")) for r in runs),
        "confidence_matches_unique_or_collision_task": all(
            math.isclose(r["readers"]["control"]["confidence"], (0.5 if r["workload"] == "collision" else 0.85), abs_tol=1e-12) and
            math.isclose(r["readers"]["control"]["uncertainty"], (0.5 if r["workload"] == "collision" else 0.15), abs_tol=1e-12)
            for r in runs),
        "prototype_omits_pair_rule_and_baseline_retains_it": all(
            r["writer"]["rule_names"].count(PAIR_RULE) == (1 if r["variant"] == "baseline" else 0) and
            r["readers"]["control"]["pair_rule_active"] == (r["variant"] == "baseline") for r in runs),
        "all_readers_close_cleanly": all(r["readers"][a]["close_status"] == "closed" for r in runs for a in ("control", "audit")),
        "audit_counters_present": all(r["readers"]["audit"]["global_counters"] is not None and
                                       r["readers"]["audit"]["per_rule_counters"] is not None for r in runs),
        "baseline_collision_marks_both_episodes": all(
            all(x["completion_confidence_cap"] == 0.5 and x["separation_status"] == "overlap_detected"
                for x in r["readers"]["control"]["cue_episode_attrs"])
            for r in runs if r["variant"] == "baseline" and r["workload"] == "collision"),
        "prototype_preserves_episode_side_effect_boundary": all(
            all(x["completion_confidence_cap"] == 0.85 and x["separation_status"] == "distinct_event_record"
                for x in r["readers"]["control"]["cue_episode_attrs"])
            for r in runs if r["variant"] == "request_count" and r["workload"] == "collision"),
    }
    summary = {}
    for variant in ("baseline", "request_count"):
        for workload in ("unique", "collision"):
            for n in SIZES:
                group = [r for r in runs if r["variant"] == variant and r["workload"] == workload and r["n"] == n]
                controls = [r["readers"]["control"] for r in group]
                audits = [r["readers"]["audit"] for r in group]
                per_rule_mean = defaultdict(float)
                for a in audits:
                    for x in a["per_rule_counters"]:
                        per_rule_mean[(x["rule_name"], x["metric"])] += x["count"] / len(audits)
                global_mean = {k: statistics.mean(a["global_counters"].get(k, 0) for a in audits)
                               for k in audits[0]["global_counters"]}
                key = f"{variant}/{workload}/{n}"
                summary[key] = {
                    "replicates": len(group), "control_tick_ms_median": statistics.median(x["tick_ns"] / 1e6 for x in controls),
                    "audit_tick_ms_median": statistics.median(x["tick_ns"] / 1e6 for x in audits),
                    "audit_overhead_ratio": statistics.median(x["tick_ns"] / 1e6 for x in audits) /
                                            statistics.median(x["tick_ns"] / 1e6 for x in controls),
                    "all_candidate_tests_per_query": global_mean.get("cand_tested", 0),
                    "all_where_evaluations_per_query": global_mean.get("where_evals", 0),
                    "term_evals_total_per_query": global_mean.get("term_evals_total", 0),
                    "count_term_evals_per_query": global_mean.get("term_eval:Count", 0),
                    "filter_term_evals_per_query": global_mean.get("term_eval:Filter", 0),
                    "pair_rule_candidate_tests_per_query": per_rule_mean.get((PAIR_RULE, "candidate_tests"), 0),
                    "retrieve_rule_candidate_tests_per_query": per_rule_mean.get((RETRIEVE_RULE, "candidate_tests"), 0),
                    "retrieve_rule_term_evals_per_query": per_rule_mean.get((RETRIEVE_RULE, "term_evaluations"), 0),
                    "retrieve_rule_effect_node_inserts_per_query": per_rule_mean.get((RETRIEVE_RULE, "effect_node_inserts"), 0),
                    "retrieve_rule_effect_attr_sets_per_query": per_rule_mean.get((RETRIEVE_RULE, "effect_attr_set_attempts"), 0),
                }
    inputs = {
        "harness": Path(__file__).resolve(),
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_EPISODIC_CUE_INDEX_VARIANT_PREREG_20260925.md",
        "world_adapter": ROOT / "substrate/world_adapter.py",
        "boot_core": ROOT / "substrate/boot_core.py",
        "seed_loader": ROOT / "substrate/seed_loader.py",
        "episodic_seed": ROOT / "seeds/episodic_working_memory_core.json",
        "memory_seed": ROOT / "seeds/memory_core.json",
        "rewrite": ROOT / "runners/dsl/src/rewrite.rs",
        "scale_audit": ROOT / "runners/dsl/src/scale_audit.rs",
        "term": ROOT / "runners/dsl/src/term.rs",
        "native_extension": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
    }
    payload = {"schema_version": 1, "run_id": "substrate-episodic-cue-index-variant-20260925-v3",
               "scope": "isolated request-count cue ambiguity prototype versus baseline pair scan",
               "claim_boundary": "Synthetic symbolic cue prototype; response-level semantics and measured envelope only; not a production seed change.",
               "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs.values()},
               "environment": {"python": platform.python_version(), "platform": platform.platform()},
               "configuration": {"sizes": SIZES, "repeats": REPEATS, "workloads": ["unique", "collision"],
                                 "variants": ["baseline", "request_count"]},
               "checks": checks, "summary": summary, "runs": runs}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": summary, "output": str(OUT)}, indent=2))
    if not all(checks.values()): raise SystemExit("cue index variant probe failed")


if __name__ == "__main__": main()
