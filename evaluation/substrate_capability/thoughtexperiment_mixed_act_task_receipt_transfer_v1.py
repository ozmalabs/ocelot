#!/usr/bin/env python3
"""Replay the existing mixed-act discourse task through isolated receipt arms."""
from __future__ import annotations

import hashlib, json, os, platform, random, subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_MIXED_ACT_TASK_RECEIPT_TRANSFER_V1_PREREG_20261001.md"
FIXTURE = ROOT / "tests/fixtures/conversational_manifold/phase3_mixed_act_dialogue.json"
SEED = ROOT / "seeds/conversation_discourse_state.json"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_mixed_act_task_receipt_transfer_v1_lock_20261001.json"
RAW = ROOT / "evaluation/reports/thoughtexperiment_mixed_act_task_receipt_transfer_v1_raw_20261001.json"
ANALYZER = ROOT / "scripts/analyze_thoughtexperiment_mixed_act_task_receipt_transfer_v1.py"
ARMS = ("direct", "eager_receipt", "shared_snapshot_receipt")
WORKERS = 8
CAP = 100_000
SOURCES = (
    "docs/research/engine_substrate/THOUGHTEXPERIMENT_MIXED_ACT_TASK_RECEIPT_TRANSFER_V1_PREREG_20261001.md",
    "evaluation/substrate_capability/thoughtexperiment_mixed_act_task_receipt_transfer_v1.py",
    "scripts/analyze_thoughtexperiment_mixed_act_task_receipt_transfer_v1.py",
    "tests/fixtures/conversational_manifold/phase3_mixed_act_dialogue.json",
    "seeds/conversation_discourse_state.json",
    "domains/discourse_state.py", "domains/conversation_action.py",
    "domains/engine_provenance.py", "substrate/boot_core.py", "substrate/world_adapter.py",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/graph.rs", "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/persist.rs", "runners/dsl/src/py.rs", "runners/dsl/src/scale_audit.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json", "runners/dsl/Cargo.lock",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    from domains.engine_provenance import build_is_stale
    from substrate_rs import _native
    return {"files": {p: sha(ROOT / p) for p in SOURCES},
            "native_path": str(Path(_native.__file__).resolve()),
            "native_sha256": sha(Path(_native.__file__).resolve()),
            "build_stale": build_is_stale(str(ROOT)),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                               text=True).strip()}


def nid(x) -> int:
    return int(x.value if hasattr(x, "value") else x)


def canonical(graph: dict) -> dict:
    nodes = sorted(graph["nodes"], key=lambda n: int(n["id"]))
    edges = sorted(graph["edges"], key=lambda e:
                   (int(e["src"]), str(e["type"]), int(e["tgt"]),
                    json.dumps(e.get("attrs", {}), sort_keys=True, separators=(",", ":"))))
    return {"nodes": nodes, "edges": edges}


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    default=str).encode()).hexdigest()


def effect_counts(delta: dict) -> dict:
    return {key: len(delta.get(key, [])) for key in
            ("nodes_added", "nodes_changed", "nodes_removed", "edges_added",
             "edges_changed", "edges_removed")}


def branch_for(adapter, arm: str):
    if arm == "eager_receipt":
        return adapter.s.fork_full_copy_experiment()
    return adapter.s.snapshot().fork()


def receipt_closure(adapter, arm: str, *, producer=None) -> dict:
    """Run either a task-owned producer (whose helper closes internally) or settle."""
    revision = adapter.s.experiment_graph_rule_revision()
    t = time.perf_counter_ns()
    branch = branch_for(adapter, arm)
    fork_ns = time.perf_counter_ns() - t
    branch.begin_experiment_delta_journal()
    branch.checkpoint_experiment_delta_journal()
    branch_agent = SimpleNamespace(s=branch, inner=branch._inner, agent=adapter.agent)
    t = time.perf_counter_ns()
    if producer is None:
        report = branch._inner.run_rules_report(CAP, False)
        progress = int(report["progress_steps"])
    else:
        event = producer(branch_agent)
        progress = None
    closure_ns = time.perf_counter_ns() - t
    t = time.perf_counter_ns()
    delta = branch.finish_experiment_delta_journal()["conclusions"]
    readout_ns = time.perf_counter_ns() - t
    branch_graph = branch._inner.graph_to_dict()
    t = time.perf_counter_ns()
    adapter.s.apply_experiment_graph_delta(revision, delta)
    adoption_ns = time.perf_counter_ns() - t
    primary_graph = adapter.inner.graph_to_dict()
    return {"branch": branch, "event": event if producer is not None else None,
            "progress_steps": progress, "delta": delta,
            "effect_counts": effect_counts(delta), "branch_matches_primary":
                canonical(branch_graph) == canonical(primary_graph),
            "fork_ns": fork_ns, "closure_ns": closure_ns,
            "readout_ns": readout_ns, "adoption_ns": adoption_ns}


