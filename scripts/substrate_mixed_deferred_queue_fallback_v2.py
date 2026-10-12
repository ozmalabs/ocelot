#!/usr/bin/env python3
"""Measure queue enqueue/drain attribution for RulePatch, TrackIdentity, and NetCollapse."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
from substrate_rs import _native
from domains.engine_provenance import assert_measuring_engine
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_DEFERRED_QUEUE_AUDIT_V2_PREREG_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/deferred_queue_audit_v2_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_deferred_queue_audit_v2_20260926.json"
COUNTS=(1,2,4);REPS=2;CAP=20000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def worker(count,arm):
 from substrate_rs import Substrate,And,Attr,Eq,Lit,Not,Var,_native
 from substrate_rs.ext import add_rule
 s=Substrate();controller=s.add_node("Microtheory",{"name":"mixed_controller"});anchor=s.add_node("MixedTrigger",{"fired":False})
 s.add_edge_unchecked(controller,"has_concept",anchor);s.add_edge_unchecked(anchor,"trigger_anchor",anchor)
 prev=[];cur=[];outputs=[];frames=[]
 signal=s.add_node("PatchSignal",{})
 for i in range(count):
  fp=s.add_node("Microtheory",{"name":f"prev_frame_{i}"});fc=s.add_node("Microtheory",{"name":f"cur_frame_{i}"})
  p=s.add_node("PrevPercept",{"feat":[float(i*10),0.0]});q=s.add_node("CurPercept",{"feat":[float(i*10)+0.05,0.05]})
  s.add_edge_unchecked(fp,"has_concept",p);s.add_edge_unchecked(fc,"has_concept",q);prev.append(p);cur.append(q);frames.extend([fp,fc])
  out=s.add_node("FrameOutput",{"done":False,"frame_index":i});s.add_edge_unchecked(fc,"has_concept",out);s.add_edge_unchecked(signal,"targets",out);outputs.append(out)
 target_idx=add_rule(s._inner,"mixed_patch_target",[("sig","targets","out")],[["set_attr","out","done",True]],where=Lit(False))
 meta=s._inner.rule_metadata(target_idx)
 patch_node=s.add_node("RulePatch",{"target_uid":int(meta["rule_uid"]),"expected_revision":int(meta["revision"]),
  "expected_content_hash":int(meta["content_hash"]),"field":"where","proposed_clause":{"type":"Lit","value":True},"status":"pending"})
 s.add_edge_unchecked(anchor,"has_patch",patch_node)
 asm=s.add_node("NetworkAssemblage",{"input_dim":1,"output_dim":1});step=s.add_node("AssemblageStep",{"order":0,"dim_behavior":"transform"});s.add_edge_unchecked(asm,"has_step",step)
 weight_ids={}
 for role,data in {"W1":[[1.0]],"b1":[0.0],"W2":[[0.0]],"b2":[0.0]}.items():
  wt=s.add_node("WeightTensor",{"role":role,"data":data});s.add_edge_unchecked(step,"has_weight",wt);s.add_edge_unchecked(frames[0],"has_concept",wt);weight_ids[role]=wt
 rn=s.add_node("ReflexNet",{"status":"self_training","eta":0.1,"surprise":0.0});s.add_edge_unchecked(rn,"net_assemblage",asm)
 obs=s.add_node("ReflexObservation",{"status":"pending","input_vec":[1.0],"target":[1.0]});s.add_edge_unchecked(anchor,"has_observation",obs);s.add_edge_unchecked(obs,"observes",rn)
 writer_idx=add_rule(s._inner,"mixed_deferred_writer",
  [("c","has_concept","a"),("a","trigger_anchor","a"),("a","has_patch","p"),("a","has_observation","obs"),("obs","observes","rn")],
  [["apply_rule_patch","p"],
   ["track_identity",{"__term__":{"type":"NodesOfType","node_type":"PrevPercept"}},{"__term__":{"type":"NodesOfType","node_type":"CurPercept"}},"feat",None,None,"identity",1.0],
   ["net_collapse","rn",{"__term__":{"type":"Attr","node":{"type":"Var","name":"obs"},"key":"input_vec"}},{"__term__":{"type":"Attr","node":{"type":"Var","name":"obs"},"key":"target"}},{"__term__":{"type":"Attr","node":{"type":"Var","name":"rn"},"key":"eta"}}],
   ["set_attr","a","fired",True], ["set_attr","obs","status","consumed"]],
  where=Not(Eq(Attr(Var("a"),"fired"),Lit(True))))
 def audit_begin():
  _native.Substrate.scale_audit_set_enabled(False)
  _native.Substrate.scale_audit_reset()
  _native.Substrate.scale_audit_set_per_rule_enabled(True)
  _native.Substrate.scale_audit_set_enabled(True)
 def audit_end():
  _native.Substrate.scale_audit_set_enabled(False)
  rows={"global":dict(_native.Substrate.scale_audit_snapshot()),
        "per_rule":[list(row) for row in _native.Substrate.scale_audit_per_rule_snapshot()]}
  _native.Substrate.scale_audit_set_per_rule_enabled(False)
  return rows
 scoped=None;global_report=None;audits={}
 if arm=="full":
  audit_begin();global_report=s._inner.run_rules_report(CAP,False);audits["full"]=audit_end()
 else:
  audit_begin();scoped=s._inner.run_rules_scoped_delta_report(controller,1,False);audits["scoped"]=audit_end()
  if arm=="scoped_fallback" and scoped["deferred_effects_pending"]:
   audit_begin();global_report=s._inner.run_rules_report(CAP,False);audits["fallback"]=audit_end()
 metadata=s._inner.rule_metadata(target_idx)
 state={"target_revision":int(metadata["revision"]),"target_content_hash":int(metadata["content_hash"]),
  "patch_status":s.node(patch_node)["attrs"].get("status"),"patch_reason":s.node(patch_node)["attrs"].get("reason"),
  "patch_result_revision":s.node(patch_node)["attrs"].get("result_revision"),"trigger_fired":s.node(anchor)["attrs"].get("fired"),
  "observation_status":s.node(obs)["attrs"].get("status"),"identities":{"previous":s._inner.get_attr_many(prev,"identity"),"current":s._inner.get_attr_many(cur,"identity")},
  "weights":{"W2":s.node(weight_ids["W2"])["attrs"].get("data"),"b2":s.node(weight_ids["b2"])["attrs"].get("data")},
  "surprise":s.node(rn)["attrs"].get("surprise"),"outputs":[s.node(x)["attrs"].get("done") for x in outputs]}
 if arm in ("full","scoped_fallback"):
  terminal=s._inner.run_rules_report(CAP,False);terminal_status=terminal["status"];terminal_progress=terminal["progress_steps"]
 else:terminal_status=None;terminal_progress=None
 return {"count":count,"arm":arm,"pid":os.getpid(),"writer_rule_index":int(writer_idx),"state":state,"audits":audits,
  "scoped_report":None if scoped is None else {"progress_steps":scoped["progress_steps"],"hit_progress_budget":scoped["hit_progress_budget"],"deferred_effects_pending":scoped["deferred_effects_pending"]},
  "global_report":global_report,"terminal_status":terminal_status,"terminal_progress":terminal_progress,
  "native_extension_sha256":sha(Path(_native.__file__).resolve())}

def inputs():
 ps={"protocol":PROTOCOL,"runner":Path(__file__).resolve(),"analyzer":ROOT/"scripts/analyze_substrate_deferred_queue_audit_v2.py",
 "rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs","graph_rules":ROOT/"runners/dsl/src/graph_rules.rs","net_forward":ROOT/"runners/dsl/src/net_forward.rs","scale_audit":ROOT/"runners/dsl/src/scale_audit.rs","term":ROOT/"runners/dsl/src/term.rs","py_binding":ROOT/"runners/dsl/src/py.rs","native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json","native_extension":Path(_native.__file__).resolve()}
 return {k:sha(v) for k,v in ps.items()}
def main():
 if sys.argv[1:]==["--lock"]:
  locked=inputs();LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(locked,indent=2,sort_keys=True)+"\n");print(json.dumps(locked,indent=2,sort_keys=True));return
 if len(sys.argv)==4 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),sys.argv[3]),sort_keys=True));return
 assert_measuring_engine()
 locked=inputs()
 if json.loads(LOCK.read_text())!=locked:raise SystemExit("input lock mismatch")
 env=dict(os.environ);env["PYTHONPATH"]=f"{ROOT/'runners/dsl/python'}:{ROOT}:{env.get('PYTHONPATH','')}"
 runs=[]
 for n in COUNTS:
  for rep in range(REPS):
   for arm in ("full","scoped_only","scoped_fallback"):
    row=json.loads(subprocess.check_output([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),arm],cwd=ROOT,env=env,text=True));row["replicate"]=rep;runs.append(row)
    print(f"pairs={n} rep={rep} arm={arm} pending={None if row['scoped_report'] is None else row['scoped_report']['deferred_effects_pending']}",flush=True)
 post=inputs()
 payload={"schema_version":1,"run_id":"substrate-deferred-queue-audit-v2-20260926","locked_inputs":locked,"post_run_inputs":post,"runs":runs,"claim_boundary":"synthetic rule firing queues RulePatch, TrackIdentity, and NetCollapse; audits enqueue producer and between-pass drain family counts"}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(f"raw report: {OUT.relative_to(ROOT)} ({len(runs)} workers)")
if __name__=="__main__":main()
