#!/usr/bin/env python3
"""Source-locked live held-topic evidence, query, and release evaluation."""
from __future__ import annotations
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_HELD_TOPIC_EVIDENCE_V1_PREREG_20260926.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_HELD_TOPIC_EVIDENCE_V1_5_1_AMENDMENT_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_live_held_topic_evidence_v1_5_1_20260926.json"
RAW = ROOT / "evaluation/reports/substrate_live_held_topic_evidence_v1_5_1_workers_raw_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/live_held_topic_evidence_v1_5_1_lock_20260926.json"
TASK_EDGE_TYPES = ("has_goal", "comprehends", "comprehended_by", "holds_answer",
    "grounded_by", "for_message", "releases", "responds_to", "sent",
    "received", "has_event")
FACTS = {
    "copper": "Copper conducts electricity and heat.",
    "basalt": "Basalt is a fine-grained igneous rock formed when lava cools quickly.",
    "hexagon": "A hexagon has six straight sides and six angles.",
}
TASKS = (
    ("What do you know about copper?", "copper", "meta"),
    ("What do you know about basalt?", "basalt", "meta"),
    ("What do you know about hexagon?", "hexagon", "meta"),
    ("What is copper?", "copper", "table"),
    ("Can you tell me about copper?", "copper", "honest_capability"),
    ("What do you know about unobtainium?", "unobtainium", "meta"),
    ("What do you know about localhitium?", "localhitium", "meta"),
)
LOCAL_HIT_ANSWER = "Localhitium is a controlled local-source fixture for this evaluation."

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def source_closure():
    paths = set()
    for folder in (ROOT / "domains", ROOT / "substrate", ROOT / "runners/dsl/python"):
        paths.update(p for p in folder.rglob("*.py") if "__pycache__" not in p.parts)
    paths.update((ROOT / "seeds").glob("*.json"))
    paths.update((ROOT / "seeds/generated").glob("*.json"))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}

def fingerprint():
    from substrate_rs import _native
    return {"protocol_sha256": sha(PROTOCOL), "amendment_sha256": sha(AMENDMENT),
        "runner_sha256": sha(__file__),
        "source_closure_sha256": source_closure(),
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}

def idof(node):
    return int(node.value if hasattr(node, "value") else node)

def measured(agent, operation):
    audit = agent.inner
    audit.scale_audit_reset()
    audit.scale_audit_set_enabled(True)
    start = time.perf_counter_ns()
    try:
        value = operation()
        elapsed = time.perf_counter_ns() - start
        counters = {str(k): int(v) for k, v in dict(audit.scale_audit_snapshot()).items()}
    finally:
        audit.scale_audit_set_enabled(False)
    return value, {"elapsed_ns": elapsed, "counters": counters}

def frame_projection(agent, inbound, goals, topic, held, evidence, receipts, replies):
    members = {inbound, *goals, *held, *evidence, *receipts, *replies}
    directed = {}
    for node in tuple(members):
        if node is None or not agent.s.has_node(node):
            continue
        for edge_type in TASK_EDGE_TYPES:
            for target in agent.inner.neighbours(node, edge_type):
                directed[(idof(node), edge_type, idof(target))] = None
            for source in agent.inner.in_neighbours(node, edge_type):
                directed[(idof(source), edge_type, idof(node))] = None
    member_ids = {idof(n) for n in members if n is not None and agent.s.has_node(n)}
    internal = [e for e in directed if e[0] in member_ids and e[2] in member_ids]
    boundary = [e for e in directed if (e[0] in member_ids) != (e[2] in member_ids)]
    return {"node_ids": sorted(member_ids), "node_count": len(member_ids),
        "edge_type_scope": list(TASK_EDGE_TYPES),
        "internal_edge_count": len(internal), "boundary_incidence_count": len(boundary),
        "internal_edges": [list(e) for e in sorted(internal)],
        "boundary_edges": [list(e) for e in sorted(boundary)]}