def episode(rep: int, arm: str) -> dict:
    started = time.perf_counter_ns()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_core import load_seeds_into
    from domains.discourse_state import (close_expectation, ensure_common_ground,
                                         ensure_discourse_state, open_goal, record_event)
    from domains.conversation_action import _record_live_goal_event
    fixture_start = time.perf_counter_ns()
    fixture = json.loads(FIXTURE.read_text())
    fixture_ns = time.perf_counter_ns() - fixture_start
    adapter_start = time.perf_counter_ns()
    agent = WorldAdapter(seeds=())
    loaded = load_seeds_into(agent.s, agent.agent, ["conversation_discourse_state"])
    people = agent.attach_chat_world("user")
    user = people["interlocutor"]
    state = ensure_discourse_state(agent, conversation_id="mixed_act_receipt_transfer", addressee=user)
    ensure_common_ground(agent, state, addressee=user)
    adapter_setup_ns = time.perf_counter_ns() - adapter_start

    event_ids: list[int] = []
    goals: list = []
    goals_by_frame: dict[int, object] = {}
    inbound_by_goal: dict[int, object] = {}
    event_frame: dict[int, int] = {}
    active_frame = -1
    frame_count = 0
    event_index_by_id: dict[int, int] = {}
    states: list[dict] = []
    receipts: list[dict] = []
    timings = {key: 0 for key in ("fixture_load_ns", "adapter_seed_setup_ns",
                                 "event_construction_ns", "branch_setup_ns",
                                 "rule_closure_ns", "journal_readout_ns",
                                 "receipt_adoption_ns", "terminal_probe_ns")}
    timings["fixture_load_ns"] = fixture_ns
    timings["adapter_seed_setup_ns"] = adapter_setup_ns

    for row in fixture["events"]:
        index, kind, relation = int(row["index"]), row["kind"], row["relation"]
        if relation in {"origin", "unsolicited"}:
            active_frame = frame_count
            frame_count += 1
        if active_frame < 0:
            raise RuntimeError("first event did not start a task frame")
        topic = "calendar" if index < 5 else "location"
        producer_result = None
        construction_start = time.perf_counter_ns()

        if kind in {"request", "question"}:
            expectation = row.get("expectation") or ("action" if kind == "request" else "answer")
            payload = {"common_ground_delta": "calendar_request"} if index == 0 else None
            event = record_event(agent, state, kind=kind, speaker=user, addressee=agent.agent,
                                 topic=topic, expectation=expectation, payload=payload)
            goal = open_goal(agent, state, kind="act_or_clarify", origin_event=event, addressee=user)
            goals.append(goal)
            goals_by_frame[active_frame] = goal
            inbound = agent.s.add_node("Message", {})
            agent.inner.set_attr(inbound, "discourse_state_id", state)
            agent.inner.set_attr(inbound, "discourse_event_id", event)
            agent.inner.add_edge_unchecked(inbound, "sent_by", user)
            inbound_by_goal[nid(goal)] = inbound
        elif kind == "assertion":
            event = record_event(agent, state, kind=kind, speaker=user, addressee=agent.agent,
                                 topic=topic, payload={"common_ground_delta": "calendar_shared"})
        elif kind == "epistemic_limit":
            event = record_event(agent, state, kind=kind, speaker=agent.agent, addressee=user,
                                 topic=topic)
            close_expectation(agent, state, event=event, disposition="deferred",
                              residual="location_unresolved")
        elif kind in {"selection", "execution", "action_result"}:
            event = None
            goal = goals_by_frame[active_frame]
            payload = ({"fixture_census": "connected_task", "fixture_index": index,
                        **({"common_ground_delta": "calendar_checked" if index == 3 else "location_shared"}
                           if kind == "action_result" else {})})

            def produce(target_agent):
                return _record_live_goal_event(target_agent, inbound_by_goal[nid(goal)], goal,
                                               kind, payload=payload)
            if arm == "direct":
                event = produce(agent)
            else:
                producer_result = receipt_closure(agent, arm, producer=produce)
                timings["branch_setup_ns"] += producer_result["fork_ns"]
                timings["rule_closure_ns"] += producer_result["closure_ns"]
                timings["journal_readout_ns"] += producer_result["readout_ns"]
                timings["receipt_adoption_ns"] += producer_result["adoption_ns"]
                if not producer_result["branch_matches_primary"]:
                    raise RuntimeError(f"producer receipt adoption mismatch at event {index}")
                event = producer_result["event"]
                receipts.append({"event_index": index, "phase": "production_helper",
                                 "effect_counts": producer_result["effect_counts"],
                                 "adopted_branch_match": True})
        else:
            raise RuntimeError(f"unsupported fixture event kind: {kind}")

        if event is not None:
            event_id = nid(event)
            event_frame[event_id] = active_frame
            if kind in {"request", "question"}:
                event_frame[nid(goals_by_frame[active_frame])] = active_frame
        if kind not in {"selection", "execution", "action_result"} or arm == "direct":
            timings["event_construction_ns"] += time.perf_counter_ns() - construction_start
        event_id = nid(event)
        event_ids.append(event_id)
        event_index_by_id[event_id] = index

        if arm == "direct":
            t = time.perf_counter_ns()
            settle = agent.inner.run_rules_report(CAP, False)
            settle_progress = int(settle["progress_steps"])
            timings["rule_closure_ns"] += time.perf_counter_ns() - t
        else:
            settle_result = receipt_closure(agent, arm)
            timings["branch_setup_ns"] += settle_result["fork_ns"]
            timings["rule_closure_ns"] += settle_result["closure_ns"]
            timings["journal_readout_ns"] += settle_result["readout_ns"]
            timings["receipt_adoption_ns"] += settle_result["adoption_ns"]
            settle_progress = settle_result["progress_steps"]
            if not settle_result["branch_matches_primary"]:
                raise RuntimeError(f"settle receipt adoption mismatch at event {index}")
            receipts.append({"event_index": index, "phase": "ordinary_settlement",
                             "progress_steps": settle_progress,
                             "effect_counts": settle_result["effect_counts"],
                             "adopted_branch_match": True})

        oracle_start = time.perf_counter_ns()
        graph = agent.inner.graph_to_dict()
        goals_at_event = []
        for goal in goals:
            transition_ids = [nid(e) for e in agent.inner.neighbours(goal, "transitioned_by")]
            goals_at_event.append({"node": nid(goal),
                                   "status": agent.s.node(goal)["attrs"].get("lifecycle_status"),
                                   "transition_event_indices": sorted(event_index_by_id[x]
                                       for x in transition_ids if x in event_index_by_id)})
        states.append({"event_index": index, "event_id": event_id,
                       "settlement_progress_steps": settle_progress,
                       "canonical_graph_sha256": digest(canonical(graph)),
                       "wire_graph_sha256": digest(graph), "goals": goals_at_event})
        _oracle_elapsed_ns = time.perf_counter_ns() - oracle_start

    if len(event_ids) != 10 or frame_count != 3 or len(goals) != 2:
        raise RuntimeError("fixture task event/frame/goal count mismatch")
    preterminal = agent.inner.graph_to_dict()
    terminal_counts = None
    t = time.perf_counter_ns()
    if arm == "direct":
        terminal = agent.inner.run_rules_report(CAP, False)
        terminal_progress = int(terminal["progress_steps"])
    else:
        terminal_result = receipt_closure(agent, arm)
        terminal_progress = terminal_result["progress_steps"]
        terminal_counts = terminal_result["effect_counts"]
    timings["terminal_probe_ns"] = time.perf_counter_ns() - t
    final_graph = agent.inner.graph_to_dict()
    final_state = agent.s.node(state)["attrs"]
    goal_results = []
    for goal in goals:
        indices = sorted(event_index_by_id[nid(e)] for e in agent.inner.neighbours(goal, "transitioned_by")
                         if nid(e) in event_index_by_id)
        goal_results.append({"node": nid(goal), "status": agent.s.node(goal)["attrs"].get("lifecycle_status"),
                             "transition_event_indices": indices})
    grounds = sorted(sorted(agent.s.node(node)["attrs"].get("claims", []))
                      for node in agent.s.nodes("CommonGround"))
    measured_route_ns = sum(timings.values())
    return {"replicate": rep, "pid": os.getpid(), "arm": arm,
            "loaded_seed_ids": sorted(str(x) for x in loaded),
            "active_lifecycle_rules": sorted(str(r[1]) for r in agent.inner.rule_access_sets()
                                             if bool(r[2]) and str(r[1]) in {"discourse_goal_select",
                                                "discourse_goal_execute", "discourse_goal_resolve"}),
            "event_ids": event_ids, "goal_ids": [nid(g) for g in goals],
            "per_event_states": states, "receipts": receipts,
            "goals": goal_results, "common_grounds": grounds,
            "final_state_attrs": final_state,
            "final_canonical_graph_sha256": digest(canonical(final_graph)),
            "final_wire_graph_sha256": digest(final_graph),
            "terminal_progress_steps": terminal_progress,
            "terminal_graph_unchanged": digest(canonical(preterminal)) == digest(canonical(final_graph)),
            "terminal_receipt_counts": terminal_counts,
            "final_node_count": len(final_graph["nodes"]), "final_edge_count": len(final_graph["edges"]),
            "timing_stages_ns": timings, "measured_route_wall_ns": measured_route_ns,
            "full_episode_wall_ns": time.perf_counter_ns() - started}


