#!/usr/bin/env python3
"""Measure authored working-memory capacity, cross-task replacement, and TTL."""
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
OUT = ROOT / "evaluation/reports/substrate_working_memory_capacity_ttl_amended_20260925.json"


def edge(agent, src, rel, tgt):
    agent.inner.add_edge_unchecked(src, rel, tgt, {})


def nodes(agent, typ):
    return [n for n in agent.s.nodes() if agent.s.node(n)["type"] == typ]


def attrs(agent, node):
    return agent.s.node(node)["attrs"]


def gate(agent, operation, epoch, *, task="same", priority=0.5, content=None, slot=None):
    node = agent.s.add_node("WorkingMemoryGate", {
        "status": "pending", "operation": operation, "epoch": float(epoch),
        "task_context_key": task, "priority": float(priority),
    })
    edge(agent, agent.agent, "has_working_memory_gate", node)
    if content is not None:
        edge(agent, node, "targets_content", content)
    if slot is not None:
        edge(agent, node, "targets_slot", slot)
    return node


def clock(agent, epoch):
    node = agent.s.add_node("MemoryClock", {"epoch": float(epoch)})
    edge(agent, agent.agent, "has_memory_clock", node)
    return node


def tick(agent, label):
    t0 = time.perf_counter_ns()
    progress = int(agent.tick())
    return {"label": label, "progress": progress,
            "tick_ns": time.perf_counter_ns() - t0}


def record_gate(agent, gate_node):
    results = list(agent.inner.neighbours(gate_node, "has_gate_result"))
    a = attrs(agent, gate_node)
    result = attrs(agent, results[0]) if len(results) == 1 else {}
    reused = list(agent.inner.neighbours(gate_node, "reused_slot"))
    return {"gate_status": a.get("status"), "gate_result": a.get("result"),
            "result_status": result.get("status"), "reason": result.get("reason"),
            "reused_slot_count": len(reused),
            "reused_slot": str(reused[0]) if len(reused) == 1 else None}


def active_slots(agent):
    return [s for s in nodes(agent, "WorkingMemorySlot") if attrs(agent, s).get("status") == "active"]


