#!/usr/bin/env python3
"""Capture repeated attached-scene describe requests and parent Goal identity."""
from __future__ import annotations
import hashlib, json, os, platform, random, statistics, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_DESCRIBE_SCENE_REPEATED_REQUEST_IDENTITY_PREREG_20260926.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_DESCRIBE_SCENE_LIFECYCLE_IDENTITY_V1_1_AMENDMENT_20260926.md"
SOURCES = {
    "world_adapter": ROOT / "substrate/world_adapter.py",
    "boot_all": ROOT / "substrate/boot_all.py",
    "conversation_action": ROOT / "domains/conversation_action.py",
    "discourse_state": ROOT / "domains/discourse_state.py",
    "reflective_faculty": ROOT / "domains/reflective_faculty.py",
    "arc_self_report": ROOT / "scripts/arc_self_report.py",
    "describe_runner": Path(__file__),
    "discourse_seed": ROOT / "seeds/conversation_discourse_state.json",
}
LOCK = ROOT / "evaluation/substrate_capability/describe_scene_lifecycle_identity_v1_1_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_describe_scene_lifecycle_identity_v1_1_20260926.json"

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def nid(x): return int(x.value if hasattr(x, "value") else x)

def lock_inputs():
    from substrate_rs import _native
    return {
        "protocol_sha256": sha(PROTOCOL), "amendment_sha256": sha(AMENDMENT), "runner_sha256": sha(__file__),
        "source_sha256": {k: sha(v) for k, v in SOURCES.items()},
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    }

def goal_row(a, goal, scene):
    attrs = a.s.node(goal)["attrs"]
    origins = list(a.inner.neighbours(goal, "originated_in"))
    messages = list(a.inner.neighbours(goal, "comprehends"))
    children = list(a.inner.neighbours(goal, "has_subgoal"))
    transitions = list(a.inner.neighbours(goal, "transitioned_by"))
    transitions.sort(key=lambda e: int(a.s.node(e)["attrs"].get("event_index", -1)))
    described = list(a.inner.neighbours(goal, "describes"))
    return {"id": nid(goal), "attrs": attrs, "origin_event_ids": [nid(x) for x in origins],
            "comprehended_message_ids": [nid(x) for x in messages],
            "transition_event_ids": [nid(x) for x in transitions],
            "transition_kinds": [a.s.node(x)["attrs"].get("kind") for x in transitions],
            "described_scene_ids": [nid(x) for x in described],
            "described_scene_parent_links": [goal in a.inner.neighbours(s, "described_by") for s in described],
            "closed": any(goal in a.inner.neighbours(s, "has_closed_goal") for s in a.s.nodes("DiscourseState")),
            "active": any(goal in a.inner.neighbours(s, "has_active_goal") for s in a.s.nodes("DiscourseState")),
            "is_scene_parent": goal in a.inner.neighbours(scene, "described_by"),
            "subgoal_ids": [nid(x) for x in children]}

