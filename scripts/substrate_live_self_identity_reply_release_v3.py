#!/usr/bin/env python3
"""Confirm receipt-backed self-report messages and failure suppression."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = (
    ("describe who you are", "instruction"),
    ("describe yourself", "instruction"),
    ("who are you", "instruction"),
    ("tell me about yourself", "instruction"),
    ("summarise the report", "instruction"),
)
ACTION_PROMPTS = {"describe yourself", "tell me about yourself"}
QUESTION_PATHS = {"describe who you are": "table", "who are you": "meta"}
NEGATIVE_PROMPT = "summarise the report"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_IDENTITY_REPLY_RELEASE_V3_PREREG_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_live_self_identity_reply_release_v3_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/live_self_identity_reply_release_v3_lock_20260926.json"

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
    return {"runner_sha256": sha(__file__), "protocol_sha256": sha(PROTOCOL),
        "source_closure_sha256": source_closure(),
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
            transcript = agent.chat_transcript()
            turn_transcript = next((entry for entry in reversed(transcript)
                                    if entry.get("turn_id") == int(mid.value)), None)
            receipts = []
            for receipt in agent.s.nodes("ProductionGateReceipt"):
                ra = agent.s.node(receipt)["attrs"]
                if (ra.get("turn_message_id") == int(mid.value)
                        or mid in agent.inner.neighbours(receipt, "for_message")):
                    receipts.append({"id": int(receipt.value), "attrs": ra,
                        "released_ids": [int(x.value) for x in agent.inner.neighbours(
                            receipt, "releases")]})
            turn_outbound = [{"id": int(m.value), "attrs": agent.s.node(m)["attrs"]}
                for m in agent.outbound_messages() if mid in agent.responds_to(m)]
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
                "reply": str(reply), "transcript_reply": turn_transcript.get("reply") if turn_transcript else None,
                "outbound_messages": turn_outbound, "receipts": receipts,
                "goal_ids": [int(g.value) for g in goals],
                "goals": [{"id": int(g.value), "attrs": agent.s.node(g)["attrs"],
                    "transition_kinds": [agent.s.node(e)["attrs"].get("kind") for e in sorted(
                        agent.inner.neighbours(g, "transitioned_by"),
                        key=lambda e: int(agent.s.node(e)["attrs"].get("event_index", -1)))],
                    "transition_events_linked": all(g in agent.inner.neighbours(e, "for_goal")
                        for e in agent.inner.neighbours(g, "transitioned_by"))}
                    for g in goals],
                "goal_kinds": [agent.s.node(g)["attrs"].get("kind") for g in goals],
                "goal_self_targets": [agent.s.node(g)["attrs"].get("self_target") for g in goals]})
        from unittest.mock import patch
        from domains import reflective_faculty
        with patch.object(reflective_faculty, "reflect",
                          side_effect=RuntimeError("preregistered faculty failure")):
            reply = agent.converse("describe yourself", speech_act="instruction", speaker="alice")
        mid = agent._last_turn_inbound
        attrs = agent.s.node(mid)["attrs"]
        goals = [g for g in agent.s.nodes("Goal") if mid in agent.inner.neighbours(g, "comprehends")]
        transcript = next((entry for entry in reversed(agent.chat_transcript())
                           if entry.get("turn_id") == int(mid.value)), None)
        failure_receipts = []
        for receipt in agent.s.nodes("ProductionGateReceipt"):
            ra = agent.s.node(receipt)["attrs"]
            if ra.get("turn_message_id") == int(mid.value):
                failure_receipts.append({"id": int(receipt.value), "attrs": ra,
                    "released_ids": [int(x.value) for x in agent.inner.neighbours(
                        receipt, "releases")]})
        candidate_nodes = [m for g in goals for m in
            agent.inner.neighbours(g, "has_reply_candidate")]
        candidate_ids = [int(m.value) for m in candidate_nodes]
        turns.append({"prompt": "describe yourself [faculty failure]", "speech_act": "instruction",
            "failure_injected": True, "reply": str(reply),
            "transcript_reply": transcript.get("reply") if transcript else None,
            "message": {k: attrs.get(k) for k in ("communication_route", "turn_reply_surface", "turn_reply_source")},
            "goals": [{"id": int(g.value), "attrs": agent.s.node(g)["attrs"],
                "transition_kinds": [agent.s.node(e)["attrs"].get("kind") for e in sorted(
                    agent.inner.neighbours(g, "transitioned_by"),
                    key=lambda e: int(agent.s.node(e)["attrs"].get("event_index", -1)))]}
                for g in goals],
            "candidate_ids": candidate_ids,
            "candidate_states": [{"id": int(m.value), "attrs": agent.s.node(m)["attrs"]}
                for m in candidate_nodes],
            "outbound_messages": [{"id": int(m.value), "attrs": agent.s.node(m)["attrs"]}
                for m in agent.outbound_messages() if mid in agent.responds_to(m)],
            "receipts": failure_receipts})
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
    checks={"three_fresh_pids":len({r["pid"] for r in runs})==3,
        "source_stable":post==locked and all(r["worker_started_inputs"]==locked and r["worker_finished_inputs"]==locked for r in runs),
        "route_signature_repeats":len({json.dumps([[t["comprehension"],t["message"],t["goal_kinds"],t["goals"],t.get("transcript_reply")] for t in r["turns"]],sort_keys=True) for r in runs})==1}
    for run in runs:
        by_prompt={t["prompt"]:t for t in run["turns"]}
        for prompt in ACTION_PROMPTS:
            turn=by_prompt[prompt]
            goals=turn["goals"]
            checks[f"{run['replicate']}_{prompt.replace(' ','_')}_single_resolved_identity_goal"]=(
                len(goals)==1 and goals[0]["attrs"].get("kind")=="report_self"
                and goals[0]["attrs"].get("self_target")=="self_identity"
                and goals[0]["attrs"].get("lifecycle_status")=="resolved"
                and goals[0]["transition_kinds"]==["selection","execution","action_result"]
                and goals[0]["transition_events_linked"]
                and turn["message"].get("communication_route")=="self_report"
                and bool(turn["reply"].strip())
                and turn["transcript_reply"]==turn["reply"]
                and len(turn["outbound_messages"])==1
                and len([r for r in turn["receipts"] if r["attrs"].get("status")=="released"])==1
                and all(int(goals[0]["id"]) in r["released_ids"]
                        and int(turn["outbound_messages"][0]["id"]) in r["released_ids"]
                        and r["attrs"].get("surface")==turn["reply"]
                        for r in turn["receipts"] if r["attrs"].get("status")=="released")
                and turn["outbound_messages"][0]["attrs"].get("candidate_surface")
                and turn["outbound_messages"][0]["attrs"].get("text")==turn["reply"])
        for prompt,path in QUESTION_PATHS.items():
            turn=by_prompt[prompt]
            checks[f"{run['replicate']}_{prompt.replace(' ','_')}_question_route"]=(
                len(turn["goals"])==0 and turn["comprehension"]["dispatch"].get("path")==path
                and bool(turn["reply"].strip()))
        negative=by_prompt[NEGATIVE_PROMPT]
        checks[f"{run['replicate']}_external_object_not_self_report"]=(
            all(g["attrs"].get("kind")!="report_self" for g in negative["goals"])
            and negative["message"].get("communication_route")!="self_report"
            and bool(negative["reply"].strip()))
        failure=by_prompt["describe yourself [faculty failure]"]
        checks[f"{run['replicate']}_failure_candidate_withheld_and_error_transcribed"]=(
            failure["failure_injected"] and failure["reply"]
            == "ERROR: no communicative response could be generated."
            and failure["transcript_reply"]==failure["reply"]
            and failure["message"].get("communication_route")=="self_report_failure"
            and len(failure["goals"])==1
            and failure["goals"][0]["attrs"].get("lifecycle_status")=="blocked"
            and failure["goals"][0]["transition_kinds"]==["selection","execution","action_failure"]
            and len(failure["candidate_states"])==1
            and failure["candidate_states"][0]["attrs"].get("turn_reply_suppressed") is True
            and len(failure["outbound_messages"])==1
            and failure["outbound_messages"][0]["attrs"].get("text")==failure["reply"]
            and failure["outbound_messages"][0]["id"] not in failure["candidate_ids"]
            and not any(r["attrs"].get("status")=="released" for r in failure["receipts"]))
    payload={"schema_version":1,"run_id":"substrate-live-self-identity-reply-release-v3-20260926",
        "claim_boundary":"A production integration check for five fixed self-identity/external-object phrasings plus controlled reflective-faculty failure in three fresh seeded processes. It tests Goal ownership, output/receipt binding, and failure suppression, not natural language coverage, answer quality, or tractability.",
        "locked_inputs":locked,"post_run_inputs":post,"runs":runs,
        "checks":checks}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps({"output":str(OUT),"checks":payload["checks"]},indent=2))
    if not all(payload["checks"].values()): raise SystemExit("route probe integrity gate failed")

if __name__ == "__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--worker": print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str))
    else: main()
