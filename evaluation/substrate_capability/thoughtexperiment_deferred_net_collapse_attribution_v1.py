#!/usr/bin/env python3
"""Source-locked producer attribution probe for deferred NetCollapse."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests")]
OVERRIDE = os.environ.get("OCELot_NATIVE_IMPORT_ROOT")
if OVERRIDE: sys.path.insert(0, OVERRIDE)
RUNNER = Path(__file__).resolve()
PREREG = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_DEFERRED_NET_COLLAPSE_ATTRIBUTION_V1_PREREG_20261002.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_deferred_net_collapse_attribution_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_deferred_net_collapse_attribution_v1_lock_20261002.json"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_deferred_net_collapse_attribution_v1_20261002.json"
SOURCES = ("runners/dsl/src/graph.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/substrate.rs", "runners/dsl/src/py.rs")
WORKERS = 3

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
    from substrate_rs import _native
    files = (RUNNER, PREREG, ANALYZER, *(ROOT / p for p in SOURCES))
    binary = Path(_native.__file__).resolve()
    return {"files": {str(p.relative_to(ROOT)): sha(p) for p in files},
            "native_binary": {"path": str(binary), "sha256": sha(binary)}}

def make_case():
    import test_reflex_net_migrated as f
    s = f._fresh_substrate(); asm = f._untrained_net(s, hidden=8)
    rn = s.add_node("ReflexNet", {"name":"probe", "status":"self_training", "eta":0.2})
    s.add_edge(rn, "net_assemblage", asm, {})
    f._install(s, f._seed_rules()["reflex_net_self_train_step"])
    obs = s.add_node("ReflexObservation", {"status":"pending", "input_vec":[0.5], "target":[0.25]})
    s.add_edge(obs, "observes", rn, {})
    return s, int(obs.value)

def summary(r): return {k:r.get(k) for k in ("status","progress_steps","passes_completed")}
def edges(r): return {tuple((int(e[0]),str(e[1]),int(e[2]))) for e in r["affected_edges"]}
def execute():
    a, obs = make_case(); traced = a.run_rules_delta_report(1000, False)
    b, _ = make_case(); exact = b.run_rules_snapshot_delta_report(1000, False)
    c, _ = make_case(); plain = c.run_rules_report(1000, False)
    events = traced["rule_write_events"]
    en = {int(n) for e in events for n in e["node_ids"]}
    ee = {tuple((int(x[0]),str(x[1]),int(x[2]))) for e in events for x in e["edges"]}
    exact_nodes = set(map(int, exact["affected_nodes"]))
    exact_edges = edges(exact)
    deferred = [e for e in events if e["deferred"]]
    origin = [e for e in deferred if e["rule_name"] == "reflex_net_self_train_step"]
    return {"plain":summary(plain),"traced":summary(traced),"exact":summary(exact),
      "event_count":len(events),"deferred_events":deferred,"origin_events":origin,
      "observation_id":obs,"observation_consumed":obs in en,
      "event_covers_exact_nodes":exact_nodes <= en,"event_covers_exact_edges":exact_edges <= ee,
      "aggregate_covers_event_nodes":en <= set(map(int,traced["affected_nodes"])),
      "aggregate_covers_event_edges":ee <= edges(traced),
      "dropped_events":int(traced["rule_write_events_dropped"])}

def worker(i):
    expected=json.loads(LOCK.read_text())["sources"]; before=frozen()
    if before != expected: raise RuntimeError("source/native fingerprint differs from lock")
    result=execute(); after=frozen()
    return {"worker_index":i,"pid":os.getpid(),"sources_before":before,"sources_after":after,
      "source_stable":before==after,"result":result}

def main():
    if len(sys.argv)==3 and sys.argv[1]=="--worker":
        print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":"))); return 0
    if sys.argv[1:]==["--lock"]:
        if LOCK.exists() or CAPTURE.exists(): raise SystemExit("refusing to overwrite lock or capture")
        LOCK.write_text(json.dumps({"schema":"DeferredNetCollapseAttributionV1Lock","sources":frozen(),"workers":WORKERS},indent=2,sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT)); return 0
    if sys.argv[1:] != ["--run"]: raise SystemExit("usage: --lock or --run")
    lock=json.loads(LOCK.read_text())
    if frozen()!=lock["sources"]: raise SystemExit("source/native drift from lock")
    env=dict(os.environ); env["PYTHONPATH"]=os.pathsep.join(filter(None,(OVERRIDE,str(ROOT/"runners/dsl/python"),str(ROOT/"tests"),str(ROOT))))
    workers=[]
    for i in range(WORKERS):
        p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
        if p.returncode: raise RuntimeError(f"worker {i} failed: {p.stderr[-2500:]}")
        workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
    if frozen()!=lock["sources"]: raise SystemExit("source/native drift during capture")
    CAPTURE.write_text(json.dumps({"schema":"DeferredNetCollapseAttributionV1Results","lock_sha256":sha(LOCK),"captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"host":platform.platform(),"workers":workers},indent=2,sort_keys=True)+"\n")
    print(CAPTURE.relative_to(ROOT)); return 0
if __name__=="__main__": raise SystemExit(main())
