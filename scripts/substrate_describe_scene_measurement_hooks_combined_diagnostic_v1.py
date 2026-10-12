#!/usr/bin/env python3
"""Test only the access-trace runner's lock proxy on plain concurrent turns."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_DESCRIBE_SCENE_MEASUREMENT_HOOKS_COMBINED_DIAGNOSTIC_V1_PREREG_20260927.md"
LOCK = ROOT / "evaluation/substrate_capability/describe_scene_measurement_hooks_combined_diagnostic_v1_lock_20260927.json"
OUT = ROOT / "evaluation/reports/describe_scene_measurement_hooks_combined_diagnostic_v1_20260927.json"
PLAIN_RUNNER = ROOT / "scripts/substrate_describe_scene_plain_concurrency_diagnostic_v1.py"
TRACE_RUNNER = ROOT / "scripts/substrate_live_describe_scene_access_trace_v2_3.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    ps = importlib.util.spec_from_file_location("plain_concurrency_v1", PLAIN_RUNNER)
    pm = importlib.util.module_from_spec(ps); assert ps and ps.loader; ps.loader.exec_module(pm)
    ts = importlib.util.spec_from_file_location("scene_trace_v2_3", TRACE_RUNNER)
    tm = importlib.util.module_from_spec(ts); assert ts and ts.loader; ts.loader.exec_module(tm)
    return {"protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__)),
            "plain_runner_inputs": pm.input_lock(), "trace_runner_inputs": tm.lock_inputs()}


class ObservedLock:
    def __init__(self, inner, attempted):
        self.inner, self.attempted = inner, attempted

    def __enter__(self):
        if threading.current_thread().name == "request-B":
            self.attempted.set()
        self.inner.acquire()
        return self

    def __exit__(self, *exc):
        self.inner.release()
        return False


def run() -> dict:
    started = lock_inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.conversation_action import attach_scene
    import domains.conversation_action as ca
    ps = importlib.util.spec_from_file_location("plain_concurrency_v1", PLAIN_RUNNER)
    pm = importlib.util.module_from_spec(ps); assert ps and ps.loader; ps.loader.exec_module(pm)

    adapter = WorldAdapter(seeds=())
    boot0=time.perf_counter_ns();load_all_seeds(adapter);boot_ns=time.perf_counter_ns()-boot0
    attach_scene(adapter,[{"kind":"static","colour":"grey"},{"kind":"meter","colour":"yellow"},{"kind":"mover","colour":"blue","responds_to_my_action":False}])
    attempted=threading.Event();adapter._conversation_lock=ObservedLock(adapter._conversation_lock,attempted)
    producer_work=[];original=ca._record_live_goal_event
    def audited(agent,inbound,goal,kind,*,payload=None):
        audit=agent.inner;audit.scale_audit_reset();audit.scale_audit_per_rule_reset()
        audit.scale_audit_set_enabled(True);audit.scale_audit_set_per_rule_enabled(True);t0=time.perf_counter_ns()
        try:
            event=original(agent,inbound,goal,kind,payload=payload);elapsed=time.perf_counter_ns()-t0
            counters={"scale":{str(k):int(v) for k,v in dict(audit.scale_audit_snapshot()).items()},"per_rule":[[int(i),str(m),int(v)] for i,m,v in audit.scale_audit_per_rule_snapshot()]}
        finally:audit.scale_audit_set_per_rule_enabled(False);audit.scale_audit_set_enabled(False)
        producer_work.append({"kind":kind,"elapsed_ns":elapsed,"counters":counters})
        return event
    ca._record_live_goal_event=audited
    original_converse=adapter.converse
    def nested_converse(text,speech_act="statement",speaker="user",context=None):
        with adapter._conversation_lock:
            return original_converse(text,speech_act=speech_act,speaker=speaker,context=context)
    adapter.converse=nested_converse
    barrier=threading.Barrier(3);outputs={};errors={};
    def call(label):
        barrier.wait()
        try:outputs[label]=adapter.converse("describe what you see",speech_act="instruction",speaker="alice")
        except BaseException as exc:errors[label]={"type":type(exc).__name__,"message":str(exc)}
    workers=[threading.Thread(target=call,args=(x,),name=f"request-{x}") for x in ("A","B")]
    for t in workers:t.start()
    barrier.wait()
    for t in workers:t.join(120)
    joined=all(not t.is_alive() for t in workers)
    ca._record_live_goal_event=original
    inbound=[m for m in adapter.s.nodes("Message") if adapter.s.node(m)["attrs"].get("from")=="interlocutor" and adapter.s.node(m)["attrs"].get("text")=="describe what you see"]
    inbound.sort(key=pm.node_id)
    requests=[pm.stage(adapter,m,adapter.s.node(m)["attrs"].get("turn_reply_surface")) for m in inbound]
    finished=lock_inputs()
    return {"schema_version":1,"run_id":"describe-scene-measurement-hooks-combined-diagnostic-v1-20260927",
            "locked_inputs":started,"post_run_inputs":finished,"source_stable":started==finished,
            "lock_proxy":"ObservedLock(trace_enabled=False)","rule_audit_wrapper":True,"nested_public_lock":True,"access_trace":False,"producer_work":producer_work,"boot_ns":boot_ns,
            "thread_joined":joined,"thread_errors":errors,"lock_attempted":attempted.is_set(),
            "worker_replies":{k:str(v) for k,v in outputs.items()},"requests":requests,
            "matched_inbound_count":len(inbound),"environment":{"python":sys.version,"platform":platform.platform()}}


def main():
    if sys.argv[1:]==["--lock"]:
        print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return
    inputs=lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=inputs:raise SystemExit("missing or stale observed-lock source lock")
    report=run();OUT.write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+"\n")
    print(json.dumps({"output":str(OUT.relative_to(ROOT)),"source_stable":report["source_stable"],"threads_joined":report["thread_joined"],"errors":report["thread_errors"],"replies":report["worker_replies"],"goals":[r["goal_count"] for r in report["requests"]]},indent=2))
    if not report["source_stable"] or not report["thread_joined"] or report["matched_inbound_count"]!=2:raise SystemExit("observed-lock diagnostic integrity failure")


if __name__=="__main__":main()
