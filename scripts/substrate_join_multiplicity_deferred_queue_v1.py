#!/usr/bin/env python3
"""Locked two-edge join and deferred-queue multiplicity evaluation."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
from substrate_rs import Substrate,_native
from domains.engine_provenance import assert_measuring_engine
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_JOIN_MULTIPLICITY_DEFERRED_QUEUE_V1_PREREG_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/join_multiplicity_deferred_queue_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_join_multiplicity_deferred_queue_v1_20260926.json"
RAW=ROOT/"evaluation/reports/substrate_join_multiplicity_deferred_queue_v1_workers_raw_20260926.json"
SOURCES=("runners/dsl/src/scale_audit.rs","runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/py.rs","runners/dsl/src/framebuffer.rs","runners/dsl/src/graph.rs")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 paths=(*SOURCES,"scripts/substrate_join_multiplicity_deferred_queue_v1.py","scripts/analyze_substrate_join_multiplicity_deferred_queue_v1.py",str(PROTOCOL.relative_to(ROOT)),"runners/dsl/python/substrate_rs/_native.build.json")
 return {"files":{p:sha(ROOT/p) for p in paths},"native_extension":sha(Path(_native.__file__).resolve()),"native_path":str(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def write_frame(path):
 w=h=4;buf=bytearray(128);buf[:4]=(0x4A425746).to_bytes(4,"little");buf[4:8]=(1).to_bytes(4,"little");buf[8:12]=w.to_bytes(4,"little");buf[12:16]=h.to_bytes(4,"little");buf[16:20]=(16).to_bytes(4,"little");buf[20:24]=(1).to_bytes(4,"little");buf[24:32]=(1).to_bytes(8,"little")
 for i in range(64,len(buf),4):buf[i:i+4]=bytes((20,40,60,255))
 Path(path).write_bytes(buf)
def arm(r,m,shm_name,audit):
 s=Substrate();fb=s._inner.fb_attach(shm_name);writers=[]
 for i in range(r):
  a=s.add_node("JoinAnchor",{});b=s.add_node("JoinTarget",{});g=s.add_node("WorldInstance",{"world_type":"Game","frame":0.0,"last_looked_seq":-1.0})
  s._inner.add_edge_unchecked(a,f"trigger_{i}",b);s._inner.add_edge_unchecked(a,f"has_game_{i}",g);s._inner.add_edge_unchecked(b,f"wants_{i}",g)
  mids=[]
  for j in range(m):
   mid=s.add_node("JoinMiddle",{"ordinal":j});mids.append(mid);s._inner.add_edge_unchecked(a,f"left_{i}",mid);s._inner.add_edge_unchecked(mid,f"right_{i}",b)
  target=f"join_target_{i}";writer=f"join_writer_{i}"
  s._inner.add_rule({"name":target,"match":[["x",f"wants_{i}","g"]],"where":{"type":"Lit","value":False},"effects":[["add_edge","x",f"seen_{i}","g",{}]]})
  wi=s._inner.add_rule({"name":writer,"match":[["a",f"trigger_{i}","b"],["a",f"left_{i}","mid"],["mid",f"right_{i}","b"],["a",f"has_game_{i}","g"]],"effects":[["set_rule_clause",target,"where",{"type":"Lit","value":True}],["fb_sample",fb,"g",2,2],["del_edge","a",f"trigger_{i}","b"]]})
  writers.append({"rule_index":wi,"name":writer})
 native=_native.Substrate;native.scale_audit_set_enabled(False);native.scale_audit_set_per_rule_enabled(False);native.scale_audit_reset();native.scale_audit_per_rule_reset()
 if audit:native.scale_audit_set_per_rule_enabled(True);native.scale_audit_set_enabled(True)
 report=s._inner.run_rules_report(1000000,False)
 counters=dict(native.scale_audit_snapshot()) if audit else {};per_rule=[list(x) for x in native.scale_audit_per_rule_snapshot()] if audit else []
 native.scale_audit_set_enabled(False);native.scale_audit_set_per_rule_enabled(False)
 graph=s.graph_to_dict();edges=graph["edges"]
 return {"report":{k:report[k] for k in ("status","progress_steps","passes_completed","budget_overshoot")},"graph":graph,"seen_edges":sum(e["type"].startswith("seen_") for e in edges),"grid_cells":sum(x["type"]=="WorldInstance" and "row" in x["attrs"] for x in graph["nodes"]),"trigger_edges":sum(e["type"].startswith("trigger_") for e in edges),"writers":writers,"counters":counters,"per_rule":per_rule}
def worker(r,m,rep):
 path=f"/dev/shm/ocelot_join_queue_{os.getpid()}_{r}_{m}";name="/"+Path(path).name
 try:
  write_frame(path);before=fingerprint();plain=arm(r,m,name,False);audit=arm(r,m,name,True);return {"rules":r,"multiplicity":m,"replicate":rep,"pid":os.getpid(),"before":before,"after":fingerprint(),"plain":plain,"audit":audit}
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
 post=fingerprint();raw={"schema_version":1,"run_id":"substrate-join-multiplicity-deferred-queue-v1-20260926","started_utc":started,"locked_inputs":locked,"post_run_inputs":post,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 summary={"schema_version":1,"raw_workers_path":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"all_worker_inputs_stable":post==locked and all(x["before"]==locked==x["after"] for x in runs),"worker_count":len(runs)};OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=="__main__":main()
