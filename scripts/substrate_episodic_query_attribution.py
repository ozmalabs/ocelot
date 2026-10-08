#!/usr/bin/env python3
"""Attribute one episodic recall tick with native scale and per-rule counters."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_episodic_query_attribution_20260925.json"
SIZES = (6, 24, 78, 192)
REPEATS = 3


def edge(agent, src, rel, tgt):
    agent.inner.add_edge_unchecked(src, rel, tgt, {})


def writer(n, path):
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("episodic_working_memory_core",))
    for i in range(n):
        context = agent.s.add_node("MemoryContext", {"context_key": f"attr-context-{i}"})
        schema = agent.s.add_node("MemorySchema", {"name": "route_state"})
        event = agent.s.add_node("EpisodicEvent", {
            "event_key": f"attr-event-{i}", "cue_key": f"attr-cue-{i}",
            "epoch": 1.0, "salience": 0.8, "surprise": 0.7, "value": 0.9,
            "observation_status": "observed", "provenance_kind": "perceived",
            "state_kind": "route", "state_summary": f"attr-route-{i}-north",
        })
        edge(agent, agent.agent, "experienced_event", event)
        edge(agent, event, "in_context", context)
        edge(agent, event, "instantiates_schema", schema)
    closure_progress = int(agent.tick())
    episode_count = sum(1 for node in agent.s.nodes() if agent.s.node(node)["type"] == "Episode")
    agent.save(path)
    result = {"pid": os.getpid(), "n": n, "closure_progress": closure_progress,
              "episode_count": episode_count, "node_count": agent.s.node_count(),
              "checkpoint_bytes": Path(path).stat().st_size,
              "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    agent.close(); print(json.dumps(result, sort_keys=True))


def reader(n, path, audit):
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter.load(path)
    query_index = n // 2
    request = agent.s.add_node("MemoryRetrievalRequest", {
        "status": "pending", "cue_key": f"attr-cue-{query_index}", "epoch": 4.0,
    })
    edge(agent, agent.agent, "has_memory_retrieval_request", request)
    agent.inner.scale_audit_set_enabled(False)
    agent.inner.scale_audit_set_per_rule_enabled(False)
    agent.inner.scale_audit_reset()
    agent.inner.scale_audit_per_rule_reset()
    if audit:
        agent.inner.scale_audit_set_enabled(True)
        agent.inner.scale_audit_set_per_rule_enabled(True)
    t0 = time.perf_counter_ns(); progress = int(agent.tick()); tick_ns = time.perf_counter_ns() - t0
    candidates = list(agent.inner.neighbours(request, "has_recall_candidate"))
    row = {"pid": os.getpid(), "n": n, "audit": audit, "query_index": query_index,
           "progress": progress, "tick_ns": tick_ns, "candidate_count": len(candidates),
           "state_summary": None, "status": None, "provenance_kind": None,
           "observation_status": None}
    if len(candidates) == 1:
        ca = agent.s.node(candidates[0])["attrs"]
        events = list(agent.inner.neighbours(candidates[0], "reconstructs_event"))
        ea = agent.s.node(events[0])["attrs"] if len(events) == 1 else {}
        row.update({"state_summary": ea.get("state_summary"), "status": ca.get("status"),
                    "provenance_kind": ca.get("provenance_kind"),
                    "observation_status": ca.get("observation_status")})
    row["expected_summary"] = f"attr-route-{query_index}-north"
    if audit:
        row["global_counters"] = dict(agent.inner.scale_audit_snapshot())
        names = {int(record[0]): str(record[1]) for record in agent.inner.rule_access_sets()}
        row["per_rule_counters"] = [
            {"rule_index": int(idx), "rule_name": names.get(int(idx), f"rule_{idx}"),
             "metric": str(metric), "count": int(count)}
            for idx, metric, count in agent.inner.scale_audit_per_rule_snapshot()
        ]
    else:
        row["global_counters"] = None; row["per_rule_counters"] = None
    agent.inner.scale_audit_set_per_rule_enabled(False)
    agent.inner.scale_audit_set_enabled(False)
    row["rss_peak_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    try:
        agent.close(); row["close_status"] = "closed"
    except Exception as exc:
        row["close_status"] = "error"; row["close_exception_type"] = type(exc).__name__
    print(json.dumps(row, sort_keys=True))


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--write":
        writer(int(sys.argv[2]), sys.argv[3]); return
    if len(sys.argv) == 5 and sys.argv[1] == "--read":
        reader(int(sys.argv[2]), sys.argv[4], sys.argv[3] == "audit"); return
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    runs = []
    with tempfile.TemporaryDirectory(prefix="episodic-query-attribution-") as td:
        for n in SIZES:
            for rep in range(REPEATS):
                path = Path(td) / f"n{n}-rep{rep}.json"
                wp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--write", str(n), str(path)],
                                    cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                w = json.loads(wp.stdout.strip())
                pair = {}
                for arm in ("control", "audit"):
                    rp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--read", str(n), arm, str(path)],
                                        cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                    pair[arm] = json.loads(rp.stdout.strip())
                runs.append({"n": n, "replicate": rep, "writer": w, "readers": pair})
    checks = {
        "complete_size_replicate_design": len(runs) == len(SIZES) * REPEATS and
            {(r["n"], r["replicate"]) for r in runs} == {(n, rep) for n in SIZES for rep in range(REPEATS)},
        "writer_and_readers_use_distinct_processes": all(
            len({r["writer"]["pid"], r["readers"]["control"]["pid"], r["readers"]["audit"]["pid"]}) == 3 for r in runs),
        "all_writers_bind_expected_episodes": all(r["writer"]["episode_count"] == r["n"] for r in runs),
        "paired_control_audit_answers_match": all(
            all(r["readers"][arm]["candidate_count"] == 1 and
                r["readers"][arm]["state_summary"] == r["readers"][arm]["expected_summary"] and
                r["readers"][arm]["status"] == "recalled" and
                r["readers"][arm]["provenance_kind"] == "recalled" and
                r["readers"][arm]["observation_status"] == "not_observed"
                for arm in ("control", "audit")) and
            r["readers"]["control"]["state_summary"] == r["readers"]["audit"]["state_summary"]
            for r in runs),
        "readers_close_cleanly": all(r["readers"][a]["close_status"] == "closed" for r in runs for a in ("control", "audit")),
        "audit_counters_present": all(r["readers"]["audit"]["global_counters"] and
                                       r["readers"]["audit"]["per_rule_counters"] is not None for r in runs),
    }
    paths = {
        "harness": Path(__file__).resolve(),
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_EPISODIC_QUERY_ATTRIBUTION_PREREG_20260925.md",
        "world_adapter": ROOT / "substrate/world_adapter.py",
        "episodic_seed": ROOT / "seeds/episodic_working_memory_core.json",
        "memory_seed": ROOT / "seeds/memory_core.json",
        "rewrite": ROOT / "runners/dsl/src/rewrite.rs",
        "scale_audit": ROOT / "runners/dsl/src/scale_audit.rs",
        "term": ROOT / "runners/dsl/src/term.rs",
        "native_extension": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
        "cargo_lock": ROOT / "runners/dsl/Cargo.lock",
    }
    summary = {}
    for n in SIZES:
        group = [r for r in runs if r["n"] == n]
        control_ms = sorted(r["readers"]["control"]["tick_ns"] / 1e6 for r in group)
        audit_ms = sorted(r["readers"]["audit"]["tick_ns"] / 1e6 for r in group)
        counters = [r["readers"]["audit"]["global_counters"] for r in group]
        aggregate = {key: sum(c.get(key, 0) for c in counters) for key in counters[0]}
        per_rule = {}
        for r in group:
            for row in r["readers"]["audit"]["per_rule_counters"]:
                k = (row["rule_name"], row["metric"])
                per_rule[k] = per_rule.get(k, 0) + row["count"]
        summary[str(n)] = {
            "replicates": len(group), "query_index": n // 2,
            "control_tick_ms_median": control_ms[len(control_ms)//2],
            "audit_tick_ms_median": audit_ms[len(audit_ms)//2],
            "audit_overhead_ratio_median": (audit_ms[len(audit_ms)//2] / control_ms[len(control_ms)//2]) if control_ms[len(control_ms)//2] else None,
            "global_counter_totals_across_replicates": aggregate,
            "global_counter_per_query_mean": {k: v / len(group) for k, v in aggregate.items()},
            "per_rule_counter_totals_across_replicates": [
                {"rule_name": k[0], "metric": k[1], "count": v}
                for k, v in sorted(per_rule.items())],
            "control_rss_peak_kib_max": max(r["readers"]["control"]["rss_peak_kib"] for r in group),
            "audit_rss_peak_kib_max": max(r["readers"]["audit"]["rss_peak_kib"] for r in group),
        }
    payload = {"schema_version": 1, "run_id": "substrate-episodic-query-attribution-20260925-v1",
               "scope": "one exact episodic retrieval query per restored graph; native per-rule scale audit paired with control",
               "claim_boundary": "Synthetic exact-cue task; operation counts are instrumented-site counts, not complete hardware cost or asymptotic proof.",
               "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},
               "environment": {"python": platform.python_version(), "platform": platform.platform()},
               "configuration": {"sizes": SIZES, "repeats": REPEATS},
               "checks": checks, "summary": summary, "runs": runs}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": summary, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("episodic query attribution pilot failed")


if __name__ == "__main__":
    main()
