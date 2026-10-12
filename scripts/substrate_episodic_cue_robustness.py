#!/usr/bin/env python3
"""Frozen exact/truncated/paraphrase cue probe for graph-authored episodic memory."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_episodic_cue_robustness_20260925.json"
TARGETS = 6


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def edge(agent, src, rel, tgt):
    agent.inner.add_edge_unchecked(src, rel, tgt, {})


def specs():
    return [{"index": i, "cue": f"route/district/{i}/door/north",
             "summary": f"district-{i}-north-door"} for i in range(TARGETS)]


def experience(agent, event_key, cue, summary, i, salience):
    context = agent.s.add_node("MemoryContext", {"context_key": f"ctx-{event_key}"})
    schema = agent.s.add_node("MemorySchema", {"name": "route_state"})
    event = agent.s.add_node("EpisodicEvent", {
        "event_key": event_key, "cue_key": cue, "epoch": 1.0,
        "salience": salience, "surprise": salience, "value": salience,
        "observation_status": "observed", "provenance_kind": "perceived",
        "state_kind": "route", "state_summary": summary,
    })
    edge(agent, agent.agent, "experienced_event", event)
    edge(agent, event, "in_context", context)
    edge(agent, event, "instantiates_schema", schema)


def run_worker(condition):
    from substrate.world_adapter import WorldAdapter

    t0 = time.perf_counter_ns()
    agent = WorldAdapter(seeds=("episodic_working_memory_core",))
    boot_ns = time.perf_counter_ns() - t0
    for x in specs():
        experience(agent, f"target-{x['index']}", x["cue"], x["summary"], x["index"], 0.8)
        if condition == "near_neighbor":
            experience(agent, f"neighbor-{x['index']}",
                       f"route/district/{x['index']}/door/northwest",
                       f"district-{x['index']}-northwest-door", x["index"], 0.99)
    t0 = time.perf_counter_ns()
    acquisition_progress = agent.tick()
    acquisition_ns = time.perf_counter_ns() - t0
    records = []
    for x in specs():
        forms = [
            ("exact", x["cue"]),
            ("truncated", f"route/district/{x['index']}/door"),
            ("paraphrase", f"north entrance in district {x['index']}"),
        ]
        for form, query_cue in forms:
            req = agent.s.add_node("MemoryRetrievalRequest", {
                "status": "pending", "cue_key": query_cue, "epoch": 4.0,
            })
            edge(agent, agent.agent, "has_memory_retrieval_request", req)
            t0 = time.perf_counter_ns()
            progress = agent.tick()
            tick_ns = time.perf_counter_ns() - t0
            candidates = list(agent.inner.neighbours(req, "has_recall_candidate"))
            outcomes = list(agent.inner.neighbours(req, "has_recall_outcome"))
            row = {"task_id": f"{form}:{x['index']}", "form": form,
                   "target_index": x["index"], "query_cue": query_cue,
                   "expected_summary": x["summary"], "candidate_count": len(candidates),
                   "progress": int(progress), "tick_ns": tick_ns}
            if len(candidates) == 1:
                ca = agent.s.node(candidates[0])["attrs"]
                events = list(agent.inner.neighbours(candidates[0], "reconstructs_event"))
                ea = agent.s.node(events[0])["attrs"] if len(events) == 1 else {}
                row.update({"status": ca.get("status"), "confidence": ca.get("confidence"),
                            "provenance_kind": ca.get("provenance_kind"),
                            "observation_status": ca.get("observation_status"),
                            "event_key": ea.get("event_key"), "state_summary": ea.get("state_summary")})
            elif len(outcomes) == 1:
                oa = agent.s.node(outcomes[0])["attrs"]
                row.update({"status": oa.get("status"), "confidence": oa.get("confidence")})
            else:
                row.update({"status": "no_response", "confidence": None})
            if form == "exact":
                row["expected_behavior"] = "exact_recall"
                row["correct"] = (row["candidate_count"] == 1 and
                                  row.get("state_summary") == x["summary"] and
                                  row.get("status") == "recalled" and
                                  row.get("provenance_kind") == "recalled" and
                                  row.get("observation_status") == "not_observed")
            else:
                row["expected_behavior"] = "insufficient_information"
                row["correct"] = (row["candidate_count"] == 0 and
                                  row.get("status") == "insufficient_information")
            records.append(row)
    ep_count = sum(1 for n in agent.s.nodes() if agent.s.node(n)["type"] == "Episode")
    result = {"condition": condition, "boot_ns": boot_ns,
              "acquisition_ns": acquisition_ns, "acquisition_progress": int(acquisition_progress),
              "episode_count": ep_count, "node_count": agent.s.node_count(),
              "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "queries": records}
    agent.close()
    return result


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(run_worker(sys.argv[2]), sort_keys=True))
        return
    arms = ("clean", "near_neighbor")
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    runs = []
    for arm in arms:
        p = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", arm],
                           cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(p.stdout.strip()))
    by_arm = {r["condition"]: r for r in runs}
    checks = {
        "declared_episode_counts": by_arm["clean"]["episode_count"] == 6 and by_arm["near_neighbor"]["episode_count"] == 12,
        "exact_cues_recall_targets": all(q["correct"] for r in runs for q in r["queries"] if q["form"] == "exact"),
        "truncated_cues_are_explicit_misses": all(q["correct"] for r in runs for q in r["queries"] if q["form"] == "truncated"),
        "paraphrase_cues_are_explicit_misses": all(q["correct"] for r in runs for q in r["queries"] if q["form"] == "paraphrase"),
        "near_neighbors_do_not_replace_exact_targets": all(
            q["state_summary"] == q["expected_summary"] for q in by_arm["near_neighbor"]["queries"] if q["form"] == "exact"),
        "unique_task_ids_per_arm": all(len({q["task_id"] for q in r["queries"]}) == 18 for r in runs),
    }
    paths = {
        "harness": Path(__file__).resolve(),
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_EPISODIC_CUE_ROBUSTNESS_PREREG_20260925.md",
        "world_adapter": ROOT / "substrate/world_adapter.py",
        "episodic_seed": ROOT / "seeds/episodic_working_memory_core.json",
        "memory_seed": ROOT / "seeds/memory_core.json",
        "native_extension": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
    }
    source_hashes = {name: sha(path) for name, path in paths.items()}
    payload = {"schema_version": 1, "run_id": "substrate-episodic-cue-robustness-20260925-v1",
               "scope": "exact, truncated, paraphrase, and lexical-neighbor cue behavior",
               "claim_boundary": "Six-item synthetic symbolic-key interface probe; not natural-language or broad semantic-memory evidence.",
               "source_sha256": {str(p.relative_to(ROOT)): source_hashes[k] for k, p in paths.items()},
               "checks": checks, "runs": runs,
               "summary": {r["condition"]: {
                   form: {"n": sum(q["form"] == form for q in r["queries"]),
                          "correct": sum(q["form"] == form and q["correct"] for q in r["queries"]),
                          "median_tick_ms": sorted(q["tick_ns"] / 1e6 for q in r["queries"] if q["form"] == form)[3]}
                   for form in ("exact", "truncated", "paraphrase")}
                   for r in runs}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": payload["summary"], "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("episodic cue robustness benchmark failed")


if __name__ == "__main__":
    main()
