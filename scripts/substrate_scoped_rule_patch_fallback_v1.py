#!/usr/bin/env python3
"""Measure graph-native RulePatch queue fallback and downstream rule parity."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_RULE_PATCH_FALLBACK_PREREG_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/scoped_rule_patch_fallback_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_scoped_rule_patch_fallback_v1_20260926.json"
SIZES=(1,2,4);REPS=2;CAP=20000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def worker(count,arm):
 from substrate_rs import Substrate,And,Attr,Eq,Lit,Not,Var,_native
 from substrate_rs.ext import add_rule
 s=Substrate();controller=s.add_node("Microtheory",{"name":"patch_controller"});signal=s.add_node("PatchSignal",{"ready":True})
 s.add_edge_unchecked(controller,"has_concept",signal)
 outputs=[];frames=[]
 for i in range(count):
  frame=s.add_node("Microtheory",{"name":f"frame_{i}"});out=s.add_node("FrameOutput",{"done":False,"frame_index":i})
  s.add_edge_unchecked(frame,"has_concept",out);s.add_edge_unchecked(signal,"targets",out);outputs.append(out);frames.append(frame)
 target_idx=add_rule(s._inner,"patch_target_rule",[("sig","targets","out")],[["set_attr","out","done",True]],where=Lit(False))
 meta=s._inner.rule_metadata(target_idx)
 patch=s.add_node("RulePatch",{"target_uid":int(meta["rule_uid"]),"expected_revision":int(meta["revision"]),
  "expected_content_hash":int(meta["content_hash"]),"field":"where","proposed_clause":{"type":"Lit","value":True},"status":"pending"})
 s.add_edge_unchecked(controller,"has_concept",patch)
 trigger=s.add_node("PatchTrigger",{"fired":False});s.add_edge_unchecked(controller,"has_concept",trigger);s.add_edge_unchecked(trigger,"uses_patch",patch)
 add_rule(s._inner,"queue_graph_rule_patch",[("c","has_concept","p"),("t","uses_patch","p"),("c","has_concept","t")],
  [["apply_rule_patch","p"],["set_attr","t","fired",True]],
  where=And([Eq(Attr(Var("p"),"status"),Lit("pending")),Not(Eq(Attr(Var("t"),"fired"),Lit(True)))]))
 scoped=None;global_report=None
 if arm=="full":global_report=s._inner.run_rules_report(CAP,False)
 else:
  scoped=s._inner.run_rules_scoped_delta_report(controller,1,False)
  if arm=="scoped_fallback" and scoped["deferred_effects_pending"]:global_report=s._inner.run_rules_report(CAP,False)
 after=s._inner.rule_metadata(target_idx)
 state={"target_revision":int(after["revision"]),"target_content_hash":int(after["content_hash"]),
  "patch_status":s.node(patch)["attrs"].get("status"),"patch_reason":s.node(patch)["attrs"].get("reason"),
  "patch_result_revision":s.node(patch)["attrs"].get("result_revision"),"trigger_fired":s.node(trigger)["attrs"].get("fired"),
  "outputs":[s.node(x)["attrs"].get("done") for x in outputs]}
 if arm in ("full","scoped_fallback"):
  terminal=s._inner.run_rules_report(CAP,False);terminal_status=terminal["status"];terminal_progress=terminal["progress_steps"]
 else:terminal_status=None;terminal_progress=None
 return {"count":count,"arm":arm,"pid":os.getpid(),"state":state,
  "initial_rule_metadata":{"uid":int(meta["rule_uid"]),"revision":int(meta["revision"]),"content_hash":int(meta["content_hash"])},
  "scoped_report":None if scoped is None else {"progress_steps":scoped["progress_steps"],"hit_progress_budget":scoped["hit_progress_budget"],"deferred_effects_pending":scoped["deferred_effects_pending"]},
  "global_report":global_report,"terminal_status":terminal_status,"terminal_progress":terminal_progress,
  "native_extension_sha256":sha(Path(_native.__file__).resolve())}

def inputs():
 ps={"protocol":PROTOCOL,"runner":Path(__file__).resolve(),"analyzer":ROOT/"scripts/analyze_substrate_scoped_rule_patch_fallback_v1.py",
 "rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs","graph_rules":ROOT/"runners/dsl/src/graph_rules.rs","py_binding":ROOT/"runners/dsl/src/py.rs","native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json"}
 return {k:sha(v) for k,v in ps.items()}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps(inputs(),indent=2,sort_keys=True));return
 if len(sys.argv)==4 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),sys.argv[3]),sort_keys=True));return
 locked=inputs()
 if json.loads(LOCK.read_text())!=locked:raise SystemExit("input lock mismatch")
 env=dict(os.environ);env["PYTHONPATH"]=f"{ROOT/'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH','')}"
 runs=[]
 for n in SIZES:
  for rep in range(REPS):
   for arm in ("full","scoped_only","scoped_fallback"):
    row=json.loads(subprocess.check_output([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),arm],cwd=ROOT,env=env,text=True));row["replicate"]=rep;runs.append(row)
    print(f"frames={n} rep={rep} arm={arm} pending={None if row['scoped_report'] is None else row['scoped_report']['deferred_effects_pending']}",flush=True)
 payload={"schema_version":1,"run_id":"scoped-rule-patch-fallback-v1-20260926","locked_inputs":locked,"runs":runs,"claim_boundary":"one graph-native RulePatch transaction with conditional full-closure fallback"}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(f"raw report: {OUT.relative_to(ROOT)} ({len(runs)} workers)")
if __name__=="__main__":main()
