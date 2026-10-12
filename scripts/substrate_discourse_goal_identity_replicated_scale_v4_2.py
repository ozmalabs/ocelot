#!/usr/bin/env python3
"""Scaled same-recipient goal identity and scoped owner-queue diagnostic."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import resource
import statistics
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_DISCOURSE_GOAL_IDENTITY_REPLICATED_SCALE_V4_2_PREREG_20260926.md"
FIXTURE = ROOT / "tests/fixtures/conversational_manifold/phase3_same_addressee_concurrent_goals_scale_v4_1.json"
SEED = ROOT / "seeds/conversation_discourse_state.json"
MATERIALIZER = ROOT / "domains/discourse_state.py"
LOCK = ROOT / "evaluation/substrate_capability/discourse_goal_identity_replicated_scale_v4_2_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_discourse_goal_identity_replicated_scale_v4_2_20260926.json"
SIZES = (2, 4, 8)
ARMS = ("temporal_full", "recipient_guard_full", "explicit_full",
        "explicit_owner_queue", "explicit_omit_wakeup")
CAP = 100_000
MAX_TURNS = 2_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nid(x) -> int:
    return int(x.value if hasattr(x, "value") else x)


def digest(graph: dict) -> str:
    return hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":"),
                                  default=str).encode()).hexdigest()


def current_rss_kib() -> int | None:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def lock_inputs() -> dict:
    from substrate_rs import _native
    native = Path(_native.__file__).resolve()
    return {
        "protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__)),
        "fixture_sha256": sha(FIXTURE), "seed_sha256": sha(SEED),
        "materializer_sha256": sha(MATERIALIZER),
        "native_extension_sha256": sha(native),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "cargo_lock_sha256": sha(ROOT / "runners/dsl/Cargo.lock"),
        "rust_sources_sha256": {name: sha(ROOT / "runners/dsl/src" / name)
                                for name in ("graph.rs", "rewrite.rs", "substrate.rs",
                                             "term.rs", "access_trace.rs", "py.rs")},
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           text=True).strip(),
        "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"],
                                                        cwd=ROOT, text=True).strip()),
    }


def install_lifecycle_variant(inner, variant: str) -> list[int]:
    names = {"discourse_goal_select", "discourse_goal_execute", "discourse_goal_resolve"}
    original = inner.export_rules()
    targets = [(i, rule) for i, rule in enumerate(original)
               if rule.get("name") in names and rule.get("active", True)]
    if variant == "temporal":
        return []
    if len(targets) != 3:
        raise RuntimeError(f"expected three lifecycle rules, found {len(targets)}")
    for index, _ in targets:
        if not inner.remove_rule(index):
            raise RuntimeError(f"failed to tombstone lifecycle rule {index}")
    added = []
    for _, prior in targets:
        rule = {k: v for k, v in prior.items()
                if k not in {"active", "batch", "content_hash", "mutation_protected",
                             "revision", "rule_uid"}}
        rule["name"] = f"{rule['name']}_{variant}_guard_probe"
        if variant == "recipient":
            rule["match"] = list(rule["match"]) + [
                ["goal", "for_addressee", "recipient"],
                ["event", "to_addressee", "recipient"],
            ]
        elif variant == "explicit":
            rule["match"] = list(rule["match"]) + [["event", "for_goal", "goal"]]
        else:
            raise ValueError(f"unknown lifecycle variant {variant}")
        added.append(int(inner.add_rule(rule)))
    return added


def add_receipt_rule(inner) -> int:
    return int(inner.add_rule({
        "name": "frame_consume_resolved_goal_receipt",
        "match_type": "Goal", "match": [["goal", "originated_in", "origin"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "goal"},
                                      "key": "lifecycle_status"},
             "b": {"type": "Lit", "value": "resolved"}},
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "origin"},
                                      "key": "resolution_receipt"},
             "b": {"type": "Lit", "value": 0.0}},
        ]},
        "effects": [["set_attr", "origin", "resolution_receipt", 1.0]],
    }))


def call_full(inner) -> dict:
    inner.scale_audit_reset(); inner.scale_audit_set_enabled(True)
    wall, cpu = time.perf_counter_ns(), time.process_time_ns()
    report = dict(inner.run_rules_report(CAP, False))
    elapsed_wall, elapsed_cpu = time.perf_counter_ns() - wall, time.process_time_ns() - cpu
    counts = {str(k): int(v) for k, v in dict(inner.scale_audit_snapshot()).items()}
    inner.scale_audit_set_enabled(False)
    return {"report": report, "wall_ns": elapsed_wall, "cpu_ns": elapsed_cpu,
            "counters": counts, "calls": 1}


def call_scoped(inner, initial_frame: int, frame_to_id: dict, ids_to_mt: dict,
                *, follow_notifications: bool) -> dict:
    queue = deque([initial_frame]); queued = {initial_frame}
    steps = turns = 0; notifications = []; reports = []; counters = {}
    wall, cpu = time.perf_counter_ns(), time.process_time_ns()
    while queue and turns < MAX_TURNS and steps < CAP:
        frame = queue.popleft(); queued.remove(frame)
        inner.scale_audit_reset(); inner.scale_audit_set_enabled(True)
        report = dict(inner.run_rules_scoped_delta_report(ids_to_mt[frame], CAP - steps, False))
        counts = {str(k): int(v) for k, v in dict(inner.scale_audit_snapshot()).items()}
        inner.scale_audit_set_enabled(False)
        for key, value in counts.items(): counters[key] = counters.get(key, 0) + value
        turns += 1; steps += int(report.get("progress_steps", 0))
        if report.get("hit_progress_budget") or report.get("deferred_effects_pending"):
            reports.append(report)
            return {"complete": False, "turns": turns, "progress_steps": steps,
                    "wall_ns": time.perf_counter_ns() - wall, "cpu_ns": time.process_time_ns() - cpu,
                    "counters": counters, "notifications": notifications, "reports": reports,
                    "failure": "budget_or_deferred"}
        mapped = []
        if follow_notifications:
            for owner in report.get("affected_microtheories", []):
                owner_id = nid(owner)
                if owner_id not in frame_to_id:
                    return {"complete": False, "turns": turns, "progress_steps": steps,
                            "wall_ns": time.perf_counter_ns() - wall,
                            "cpu_ns": time.process_time_ns() - cpu, "counters": counters,
                            "notifications": notifications, "reports": reports + [report],
                            "failure": f"unmapped owner id {owner_id}"}
                target = frame_to_id[owner_id]
                if target != frame:
                    mapped.append(target)
                    if target not in queued:
                        queue.append(target); queued.add(target)
        notifications.append({"source_frame": frame, "native_owners": sorted(set(mapped)),
                              "affected_microtheories": [nid(x) for x in
                                                          report.get("affected_microtheories", [])],
                              "affected_nodes": [nid(x) for x in report.get("affected_nodes", [])]})
        reports.append(report)
    return {"complete": not queue and turns < MAX_TURNS and steps < CAP,
            "turns": turns, "progress_steps": steps,
            "wall_ns": time.perf_counter_ns() - wall, "cpu_ns": time.process_time_ns() - cpu,
            "counters": counters, "notifications": notifications, "reports": reports,
            "failure": None if not queue else "turn_or_progress_cap"}


def run_arm(arm: str, size: int, replicate: int, config: dict) -> dict:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_core import load_seeds_into
    from domains.discourse_state import ensure_common_ground, ensure_discourse_state, open_goal, record_event

    rss_after_import_kib = current_rss_kib()

    variant = "temporal" if arm == "temporal_full" else (
        "recipient" if arm == "recipient_guard_full" else "explicit")
    agent = WorldAdapter(seeds=())
    load_seeds_into(agent.s, agent.agent, ["conversation_discourse_state"])
    patched_rules = install_lifecycle_variant(agent.inner, variant)
    sentinel = add_receipt_rule(agent.inner)
    user = agent.attach_chat_world("shared_user")["interlocutor"]
    state = ensure_discourse_state(agent, conversation_id=f"identity_scale_{size}", addressee=user)
    ensure_common_ground(agent, state, addressee=user)
    frame_count = 2 * size
    setup_start = time.perf_counter_ns()
    frames = [agent.s.add_node("Microtheory", {
        "name": f"goal_identity_frame_{i}", "frame_kind": "origin" if i < size else "operation"})
        for i in range(frame_count)]
    frame_setup_ns = time.perf_counter_ns() - setup_start
    rss_before_events_kib = current_rss_kib()
    ids_to_mt = {i: frames[i] for i in range(frame_count)}
    frame_to_id = {nid(mt): i for i, mt in ids_to_mt.items()}
    goals = {}; origin_events = {}; checkpoints = []

    def settle(event_index: int, current_frame: int, event_node) -> None:
        if arm in {"temporal_full", "recipient_guard_full", "explicit_full"}:
            result = call_full(agent.inner)
            complete = result["report"].get("status") == "fixed_point"
        else:
            result = call_scoped(agent.inner, current_frame, frame_to_id, ids_to_mt,
                                 follow_notifications=(arm == "explicit_owner_queue"))
            complete = result["complete"]
        graph = agent.inner.graph_to_dict()
        checkpoints.append({"event_index": event_index, "event_id": nid(event_node),
                            "event_frame": current_frame, "complete": complete,
                            "settlement": result, "graph_digest": digest(graph),
                            "goal_states": {str(i): agent.s.node(g)["attrs"].get("lifecycle_status")
                                            for i, g in goals.items()},
                            "origin_receipts": {str(i): float(agent.s.node(origin_events[i])["attrs"].get(
                                "resolution_receipt", 0.0)) for i in origin_events}})

    event_index = 0
    for i in range(size):
        event = record_event(agent, state, kind="request", speaker=user, addressee=agent.agent,
                             expectation="action", interaction_mode="asynchronous",
                             payload={"common_ground_delta": f"request_{i}"})
        agent.inner.set_attr(event, "resolution_receipt", 0.0)
        goal = open_goal(agent, state, kind=f"task_{i}", origin_event=event, addressee=user)
        agent.inner.add_edge_unchecked(frames[i], "has_concept", event)
        agent.inner.add_edge_unchecked(frames[i], "has_concept", goal)
        goals[i] = goal; origin_events[i] = event
        settle(event_index, i, event); event_index += 1

    fixture_edges = 0
    for i in range(size):
        for kind in ("selection", "execution", "action_result"):
            payload = {"common_ground_delta": f"result_{i}"} if kind == "action_result" else None
            event = record_event(agent, state, kind=kind, speaker=agent.agent, addressee=user,
                                 interaction_mode="native", payload=payload)
            # This task identity edge is the independently declared input relation, present in all arms.
            agent.inner.add_edge_unchecked(event, "for_goal", goals[i]); fixture_edges += 1
            operation_frame = size + i
            agent.inner.add_edge_unchecked(frames[operation_frame], "has_concept", event)
            settle(event_index, operation_frame, event); event_index += 1

    final_graph = agent.inner.graph_to_dict()
    recovery = None
    if arm == "explicit_omit_wakeup":
        recovery = call_full(agent.inner)
        final_graph = agent.inner.graph_to_dict()
    goal_rows = {}
    for i, goal in goals.items():
        transitions = sorted(int(agent.s.node(e)["attrs"]["event_index"])
                             for e in agent.inner.neighbours(goal, "transitioned_by"))
        goal_rows[str(i)] = {"origin_frame": i, "lifecycle_status": agent.s.node(goal)["attrs"].get(
            "lifecycle_status"), "transition_event_indices": transitions}
    grounds = [agent.s.node(n)["attrs"] for n in agent.s.nodes("CommonGround")]
    return {"arm": arm, "size": size, "replicate": replicate, "pid": os.getpid(),
            "frame_count": frame_count, "frame_setup_ns": frame_setup_ns,
            "rss_after_import_kib": rss_after_import_kib,
            "rss_before_events_kib": rss_before_events_kib,
            "rss_after_settlement_kib": current_rss_kib(),
            "task_link_edges": fixture_edges, "patched_rule_indices": patched_rules,
            "sentinel_rule_index": sentinel, "checkpoints": checkpoints,
            "final_graph_digest": digest(final_graph),
            "final_goals": goal_rows,
            "final_origin_receipts": {str(i): float(agent.s.node(event)["attrs"].get(
                "resolution_receipt", 0.0)) for i, event in origin_events.items()},
            "final_common_grounds": grounds, "recovery": recovery,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--lock":
        print(json.dumps({"locked_inputs": lock_inputs()}, indent=2, sort_keys=True)); return
    locked = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale lock")
    config = json.loads(FIXTURE.read_text())
    if len(sys.argv) == 4 and sys.argv[1].startswith("--worker="):
        arm = sys.argv[1].split("=", 1)[1]
        print(json.dumps(run_arm(arm, int(sys.argv[2]), int(sys.argv[3]), config),
                         sort_keys=True, default=str)); return
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    jobs = [(int(size), rep, arm) for size in config["goal_counts"]
            for rep in range(3) for arm in ARMS]
    random.Random(20260926).shuffle(jobs)
    runs = []
    for size, rep, arm in jobs:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                               f"--worker={arm}", str(size), str(rep)], cwd=ROOT, env=env,
                              text=True, capture_output=True, check=True)
        runs.append(json.loads(proc.stdout))
    by_key = {(r["size"], r["replicate"], r["arm"]): r for r in runs}
    gates = {}
    summary = {}
    for size in map(int, config["goal_counts"]):
        replicate_gates = {}
        for rep in range(3):
            temporal = by_key[(size, rep, "temporal_full")]
            recipient = by_key[(size, rep, "recipient_guard_full")]
            explicit = by_key[(size, rep, "explicit_full")]
            owner = by_key[(size, rep, "explicit_owner_queue")]
            omitted = by_key[(size, rep, "explicit_omit_wakeup")]
            expected = {str(i): [size + 3 * i + j for j in range(3)] for i in range(size)}
            get_paths = lambda run: {i: goal["transition_event_indices"]
                                     for i, goal in run["final_goals"].items()}
            expected_owner = []
            for cp in owner["checkpoints"]:
                for call in cp["settlement"].get("notifications", []):
                    expected_owner.extend((cp["event_index"], int(target))
                        for target in call["native_owners"] if int(target) != int(call["source_frame"]))
            omitted_diffs = [i for i, (a, b) in enumerate(zip(explicit["checkpoints"],
                                                               omitted["checkpoints"]))
                             if a["graph_digest"] != b["graph_digest"]]
            owner_parity = [a["graph_digest"] == b["graph_digest"]
                            for a, b in zip(explicit["checkpoints"], owner["checkpoints"])]
            replicate_gates[str(rep)] = {
                "global_arms_fixed_point": all(cp["complete"] for run in (temporal, recipient, explicit)
                                                for cp in run["checkpoints"]),
                "explicit_task_oracle": get_paths(explicit) == expected and get_paths(owner) == expected,
                "temporal_and_recipient_controls_fail_task_oracle": get_paths(temporal) != expected
                    and get_paths(recipient) != expected,
                "owner_queue_exact_parity_each_checkpoint": all(owner_parity),
                "notification_reaches_each_origin_at_result": all(
                    (size + 3 * i + 2, i) in expected_owner for i in range(size)),
                "omitted_receipt_stale_each_result": all(
                    omitted["checkpoints"][size + 3 * i + 2]["origin_receipts"].get(str(i)) == 0.0
                    for i in range(size)),
                "omitted_wakeup_produces_divergence": bool(omitted_diffs),
                "global_recovery_restores_exact_graph": omitted["final_graph_digest"]
                    == explicit["final_graph_digest"],
                "owner_receipts_resolved": owner["final_origin_receipts"]
                    == {str(i): 1.0 for i in range(size)},
                "scoped_reports_complete": all(cp["complete"] for run in (owner, omitted)
                                                for cp in run["checkpoints"]),
                "rss_samples_present": all(run["rss_before_events_kib"] is not None
                    and run["rss_after_settlement_kib"] is not None
                    for run in (temporal, recipient, explicit, owner, omitted)),
            }
        gates[str(size)] = replicate_gates
        arms_summary = {}
        for arm in ARMS:
            rows = []
            for rep in range(3):
                run = by_key[(size, rep, arm)]
                counts = {}
                for cp in run["checkpoints"]:
                    for key, value in cp["settlement"].get("counters", {}).items():
                        counts[key] = counts.get(key, 0) + int(value)
                wall = sum(int(cp["settlement"].get("wall_ns", 0)) for cp in run["checkpoints"])
                cpu = sum(int(cp["settlement"].get("cpu_ns", 0)) for cp in run["checkpoints"])
                rss_delta = (run["rss_after_settlement_kib"] - run["rss_before_events_kib"]
                             if run["rss_after_settlement_kib"] is not None
                             and run["rss_before_events_kib"] is not None else None)
                rows.append({"replicate": rep, "candidate_pairs": counts.get("cand_tested", 0),
                    "term_evaluations": counts.get("term_evals_total", 0), "wall_ns": wall,
                    "cpu_ns": cpu, "queue_turns": sum(cp["settlement"].get("turns", 0)
                        for cp in run["checkpoints"]), "frame_setup_ns": run["frame_setup_ns"],
                    "peak_rss_kib": run["peak_rss_kib"],
                    "rss_after_import_kib": run["rss_after_import_kib"],
                    "rss_before_events_kib": run["rss_before_events_kib"],
                    "rss_after_settlement_kib": run["rss_after_settlement_kib"],
                    "rss_delta_events_to_settlement_kib": rss_delta})
            arms_summary[arm] = {"per_replicate": rows}
            for metric in ("candidate_pairs", "term_evaluations", "wall_ns", "cpu_ns", "queue_turns",
                           "frame_setup_ns", "peak_rss_kib", "rss_delta_events_to_settlement_kib"):
                values = [row[metric] for row in rows if row[metric] is not None]
                if values:
                    arms_summary[arm][metric + "_median"] = statistics.median(values)
                    arms_summary[arm][metric + "_range"] = [min(values), max(values)]
        full = arms_summary["explicit_full"]["per_replicate"]
        queue = arms_summary["explicit_owner_queue"]["per_replicate"]
        ratios = {"candidate_pairs": [q["candidate_pairs"] / max(1, f["candidate_pairs"])
                                      for f, q in zip(full, queue)],
                  "term_evaluations": [q["term_evaluations"] / max(1, f["term_evaluations"])
                                       for f, q in zip(full, queue)],
                  "wall": [q["wall_ns"] / max(1, f["wall_ns"]) for f, q in zip(full, queue)]}
        summary[str(size)] = {"replicates": 3, "event_count": 4 * size, "frame_count": 2 * size,
            "checkpoint_parity_count": 12 * size, "arms": arms_summary,
            "owner_over_full_ratios_by_replicate": ratios,
            "owner_over_full_ratio_medians": {k: statistics.median(v) for k, v in ratios.items()}}
    checks = {
        "forty_five_workers_and_unique_pids": len(runs) == 45 and len({r["pid"] for r in runs}) == 45,
        "all_replicate_gates_pass": all(all(all(v.values()) for v in rep_gates.values())
                                         for rep_gates in gates.values()),
        "rss_samples_present_in_all_workers": all(r["rss_after_import_kib"] is not None
            and r["rss_before_events_kib"] is not None and r["rss_after_settlement_kib"] is not None
            for r in runs),
    }
    payload = {"schema_version": 1,
        "run_id": "substrate-discourse-goal-identity-replicated-scale-v4.2-20260926",
        "claim_boundary": "Three-replicate N=16/32/64 extension of one generated same-addressee goal-identity family. Explicit for_goal links preserve task and owner-queue parity. RSS is process resident delta, not allocator-level attribution; no natural-workload or formal complexity claim.",
        "locked_inputs": locked, "lock_sha256": sha(LOCK),
        "environment": {"python": sys.version, "platform": platform.platform(),
            "OZMA_NO_LLM": env["OZMA_NO_LLM"],
            "OZMA_SEED_PERSIST_DISABLED": env["OZMA_SEED_PERSIST_DISABLED"]},
        "schedule": [list(job) for job in jobs], "checks": checks,
        "replicate_gates": gates, "summary": summary, "runs": runs}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks,
                      "replicate_gates": gates, "summary": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("replicated identity scale probe failed a gate; raw report preserved")


if __name__ == "__main__":
    main()
