#!/usr/bin/env python3
"""Check full-closure fallback for queued native NetCollapse writes."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SCOPED_NET_COLLAPSE_FALLBACK_PREREG_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/scoped_net_collapse_fallback_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_scoped_net_collapse_fallback_v1_20260926.json"
SIZES=(1,2,4);REPS=2;CAP=20000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def worker(count,arm):
 from substrate_rs import Substrate,And,Attr,Eq,Lit,Var,_native
 from substrate_rs.ext import add_rule
 s=Substrate();controller=s.add_node("Microtheory",{"name":"net_controller"});anchor=s.add_node("Anchor",{})
 s.add_edge_unchecked(controller,"has_concept",anchor);s.add_edge_unchecked(anchor,"net_update_anchor",anchor)
 frame_states=[]
 for i in range(count):
  frame=s.add_node("Microtheory",{"name":f"consumer_{i}"})
  asm=s.add_node("NetworkAssemblage",{"input_dim":1,"output_dim":1})
  step=s.add_node("AssemblageStep",{"order":0,"dim_behavior":"transform"});s.add_edge_unchecked(asm,"has_step",step)
  weights={"W1":[[1.0]],"b1":[0.0],"W2":[[0.0]],"b2":[0.0]};wids={}
  for role,data in weights.items():
   wt=s.add_node("WeightTensor",{"role":role,"data":data});s.add_edge_unchecked(step,"has_weight",wt);s.add_edge_unchecked(frame,"has_concept",wt);wids[role]=wt
  rn=s.add_node("ReflexNet",{"status":"self_training","eta":0.1,"surprise":0.0});s.add_edge_unchecked(rn,"net_assemblage",asm)
  obs=s.add_node("ReflexObservation",{"status":"pending","input_vec":[1.0],"target":[1.0]})
  s.add_edge_unchecked(controller,"has_concept",obs);s.add_edge_unchecked(obs,"observes",rn)
  frame_states.append({"frame":frame,"asm":asm,"rn":rn,"obs":obs,"weights":wids})
 add_rule(s._inner,"scoped_deferred_net_collapse",
  [("controller","has_concept","obs"),("obs","observes","rn"),("rn","net_assemblage","asm"),("controller","has_concept","anchor"),("anchor","net_update_anchor","anchor")],
  [["net_collapse","rn",{"__term__":{"type":"Attr","node":{"type":"Var","name":"obs"},"key":"input_vec"}},{"__term__":{"type":"Attr","node":{"type":"Var","name":"obs"},"key":"target"}},{"__term__":{"type":"Attr","node":{"type":"Var","name":"rn"},"key":"eta"}}],
   ["set_attr","obs","status","consumed"]],
  where=And([Eq(Attr(Var("obs"),"status"),Lit("pending")),Eq(Attr(Var("rn"),"status"),Lit("self_training"))]))
 scoped=None;global_report=None
 if arm=="full":global_report=s._inner.run_rules_report(CAP,False)
 else:
  scoped=s._inner.run_rules_scoped_delta_report(controller,1,False)
  if arm=="scoped_fallback" and scoped["deferred_effects_pending"]:global_report=s._inner.run_rules_report(CAP,False)
 def projection():
  rows=[]
  for x in frame_states:
   rows.append({"w2":s.node(x["weights"]["W2"])["attrs"].get("data"),"b2":s.node(x["weights"]["b2"])["attrs"].get("data"),
    "surprise":s.node(x["rn"])["attrs"].get("surprise"),"observation_status":s.node(x["obs"])["attrs"].get("status")})
  return {"nets":rows,"anchor_done":s.node(anchor)["attrs"].get("tracking_done")}
 state=projection()
 if arm in ("full","scoped_fallback"):
  terminal=s._inner.run_rules_report(CAP,False);terminal_status=terminal["status"];terminal_progress=terminal["progress_steps"]
 else:terminal_status=None;terminal_progress=None
 result={"count":count,"frame_count":count,"arm":arm,"pid":os.getpid(),"state":state,
  "scoped_report":None if scoped is None else {"progress_steps":scoped["progress_steps"],"hit_progress_budget":scoped["hit_progress_budget"],"deferred_effects_pending":scoped["deferred_effects_pending"],"affected_microtheories":scoped["affected_microtheories"]},
  "global_report":global_report,"terminal_status":terminal_status,"terminal_progress":terminal_progress,
  "native_extension_sha256":sha(Path(_native.__file__).resolve())}
 return result

def inputs():
 ps={"protocol":PROTOCOL,"runner":Path(__file__).resolve(),"analyzer":ROOT/"scripts/analyze_substrate_scoped_net_collapse_fallback_v1.py",
 "rewrite":ROOT/"runners/dsl/src/rewrite.rs","substrate":ROOT/"runners/dsl/src/substrate.rs","net_forward":ROOT/"runners/dsl/src/net_forward.rs","py_binding":ROOT/"runners/dsl/src/py.rs","native_build_manifest":ROOT/"runners/dsl/python/substrate_rs/_native.build.json"}
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
    print(f"nets={n} rep={rep} arm={arm} pending={None if row['scoped_report'] is None else row['scoped_report']['deferred_effects_pending']}",flush=True)
 payload={"schema_version":1,"run_id":"scoped-net-collapse-fallback-v1-20260926","locked_inputs":locked,"runs":runs,"claim_boundary":"one deterministic NetCollapse queue fixture; explicit full fallback only"}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(f"raw report: {OUT.relative_to(ROOT)} ({len(runs)} workers)")
if __name__=="__main__":main()
