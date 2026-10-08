#!/usr/bin/env python3
"""Source-locked multi-producer attribution probe for deferred RulePatch."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
OVERRIDE=os.environ.get("OCELot_NATIVE_IMPORT_ROOT")
if OVERRIDE: sys.path.insert(0,OVERRIDE)
RUNNER=Path(__file__).resolve()
PREREG=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_DEFERRED_RULE_PATCH_ATTRIBUTION_V1_PREREG_20261002.md"
ANALYZER=ROOT/"evaluation/substrate_capability/analyze_thoughtexperiment_deferred_rule_patch_attribution_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_deferred_rule_patch_attribution_v1_lock_20261002.json"
CAPTURE=ROOT/"evaluation/reports/thoughtexperiment_deferred_rule_patch_attribution_v1_20261002.json"
SOURCES=("runners/dsl/src/graph.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs")
WORKERS=3
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,PREREG,ANALYZER,*(ROOT/p for p in SOURCES)); b=Path(_native.__file__).resolve()
 return {"files":{str(p.relative_to(ROOT)):sha(p) for p in files},"native_binary":{"path":str(b),"sha256":sha(b)}}
def make_case():
 from substrate_rs import _native
 s=_native.Substrate()
 target=s.add_rule({"name":"patch_target","match":[],"where":{"type":"Lit","value":False},"effects":[]})
 meta=s.rule_metadata(target)
 anchor=s.add_node("Anchor",{"done_alpha":False,"done_beta":False})
 patch=s.add_node("RulePatch",{"target_uid":meta["rule_uid"],"expected_revision":meta["revision"],
  "expected_content_hash":meta["content_hash"],"field":"where","proposed_clause":{"type":"Lit","value":True}})
 s.add_edge_unchecked(anchor,"has_patch",patch)
 for name,flag in (("submit_alpha","done_alpha"),("submit_beta","done_beta")):
  s.add_rule({"name":name,"match":[["a","has_patch","p"]],
   "where":{"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"a"},"key":flag},"b":{"type":"Lit","value":False}},
   "effects":[["apply_rule_patch","p"],["set_attr","a",flag,True]]})
 before=s.export_rules_prefix("patch_target")[0]
 return s,patch,int(patch.value),before
def summary(r): return {k:r.get(k) for k in ("status","progress_steps","passes_completed")}
def edges(r): return {tuple((int(e[0]),str(e[1]),int(e[2]))) for e in r["affected_edges"]}
def execute():
 s,patch,pid,before=make_case(); traced=s.run_rules_delta_report(1000,False)
 sx,_,_,_=make_case(); exact=sx.run_rules_snapshot_delta_report(1000,False)
 sp,_,_,_=make_case(); plain=sp.run_rules_report(1000,False)
 event=traced["rule_write_events"]; deferred=[e for e in event if e["deferred"]]
 target_after=s.export_rules_prefix("patch_target")[0]; patch_attrs=s.node(patch)["attrs"]
 en={int(n) for e in event for n in e["node_ids"]}; ee={tuple((int(x[0]),str(x[1]),int(x[2]))) for e in event for x in e["edges"]}
 exn=set(map(int,exact["affected_nodes"])); exe=edges(exact)
 status=patch_attrs.get("status"); status=status.get("value") if isinstance(status,dict) else status
 return {"plain":summary(plain),"traced":summary(traced),"exact":summary(exact),"events":event,"deferred_events":deferred,
  "producer_names":sorted({name for e in deferred for name in e.get("origin_rules",[e["rule_name"]])}),
  "expected_producers":["submit_alpha","submit_beta"],"patch_status":status,
  "target_revision_before":before["revision"],"target_revision_after":target_after["revision"],
  "target_changed":before!=target_after,"exact_patch_node_covered":pid in en,
  "event_covers_exact_nodes":exn<=en,"event_covers_exact_edges":exe<=ee,
  "aggregate_covers_event_nodes":en<=set(map(int,traced["affected_nodes"])),"aggregate_covers_event_edges":ee<=edges(traced),
  "dropped_events":int(traced["rule_write_events_dropped"])}
def worker(i):
 expected=json.loads(LOCK.read_text())["sources"]; before=frozen()
 if before!=expected: raise RuntimeError("source/native fingerprint differs from lock")
 result=execute(); after=frozen()
 return {"worker_index":i,"pid":os.getpid(),"sources_before":before,"sources_after":after,"source_stable":before==after,"result":result}
def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker": print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":"))); return 0
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or CAPTURE.exists(): raise SystemExit("refusing to overwrite lock or capture")
  LOCK.write_text(json.dumps({"schema":"DeferredRulePatchAttributionV1Lock","sources":frozen(),"workers":WORKERS},indent=2,sort_keys=True)+"\n"); print(LOCK.relative_to(ROOT)); return 0
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
 CAPTURE.write_text(json.dumps({"schema":"DeferredRulePatchAttributionV1Results","lock_sha256":sha(LOCK),"captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"host":platform.platform(),"workers":ws},indent=2,sort_keys=True)+"\n"); print(CAPTURE.relative_to(ROOT)); return 0
if __name__=="__main__": raise SystemExit(main())
