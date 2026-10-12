#!/usr/bin/env python3
"""Measure an endpoint-degree order oracle against the install-time count tie."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,time
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
from substrate_rs import Substrate,_native
from domains.engine_provenance import assert_measuring_engine
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_ENDPOINT_DEGREE_JOIN_ORDER_V1_PREREG_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/endpoint_degree_join_order_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_endpoint_degree_join_order_v1_20260926.json"
RAW=ROOT/"evaluation/reports/substrate_endpoint_degree_join_order_v1_workers_raw_20260926.json"
SOURCES=("runners/dsl/src/scale_audit.rs","runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/py.rs","runners/dsl/src/framebuffer.rs","runners/dsl/src/graph.rs")
PREDECESSORS=("docs/research/engine_substrate/SUBSTRATE_JOIN_DEGREE_SKEW_V1_RESULTS_20260926.md","evaluation/reports/substrate_join_degree_skew_v1_analysis_20260926.json","scripts/substrate_join_degree_skew_v1.py","scripts/analyze_substrate_join_degree_skew_v1.py")
FAMILIES=("rule_edits","fb_samples")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 paths=(*SOURCES,*PREDECESSORS,"scripts/substrate_endpoint_degree_join_order_v1.py","scripts/analyze_substrate_endpoint_degree_join_order_v1.py",str(PROTOCOL.relative_to(ROOT)),"runners/dsl/python/substrate_rs/_native.build.json")
 return {"files":{p:sha(ROOT/p) for p in paths},"native_extension":sha(Path(_native.__file__).resolve()),"native_path":str(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def write_frame(path):
 buf=bytearray(128);buf[:4]=(0x4A425746).to_bytes(4,"little");buf[4:8]=(1).to_bytes(4,"little");buf[8:12]=(4).to_bytes(4,"little");buf[12:16]=(4).to_bytes(4,"little");buf[16:20]=(16).to_bytes(4,"little");buf[20:24]=(1).to_bytes(4,"little");buf[24:32]=(1).to_bytes(8,"little")
 for i in range(64,len(buf),4):buf[i:i+4]=bytes((20,40,60,255))
 Path(path).write_bytes(buf)
def estimate(left_edges,right_edges,a,b):
 c0=time.process_time_ns();t0=time.perf_counter_ns();candidates_left=[t for s,t in left_edges if s==a];candidates_right=[s for s,t in right_edges if t==b];right_out=Counter(s for s,_ in right_edges);left_out=Counter(s for s,_ in left_edges)
 left_then_right=len(candidates_left)+sum(right_out[mid] for mid in candidates_left)
 right_then_left=len(candidates_right)+sum(left_out[a] for _ in candidates_right)
 elapsed=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-c0
 return {"left_then_right":left_then_right,"right_then_left":right_then_left,"selected":"left_then_right" if left_then_right<=right_then_left else "right_then_left","work_items":len(left_edges)+len(right_edges)+len(candidates_left)+len(candidates_right),"planning_cpu_ns":cpu,"planning_wall_ns":elapsed}
def arm(m,q,policy,shm_name,audit):
 s=Substrate();fb=s._inner.fb_attach(shm_name);a=s.add_node("JoinAnchor",{});b=s.add_node("JoinTarget",{});g=s.add_node("WorldInstance",{"world_type":"Game","frame":0.0,"last_looked_seq":-1.0})
 s._inner.add_edge_unchecked(a,"trigger",b);s._inner.add_edge_unchecked(a,"has_game",g);s._inner.add_edge_unchecked(b,"wants",g);left_edges=[];right_edges=[]
 for k in range(m):
  mid=s.add_node("JoinMiddle",{"ordinal":k,"kind":"true"});s._inner.add_edge_unchecked(a,"left",mid);s._inner.add_edge_unchecked(mid,"right",b);left_edges.append((a,mid));right_edges.append((mid,b))
 decoys=q*m//2
 for k in range(decoys):
  mid=s.add_node("JoinMiddle",{"ordinal":k,"kind":"left_decoy"});s._inner.add_edge_unchecked(a,"left",mid);left_edges.append((a,mid))
 for k in range(decoys):
  mid=s.add_node("JoinMiddle",{"ordinal":k,"kind":"right_decoy"});s._inner.add_edge_unchecked(mid,"right",b);right_edges.append((mid,b))
 estimate_result=estimate(left_edges,right_edges,a,b) if policy=="endpoint_degree" else {"left_then_right":None,"right_then_left":None,"selected":"control_authored_order","work_items":0,"planning_cpu_ns":0,"planning_wall_ns":0}
 # The current add_rule tie handler maps authored LR to installed RL, and vice versa.
 authored="trigger_right_left" if policy=="endpoint_degree" and estimate_result["selected"]=="left_then_right" else "trigger_left_right"
 target="join_target";writer="join_writer";s._inner.add_rule({"name":target,"match":[["x","wants","g"]],"where":{"type":"Lit","value":False},"effects":[["add_edge","x","seen","g",{}]]})
 edges={"trigger":["a","trigger","b"],"left":["a","left","mid"],"right":["mid","right","b"],"game":["a","has_game","g"]};names=("trigger","right","left","game") if authored=="trigger_right_left" else ("trigger","left","right","game")
 t_install=time.perf_counter_ns();wi=s._inner.add_rule({"name":writer,"match":[edges[x] for x in names],"effects":[["set_rule_clause",target,"where",{"type":"Lit","value":True}],["fb_sample",fb,"g",2,2],["del_edge","a","trigger","b"]]});install_ns=time.perf_counter_ns()-t_install
 installed=[list(e) for e in s._inner.export_rules()[wi]["match"]]
 native=_native.Substrate;native.scale_audit_set_enabled(False);native.scale_audit_set_per_rule_enabled(False);native.scale_audit_reset();native.scale_audit_per_rule_reset()
 if audit:native.scale_audit_set_per_rule_enabled(True);native.scale_audit_set_enabled(True)
 c0=time.process_time_ns();w0=time.perf_counter_ns();report=s._inner.run_rules_report(1000000,False);closure_wall=time.perf_counter_ns()-w0;closure_cpu=time.process_time_ns()-c0
 counters=dict(native.scale_audit_snapshot()) if audit else {};per=[list(x) for x in native.scale_audit_per_rule_snapshot()] if audit else [];clauses=[list(x) for x in native.scale_audit_match_clause_snapshot()] if audit else []
 native.scale_audit_set_enabled(False);native.scale_audit_set_per_rule_enabled(False);graph=s.graph_to_dict();es=graph["edges"]
 return {"report":{k:report[k] for k in ("status","progress_steps","passes_completed","budget_overshoot")},"graph":graph,"seen_edges":sum(e["type"]=="seen" for e in es),"grid_cells":sum(n["type"]=="WorldInstance" and "row" in n["attrs"] for n in graph["nodes"]),"trigger_edges":sum(e["type"]=="trigger" for e in es),"writer_rule_index":wi,"authored_order":list(names),"installed_match":installed,"estimate":estimate_result,"install_ns":install_ns,"closure_cpu_ns":closure_cpu,"closure_wall_ns":closure_wall,"counters":counters,"per_rule":per,"match_clause_candidates":clauses}
def worker(m,q,policy,rep):
 path=f"/dev/shm/ocelot_endpoint_order_{os.getpid()}_{m}_{q}_{policy}";name="/"+Path(path).name
 try:
  write_frame(path);before=fingerprint();plain=arm(m,q,policy,name,False);audit=arm(m,q,policy,name,True);return {"multiplicity":m,"decoy_ratio":q,"policy":policy,"replicate":rep,"pid":os.getpid(),"before":before,"after":fingerprint(),"plain":plain,"audit":audit}
 finally:Path(path).unlink(missing_ok=True)
def cells():
 for m in (4,16,64):
  for q in (0,4,16):
   for policy in ("count_control","endpoint_degree"):
    for rep in range(3):yield m,q,policy,rep
def main():
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],int(sys.argv[5])),sort_keys=True));return
 assert_measuring_engine()
 if sys.argv[1:]==["--lock"]:LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=locked:raise SystemExit("missing or stale source/native lock")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));started=datetime.now(timezone.utc).isoformat();runs=[]
 for m,q,p,rep in cells():
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(m),str(q),p,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(cp.stdout))
 post=fingerprint();raw={"schema_version":1,"run_id":"substrate-endpoint-degree-join-order-v1-20260926","started_utc":started,"locked_inputs":locked,"post_run_inputs":post,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 summary={"schema_version":1,"raw_workers_path":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"all_worker_inputs_stable":post==locked and all(x["before"]==locked==x["after"] for x in runs),"worker_count":len(runs)};OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=="__main__":main()