def capture_turn(agent, prompt, expected_topic, expected_path):
    import domains.comprehend_text as ct
    original = ct.comprehend_text
    captured = []
    def observe(*args, **kwargs):
        comp = original(*args, **kwargs)
        captured.append(comp)
        return comp
    ct.comprehend_text = observe
    ground_calls = []
    try:
        if expected_topic in {"unobtainium", "localhitium"}:
            from unittest.mock import patch
            import domains.topic_grounding as tg
            original_ground_topic = tg.ground_topic
            def controlled_grounder(_agent, phrase, **kwargs):
                import traceback
                inbound = getattr(_agent, "_last_turn_inbound", None)
                goal_state = []
                if inbound is not None:
                    for goal in _agent.inner.neighbours(_agent.agent, "has_goal"):
                        if (_agent.s.has_node(goal)
                                and inbound in _agent.inner.neighbours(goal, "comprehends")
                                and _agent.s.node(goal)["attrs"].get("kind") == "answer_topic"):
                            goal_state.append({"id": idof(goal), "attrs": dict(_agent.s.node(goal)["attrs"])})
                requests = [{"id": idof(node), "type": _agent.s.node(node)["type"],
                    "attrs": dict(_agent.s.node(node)["attrs"])}
                    for typ in ("SearchRequest", "GroundRequest")
                    for node in _agent.s.nodes(typ)
                    if str(_agent.s.node(node)["attrs"].get("query") or "").strip().casefold() == str(phrase).strip().casefold()]
                ground_calls.append({"phrase": str(phrase), "kwargs": kwargs,
                    "injected_local_hit": expected_topic == "localhitium",
                    "call_stack": [{"function": frame.name, "file": Path(frame.filename).name,
                        "line": frame.lineno} for frame in traceback.extract_stack(limit=9)[:-1]],
                    "goal_state_before_call": goal_state,
                    "matching_requests_before_call": requests,
                    "node_count_before_call": _agent.s.node_count(),
                    "edge_count_before_call": _agent.s.edge_count()})
                if expected_topic == "unobtainium":
                    return None
                return original_ground_topic(_agent, phrase, **kwargs)
            def local_source_hit(_agent, phrase):
                if str(phrase).strip().casefold() == "localhitium":
                    result = _agent.learn_from_teacher(str(phrase), {
                        "answer": LOCAL_HIT_ANSWER,
                        "learn": [{"phrase": str(phrase), "answer": LOCAL_HIT_ANSWER}]})
                    return result or LOCAL_HIT_ANSWER
                return None
            with patch.object(tg, "ground_topic", side_effect=controlled_grounder), \
                    patch.object(tg, "_ground_local", side_effect=local_source_hit):
                reply, work = measured(agent, lambda: agent.converse(
                    prompt, speech_act="question", speaker="alice"))
        else:
            reply, work = measured(agent, lambda: agent.converse(
                prompt, speech_act="question", speaker="alice"))
    finally:
        ct.comprehend_text = original

    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    comp = captured[-1] if captured else None
    goals = [g for g in agent.s.nodes("Goal")
             if inbound in agent.inner.neighbours(g, "comprehends")]
    topic_goals = [g for g in goals if agent.s.node(g)["attrs"].get("kind") == "answer_topic"]
    held = [n for n in agent.s.nodes("HeldAnswer")
            if agent.s.node(n)["attrs"].get("topic") == expected_topic]
    evidence = [e for h in held for e in agent.inner.neighbours(h, "grounded_by")
        if agent.s.has_node(e)
        and agent.s.node(e).get("type") == "TopicGroundingEvidence"
        and agent.s.node(e)["attrs"].get("kind") == "topic_answer"]
    receipts = [r for r in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(r)["attrs"].get("turn_message_id") == idof(inbound)]
    replies = [m for m in agent.outbound_messages() if inbound in agent.responds_to(m)]
    matching_requests_after = [{"id": idof(node), "type": agent.s.node(node)["type"],
        "attrs": dict(agent.s.node(node)["attrs"])}
        for kind in ("SearchRequest", "GroundRequest")
        for node in agent.s.nodes(kind)
        if str(agent.s.node(node)["attrs"].get("query") or "").strip().casefold()
        == str(expected_topic).casefold()]
    matching_evidence = [e for e in evidence
        if agent.s.node(e)["attrs"].get("referent") == expected_topic
        and agent.s.node(e)["attrs"].get("status") == "supported"
        and agent.s.node(e)["attrs"].get("evidence_path")]
    frame = frame_projection(agent, inbound, goals, expected_topic, held,
                             matching_evidence, receipts, replies)
    return {"prompt": prompt, "expected_topic": expected_topic,
        "expected_path": expected_path, "reply": str(reply), "work": work,
        "message_id": idof(inbound),
        "message": {k: attrs.get(k) for k in (
            "comp_kind", "comp_topic", "comp_know_concept", "comp_dispatch_path",
            "comp_dispatch_meta", "communication_route", "turn_reply_surface",
            "turn_reply_source", "communication_interpretation_id")},
        "comprehension": None if comp is None else {
            "kind": comp.kind, "fastpath": comp.fastpath,
            "table_kind": getattr(comp.table_spec, "kind", None),
            "dispatch": comp.dispatch, "intent": comp.intent},
        "goals": [{"id": idof(g), "attrs": agent.s.node(g)["attrs"]} for g in goals],
        "answer_topic_goal_ids": [idof(g) for g in topic_goals],
        "held_answer_ids": [idof(h) for h in held],
        "held_answers": [{"id": idof(h), "attrs": agent.s.node(h)["attrs"]} for h in held],
        "evidence_ids": [idof(e) for e in matching_evidence],
        "evidence": [{"id": idof(e), "attrs": agent.s.node(e)["attrs"]}
                     for e in matching_evidence],
        "receipts": [{"id": idof(r), "attrs": agent.s.node(r)["attrs"],
            "released_ids": [idof(n) for n in agent.inner.neighbours(r, "releases")]}
            for r in receipts],
        "reply_messages": [{"id": idof(m), "attrs": agent.s.node(m)["attrs"]}
                           for m in replies],
        "grounder_calls": ground_calls, "matching_requests_after": matching_requests_after,
        "task_frame": frame}