def worker(rep: int) -> dict:
    before = fingerprint()
    import_start = time.perf_counter_ns()
    from substrate.world_adapter import WorldAdapter  # warm imports before arm timing
    from substrate.boot_core import load_seeds_into
    from domains.discourse_state import close_expectation, ensure_common_ground, ensure_discourse_state, open_goal, record_event
    from domains.conversation_action import _record_live_goal_event
    import_ns = time.perf_counter_ns() - import_start
    order = list(ARMS)
    random.Random(20261002 + rep).shuffle(order)
    episodes = [episode(rep, arm) for arm in order]
    after = fingerprint()
    return {"replicate": rep, "pid": os.getpid(), "before": before, "after": after,
            "worker_import_warm": True, "worker_module_import_ns": import_ns,
            "arm_order": order, "episodes": episodes}


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True))
        return 0
    if sys.argv[1:] == ["--lock"]:
        current = fingerprint()
        if current["build_stale"]:
            raise SystemExit("native engine build is stale")
        LOCK.write_text(json.dumps({"locked_inputs": current}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT)); return 0
    frozen = fingerprint()
    if frozen["build_stale"] or not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != frozen:
        raise SystemExit("missing/stale lock or native build; run --lock after preregistration")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), env.get("PYTHONPATH", "")))
    env["PYTHONHASHSEED"] = "0"; env["OZMA_NO_LLM"] = "1"; env["OZMA_SEED_PERSIST_DISABLED"] = "1"
    reps = list(range(WORKERS)); random.Random(20261002).shuffle(reps)
    runs = []
    for serial, rep in enumerate(reps, 1):
        done = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True)
        runs.append(json.loads(done.stdout) if done.returncode == 0 else
                    {"replicate": rep, "worker_error": done.stderr[-5000:], "returncode": done.returncode})
        RAW.with_suffix(".partial.json").write_text(json.dumps({"schema": "MixedActTaskReceiptTransferV1Partial",
            "locked_inputs": frozen, "runs": runs}, indent=2, sort_keys=True) + "\n")
        print(f"worker {serial}/{WORKERS} replicate={rep} rc={done.returncode}", flush=True)
    post = fingerprint()
    capture = {"schema": "MixedActTaskReceiptTransferV1Capture", "host": {"platform": platform.platform(),
        "machine": platform.machine(), "logical_cpu_count": os.cpu_count()}, "locked_inputs": frozen,
        "post_run_inputs": post, "worker_count": WORKERS, "arms": list(ARMS), "runs": runs}
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    if RAW.with_suffix(".partial.json").exists(): RAW.with_suffix(".partial.json").unlink()
    subprocess.run([sys.executable, str(ANALYZER)], cwd=ROOT, env=env, check=True)
    print(json.dumps({"workers": len(runs), "source_stable": post == frozen,
                      "raw": str(RAW.relative_to(ROOT))}, sort_keys=True))
    return int(len(runs) != WORKERS or post != frozen or any("worker_error" in r for r in runs))


if __name__ == "__main__":
    raise SystemExit(main())
