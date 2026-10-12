#!/usr/bin/env python3
"""Higher-multiplicity join-order sweep with match-clause candidate attribution."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
from substrate_rs import Substrate,_native
from domains.engine_provenance import assert_measuring_engine
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_JOIN_MULTIPLICITY_CLAUSE_ATTRIBUTION_V1_1_PREREG_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/join_multiplicity_clause_attribution_v1_1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_join_multiplicity_clause_attribution_v1_1_20260926.json"
RAW=ROOT/"evaluation/reports/substrate_join_multiplicity_clause_attribution_v1_1_workers_raw_20260926.json"
SOURCES=("runners/dsl/src/scale_audit.rs","runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/py.rs","runners/dsl/src/framebuffer.rs","runners/dsl/src/graph.rs")
PREDECESSORS=("scripts/substrate_join_multiplicity_deferred_queue_v1.py","scripts/analyze_substrate_join_multiplicity_deferred_queue_v1.py","docs/research/engine_substrate/SUBSTRATE_JOIN_MULTIPLICITY_DEFERRED_QUEUE_V1_RESULTS_20260926.md","evaluation/reports/substrate_join_multiplicity_deferred_queue_v1_analysis_20260926.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 paths=(*SOURCES,*PREDECESSORS,"scripts/substrate_join_multiplicity_clause_attribution_v1_1.py","scripts/analyze_substrate_join_multiplicity_clause_attribution_v1_1.py",str(PROTOCOL.relative_to(ROOT)),"runners/dsl/python/substrate_rs/_native.build.json")
 return {"files":{p:sha(ROOT/p) for p in paths},"native_extension":sha(Path(_native.__file__).resolve()),"native_path":str(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def write_frame(path):
 buf=bytearray(128);buf[:4]=(0x4A425746).to_bytes(4,"little");buf[4:8]=(1).to_bytes(4,"little");buf[8:12]=(4).to_bytes(4,"little");buf[12:16]=(4).to_bytes(4,"little");buf[16:20]=(16).to_bytes(4,"little");buf[20:24]=(1).to_bytes(4,"little");buf[24:32]=(1).to_bytes(8,"little")
 for i in range(64,len(buf),4):buf[i:i+4]=bytes((20,40,60,255))
 Path(path).write_bytes(buf)
def arm(r,m,order,shm_name,audit):
 s=Substrate();fb=s._inner.fb_attach(shm_name);writers=[]
 for j in range(r):
  a=s.add_node("JoinAnchor",{});b=s.add_node("JoinTarget",{});g=s.add_node("WorldInstance",{"world_type":"Game","frame":0.0,"last_looked_seq":-1.0})
  s._inner.add_edge_unchecked(a,f"trigger_{j}",b);s._inner.add_edge_unchecked(a,f"has_game_{j}",g);s._inner.add_edge_unchecked(b,f"wants_{j}",g)
  for k in range(m):
   mid=s.add_node("JoinMiddle",{"ordinal":k});s._inner.add_edge_unchecked(a,f"left_{j}",mid);s._inner.add_edge_unchecked(mid,f"right_{j}",b)
  target=f"join_target_{j}";writer=f"join_writer_{j}"
  s._inner.add_rule({"name":target,"match":[["x",f"wants_{j}","g"]],"where":{"type":"Lit","value":False},"effects":[["add_edge","x",f"seen_{j}","g",{}]]})
  edges={"trigger":["a",f"trigger_{j}","b"],"left":["a",f"left_{j}","mid"],"right":["mid",f"right_{j}","b"],"game":["a",f"has_game_{j}","g"]}
  order_names=("trigger","left","right","game") if order=="trigger_left_right" else ("trigger","right","left","game")
  wi=s._inner.add_rule({"name":writer,"match":[edges[x] for x in order_names],"effects":[["set_rule_clause",target,"where",{"type":"Lit","value":True}],["fb_sample",fb,"g",2,2],["del_edge","a",f"trigger_{j}","b"]]});writers.append({"rule_index":wi,"name":writer})
 installed_match=[list(edge) for edge in s._inner.export_rules()[writers[0]["rule_index"]]["match"]]
 native=_native.Substrate;native.scale_audit_set_enabled(False);native.scale_audit_set_per_rule_enabled(False);native.scale_audit_reset();native.scale_audit_per_rule_reset()
 if audit:native.scale_audit_set_per_rule_enabled(True);native.scale_audit_set_enabled(True)
 report=s._inner.run_rules_report(1000000,False)
 counters=dict(native.scale_audit_snapshot()) if audit else {};per_rule=[list(x) for x in native.scale_audit_per_rule_snapshot()] if audit else [];clause_rows=[list(x) for x in native.scale_audit_match_clause_snapshot()] if audit else []
 native.scale_audit_set_enabled(False);native.scale_audit_set_per_rule_enabled(False)
 graph=s.graph_to_dict();edges_out=graph["edges"]
 return {"report":{k:report[k] for k in ("status","progress_steps","passes_completed","budget_overshoot")},"graph":graph,"seen_edges":sum(e["type"].startswith("seen_") for e in edges_out),"grid_cells":sum(x["type"]=="WorldInstance" and "row" in x["attrs"] for x in graph["nodes"]),"trigger_edges":sum(e["type"].startswith("trigger_") for e in edges_out),"writers":writers,"counters":counters,"per_rule":per_rule,"match_clause_candidates":clause_rows,"authored_match_order":order_names,"installed_match":installed_match}
def worker(r,m,order,rep):
 path=f"/dev/shm/ocelot_join_clause_{os.getpid()}_{r}_{m}";name="/"+Path(path).name
 try:
  write_frame(path);before=fingerprint();plain=arm(r,m,order,name,False);audit=arm(r,m,order,name,True);return {"rules":r,"multiplicity":m,"order":order,"replicate":rep,"pid":os.getpid(),"before":before,"after":fingerprint(),"plain":plain,"audit":audit}
 finally:Path(path).unlink(missing_ok=True)
def main():
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],int(sys.argv[5])),sort_keys=True));return
 assert_measuring_engine()
 if sys.argv[1:]==["--lock"]:LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=locked:raise SystemExit("missing or stale source/native lock")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));started=datetime.now(timezone.utc).isoformat();runs=[]
 for r in (1,8):
  for m in (1,4,16,32,64):
   for order in ("trigger_left_right","trigger_right_left"):
    for rep in range(3):
     p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(r),str(m),order,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post=fingerprint();raw={"schema_version":1,"run_id":"substrate-join-multiplicity-clause-attribution-v1.1-20260926","started_utc":started,"locked_inputs":locked,"post_run_inputs":post,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 summary={"schema_version":1,"raw_workers_path":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"all_worker_inputs_stable":post==locked and all(x["before"]==locked==x["after"] for x in runs),"worker_count":len(runs)};OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=="__main__":main()
