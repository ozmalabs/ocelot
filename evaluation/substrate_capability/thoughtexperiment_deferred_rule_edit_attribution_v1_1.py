#!/usr/bin/env python3
"""Source-locked producer attribution probe for deferred live RuleEdits."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
OVERRIDE=os.environ.get("OCELot_NATIVE_IMPORT_ROOT")
if OVERRIDE: sys.path.insert(0,OVERRIDE)
RUNNER=Path(__file__).resolve()
PREREG=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_DEFERRED_RULE_EDIT_ATTRIBUTION_V1_1_PREREG_20261002.md"
ANALYZER=ROOT/"evaluation/substrate_capability/analyze_thoughtexperiment_deferred_rule_edit_attribution_v1_1.py"
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_attribution_v1_1_lock_20261002.json"
CAPTURE=ROOT/"evaluation/reports/thoughtexperiment_deferred_rule_edit_attribution_v1_1_20261002.json"
SOURCES=("runners/dsl/src/graph.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs")
WORKERS=3
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,PREREG,ANALYZER,*(ROOT/p for p in SOURCES)); b=Path(_native.__file__).resolve()
 return {"files":{str(p.relative_to(ROOT)):sha(p) for p in files},"native_binary":{"path":str(b),"sha256":sha(b)}}
def make_case():
 from substrate_rs import _native
 s=_native.Substrate(); a=s.add_node("Anchor",{"done":False}); mark=s.add_node("Marker",{}); target=s.add_node("Target",{})
 s.add_edge_unchecked(a,"edit",mark); s.add_edge_unchecked(a,"target",target)
 s.add_rule({"name":"edit_target_clause","match":[["a","edit","m"]],
   "where":{"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"a"},"key":"done"},"b":{"type":"Lit","value":False}},
   "effects":[["set_rule_clause","target_rule","where",{"__term__":{"type":"Lit","value":{"type":"Lit","value":True}}}],["set_attr","a","done",True]]})
 s.add_rule({"name":"target_rule","match":[["a","target","t"]],"where":{"type":"Lit","value":False},"effects":[["set_attr","t","edited",True]]})
 before=s.export_rules_prefix("target_rule")
 return s,int(target.value),before
def snap(r): return {k:r.get(k) for k in ("status","progress_steps","passes_completed")}
def edge_set(r): return {tuple((int(e[0]),str(e[1]),int(e[2]))) for e in r["affected_edges"]}
def execute():
 s,nid,before=make_case(); traced=s.run_rules_delta_report(1000,False)
 sx,nx,_=make_case(); exact=sx.run_rules_snapshot_delta_report(1000,False)
 sp,npid,_=make_case(); plain=sp.run_rules_report(1000,False)
 after=s.export_rules_prefix("target_rule"); ev=traced["rule_write_events"]
 en={int(n) for e in ev for n in e["node_ids"]}; ee={tuple((int(x[0]),str(x[1]),int(x[2]))) for e in ev for x in e["edges"]}
 exn=set(map(int,exact["affected_nodes"])); exe=edge_set(exact)
 deferred=[e for e in ev if e["deferred"]]; origin=[e for e in deferred if e["rule_name"]=="edit_target_clause"]
 return {"plain":snap(plain),"traced":snap(traced),"exact":snap(exact),"events":ev,"deferred_events":deferred,"origin_events":origin,
  "target_id":nid,"graph_target_written":nid in en,"target_rule_before":before,"target_rule_after":after,
  "rule_definition_changed":before!=after,"final_rule_entries":after,
  "event_covers_exact_nodes":exn<=en,"event_covers_exact_edges":exe<=ee,
  "aggregate_covers_event_nodes":en<=set(map(int,traced["affected_nodes"])),"aggregate_covers_event_edges":ee<=edge_set(traced),"dropped_events":int(traced["rule_write_events_dropped"])}
def worker(i):
 expected=json.loads(LOCK.read_text())["sources"]; before=frozen()
 if before!=expected: raise RuntimeError("source/native fingerprint differs from lock")
 result=execute(); after=frozen()
 return {"worker_index":i,"pid":os.getpid(),"sources_before":before,"sources_after":after,"source_stable":before==after,"result":result}
def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker": print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":"))); return 0
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or CAPTURE.exists(): raise SystemExit("refusing to overwrite lock or capture")
  LOCK.write_text(json.dumps({"schema":"DeferredRuleEditAttributionV1_1Lock","sources":frozen(),"workers":WORKERS},indent=2,sort_keys=True)+"\n"); print(LOCK.relative_to(ROOT)); return 0
 if sys.argv[1:]!=["--run"]: raise SystemExit("usage: --lock or --run")
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock["sources"]: raise SystemExit("source/native drift from lock")
 env=dict(os.environ); env["PYTHONPATH"]=os.pathsep.join(filter(None,(OVERRIDE,str(ROOT/"runners/dsl/python"),str(ROOT))))
 ws=[]
 for i in range(WORKERS):
  p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode: raise RuntimeError(f"worker {i} failed: {p.stderr[-2500:]}")
  ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock["sources"]: raise SystemExit("source/native drift during capture")
 CAPTURE.write_text(json.dumps({"schema":"DeferredRuleEditAttributionV1_1Results","lock_sha256":sha(LOCK),"captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"host":platform.platform(),"workers":ws},indent=2,sort_keys=True)+"\n"); print(CAPTURE.relative_to(ROOT)); return 0
if __name__=="__main__": raise SystemExit(main())
