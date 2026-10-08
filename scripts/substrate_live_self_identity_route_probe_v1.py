#!/usr/bin/env python3
"""Source-locked route probe for nearby self-identity request phrasings."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = (
    ("describe who you are", "instruction"),
    ("describe yourself", "instruction"),
    ("who are you", "instruction"),
    ("tell me about yourself", "instruction"),
)
OUT = ROOT / "evaluation/reports/substrate_live_self_identity_route_probe_v1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/live_self_identity_route_probe_v1_lock_20260926.json"

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def source_closure():
    paths = set()
    for folder in (ROOT / "domains", ROOT / "substrate", ROOT / "runners/dsl/python"):
        paths.update(p for p in folder.rglob("*.py") if "__pycache__" not in p.parts)
    paths.update((ROOT / "seeds").glob("*.json"))
    paths.update((ROOT / "seeds/generated").glob("*.json"))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}

def fingerprint():
    from substrate_rs import _native
    return {"runner_sha256": sha(__file__), "source_closure_sha256": source_closure(),
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}

def worker(rep):
    started = fingerprint()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    import domains.comprehend_text as ct
    original = ct.comprehend_text
    captured = []
    def observe(*args, **kwargs):
        comp = original(*args, **kwargs)
        captured.append(comp)
        return comp
    ct.comprehend_text = observe
    try:
        agent = WorldAdapter(seeds=())
        load_all_seeds(agent)
        turns = []
        for prompt, speech_act in PROMPTS:
            captured.clear()
            t0 = time.perf_counter_ns()
            reply = agent.converse(prompt, speech_act=speech_act, speaker="alice")
            elapsed = time.perf_counter_ns() - t0
            mid = agent._last_turn_inbound
            attrs = agent.s.node(mid)["attrs"]
            comp = captured[-1] if captured else None
            goals = [g for g in agent.s.nodes("Goal") if mid in agent.inner.neighbours(g, "comprehends")]
            turns.append({"prompt": prompt, "speech_act": speech_act, "elapsed_ns": elapsed,
                "comprehension_calls": len(captured),
                "comprehension": None if comp is None else {
                    "kind": comp.kind, "focus": comp.focus, "reflexive": comp.reflexive,
                    "fastpath": comp.fastpath, "table_kind": getattr(comp.table_spec, "kind", None),
                    "dispatch": comp.dispatch, "intent": comp.intent},
                "message": {k: attrs.get(k) for k in (
                    "comp_kind", "comp_predicate", "comp_content", "comp_topic",
                    "comp_dispatch_path", "comp_dispatch_meta", "comp_reflexive",
                    "comp_intent", "instruction_outcome", "communication_route",
                    "communication_interpretation_id", "communication_repair_route")},
                "reply": str(reply), "goal_ids": [int(g.value) for g in goals],
                "goals": [{"id": int(g.value), "attrs": agent.s.node(g)["attrs"],
                    "transition_kinds": [agent.s.node(e)["attrs"].get("kind") for e in sorted(
                        agent.inner.neighbours(g, "transitioned_by"),
                        key=lambda e: int(agent.s.node(e)["attrs"].get("event_index", -1)))],
                    "transition_events_linked": all(g in agent.inner.neighbours(e, "for_goal")
                        for e in agent.inner.neighbours(g, "transitioned_by"))}
                    for g in goals],
                "goal_kinds": [agent.s.node(g)["attrs"].get("kind") for g in goals],
                "goal_self_targets": [agent.s.node(g)["attrs"].get("self_target") for g in goals]})
    finally:
        ct.comprehend_text = original
    return {"replicate": rep, "pid": os.getpid(), "turns": turns,
            "worker_started_inputs": started, "worker_finished_inputs": fingerprint()}

def main():
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": fingerprint()}, indent=2, sort_keys=True)); return
    locked = fingerprint()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock")
    env = dict(os.environ); env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    paths = [str(ROOT), str(ROOT / "runners/dsl/python")]
    if env.get("PYTHONPATH"): paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    runs=[]
    for rep in range(3):
        p=subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(p.stdout))
    post=fingerprint()
    payload={"schema_version":1,"run_id":"substrate-live-self-identity-route-probe-v1-20260926",
        "claim_boundary":"Four self-identity phrasings are compared at the live comprehension/dispatch boundary in three fresh seeded processes. This diagnoses route selection; it is not an accuracy or prevalence estimate.",
        "locked_inputs":locked,"post_run_inputs":post,"runs":runs,
        "checks":{"three_fresh_pids":len({r["pid"] for r in runs})==3,
          "source_stable":post==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),
          "route_signature_repeats":len({json.dumps([[t["comprehension"],t["message"],t["goal_kinds"]] for t in r["turns"]],sort_keys=True) for r in runs})==1}}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps({"output":str(OUT),"checks":payload["checks"]},indent=2))
    if not all(payload["checks"].values()): raise SystemExit("route probe integrity gate failed")

if __name__ == "__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--worker": print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str))
    else: main()