def run_worker(scenario):
    from substrate.world_adapter import WorldAdapter

    t0 = time.perf_counter_ns()
    agent = WorldAdapter(seeds=("episodic_working_memory_core",))
    boot_ns = time.perf_counter_ns() - t0
    policy = nodes(agent, "WorkingMemoryPolicy")[0]
    if scenario in ("capacity", "replacement"):
        agent.inner.set_attr(policy, "maximum_slots", 2.0)
    ticks, gates = [], []
    if scenario == "capacity":
        for i in range(3):
            content = agent.s.add_node("Concept", {"name": f"same-task-{i}"})
            g = gate(agent, "input", i + 1, task="same", priority=0.5 + i * 0.1, content=content)
            ticks.append(tick(agent, f"input-{i}")); gates.append(record_gate(agent, g))
    elif scenario == "replacement":
        inputs = [("low-chat", "chat", 0.1), ("high-chat", "chat", 0.9), ("project", "project", 0.8)]
        for i, (name, task, priority) in enumerate(inputs):
            content = agent.s.add_node("Concept", {"name": name})
            g = gate(agent, "input", i + 1, task=task, priority=priority, content=content)
            ticks.append(tick(agent, f"input-{name}")); gates.append(record_gate(agent, g))
    elif scenario in ("ttl_unmaintained", "ttl_maintained"):
        content = agent.s.add_node("Concept", {"name": "ttl-target"})
        g = gate(agent, "input", 1, content=content)
        ticks.append(tick(agent, "input")); gates.append(record_gate(agent, g))
        slot = active_slots(agent)[0]
        expiry_before = attrs(agent, slot).get("expires_epoch")
        if scenario == "ttl_maintained":
            mg = gate(agent, "maintain", 8, slot=slot)
            ticks.append(tick(agent, "maintain-8")); gates.append(record_gate(agent, mg))
        clock(agent, 8); ticks.append(tick(agent, "clock-8"))
        state_at_8 = {"status": attrs(agent, slot).get("status"),
                      "expires_epoch": attrs(agent, slot).get("expires_epoch"),
                      "held_content_count": len(list(agent.inner.neighbours(slot, "holds_content")))}
        clock(agent, 9); ticks.append(tick(agent, "clock-9"))
        state_at_9 = {"status": attrs(agent, slot).get("status"),
                      "expires_epoch": attrs(agent, slot).get("expires_epoch"),
                      "held_content_count": len(list(agent.inner.neighbours(slot, "holds_content")))}
        if scenario == "ttl_maintained":
            clock(agent, 16); ticks.append(tick(agent, "clock-16"))
        state_final = {"status": attrs(agent, slot).get("status"),
                       "terminal_reason": attrs(agent, slot).get("terminal_reason"),
                       "terminal_epoch": attrs(agent, slot).get("terminal_epoch"),
                       "expires_epoch": attrs(agent, slot).get("expires_epoch"),
                       "held_content_count": len(list(agent.inner.neighbours(slot, "holds_content")))}
        expiry_data = {"initial_expiry": expiry_before, "at_epoch_8": state_at_8,
                       "at_epoch_9": state_at_9, "final": state_final}
    else:
        raise ValueError(scenario)
    slots = []
    for s in nodes(agent, "WorkingMemorySlot"):
        sa = attrs(agent, s)
        held = list(agent.inner.neighbours(s, "holds_content"))
        slots.append({"status": sa.get("status"), "task_context_key": sa.get("task_context_key"),
                      "priority": sa.get("priority"), "expires_epoch": sa.get("expires_epoch"),
                      "interference_count": sa.get("interference_count"),
                      "last_replacement_reason": sa.get("last_replacement_reason"),
                      "held_content": [attrs(agent, c).get("name") for c in held]})
    result = {"scenario": scenario, "boot_ns": boot_ns, "ticks": ticks, "gates": gates,
              "slots": slots, "active_slot_count": len(active_slots(agent)),
              "slot_count": len(nodes(agent, "WorkingMemorySlot")),
              "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    if scenario.startswith("ttl_"):
        result["expiry"] = expiry_data
    agent.close()
    return result


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(run_worker(sys.argv[2]), sort_keys=True)); return
    scenarios = ("capacity", "replacement", "ttl_unmaintained", "ttl_maintained")
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH', '')}"
    runs = []
    for scenario in scenarios:
        p = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", scenario],
                           cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(p.stdout.strip()))
    by = {r["scenario"]: r for r in runs}
    checks = {
        "same_task_capacity_refuses_third_input": (
            by["capacity"]["active_slot_count"] == 2 and
            [x["result_status"] for x in by["capacity"]["gates"]] == ["accepted", "accepted", "refused"] and
            by["capacity"]["gates"][2]["reason"] == "capacity_limit"),
        "cross_task_replacement_evicts_low_priority_foreign_slot": (
            by["replacement"]["active_slot_count"] == 2 and
            by["replacement"]["gates"][2]["result_status"] == "accepted_with_interference" and
            by["replacement"]["gates"][2]["reused_slot_count"] == 1 and
            any("project" in s["held_content"] and s["interference_count"] == 1 and
                s["last_replacement_reason"] == "cross_task_interference" for s in by["replacement"]["slots"]) and
            any("high-chat" in s["held_content"] for s in by["replacement"]["slots"]) and
            not any("low-chat" in s["held_content"] for s in by["replacement"]["slots"])),
        "unmaintained_ttl_expires_at_epoch_9": (
            by["ttl_unmaintained"]["expiry"]["initial_expiry"] == 9.0 and
            by["ttl_unmaintained"]["expiry"]["at_epoch_8"]["status"] == "active" and
            by["ttl_unmaintained"]["expiry"]["final"]["status"] == "expired" and
            by["ttl_unmaintained"]["expiry"]["final"]["held_content_count"] == 0),
        "maintenance_extends_ttl_and_then_expires": (
            by["ttl_maintained"]["expiry"]["initial_expiry"] == 9.0 and
            by["ttl_maintained"]["expiry"]["at_epoch_8"]["expires_epoch"] == 16.0 and
            by["ttl_maintained"]["expiry"]["at_epoch_9"]["status"] == "active" and
            by["ttl_maintained"]["expiry"]["final"]["status"] == "expired" and
            by["ttl_maintained"]["expiry"]["final"]["held_content_count"] == 0),
    }
    paths = {
        "harness": Path(__file__).resolve(),
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_WORKING_MEMORY_CAPACITY_TTL_PREREG_20260925.md",
        "world_adapter": ROOT / "substrate/world_adapter.py",
        "episodic_seed": ROOT / "seeds/episodic_working_memory_core.json",
        "memory_seed": ROOT / "seeds/memory_core.json",
        "native_extension": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
    }
    payload = {"schema_version": 1, "run_id": "substrate-working-memory-capacity-ttl-20260925-v2",
               "scope": "authored working-memory gate capacity, interference replacement, and epoch TTL",
               "claim_boundary": "Synthetic two-slot mechanism measurement; not long-term memory, natural task utility, or scale evidence.",
               "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},
               "checks": checks, "runs": runs,
               "summary": {"all_checks_pass": all(checks.values()),
                           "boot_ms": {r["scenario"]: r["boot_ns"] / 1e6 for r in runs},
                           "tick_ms": {r["scenario"]: {t["label"]: t["tick_ns"] / 1e6 for t in r["ticks"]} for r in runs}}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": payload["summary"], "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("working-memory capacity/TTL pilot failed")


if __name__ == "__main__":
    main()
