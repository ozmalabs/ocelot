#!/usr/bin/env python3
"""Paired known-answer episodic recall task under interference and memory controls."""
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
OUT = ROOT / "evaluation/reports/substrate_episodic_memory_task_pilot_20260925.json"
TARGET_COUNT = 6
INTERFERENCE_LEVELS = {"memory_small": 0, "memory_medium": 18, "memory_large": 72}
ANSWER_THRESHOLD = 0.75


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def edge(agent, src, rel, tgt):
    agent.inner.add_edge_unchecked(src, rel, tgt, {})


def add_experience(agent, *, event_key, cue_key, context_key, summary,
                   salience, surprise, value, epoch=1.0):
    context = agent.s.add_node("MemoryContext", {"context_key": context_key})
    schema = agent.s.add_node("MemorySchema", {"name": "route_state"})
    event = agent.s.add_node("EpisodicEvent", {
        "event_key": event_key, "cue_key": cue_key, "epoch": float(epoch),
        "salience": float(salience), "surprise": float(surprise),
        "value": float(value), "observation_status": "observed",
        "provenance_kind": "perceived", "state_kind": "route",
        "state_summary": summary,
    })
    edge(agent, agent.agent, "experienced_event", event)
    edge(agent, event, "in_context", context)
    edge(agent, event, "instantiates_schema", schema)
    return event


def target_specs():
    return [{
        "cue_key": f"target-cue-{i}",
        "event_key": f"target-event-{i}",
        "summary": f"route-target-{i}-north-door",
    } for i in range(TARGET_COUNT)]


def add_targets(agent, *, collision=False):
    events = {}
    for i, task in enumerate(target_specs()):
        events[task["cue_key"]] = add_experience(
            agent, event_key=task["event_key"], cue_key=task["cue_key"],
            context_key=f"target-context-{i}", summary=task["summary"],
            salience=0.8, surprise=0.7, value=0.9,
        )
        if collision:
            add_experience(
                agent, event_key=f"alternative-event-{i}", cue_key=task["cue_key"],
                context_key=f"alternative-context-{i}",
                summary=f"route-alternative-{i}-south-door",
                salience=0.2, surprise=0.1, value=0.1,
            )
    return events


def add_distractors(agent, count, prefix):
    for i in range(count):
        add_experience(
            agent, event_key=f"{prefix}-event-{i}", cue_key=f"{prefix}-cue-{i}",
            context_key=f"{prefix}-context-{i}",
            summary=f"unrelated-state-{i}", salience=0.99,
            surprise=0.99, value=0.99,
        )


def query(agent, cue_key, query_id):
    request = agent.s.add_node("MemoryRetrievalRequest", {
        "status": "pending", "cue_key": cue_key, "epoch": 4.0,
    })
    edge(agent, agent.agent, "has_memory_retrieval_request", request)
    t0 = time.perf_counter_ns()
    progress = agent.tick()
    tick_ns = time.perf_counter_ns() - t0
    recalls = list(agent.inner.neighbours(request, "has_recall_candidate"))
    outcomes = list(agent.inner.neighbours(request, "has_recall_outcome"))
    row = {
        "query_id": query_id, "cue_key": cue_key,
        "tick_progress": int(progress), "tick_ns": tick_ns,
        "candidate_count": len(recalls), "outcome_count": len(outcomes),
    }
    if len(recalls) == 1:
        candidate = recalls[0]
        attrs = agent.s.node(candidate)["attrs"]
        events = list(agent.inner.neighbours(candidate, "reconstructs_event"))
        event_attrs = agent.s.node(events[0])["attrs"] if len(events) == 1 else {}
        row.update({
            "status": attrs.get("status"), "confidence": attrs.get("confidence"),
            "uncertainty": attrs.get("uncertainty"),
            "provenance_kind": attrs.get("provenance_kind"),
            "observation_status": attrs.get("observation_status"),
            "event_key": event_attrs.get("event_key"),
            "state_summary": event_attrs.get("state_summary"),
            "reconstructed_event_count": len(events),
        })
    elif len(outcomes) == 1:
        attrs = agent.s.node(outcomes[0])["attrs"]
        row.update({
            "status": attrs.get("status"), "confidence": attrs.get("confidence"),
            "uncertainty": attrs.get("uncertainty"),
            "provenance_kind": attrs.get("provenance_kind"),
            "observation_status": attrs.get("observation_status"),
        })
    else:
        row.update({"status": "no_memory_response", "confidence": None,
                    "uncertainty": None, "provenance_kind": None,
                    "observation_status": None})
    return row


