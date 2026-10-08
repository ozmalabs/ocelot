#!/usr/bin/env python3
"""Fresh-process checkpoint and exact-recall scale sweep for episodic graph memory."""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_episodic_checkpoint_scale_20260925.json"
SIZES = (6, 24, 78, 192)
REPEATS = 2


def edge(agent, src, rel, tgt):
    agent.inner.add_edge_unchecked(src, rel, tgt, {})


def writer(n, path):
    from substrate.world_adapter import WorldAdapter

    t0 = time.perf_counter_ns()
    agent = WorldAdapter(seeds=("episodic_working_memory_core",))
    boot_ns = time.perf_counter_ns() - t0
    for i in range(n):
        context = agent.s.add_node("MemoryContext", {"context_key": f"scale-context-{i}"})
        schema = agent.s.add_node("MemorySchema", {"name": "route_state"})
        event = agent.s.add_node("EpisodicEvent", {
            "event_key": f"scale-event-{i}", "cue_key": f"scale-cue-{i}",
            "epoch": 1.0, "salience": 0.8, "surprise": 0.7, "value": 0.9,
            "observation_status": "observed", "provenance_kind": "perceived",
            "state_kind": "route", "state_summary": f"scale-route-{i}-north",
        })
        edge(agent, agent.agent, "experienced_event", event)
        edge(agent, event, "in_context", context)
        edge(agent, event, "instantiates_schema", schema)
    t0 = time.perf_counter_ns(); progress = int(agent.tick()); closure_ns = time.perf_counter_ns() - t0
    episode_count = sum(1 for node in agent.s.nodes() if agent.s.node(node)["type"] == "Episode")
    t0 = time.perf_counter_ns(); agent.save(path); save_ns = time.perf_counter_ns() - t0
    result = {"pid": os.getpid(), "n": n, "boot_ns": boot_ns, "closure_ns": closure_ns,
              "closure_progress": progress, "save_ns": save_ns, "checkpoint_bytes": Path(path).stat().st_size,
              "episode_count": episode_count, "node_count": agent.s.node_count(),
              "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    agent.close(); print(json.dumps(result, sort_keys=True))


def reader(n, path):
    from substrate.world_adapter import WorldAdapter

    t0 = time.perf_counter_ns(); agent = WorldAdapter.load(path); load_ns = time.perf_counter_ns() - t0
    episode_count = sum(1 for node in agent.s.nodes() if agent.s.node(node)["type"] == "Episode")
    queries = []
    for i in range(n):
        req = agent.s.add_node("MemoryRetrievalRequest", {
            "status": "pending", "cue_key": f"scale-cue-{i}", "epoch": 4.0,
        })
        edge(agent, agent.agent, "has_memory_retrieval_request", req)
        t0 = time.perf_counter_ns(); progress = int(agent.tick()); tick_ns = time.perf_counter_ns() - t0
        candidates = list(agent.inner.neighbours(req, "has_recall_candidate"))
        row = {"index": i, "tick_ns": tick_ns, "progress": progress,
               "candidate_count": len(candidates), "state_summary": None,
               "status": None, "provenance_kind": None, "observation_status": None}
        if len(candidates) == 1:
            cattrs = agent.s.node(candidates[0])["attrs"]
            events = list(agent.inner.neighbours(candidates[0], "reconstructs_event"))
            eattrs = agent.s.node(events[0])["attrs"] if len(events) == 1 else {}
            row.update({"state_summary": eattrs.get("state_summary"),
                        "status": cattrs.get("status"),
                        "provenance_kind": cattrs.get("provenance_kind"),
                        "observation_status": cattrs.get("observation_status")})
        row["expected_summary"] = f"scale-route-{i}-north"
        queries.append(row)
    result = {"pid": os.getpid(), "n": n, "load_ns": load_ns,
              "episode_count": episode_count, "node_count": agent.s.node_count(),
              "queries": queries, "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    try:
        agent.close(); result["close_status"] = "closed"
    except Exception as exc:
        result["close_status"] = "error"; result["close_exception_type"] = type(exc).__name__
    print(json.dumps(result, sort_keys=True))


def p95(values):
    return sorted(values)[max(0, math.ceil(0.95 * len(values)) - 1)]


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--write":
        writer(int(sys.argv[2]), sys.argv[3]); return
    if len(sys.argv) == 4 and sys.argv[1] == "--read":
        reader(int(sys.argv[2]), sys.argv[3]); return
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    runs = []
    with tempfile.TemporaryDirectory(prefix="episodic-checkpoint-scale-") as td:
        for n in SIZES:
            for rep in range(REPEATS):
                path = Path(td) / f"n{n}-rep{rep}.json"
                wp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--write", str(n), str(path)],
                                    cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                writer_result = json.loads(wp.stdout.strip())
                rp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--read", str(n), str(path)],
                                    cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                reader_result = json.loads(rp.stdout.strip())
                runs.append({"n": n, "replicate": rep, "writer": writer_result, "reader": reader_result,
                             "distinct_pids": writer_result["pid"] != reader_result["pid"]})
    checks = {
        "all_declared_sizes_and_repeats": len(runs) == len(SIZES) * REPEATS and
            {(r["n"], r["replicate"]) for r in runs} == {(n, rep) for n in SIZES for rep in range(REPEATS)},
        "distinct_process_per_writer_reader": all(r["distinct_pids"] for r in runs),
        "all_writers_bind_declared_episode_count": all(r["writer"]["episode_count"] == r["n"] for r in runs),
        "all_readers_restore_declared_episode_count": all(r["reader"]["episode_count"] == r["n"] for r in runs),
        "all_keys_recalled_exactly": all(len(r["reader"]["queries"]) == r["n"] and all(
            q["candidate_count"] == 1 and q["state_summary"] == q["expected_summary"] and
            q["status"] == "recalled" and q["provenance_kind"] == "recalled" and
            q["observation_status"] == "not_observed" for q in r["reader"]["queries"]) for r in runs),
        "all_loaded_adapters_close_cleanly": all(r["reader"]["close_status"] == "closed" for r in runs),
    }
    paths = {
        "harness": Path(__file__).resolve(),
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_EPISODIC_CHECKPOINT_SCALE_PREREG_20260925.md",
        "world_adapter": ROOT / "substrate/world_adapter.py",
        "episodic_seed": ROOT / "seeds/episodic_working_memory_core.json",
        "memory_seed": ROOT / "seeds/memory_core.json",
        "native_extension": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
    }
    aggregate = {}
    for n in SIZES:
        group = [r for r in runs if r["n"] == n]
        latencies = [q["tick_ns"] / 1e6 for r in group for q in r["reader"]["queries"]]
        aggregate[str(n)] = {
            "replicates": len(group), "exact_recalls": sum(q["state_summary"] == q["expected_summary"]
                for r in group for q in r["reader"]["queries"]),
            "total_queries": len(latencies),
            "checkpoint_bytes_median": sorted(r["writer"]["checkpoint_bytes"] for r in group)[len(group)//2],
            "save_ms_median": sorted(r["writer"]["save_ns"] / 1e6 for r in group)[len(group)//2],
            "load_ms_median": sorted(r["reader"]["load_ns"] / 1e6 for r in group)[len(group)//2],
            "closure_ms_median": sorted(r["writer"]["closure_ns"] / 1e6 for r in group)[len(group)//2],
            "query_tick_ms_median": sorted(latencies)[len(latencies)//2],
            "query_tick_ms_p95": p95(latencies), "query_tick_ms_max": max(latencies),
            "query_tick_ms_total_per_reader_median": sorted(sum(q["tick_ns"] for q in r["reader"]["queries"])/1e6
                for r in group)[len(group)//2],
            "writer_rss_peak_kib_max": max(r["writer"]["rss_peak_kib"] for r in group),
            "reader_rss_peak_kib_max": max(r["reader"]["rss_peak_kib"] for r in group),
        }
    payload = {"schema_version": 1, "run_id": "substrate-episodic-checkpoint-scale-20260925-v1",
               "scope": "fresh-process full graph checkpoint save/load and all-key exact episodic retrieval, N=6..192",
               "claim_boundary": "Two-replicate synthetic checkpoint scale envelope; not long-term index or natural-task evidence.",
               "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},
               "environment": {"python": platform.python_version(), "platform": platform.platform()},
               "configuration": {"sizes": SIZES, "repeats": REPEATS},
               "checks": checks, "summary": aggregate, "runs": runs}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": aggregate, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("episodic checkpoint scale sweep failed")


if __name__ == "__main__":
    main()