def worker(rep):
    started = lock_inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.conversation_action import attach_scene
    a = WorldAdapter(seeds=())
    t0 = time.perf_counter_ns(); load_all_seeds(a); boot_ns = time.perf_counter_ns() - t0
    scene = attach_scene(a, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False},
    ])
    turns = []
    for i in range(2):
        goals_before = {nid(g) for g in a.s.nodes("Goal")}
        t0 = time.perf_counter_ns()
        reply = a.converse("describe what you see", speech_act="instruction", speaker="alice")
        elapsed_ns = time.perf_counter_ns() - t0
        message = a._last_turn_inbound
        ma = a.s.node(message)["attrs"]
        origin = ma.get("discourse_event_id")
        state = ma.get("discourse_state_id")
        matching = [g for g in a.s.nodes("Goal") if message in a.inner.neighbours(g, "comprehends")]
        goal = matching[0] if len(matching) == 1 else None
        new_goals = [g for g in a.s.nodes("Goal") if nid(g) not in goals_before]
        scene_parents = list(a.inner.neighbours(scene, "described_by"))
        events = list(a.inner.neighbours(state, "has_event")) if state is not None else []
        goal_events = [e for e in events if goal is not None and goal in a.inner.neighbours(e, "for_goal")]
        goal_events.sort(key=lambda e: int(a.s.node(e)["attrs"].get("event_index", -1)))
        turns.append({
            "turn": i, "elapsed_ns": elapsed_ns, "reply_nonempty": bool(reply),
            "reply": str(reply), "route": ma.get("communication_route"),
            "message_id": nid(message), "origin_event_id": nid(origin) if origin is not None else None,
            "origin_event_kind": a.s.node(origin)["attrs"].get("kind") if origin is not None else None,
            "new_goal_ids": [nid(g) for g in new_goals],
            "matching_goal_ids": [nid(g) for g in matching],
            "matching_goals": [goal_row(a, g, scene) for g in matching],
            "scene_parent_ids": [nid(g) for g in scene_parents],
            "scene_parents": [goal_row(a, g, scene) for g in scene_parents],
            "state_event_kinds": [a.s.node(e)["attrs"].get("kind") for e in events],
            "lifecycle_event_count": sum(a.s.node(e)["attrs"].get("kind") in
                {"selection", "execution", "action_result", "action_failure"} for e in events),
            "goal_lifecycle_events": [{"id": nid(e), "kind": a.s.node(e)["attrs"].get("kind"),
                "for_goal_ids": [nid(g) for g in a.inner.neighbours(e, "for_goal")]}
                for e in goal_events],
        })
    finished = lock_inputs()
    distinct_parent_identity = (len(turns) == 2 and all(len(t["matching_goal_ids"]) == 1 for t in turns)
        and turns[0]["matching_goal_ids"][0] != turns[1]["matching_goal_ids"][0])
    each_goal_owns_only_its_request = all(
        len(t["matching_goals"]) == 1
        and t["matching_goals"][0]["comprehended_message_ids"] == [t["message_id"]]
        and t["matching_goals"][0]["origin_event_ids"] == [t["origin_event_id"]]
        and t["matching_goals"][0]["transition_kinds"] == ["selection", "execution", "action_result"]
        and t["matching_goals"][0]["closed"] and not t["matching_goals"][0]["active"]
        and len(t["matching_goals"][0]["subgoal_ids"]) == 3
        and all(t["matching_goals"][0]["described_scene_parent_links"])
        and [e["kind"] for e in t["goal_lifecycle_events"]] == ["selection", "execution", "action_result"]
        and all(e["for_goal_ids"] == t["matching_goal_ids"] for e in t["goal_lifecycle_events"])
        for t in turns)
    return {"replicate": rep, "pid": os.getpid(), "boot_ns": boot_ns, "turns": turns,
        "distinct_parent_identity": distinct_parent_identity,
        "each_goal_owns_only_its_request": each_goal_owns_only_its_request,
        "both_replies_nonempty": all(t["reply_nonempty"] for t in turns),
        "worker_started_inputs": started, "worker_finished_inputs": finished}

def main():
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": lock_inputs()}, indent=2, sort_keys=True)); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str)); return
    locked = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale lock")
    env = dict(os.environ); env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    jobs = [0, 1, 2]; random.Random(20260926).shuffle(jobs); runs = []
    for rep in jobs:
        p = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(p.stdout))
    post = lock_inputs()
    shape = lambda r: [{"route": t["route"], "reply_nonempty": t["reply_nonempty"],
        "origin_event_kind": t["origin_event_kind"], "new_goal_count": len(t["new_goal_ids"]),
        "matching_goal_count": len(t["matching_goal_ids"]), "event_kinds": t["state_event_kinds"],
        "life_kinds": [e["kind"] for e in t["goal_lifecycle_events"]],
        "goal_status": t["matching_goals"][0]["attrs"].get("lifecycle_status") if t["matching_goals"] else None,
        "child_count": len(t["matching_goals"][0]["subgoal_ids"]) if t["matching_goals"] else 0} for t in r["turns"]]
    checks = {
        "three_distinct_fresh_pids": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
        "two_nonempty_replies_per_worker": all(r["both_replies_nonempty"] for r in runs),
        "source_stable_workers_and_postrun": post == locked and all(
            r["worker_started_inputs"] == locked and r["worker_finished_inputs"] == locked for r in runs),
        "identity_gate_passes_all_workers": all(r["distinct_parent_identity"] and r["each_goal_owns_only_its_request"] for r in runs),
        "normalized_graph_shape_repeats": len({json.dumps(shape(r), sort_keys=True) for r in runs}) == 1,
    }
    payload = {"schema_version": 1, "run_id": "substrate-describe-scene-lifecycle-identity-v1_1-20260926",
        "claim_boundary": "Three fresh full-seed workers capture repeated sequential attached-scene describe requests after request-scoped Goal identity and parent lifecycle integration. This does not establish concurrent safety or general action-route capability.",
        "locked_inputs": locked, "post_run_inputs": post, "lock_sha256": sha(LOCK),
        "environment": {"python": sys.version, "platform": platform.platform()}, "schedule": jobs,
        "checks": checks,
        "summary": {"replicates": len(runs), "boot_ns_median": statistics.median(r["boot_ns"] for r in runs),
            "turn_ns_median": statistics.median(t["elapsed_ns"] for r in runs for t in r["turns"])},
        "runs": runs}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks, "summary": payload["summary"]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("probe validity gate failed; inspect preserved raw capture")

if __name__ == "__main__": main()