def worker(rep):
    started = fingerprint()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    agent = WorldAdapter(seeds=())
    boot_start = time.perf_counter_ns()
    load_all_seeds(agent)
    boot_ns = time.perf_counter_ns() - boot_start
    teaching = []
    for topic, answer in FACTS.items():
        result, work = measured(agent, lambda topic=topic, answer=answer:
            agent.learn_from_teacher(topic, {"answer": answer,
                "learn": [{"phrase": topic, "answer": answer}]}))
        teaching.append({"topic": topic, "expected_answer": answer,
                         "returned_answer": result, "work": work})
    turns = [capture_turn(agent, *task) for task in TASKS]
    nodes = list(agent.s.nodes())
    node_types = [agent.s.node(node)["type"] for node in nodes]
    finished = fingerprint()
    return {"replicate": rep, "pid": os.getpid(), "boot_ns": boot_ns,
        "teaching": teaching, "turns": turns,
        "final_graph": {"node_count": agent.s.node_count(),
            "edge_count": agent.s.edge_count(),
            "node_type_counts": {kind: sum(node_type == kind for node_type in node_types)
                for kind in sorted(set(node_types))}},
        "worker_started_inputs": started, "worker_finished_inputs": finished}

def main():
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": fingerprint()}, indent=2, sort_keys=True)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str)); return
    locked = fingerprint()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    paths = [str(ROOT), str(ROOT / "runners/dsl/python")]
    if env.get("PYTHONPATH"): paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    runs = []
    runs = []
    for rep in range(3):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()),
            "--worker", str(rep)], cwd=ROOT, env=env, text=True,
            capture_output=True, check=True)
        runs.append(json.loads(proc.stdout))
        RAW.write_text(json.dumps({"run_id": "substrate-live-held-topic-evidence-v1.5.1-workers-20260926",
            "locked_inputs": locked, "runs": runs}, indent=2, sort_keys=True,
            default=str) + "\n")
    raw = {"run_id": "substrate-live-held-topic-evidence-v1.5.1-workers-20260926",
           "locked_inputs": locked, "runs": runs}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    post = fingerprint()
    checks = {"three_fresh_pids": len({r["pid"] for r in runs}) == 3,
        "source_stable": post == locked and all(
            r["worker_started_inputs"] == locked and r["worker_finished_inputs"] == locked
            for r in runs),
        "route_and_answer_signature_repeats": len({json.dumps([
            [t["prompt"], t["message"], t["comprehension"], t["reply"],
             t["goals"], t["evidence"], t["receipts"]] for t in r["turns"]],
            sort_keys=True) for r in runs}) == 1}
    for run in runs:
        for teach in run["teaching"]:
            topic = teach["topic"]
            checks[f"{run['replicate']}_teaching_{topic}_returns_answer"] = (
                teach["returned_answer"] == teach["expected_answer"])
        for turn in run["turns"]:
            topic = turn["expected_topic"]
            prefix = f"{run['replicate']}_{turn['prompt']}"
            dispatch = (turn["comprehension"] or {}).get("dispatch", {})
            if topic not in {"unobtainium", "localhitium"}:
                held = turn["held_answers"]
                goal_ok = (len(turn["answer_topic_goal_ids"]) == 1
                    and len(turn["goals"]) == 1
                    and turn["goals"][0]["attrs"].get("concept") == topic)
                receipt_ok = any(r["attrs"].get("status") == "released"
                    and r["attrs"].get("surface") == turn["reply"]
                    and any(i in r["released_ids"] for i in turn["answer_topic_goal_ids"] + turn["held_answer_ids"])
                    for r in turn["receipts"])
                checks[prefix + "_supported_answer_released"] = (
                    turn["reply"] == FACTS[topic]
                    and len(held) == 1 and held[0]["attrs"].get("text") == FACTS[topic]
                    and held[0]["attrs"].get("grounding_referent") == topic
                    and held[0]["attrs"].get("grounding_status") == "supported"
                    and len(turn["evidence"]) >= 1
                    and goal_ok and receipt_ok
                    and dispatch.get("path") == turn["expected_path"])
            elif topic == "unobtainium":
                checks[prefix + "_unknown_topic_stays_unresolved"] = (
                    len(turn["answer_topic_goal_ids"]) == 1
                    and len(turn["grounder_calls"]) >= 1
                    and turn["grounder_calls"][0]["phrase"].lower() == "unobtainium"
                    and turn["goals"][0]["attrs"].get("outcome") == "unresolved"
                    and "copper conducts electricity" not in turn["reply"].lower()
                    and "unobtainium" in turn["reply"].lower()
                    and dispatch.get("path") == turn["expected_path"])
            else:
                expected_answer = LOCAL_HIT_ANSWER
                local_request_statuses = {
                    request["type"]: request["attrs"].get("status")
                    for request in turn["matching_requests_after"]}
                checks[prefix + "_injected_local_hit_answers_and_releases"] = (
                    turn["reply"] == expected_answer
                    and len(turn["grounder_calls"]) == 1
                    and turn["grounder_calls"][0].get("injected_local_hit") is True
                    and len(turn["held_answers"]) == 1
                    and turn["held_answers"][0]["attrs"].get("text") == expected_answer
                    and turn["held_answers"][0]["attrs"].get("grounding_status") == "supported"
                    and len(turn["evidence"]) >= 1
                    and turn["goals"][0]["attrs"].get("outcome") == "resolved"
                    and any(receipt["attrs"].get("status") == "released"
                        and receipt["attrs"].get("surface") == expected_answer
                        for receipt in turn["receipts"])
                    and local_request_statuses.get("GroundRequest") == "superseded"
                    and local_request_statuses.get("SearchRequest") == "superseded"
                    and dispatch.get("path") == turn["expected_path"])
    unknown_turns = [next(t for t in r["turns"] if t["expected_topic"] == "unobtainium") for r in runs]
    local_hit_turns = [next(t for t in r["turns"] if t["expected_topic"] == "localhitium") for r in runs]
    unknown_call_counts = [len(t["grounder_calls"]) for t in unknown_turns]
    local_hit_call_counts = [len(t["grounder_calls"]) for t in local_hit_turns]
    checks["unknown_no_result_call_count_repeats"] = (
        len(set(unknown_call_counts)) == 1 and unknown_call_counts[0] == 1)
    checks["unknown_local_miss_reused_by_dispatch"] = all(
        any(req["type"] == "GroundRequest"
            and req["attrs"].get("status") == "failed"
            and req["attrs"].get("local_grounding_outcome") == "miss"
            and req["attrs"].get("local_grounding_turn_id") == str(t["message_id"])
            for req in t["matching_requests_after"])
        and any(req["type"] == "SearchRequest"
            and req["attrs"].get("status") == "failed"
            for req in t["matching_requests_after"])
        for t in unknown_turns)
    checks["injected_local_hit_call_count_repeats"] = (
        len(set(local_hit_call_counts)) == 1 and local_hit_call_counts[0] == 1)
    payload = {"schema_version": 1,
        "run_id": "substrate-live-held-topic-evidence-v1.5.1-20260926",
        "claim_boundary": "Three independently taught held answers are queried through three observed comprehension routes in three fresh full-seed workers. A controlled unknown miss and injected _ground_local hit evaluate same-turn local miss reuse. The injected hit traverses the production ground_topic resolver and learn_from_teacher integration but does not benchmark the real Wikipedia corpus. The miss control verifies one inline lookup, exact GroundRequest source-turn marking and failure without a second lookup, independent SearchRequest processing, and stable unresolved/no-leak reply. This is not a broad language or tractability estimate.",
        "locked_inputs": locked, "post_run_inputs": post,
        "raw_workers_path": str(RAW.relative_to(ROOT)),
        "summary": {"unknown_no_result_grounder_calls_per_worker": unknown_call_counts,
            "injected_local_hit_grounder_calls_per_worker": local_hit_call_counts},
        "environment": {"python": sys.version, "platform": platform.platform()},
        "checks": checks, "runs": runs}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"output": str(OUT), "raw_workers": str(RAW),
        "checks": checks}, indent=2))
    if not all(checks.values()): raise SystemExit("held-topic evidence gate failed")

if __name__ == "__main__": main()
