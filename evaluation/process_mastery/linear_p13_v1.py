"""Paired P13 sleep, library and strategy evaluation.

Python installs paired worlds/events, advances the native world adapter, and
reads graph receipts. Process selection, solving, strategy recall and sleep
stage transitions remain native seed rules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "runners/dsl/python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from evaluation.process_mastery.scorecard import write_scorecard  # noqa: E402
from substrate.boot_profiles import boot_cognition_on  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402
import substrate_rs  # noqa: E402

PHASE = "linear-p13-v1"
ARMS = ("full_sleep", "replay_only", "awake_rehearsal", "no_offline")
LIMITS = {"ticks_per_epoch": 8, "max_steps_per_tick": 100_000,
          "budget_capacity": 32.0, "source_tasks": 2, "delayed_tasks": 1}
ALLOCATIONS = {"paired_streams": 200, "interrupt_restart_controls": 100}
DEV_SEED = 13_000_000
HELDOUT_SEED = 13_100_000
ACTION = [1, 2, 0]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                           default=str).encode())


def provenance():
    paths = (
        "evaluation/process_mastery/linear_p13_v1.py",
        "evaluation/process_mastery/analyze_linear_p13_v1.py",
        "evaluation/process_mastery/harness.py",
        "evaluation/process_mastery/scorecard.py",
        "substrate/boot_profiles.py", "substrate/world_adapter.py",
        "substrate/boot_core.py", "substrate/seed_loader.py",
        "seeds/cognition_on_params.json", "seeds/consolidation_scheduler.json",
        "seeds/episodic_working_memory_core.json", "seeds/process_schema.json",
        "seeds/default_mode_core.json", "seeds/thinking_budget.json",
        "seeds/extended_thinking.json",
        "seeds/process_solving.json", "seeds/sleep_regime.json",
        "seeds/library_learning.json", "seeds/strategy_library.json",
        "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
        "runners/dsl/src/lib.rs", "runners/dsl/src/process_algebra.rs",
        "runners/dsl/src/term.rs", "runners/dsl/src/cognitive_cycle.rs",
        "runners/dsl/src/area_scheduler.rs", "runners/dsl/src/clock.rs",
        "runners/dsl/src/substrate.rs", "runners/dsl/src/graph.rs",
        "runners/dsl/src/graph_rules.rs", "runners/dsl/src/checker.rs",
        "runners/dsl/src/prog_eval.rs", "runners/dsl/src/rule_json.rs",
        "runners/dsl/src/seed_manifest.rs", "runners/dsl/src/py.rs",
    )
    bundle = hashlib.sha256()
    for rel in paths:
        bundle.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    profile_paths = ("substrate/boot_profiles.py", "seeds/cognition_on_params.json")
    profile_bundle = hashlib.sha256()
    for rel in profile_paths:
        profile_bundle.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    world_path = "substrate/world_adapter.py"
    world_bundle = hashlib.sha256(world_path.encode() + b"\0"
                                  + (ROOT / world_path).read_bytes() + b"\0")
    engine_paths = (
        "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
        "runners/dsl/src/lib.rs", "runners/dsl/src/process_algebra.rs",
        "runners/dsl/src/term.rs", "runners/dsl/src/cognitive_cycle.rs",
        "runners/dsl/src/area_scheduler.rs", "runners/dsl/src/clock.rs",
        "runners/dsl/src/substrate.rs", "runners/dsl/src/graph.rs",
        "runners/dsl/src/graph_rules.rs", "runners/dsl/src/checker.rs",
        "runners/dsl/src/prog_eval.rs", "runners/dsl/src/rule_json.rs",
        "runners/dsl/src/seed_manifest.rs", "runners/dsl/src/py.rs",
    )
    engine_bundle = hashlib.sha256()
    for rel in engine_paths:
        engine_bundle.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                         cwd=ROOT, text=True).strip()
    except Exception:
        commit = "unavailable"
    return {"phase": PHASE, "git_commit": commit,
            "source_bundle_sha256": bundle.hexdigest(),
            "profile_sha256": profile_bundle.hexdigest(),
            "world_adapter_sha256": world_bundle.hexdigest(),
            "engine_source_sha256": engine_bundle.hexdigest(),
            "runner_sha256": _sha(Path(__file__).read_bytes()),
            "analyzer_sha256": _sha((ROOT / "evaluation/process_mastery/analyze_linear_p13_v1.py").read_bytes()),
            "engine_binary_sha256": _sha(Path(substrate_rs.__file__).read_bytes()),
            "python": sys.version.split()[0], "limits": dict(LIMITS)}


def _edge(agent, src, edge, tgt):
    agent.inner.add_edge_unchecked(src, edge, tgt, {})


def _nodes(agent, kind):
    return [n for n in agent.s.nodes()
            if agent.s.node(n)["type"] == kind]


def _set_policy(agent, kind, enabled, **attrs):
    nodes = _nodes(agent, kind)
    if not nodes:
        raise RuntimeError(f"missing required P13 adapter policy {kind}")
    current = [n for n in nodes
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    selected = current[0] if current else nodes[0]
    for node in nodes:
        agent.inner.set_attr(node, "enabled", float(bool(enabled) and node == selected))
        for key, value in attrs.items():
            agent.inner.set_attr(node, key, value)


def _agent(arm):
    started = time.perf_counter()
    agent = boot_cognition_on()
    boot_seconds = time.perf_counter() - started
    # Hold the shared process world and solving machinery constant. Only the
    # registered offline/strategy treatments vary by arm.
    _set_policy(agent, "ProcessSchemaPolicy", 1.0)
    _set_policy(agent, "SolverPolicy", 1.0, max_steps=64.0)
    _set_policy(agent, "InvariantMinerPolicy", 1.0)
    _set_policy(agent, "InventionPolicy", 0.0)
    _set_policy(agent, "ConsolidationSchedulerPolicy", 1.0 if arm != "no_offline" else 0.0)
    treatment = arm == "full_sleep"
    _set_policy(agent, "SleepRegimePolicy", 1.0 if treatment else 0.0)
    _set_policy(agent, "LibraryLearningPolicy", 1.0 if treatment else 0.0)
    _set_policy(agent, "StrategyLibraryPolicy", 1.0 if treatment else 0.0)
    budgets = [n for n in _nodes(agent, "ThinkingBudget")
               if agent.s.node(n)["attrs"].get("enabled") == 1.0]
    if len(budgets) != 1:
        raise RuntimeError(f"expected one enabled shared ThinkingBudget, found {len(budgets)}")
    budget = budgets[0]
    agent.inner.set_attr(budget, "capacity", LIMITS["budget_capacity"])
    agent.inner.set_attr(budget, "remaining", LIMITS["budget_capacity"])
    agent.inner.set_attr(budget, "refill_per_epoch", 2.0)
    return agent, boot_seconds, budget


def _add_domain(agent, seed, *, size=3, prefix="cycle"):
    domain_name = f"p13-{prefix}-{seed}"
    domain = agent.s.add_node("ProcessDomain", {
        "name": domain_name, "kind": "permutation", "probes": [list(range(size))],
        "probe_epoch": 0, "source_epoch": 0, "model_epoch": 0,
        "frame_epoch": 0,
    })
    _edge(agent, agent.agent, "has_process_domain", domain)
    if size == 3:
        processes = (("cycle", ACTION), ("swap", [1, 0, 2]))
    else:
        processes = []
        for index in range(size - 1):
            params = list(range(size))
            params[index], params[size - 1] = params[size - 1], params[index]
            processes.append((f"swap-{index}", params))
    for name, params in processes:
        process = agent.s.add_node("ProcessSchema", {
            "name": name, "kind": "permutation", "domain": domain_name,
            "domain_kind": "permutation", "params": params, "cost": 1.0,
            "provenance": "held", "status": "active", "owner_agent": agent.agent,
            "invariants": [], "source_epoch": 0, "model_epoch": 0,
            "frame_epoch": 0, "probe_epoch": 0, "source_probe_epoch": 0,
        })
        _edge(agent, agent.agent, "has_process_schema", process)
    return domain_name


def _task(agent, domain, name, initial, goal, seed):
    task = agent.s.add_node("SolveTask", {
        "domain": domain, "name": name, "initial_state": list(initial),
        "state": list(initial), "goal": list(goal), "status": "active",
        "steps": 0, "moves": 0.0, "trace": [], "stuck_count": 0,
        "tools_seen": 0, "pmb_seed": seed,
    })
    _edge(agent, agent.agent, "has_solve_task", task)
    domain_node = next(n for n in _nodes(agent, "ProcessDomain")
                       if agent.s.node(n)["attrs"].get("name") == domain)
    _edge(agent, task, "about_domain", domain_node)
    return task


def _settle(agent, n=8):
    total = 0
    for _ in range(n):
        total += agent.inner.run_rules(LIMITS["max_steps_per_tick"])
    return total


def _apply_sequence(agent, state, processes):
    value = list(state)
    for process in processes:
        value = agent.inner.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "p"},
             "state": {"type": "Var", "name": "state"}},
            {"p": agent.s.node(process)["attrs"]["params"], "state": value})
        if value is None:
            raise RuntimeError("native process world adapter could not apply held process")
    return list(value)


def _interference_event(agent, seed):
    context = agent.s.add_node("MemoryContext", {
        "context_key": f"p13-interference:{seed}", "kind": "unrelated_context"})
    schema = agent.s.add_node("MemorySchema", {
        "name": f"unrelated-route:{seed}", "context_key": f"p13-interference:{seed}"})
    event = agent.s.add_node("EpisodicEvent", {
        "event_key": f"interference:{seed}", "cue_key": f"interference-cue:{seed}",
        "epoch": 6.0, "salience": 0.95, "surprise": 0.9, "value": 0.0,
        "observation_status": "observed", "provenance_kind": "perceived",
        "state_kind": "world_state", "state_summary": "unrelated interference event",
    })
    _edge(agent, agent.agent, "experienced_event", event)
    _edge(agent, event, "in_context", context)
    _edge(agent, event, "instantiates_schema", schema)
    tick_steps = 0
    for _ in range(LIMITS["ticks_per_epoch"]):
        tick_steps += agent.tick()
    return event, tick_steps


def _sleep_input(agent, seed, *, interrupt=False):
    tick_steps = 0
    context = agent.s.add_node("MemoryContext", {"context_key": f"p13:{seed}"})
    schema = agent.s.add_node("MemorySchema", {"name": f"observed-route:{seed}"})
    episode = agent.s.add_node("EpisodicEvent", {
        "event_key": f"observed:{seed}", "cue_key": f"cue:{seed}", "epoch": 0.0,
        "salience": 0.8, "surprise": 0.5, "value": 0.5,
        "observation_status": "observed", "provenance_kind": "perceived",
        "state_kind": "world_state", "state_summary": "observed world event",
    })
    _edge(agent, agent.agent, "experienced_event", episode)
    _edge(agent, episode, "in_context", context)
    _edge(agent, episode, "instantiates_schema", schema)
    for _ in range(LIMITS["ticks_per_epoch"]):
        tick_steps += agent.tick()
    for epoch in range(1, 6):
        sample = agent.s.add_node("NetworkModeSample", {
            "epoch": float(epoch), "default_mode_weight": 1.0,
            "exteroceptive_load": 0.0, "task_demand": 1.0 if interrupt and epoch == 2 else 0.0,
            "interoceptive_urgency": 0.0, "uncertainty": 0.0,
            "idle_duration": 8.0, "status": "raw",
        })
        _edge(agent, agent.agent, "has_network_mode_sample", sample)
        for _ in range(LIMITS["ticks_per_epoch"]):
            tick_steps += agent.tick()
    receipts = _nodes(agent, "SleepStageReceipt")
    replay_traces = _nodes(agent, "ReplayTrace")
    return {"sleep_receipts": len(receipts),
            "replay_traces": len(replay_traces),
            "stages": [agent.s.node(n)["attrs"].get("stage") for n in receipts],
            "receipt_audit": [{
                "stage": agent.s.node(n)["attrs"].get("stage"),
                "status": agent.s.node(n)["attrs"].get("status"),
                "provenance_kind": agent.s.node(n)["attrs"].get("provenance_kind"),
                "observation_status": agent.s.node(n)["attrs"].get("observation_status"),
                "shared_budget_debit": agent.s.node(n)["attrs"].get("shared_budget_debit"),
                "funded_request": bool(agent.inner.neighbours(n, "funded_by_request")),
                "follows_prior": bool(agent.inner.neighbours(n, "follows_stage_receipt")),
            } for n in receipts],
            "sleep_stage_debit_total": sum(
                float(agent.s.node(n)["attrs"].get("shared_budget_debit", 0.0))
                for n in receipts
                if agent.s.node(n)["attrs"].get("stage") != "replay"),
            "cycle_request_debits": sum(
                float(agent.s.node(request)["attrs"].get("cost", 0.0))
                for cycle in _nodes(agent, "MemoryCycle")
                for request in agent.inner.neighbours(cycle, "has_consolidation_task_request")
                if agent.inner.neighbours(request, "draws_on_thinking_budget")
                and agent.s.node(request)["attrs"].get("status") == "serviced"),
            "cycle_request_count": sum(
                1 for cycle in _nodes(agent, "MemoryCycle")
                for request in agent.inner.neighbours(cycle, "has_consolidation_task_request")
                if agent.inner.neighbours(request, "draws_on_thinking_budget")
                and agent.s.node(request)["attrs"].get("status") == "serviced"),
            "native_rule_steps": tick_steps,
            "interrupted": bool(interrupt and any(
                agent.s.node(n)["attrs"].get("sleep_stage_cursor") == "consolidate"
                for n in _nodes(agent, "MemoryCycle")))}


def _run_trial(seed, arm, split, *, awake_compute_target=0):
    agent, boot_seconds, budget = _agent(arm)
    started_nodes = len(list(agent.s.nodes()))
    _set_policy(agent, "StrategyLibraryPolicy", 0.0)
    domain = _add_domain(agent, seed, size=33, prefix="library")
    library_primitives = [n for n in _nodes(agent, "ProcessSchema")
                          if agent.s.node(n)["attrs"].get("domain") == domain
                          and agent.s.node(n)["attrs"].get("provenance") == "held"]
    source_initial = list(range(1, 33)) + [0]
    source_goal = list(range(33))
    source_tasks = []
    native_rule_steps = 0
    for i in range(LIMITS["source_tasks"]):
        task = _task(agent, domain, f"library-source-{i}",
                     source_initial, source_goal, seed)
        native_rule_steps += _settle(agent, n=80)
        source_tasks.append(task)
    if not all(agent.s.node(n)["attrs"].get("status") == "solved" for n in source_tasks):
        raise RuntimeError(f"{arm} source-task adapter failed to solve seed {seed}")

    sleep = {"sleep_receipts": 0, "replay_traces": 0, "stages": [], "interrupted": False}
    awake_rehearsal_steps = 0
    awake_rehearsal_count = 0
    if arm in ("full_sleep", "replay_only"):
        sleep = _sleep_input(agent, seed)
        native_rule_steps += sleep["native_rule_steps"]
    elif arm == "awake_rehearsal":
        # Match the full-sleep arm's measured native rule steps using short,
        # real one-primitive rehearsal tasks from the same process bank.
        awake_start_steps = native_rule_steps
        awake_rehearsal_count = 0
        rehearsal_index = LIMITS["source_tasks"]
        while native_rule_steps - awake_start_steps < awake_compute_target:
            rehearsal_initial = list(range(33))
            swap_index = rehearsal_index % 32
            rehearsal_initial[swap_index], rehearsal_initial[32] = (
                rehearsal_initial[32], rehearsal_initial[swap_index])
            rehearsal = _task(agent, domain, f"awake-match-{rehearsal_index}",
                              rehearsal_initial, source_goal, seed)
            native_rule_steps += _settle(agent, n=80)
            if agent.s.node(rehearsal)["attrs"].get("status") != "solved":
                raise RuntimeError(f"matched-compute rehearsal failed for seed {seed}")
            rehearsal_index += 1
            awake_rehearsal_count += 1
        awake_rehearsal_steps = native_rule_steps - awake_start_steps
    else:
        awake_rehearsal_steps = 0
        awake_rehearsal_count = 0

    interference, interference_steps = _interference_event(agent, seed)
    native_rule_steps += interference_steps

    delayed_initial = [2, *range(3, 33), 0, 1]
    delayed_goal = _apply_sequence(agent, delayed_initial, library_primitives)
    strategy_entries_before_delayed = len(_nodes(agent, "StrategyLibraryEntry"))
    delayed = _task(agent, domain, "delayed-library-heldout",
                    delayed_initial, delayed_goal, seed)
    native_rule_steps += _settle(agent, n=80)
    delayed_attrs = agent.s.node(delayed)["attrs"]
    solved = delayed_attrs.get("status") == "solved" and delayed_attrs.get("state") == delayed_goal

    chunks = [n for n in _nodes(agent, "ProcessLibraryChunk")
              if agent.s.node(n)["attrs"].get("domain") == domain]
    chunk_cost = agent.s.node(chunks[0])["attrs"].get("library_cost") if chunks else 2 * 32
    inline_cost = 2 * 32
    package_cost_per_source = chunk_cost / 2.0
    reuse_cost = package_cost_per_source + 1.0  # one schema application after retrieval
    primitive_reference_work = len(agent.s.node(source_tasks[0])["attrs"].get("trace", []))
    library_reduction = (1.0 - reuse_cost / max(1.0, float(primitive_reference_work))) if chunks else 0.0

    # Separate small structural family exercises P13.04 on native solved
    # traces after the sleep/library panel; controls retain primitive search.
    strategy_domain = _add_domain(agent, seed, size=3, prefix="strategy")
    _set_policy(agent, "StrategyLibraryPolicy", 1.0 if arm == "full_sleep" else 0.0)
    strategy_sources = []
    for i in range(2):
        task = _task(agent, strategy_domain, f"strategy-source-{i}",
                     [0, 1, 2], [2, 0, 1], seed)
        native_rule_steps += _settle(agent)
        strategy_sources.append(task)
    if arm == "full_sleep":
        _set_policy(agent, "SolverPolicy", 0.0)
    strategy_initial = [2, 1, 0]
    strategy_goal = _apply_sequence(
        agent, strategy_initial,
        [n for n in _nodes(agent, "ProcessSchema")
         if agent.s.node(n)["attrs"].get("domain") == strategy_domain
         and agent.s.node(n)["attrs"].get("name") == "cycle"])
    strategy_task = _task(agent, strategy_domain, "delayed-strategy-heldout",
                          strategy_initial, strategy_goal, seed)
    native_rule_steps += _settle(agent)
    if agent.s.node(strategy_task)["attrs"].get("status") != "solved":
        raise RuntimeError(f"{arm} strategy subpanel failed seed {seed}")
    if arm == "full_sleep":
        _set_policy(agent, "SolverPolicy", 1.0, max_steps=64.0)
    strategy_attempts = list(agent.inner.neighbours(delayed, "has_strategy_recall_attempt"))
    strategy_attempts += list(agent.inner.neighbours(strategy_task, "has_strategy_recall_attempt"))
    request_nodes = list(agent.inner.neighbours(strategy_task, "has_strategy_recall_request"))
    used_schema = list(agent.inner.neighbours(strategy_task, "recalls_strategy_entry"))
    budget_requests = [n for n in request_nodes
                       if agent.s.node(n)["attrs"].get("requester_kind") == "strategy_library_recall"]
    strategy_debits = sum(float(agent.s.node(n)["attrs"].get("cost", 0.0))
                          for n in budget_requests
                          if agent.s.node(n)["attrs"].get("status") == "approved")
    stage_debits = float(sleep.get("sleep_stage_debit_total", 0.0))
    cycle_debits = float(sleep.get("cycle_request_debits", 0.0))
    declared_debits = stage_debits + cycle_debits + strategy_debits
    budget_balance_delta = LIMITS["budget_capacity"] - agent.s.node(budget)["attrs"].get("remaining", 0.0)
    schema_nodes = [n for n in _nodes(agent, "ProcessSchema")
                    if agent.s.node(n)["attrs"].get("provenance") == "held"]
    common_access = _digest(sorted((agent.s.node(n)["attrs"].get("name"),
                                    agent.s.node(n)["attrs"].get("params"))
                                   for n in schema_nodes))
    forbidden_answer_keys = {"solution", "answer", "oracle_trace", "expected_trace"}
    answer_fields_absent = all(not forbidden_answer_keys.intersection(
        agent.s.node(n)["attrs"]) for n in agent.s.nodes())
    record = {
        "status": "COMPLETED" if solved else "FAILED", "family": "paired_delayed_task",
        "seed": seed, "profile": arm, "split": split,
        "outcome": "solved" if solved else delayed_attrs.get("status"),
        "accuracy": int(solved), "delayed_steps": delayed_attrs.get("steps"),
        "delayed_trace_length": len(delayed_attrs.get("trace", [])),
        "source_task_outcomes": [agent.s.node(n)["attrs"].get("status") for n in source_tasks],
        "strategy_source_task_outcomes": [agent.s.node(n)["attrs"].get("status")
                                          for n in strategy_sources],
        "strategy_recall_attempts": len(strategy_attempts),
        "strategy_recall_requests": len(request_nodes),
        "strategy_recall_request_statuses": [agent.s.node(n)["attrs"].get("status")
                                             for n in request_nodes],
        "strategy_recall_fallbacks": len(list(agent.inner.neighbours(
            strategy_task, "has_strategy_recall_fallback"))),
        "strategy_recall_fallback_reasons": [
            agent.s.node(n)["attrs"].get("reason")
            for n in agent.inner.neighbours(strategy_task, "has_strategy_recall_fallback")],
        "strategy_attempt_statuses": [agent.s.node(n)["attrs"].get("status")
                                      for n in strategy_attempts],
        "strategy_entries": len(_nodes(agent, "StrategyLibraryEntry")),
        "strategy_entries_before_library_delayed": strategy_entries_before_delayed,
        "strategy_recalled": bool(used_schema),
        "strategy_candidate_count": (agent.s.node(strategy_attempts[0])["attrs"].get("candidate_count")
                                     if strategy_attempts else 0),
        "strategy_delayed_status": agent.s.node(strategy_task)["attrs"].get("status"),
        "library_chunks": len(chunks), "library_reuse": bool(chunks and
            any(n in {p for chunk in chunks
                      for p in agent.inner.neighbours(chunk, "has_library_process")}
                for n in delayed_attrs.get("trace", []))),
        "library_source_trace_length": len(agent.s.node(source_tasks[0])["attrs"].get("trace", [])),
        "library_inline_cost": inline_cost, "library_package_cost": chunk_cost,
        "library_reuse_cost": reuse_cost,
        "library_exact_work_reduction": library_reduction,
        "sleep": sleep, "budget_debit": declared_debits,
        "budget_balance_delta": budget_balance_delta,
        "budget_stage_debits": stage_debits,
        "budget_cycle_admission_debits": cycle_debits,
        "budget_strategy_debits": strategy_debits,
        "budget_refill_per_epoch": 2.0,
        "native_rule_steps": native_rule_steps,
        "sleep_native_rule_steps": sleep.get("native_rule_steps", 0),
        "awake_rehearsal_native_rule_steps": awake_rehearsal_steps,
        "budget_remaining": agent.s.node(budget)["attrs"].get("remaining"),
        "budget_request_count": len(budget_requests) + sleep.get("cycle_request_count", 0),
        "world_access_sha256": common_access,
        "world_sha256": _digest({"seed": seed, "domain": domain,
                                 "held_processes": [(agent.s.node(n)["attrs"].get("name"),
                                                     agent.s.node(n)["attrs"].get("params"))
                                                    for n in schema_nodes],
                                 "delayed_initial": delayed_initial,
                                 "delayed_goal": delayed_goal,
                                 "strategy_initial": strategy_initial,
                                 "strategy_goal": strategy_goal,
                                 "interference_event": agent.s.node(interference)["attrs"].get("event_key")}),
        "answer_fields_absent": answer_fields_absent,
        "evidence_exposures": (LIMITS["source_tasks"] + len(strategy_sources) + 1
                               + awake_rehearsal_count),
        "awake_rehearsal_task_count": awake_rehearsal_count,
        "interference_event_id": agent.s.node(interference)["attrs"].get("event_key"),
        "world_actions": 0,
        "boot_seconds": boot_seconds,
        "graph_node_growth": len(list(agent.s.nodes())) - started_nodes,
        "graph_nodes_end": len(list(agent.s.nodes())),
        "graph_estimated_bytes_end": len(json.dumps(
            [agent.s.node(n) for n in agent.s.nodes()], sort_keys=True,
            default=str).encode()),
        "world_adapter_ticks": (LIMITS["ticks_per_epoch"] *
                                 ((6 if sleep["replay_traces"] else 0) + 1)),
        "input_audit": {"answer_fields_absent": answer_fields_absent,
                        "no_hidden_delayed_strategy": strategy_entries_before_delayed == 0,
                        "same_primitive_access_hash": common_access},
    }
    if arm == "full_sleep" and not sleep["sleep_receipts"]:
        agent.close()
        raise RuntimeError(f"full-sleep adapter produced no native sleep receipt for seed {seed}")
    if arm == "replay_only" and not sleep["replay_traces"]:
        agent.close()
        raise RuntimeError(f"P1 replay adapter produced no replay for seed {seed}")
    agent.close()
    return record


def _run_control(seed, split="development"):
    agent, boot_seconds, budget = _agent("full_sleep")
    context = agent.s.add_node("MemoryContext", {"context_key": f"p13-control:{seed}"})
    schema = agent.s.add_node("MemorySchema", {"name": f"control-route:{seed}"})
    episode = agent.s.add_node("EpisodicEvent", {
        "event_key": f"control-event:{seed}", "cue_key": f"control-cue:{seed}",
        "epoch": 0.0, "salience": 0.8, "surprise": 0.5, "value": 0.5,
        "observation_status": "observed", "provenance_kind": "perceived",
        "state_kind": "world_state", "state_summary": "observed control event",
    })
    _edge(agent, agent.agent, "experienced_event", episode)
    _edge(agent, episode, "in_context", context)
    _edge(agent, episode, "instantiates_schema", schema)
    for _ in range(LIMITS["ticks_per_epoch"]):
        agent.tick()

    def add_sample(target, epoch, demand):
        sample = target.s.add_node("NetworkModeSample", {
            "epoch": float(epoch), "default_mode_weight": 1.0,
            "exteroceptive_load": 0.0, "task_demand": float(demand),
            "interoceptive_urgency": 0.0, "uncertainty": 0.0,
            "idle_duration": 8.0, "status": "raw",
        })
        _edge(target, target.agent, "has_network_mode_sample", sample)
        for _ in range(LIMITS["ticks_per_epoch"]):
            target.tick()

    add_sample(agent, 1, 0.0)
    cycles = _nodes(agent, "MemoryCycle")
    receipts = _nodes(agent, "SleepStageReceipt")
    if len(cycles) != 1 or not receipts:
        raise RuntimeError(f"interrupt control failed to enter staged sleep for seed {seed}")
    add_sample(agent, 2, 1.0)
    before_restart_cursor = agent.s.node(cycles[0])["attrs"].get("sleep_stage_cursor")
    pending = before_restart_cursor == "consolidate"
    receipt_count = len(_nodes(agent, "SleepStageReceipt"))
    remaining_before_restart = agent.s.node(budget)["attrs"].get("remaining")
    with tempfile.TemporaryDirectory(prefix="linear-p13-control-") as tmp:
        checkpoint = Path(tmp) / "interrupt-resume.json"
        agent.save(checkpoint)
        agent.close()
        resumed = WorldAdapter.load(checkpoint)
        resumed_cycles = _nodes(resumed, "MemoryCycle")
        if len(resumed_cycles) != 1:
            resumed.close()
            raise RuntimeError("P13 restart lost or duplicated the interrupted cycle")
        cursor_persisted = (resumed.s.node(resumed_cycles[0])["attrs"].get("sleep_stage_cursor")
                            == "consolidate")
        add_sample(resumed, 3, 0.0)
        resumed_cycle = _nodes(resumed, "MemoryCycle")[0]
        stages = [resumed.s.node(n)["attrs"].get("stage")
                  for n in resumed.inner.neighbours(resumed_cycle, "has_sleep_stage_receipt")]
        resumed_budget = next(n for n in _nodes(resumed, "ThinkingBudget")
                              if resumed.s.node(n)["attrs"].get("enabled") == 1.0)
        remaining_after_resume = resumed.s.node(resumed_budget)["attrs"].get("remaining")
        resumed_receipt_count = len(_nodes(resumed, "SleepStageReceipt"))
        for _ in range(4):
            resumed.tick()
        after_repeat_count = len(_nodes(resumed, "SleepStageReceipt"))
        after_repeat_budget = resumed.s.node(resumed_budget)["attrs"].get("remaining")
        no_duplicate = (after_repeat_count == resumed_receipt_count
                        and after_repeat_budget == remaining_after_resume)
        restart_succeeded = cursor_persisted and "replay" in stages and "consolidate" in stages
        resumed.close()
    record = {"status": "COMPLETED" if pending and no_duplicate and restart_succeeded else "FAILED",
              "family": "interrupt_restart_control", "seed": seed,
              "profile": "full_sleep_interrupt", "split": split,
              "foreground_pending": pending, "same_epoch_no_duplicate_receipt": no_duplicate,
              "restart_cursor_persisted": cursor_persisted,
              "restart_resumed_next_stage": restart_succeeded,
              "receipt_count_before_restart": receipt_count,
              "stages_after_restart": stages,
              "budget_remaining_before_restart": remaining_before_restart,
              "budget_remaining_after_resume": remaining_after_resume,
              "budget_remaining_after_repeat": after_repeat_budget,
              "boot_seconds": boot_seconds,
              "world_actions": 0, "evidence_exposures": 1}
    return record


def run(*, split="development", n=1, self_check=False):
    if n < 1 or n > 200:
        raise ValueError("n must be in [1, 200]")
    if split == "heldout" and not self_check and n != ALLOCATIONS["paired_streams"]:
        raise ValueError("the frozen held-out draw requires exactly 200 paired streams")
    start_seed = DEV_SEED if split == "development" else HELDOUT_SEED
    rows = []
    for offset in range(n):
        seed = start_seed + offset
        # The four arms receive the same domain, source tasks and delayed task.
        full_row = None
        for arm in ARMS:
            row = _run_trial(
                seed, arm, split,
                awake_compute_target=(full_row["sleep_native_rule_steps"]
                                      if arm == "awake_rehearsal" and full_row else 0),
            )
            rows.append(row)
            if arm == "full_sleep":
                full_row = row
    control_n = 1 if self_check or split == "development" else ALLOCATIONS["interrupt_restart_controls"]
    for offset in range(control_n):
        rows.append(_run_control(start_seed + 50_000 + offset, split))
    metadata = {"phase": PHASE, "split": split,
                "seed_allocation": {"paired_streams_per_arm": n,
                                    "interrupt_restart_controls": control_n},
                "arms": list(ARMS), "limits": dict(LIMITS),
                "artifact_provenance": provenance(),
                "limitations": {"memory_accuracy": "measured only through native delayed SolveTask outcomes; no unobserved retrieval answer is inserted",
                                "library_reuse": "requires a native cost-positive repeated trace; short one-step source traces remain ineligible",
                                "world_actions": "zero external actions; this panel scores native simulated task outcomes"},
                "self_check": bool(self_check)}
    return {"schema": "pmb-scorecard-v1", "metadata": metadata, "records": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    payload = run(split="development" if args.self_check else args.split,
                  n=1 if args.self_check else args.n, self_check=args.self_check)
    if args.output:
        write_scorecard(args.output, metadata=payload["metadata"], records=payload["records"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
