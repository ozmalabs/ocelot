#!/usr/bin/env python3
"""Trace all five deferred queue families under scoped closure and fallback."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
from substrate_rs import Substrate,_native
from domains.engine_provenance import assert_measuring_engine
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V5_PREREG_20261001.md"
LOCK=ROOT/"evaluation/substrate_capability/all_queue_scoped_fallback_v5_lock_20261001.json"
OUT=ROOT/"evaluation/reports/all_queue_scoped_fallback_v5_20261001.json"
RAW=ROOT/"evaluation/reports/all_queue_scoped_fallback_v5_workers_20261001.json"
SOURCES=("runners/dsl/src/scale_audit.rs","runners/dsl/src/substrate.rs","runners/dsl/src/access_trace.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/py.rs","runners/dsl/src/framebuffer.rs","runners/dsl/src/graph.rs","runners/dsl/src/term.rs","runners/dsl/src/net_forward.rs")
FAMILIES=("rule_edits","rule_patches","fb_samples","track_identity","net_collapses")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 paths=(*SOURCES,"scripts/substrate_all_queue_scoped_fallback_v5.py","scripts/analyze_substrate_all_queue_scoped_fallback_v5.py",str(PROTOCOL.relative_to(ROOT)),"runners/dsl/python/substrate_rs/_native.build.json")
 return {"files":{p:sha(ROOT/p) for p in paths},"native_extension":sha(Path(_native.__file__).resolve()),"native_path":str(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def write_frame(path):
 w=h=4;buf=bytearray(128);buf[:4]=(0x4A425746).to_bytes(4,"little");buf[4:8]=(1).to_bytes(4,"little");buf[8:12]=w.to_bytes(4,"little");buf[12:16]=h.to_bytes(4,"little");buf[16:20]=(16).to_bytes(4,"little");buf[20:24]=(1).to_bytes(4,"little");buf[24:32]=(1).to_bytes(8,"little")
 for i in range(64,len(buf),4):buf[i:i+4]=bytes((20,40,60,255))
 Path(path).write_bytes(buf)
def make(r,m,shm_name):
 s=Substrate();fb=s._inner.fb_attach(shm_name);owner=s.add_node("Microtheory",{"name":"queue_owner"});sink=s.add_node("OrderProbeSink",{});s._inner.add_edge_unchecked(owner,"has_concept",sink);writers=[]
 s._inner.add_rule({"name":"verify_scoped_join_outputs","match":[["a","handled_mid","mid"]],"effects":[["add_edge","mid","verified_by","a",{}]]})
 for i in range(r):
  a=s.add_node("JoinAnchor",{});b=s.add_node("JoinTarget",{});g=s.add_node("WorldInstance",{"world_type":"Game","frame":0.0,"last_looked_seq":-1.0})
  s._inner.add_edge_unchecked(owner,"has_concept",a);s._inner.add_edge_unchecked(a,f"trigger_{i}",b);s._inner.add_edge_unchecked(a,f"has_game_{i}",g);s._inner.add_edge_unchecked(b,f"wants_{i}",g)
  previous_type=f"PrevPercept_{i}";current_type=f"CurPercept_{i}"
  prev=s.add_node(previous_type,{"feat":[float(i*10),0.0]});cur=s.add_node(current_type,{"feat":[float(i*10)+0.05,0.05]})
  s._inner.add_edge_unchecked(a,"has_previous_percept",prev);s._inner.add_edge_unchecked(a,"has_current_percept",cur)
  assemblage=s.add_node("NetworkAssemblage",{"input_dim":1,"output_dim":1});step=s.add_node("AssemblageStep",{"order":0,"dim_behavior":"transform"});s._inner.add_edge_unchecked(assemblage,"has_step",step)
  weight_ids={}
  for role,data in {"W1":[[1.0]],"b1":[0.0],"W2":[[0.0]],"b2":[0.0]}.items():
   wt=s.add_node("WeightTensor",{"role":role,"data":data});s._inner.add_edge_unchecked(step,"has_weight",wt);s._inner.add_edge_unchecked(a,"has_concept",wt);weight_ids[role]=wt
  net=s.add_node("ReflexNet",{"status":"self_training","eta":0.1,"surprise":0.0});s._inner.add_edge_unchecked(net,"net_assemblage",assemblage)
  obs=s.add_node("ReflexObservation",{"status":"pending","input_vec":[1.0],"target":[1.0]});s._inner.add_edge_unchecked(a,"has_observation",obs);s._inner.add_edge_unchecked(obs,"observes",net)
  mids=[]
  for j in range(m):
   mid=s.add_node("JoinMiddle",{"ordinal":j});mids.append(mid);s._inner.add_edge_unchecked(a,f"left_{i}",mid);s._inner.add_edge_unchecked(mid,f"right_{i}",b);s._inner.add_edge_unchecked(mid,"has_sink",sink)
  for j,mid in enumerate(mids):s._inner.add_edge_unchecked(mid,f"next_{i}",mids[(j+1)%m])
  target=f"join_target_{i}";writer=f"join_writer_{i}"
  ti=s._inner.add_rule({"name":target,"match":[["x",f"wants_{i}","g"]],"where":{"type":"Lit","value":False},"effects":[["add_edge","x",f"seen_{i}","g",{}]]})
  meta=s._inner.rule_metadata(ti)
  patch=s.add_node("RulePatch",{"target_uid":int(meta["rule_uid"]),"expected_revision":int(meta["revision"]),"expected_content_hash":int(meta["content_hash"]),"field":"where","proposed_clause":{"type":"Lit","value":True},"status":"pending"});s._inner.add_edge_unchecked(a,"has_patch",patch)
  wi=s._inner.add_rule({"name":writer,"match":[["a",f"trigger_{i}","b"],["a",f"left_{i}","mid"],["mid",f"right_{i}","b"],["mid",f"next_{i}","next_mid"],["a",f"has_game_{i}","g"],["a","has_patch","p"],["a","has_observation","obs"],["obs","observes","rn"]],"effects":[["del_edge","next_mid",f"right_{i}","b"],["add_edge","a","handled_mid","mid",{}],["apply_rule_patch","p"],["set_rule_clause",target,"where",{"type":"Lit","value":True}],["track_identity",{"__term__":{"type":"NodesOfType","node_type":previous_type}},{"__term__":{"type":"NodesOfType","node_type":current_type}},"feat",None,None,"identity",1.0],["net_collapse","rn",{"__term__":{"type":"Attr","node":{"type":"Var","name":"obs"},"key":"input_vec"}},{"__term__":{"type":"Attr","node":{"type":"Var","name":"obs"},"key":"target"}},{"__term__":{"type":"Attr","node":{"type":"Var","name":"rn"},"key":"eta"}}],["fb_sample",fb,"g",2,2],["del_edge","a",f"trigger_{i}","b"],["set_attr","obs","status","consumed"]]})
  writers.append({"rule_index":int(wi),"target_index":int(ti),"patch":int(patch.value if hasattr(patch,"value") else patch),"game":int(g.value if hasattr(g,"value") else g)})
 s._inner.add_rule({"name":"order_sensitive_last_match","match":[["a","handled_mid","mid"],["mid","has_sink","sink"]],"where":{"type":"Not","arg":{"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"sink"},"key":"probe_done"},"b":{"type":"Lit","value":True}}},"effects":[["set_attr","sink","selected_mid",{"__term__":{"type":"Var","name":"mid"}}],["set_attr","sink","probe_done",True]]})
 return s,owner,writers,sink
def phase(s,call):
 n=_native.Substrate;n.scale_audit_set_enabled(False);n.scale_audit_set_per_rule_enabled(False);n.scale_audit_reset();n.scale_audit_per_rule_reset();n.scale_audit_set_per_rule_enabled(True);n.scale_audit_set_enabled(True);n.runtime_access_trace_reset();n.runtime_work_trace_set_all_scopes_enabled(True)
 try:report=call()
 finally:n.runtime_work_trace_set_all_scopes_enabled(False);n.scale_audit_set_enabled(False)
 rows,dropped=n.runtime_work_trace_all_scopes_snapshot();work={"dropped":int(dropped),"rows":[{"scope":int(sc),"operation_id":int(op),"producer_rule_uid":int(uid),"kind":str(k),"subject":None if sub is None else int(sub),"units":int(u)} for sc,op,uid,k,sub,u in rows]}
 counters=dict(n.scale_audit_snapshot());per_rule=[list(x) for x in n.scale_audit_per_rule_snapshot()];n.scale_audit_set_per_rule_enabled(False)
 return report,{"counters":counters,"per_rule":per_rule,"runtime_work_trace":work}
def arm(r,m,name,which):
 s,owner,writers,sink=make(r,m,name);phases={}
 if which=="full":
  report,audit=phase(s,lambda:s._inner.run_rules_report(1000000,False));phases["full"]={"report":report,"audit":audit}
 else:
  scoped,audit=phase(s,lambda:s._inner.run_rules_scoped_delta_report(owner,1000000,False));phases["scoped"]={"report":{k:scoped[k] for k in ("progress_steps","hit_progress_budget","deferred_effects_pending")},"audit":audit}
  if which=="scoped_fallback":
   fallback,audit=phase(s,lambda:s._inner.run_rules_report(1000000,False));phases["fallback"]={"report":fallback,"audit":audit}
 graph=s.graph_to_dict();edges=graph["edges"]
 sink_attrs=next(x["attrs"] for x in graph["nodes"] if x["id"]==int(sink.value if hasattr(sink,"value") else sink))
 return {"phases":phases,"graph":graph,"selected_mid":sink_attrs.get("selected_mid"),"seen_edges":sum(e["type"].startswith("seen_") for e in edges),"handled_mid_edges":sum(e["type"]=="handled_mid" for e in edges),"verified_edges":sum(e["type"]=="verified_by" for e in edges),"right_edges":sum(e["type"].startswith("right_") for e in edges),"grid_cells":sum(x["type"]=="WorldInstance" and "row" in x["attrs"] for x in graph["nodes"]),"trigger_edges":sum(e["type"].startswith("trigger_") for e in edges),"writers":writers}
def worker(r,m,rep):
 path=f"/dev/shm/ocelot_scoped_all_queue_{os.getpid()}_{r}_{m}";name="/"+Path(path).name
 try:
  write_frame(path);before=fingerprint();arms={a:arm(r,m,name,a) for a in ("full","scoped_only","scoped_fallback")};return {"rules":r,"multiplicity":m,"replicate":rep,"pid":os.getpid(),"before":before,"after":fingerprint(),"arms":arms}
 finally:Path(path).unlink(missing_ok=True)
def main():
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])),sort_keys=True));return
 assert_measuring_engine()
 if sys.argv[1:]==["--lock"]:LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=locked:raise SystemExit("missing or stale source/native lock")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));started=datetime.now(timezone.utc).isoformat();runs=[]
 for r in (1,8,32):
  for m in (1,4,16):
   for rep in range(3):
    p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(r),str(m),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post=fingerprint();raw={"schema_version":1,"run_id":"substrate-all-queue-scoped-fallback-v5-20261001","started_utc":started,"locked_inputs":locked,"post_run_inputs":post,"runs":runs};RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 summary={"schema_version":1,"raw_workers_path":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"all_worker_inputs_stable":post==locked and all(x["before"]==locked==x["after"] for x in runs),"worker_count":len(runs)};OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=="__main__":main()