def run_condition(name):
    from substrate.world_adapter import WorldAdapter

    boot_t0 = time.perf_counter_ns()
    if name == "no_memory":
        agent = WorldAdapter(seeds=())
    else:
        agent = WorldAdapter(seeds=("episodic_working_memory_core",))
    boot_ns = time.perf_counter_ns() - boot_t0
    acquire_ns = 0
    acquire_progress = 0
    if name in INTERFERENCE_LEVELS:
        add_targets(agent)
        add_distractors(agent, INTERFERENCE_LEVELS[name], name)
        t0 = time.perf_counter_ns()
        acquire_progress = agent.tick()
        acquire_ns = time.perf_counter_ns() - t0
        acquisition_episode_count = sum(
            1 for nid in agent.s.nodes()
            if agent.s.node(nid)["type"] == "Episode"
        )
        queries = [(f"unique:{x['cue_key']}", x["cue_key"], x["summary"], "unique")
                   for x in target_specs()]
    elif name == "memory_collision":
        add_targets(agent, collision=True)
        add_distractors(agent, 18, name)
        t0 = time.perf_counter_ns()
        acquire_progress = agent.tick()
        acquire_ns = time.perf_counter_ns() - t0
        acquisition_episode_count = sum(
            1 for nid in agent.s.nodes()
            if agent.s.node(nid)["type"] == "Episode"
        )
        queries = [(f"ambiguous:{x['cue_key']}", x["cue_key"],
                    [x["summary"], f"route-alternative-{i}-south-door"], "ambiguous")
                   for i, x in enumerate(target_specs())]
    else:
        acquisition_episode_count = 0
        queries = [(f"unique:{x['cue_key']}", x["cue_key"], x["summary"], "unique")
                   for x in target_specs()]
        queries += [(f"ambiguous:{x['cue_key']}", x["cue_key"], None, "ambiguous")
                    for x in target_specs()]

    # Every condition receives the same unknown-cue negative control.
    rows = []
    for query_id, cue_key, expected, kind in queries:
        row = query(agent, cue_key, query_id)
        row["task_kind"] = kind
        row["expected_summary"] = expected
        row["answer_threshold"] = ANSWER_THRESHOLD
        row["evaluator_action"] = (
            "answer" if row["confidence"] is not None and row["confidence"] >= ANSWER_THRESHOLD
            else "abstain"
        )
        if kind == "unique":
            row["task_correct"] = (row.get("state_summary") == expected
                                   if row["evaluator_action"] == "answer"
                                   else False)
        else:
            valid = set(expected) if isinstance(expected, list) else set()
            row["task_correct"] = (
                row["evaluator_action"] == "abstain" and
                (row.get("state_summary") is None or row.get("state_summary") in valid)
            )
        rows.append(row)

    unknown = query(agent, "never-seen-cue", "unknown-cue")
    unknown["task_kind"] = "unknown"
    unknown["expected_summary"] = None
    unknown["answer_threshold"] = ANSWER_THRESHOLD
    unknown["evaluator_action"] = (
        "answer" if unknown["confidence"] is not None and
        unknown["confidence"] >= ANSWER_THRESHOLD else "abstain"
    )
    unknown["task_correct"] = (unknown["evaluator_action"] == "abstain" and
                               unknown.get("status") in
                               ("insufficient_information", "no_memory_response"))
    rows.append(unknown)
    final_episode_count = sum(
        1 for nid in agent.s.nodes()
        if agent.s.node(nid)["type"] == "Episode"
    )
    record = {
        "condition": name, "boot_ns": boot_ns,
        "acquisition_tick_ns": acquire_ns, "acquisition_progress": int(acquire_progress),
        "acquisition_episode_count": acquisition_episode_count,
        "final_episode_count": final_episode_count,
        "node_count": agent.s.node_count(),
        "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "queries": rows,
    }
    agent.close()
    return record


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(run_condition(sys.argv[2]), sort_keys=True))
        return
    conditions = (*INTERFERENCE_LEVELS.keys(), "memory_collision",
                  "reset_memory", "no_memory")
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    runs = []
    for condition in conditions:
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", condition],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True,
        )
        row = json.loads(proc.stdout.strip())
        runs.append(row)
        print(f"{condition}: episodes={row['acquisition_episode_count']} "
              f"queries={len(row['queries'])} answered="
              f"{sum(q['evaluator_action']=='answer' for q in row['queries'])}", flush=True)

    by_name = {r["condition"]: r for r in runs}
    unique_mem = [q for name in INTERFERENCE_LEVELS
                  for q in by_name[name]["queries"] if q["task_kind"] == "unique"]
    ambiguous = [q for q in by_name["memory_collision"]["queries"]
                 if q["task_kind"] == "ambiguous"]
    reset_rows = by_name["reset_memory"]["queries"]
    no_rows = by_name["no_memory"]["queries"]
    checks = {
        "unique_memory_recalls_exact_answer": all(
            q["candidate_count"] == 1 and q["task_correct"] and
            q["provenance_kind"] == "recalled" and
            q["observation_status"] == "not_observed" for q in unique_mem),
        "unique_recall_survives_unrelated_interference": all(q["task_correct"] for q in unique_mem),
        "collision_confidence_causes_abstention": all(
            q["candidate_count"] == 1 and q["confidence"] == 0.5 and
            q["uncertainty"] == 0.5 and q["evaluator_action"] == "abstain" and
            q["task_correct"] for q in ambiguous),
        "unknown_cue_never_gets_answer": all(
            r["queries"][-1]["task_correct"] and
            r["queries"][-1]["evaluator_action"] == "abstain" for r in runs),
        "reset_memory_explicitly_abstains": all(
            q["status"] == "insufficient_information" and q["evaluator_action"] == "abstain"
            for q in reset_rows),
        "no_memory_has_no_false_candidate": all(
            q["candidate_count"] == 0 and q["evaluator_action"] == "abstain"
            for q in no_rows),
        "matched_query_catalog": len(reset_rows) == len(no_rows) == 13,
        "acquisition_sizes_as_declared": all(
            by_name[name]["acquisition_episode_count"] == 6 + count
            for name, count in INTERFERENCE_LEVELS.items()),
    }
    source_paths = [
        Path(__file__).resolve(), ROOT / "substrate/world_adapter.py",
        ROOT / "substrate/boot_core.py", ROOT / "substrate/seed_loader.py",
        ROOT / "seeds/episodic_working_memory_core.json", ROOT / "seeds/memory_core.json",
        ROOT / "runners/dsl/src/rewrite.rs", ROOT / "runners/dsl/src/term.rs",
        ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
        ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
        ROOT / "runners/dsl/Cargo.lock",
    ]
    summary = {
        "conditions": len(runs),
        "unique_memory_queries": len(unique_mem),
        "unique_memory_accuracy": sum(q["task_correct"] for q in unique_mem) / len(unique_mem),
        "ambiguous_queries": len(ambiguous),
        "ambiguous_abstention_rate": sum(q["evaluator_action"] == "abstain" for q in ambiguous) / len(ambiguous),
        "reset_memory_answers": sum(q["evaluator_action"] == "answer" for q in reset_rows),
        "no_memory_answers": sum(q["evaluator_action"] == "answer" for q in no_rows),
        "max_unique_task_retrieval_ms_by_arm": {
            name: sum(q["tick_ns"] for q in by_name[name]["queries"] if q["task_kind"] == "unique") / 1e6
            for name in INTERFERENCE_LEVELS
        },
        "acquisition_ms_by_arm": {
            name: by_name[name]["acquisition_tick_ns"] / 1e6 for name in INTERFERENCE_LEVELS
        },
    }
    payload = {
        "schema_version": 1,
        "run_id": "substrate-episodic-memory-task-pilot-20260925-v1",
        "scope": "graph-authored episodic cue retrieval with known-answer tasks, unrelated-memory interference, ambiguity, reset-memory and no-memory controls",
        "claim_boundary": "Controlled substrate task pilot on authored episodic rules. Does not establish natural task utility, broad semantic memory, or independent evaluator status.",
        "configuration": {"target_count": TARGET_COUNT,
                          "unrelated_interference_counts": INTERFERENCE_LEVELS,
                          "ambiguous_cue_pairs": TARGET_COUNT,
                          "answer_confidence_threshold": ANSWER_THRESHOLD,
                          "conditions": conditions},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "processor": platform.processor()},
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths},
        "checks": checks, "summary": summary, "runs": runs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"runs": len(runs), "checks": checks,
                      "summary": summary, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("episodic memory task benchmark failed")


if __name__ == "__main__":
    main()
