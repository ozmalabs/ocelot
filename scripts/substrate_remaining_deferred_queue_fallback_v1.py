#!/usr/bin/env python3
"""Measure scoped pending and global fallback for RuleEdit/FbSample queues."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
from substrate_rs import Substrate,_native
from domains.engine_provenance import assert_measuring_engine
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_REMAINING_DEFERRED_QUEUE_FALLBACK_V1_PREREG_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/remaining_deferred_queue_fallback_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_remaining_deferred_queue_fallback_v1_20260926.json"
RAW=ROOT/"evaluation/reports/substrate_remaining_deferred_queue_fallback_v1_workers_raw_20260926.json"
FAMILIES=("rule_edits","fb_samples")
SOURCES=("runners/dsl/src/scale_audit.rs","runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/py.rs","runners/dsl/src/framebuffer.rs")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 paths=(*SOURCES,"scripts/substrate_remaining_deferred_queue_fallback_v1.py","scripts/analyze_substrate_remaining_deferred_queue_fallback_v1.py","scripts/substrate_remaining_deferred_queue_families_v1.py",str(PROTOCOL.relative_to(ROOT)),"runners/dsl/python/substrate_rs/_native.build.json")
 return {"files":{p:sha(ROOT/p) for p in paths},"native_extension":sha(Path(_native.__file__).resolve()),"native_path":str(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def write_frame(path):
 w=h=4;stride=16;buf=bytearray(64+w*h*4);buf[:4]=(0x4A425746).to_bytes(4,"little");buf[4:8]=(1).to_bytes(4,"little");buf[8:12]=w.to_bytes(4,"little");buf[12:16]=h.to_bytes(4,"little");buf[16:20]=stride.to_bytes(4,"little");buf[20:24]=(1).to_bytes(4,"little");buf[24:32]=(1).to_bytes(8,"little")
 for i in range(64,len(buf),4):buf[i:i+4]=bytes((20,40,60,255))
 Path(path).write_bytes(buf)
def make(n,shm_name):
 s=Substrate();fb=s._inner.fb_attach(shm_name);owner=s.add_node("Microtheory",{"name":"queue_owner"});writers=[]
 for i in range(n):
  a=s.add_node("QueueAnchor",{});b=s.add_node("QueueTarget",{});g=s.add_node("WorldInstance",{"world_type":"Game","frame":0.0,"last_looked_seq":-1.0})
  s._inner.add_edge_unchecked(owner,"has_concept",a);s._inner.add_edge_unchecked(a,f"trigger_{i}",b);s._inner.add_edge_unchecked(a,f"has_game_{i}",g);s._inner.add_edge_unchecked(b,f"wants_{i}",g)
  target=f"queue_target_{i}";writer=f"queue_writer_{i}"
  s._inner.add_rule({"name":target,"match":[["x",f"wants_{i}","g"]],"where":{"type":"Lit","value":False},"effects":[["add_edge","x",f"seen_{i}","g",{}]]})
  wi=s._inner.add_rule({"name":writer,"match":[["c","has_concept","a"],["a",f"trigger_{i}","b"],["a",f"has_game_{i}","g"]],"effects":[["set_rule_clause",target,"where",{"type":"Lit","value":True}],["fb_sample",fb,"g",2,2],["del_edge","a",f"trigger_{i}","b"]]})
  writers.append({"rule_index":wi,"name":writer})
 return s,owner,writers
def capture(n,name,arm):
 s,owner,writers=make(n,name);native=_native.Substrate
 def begin():native.scale_audit_set_enabled(False);native.scale_audit_set_per_rule_enabled(False);native.scale_audit_reset();native.scale_audit_per_rule_reset();native.scale_audit_set_per_rule_enabled(True);native.scale_audit_set_enabled(True)
 def end():
  native.scale_audit_set_enabled(False);g=dict(native.scale_audit_snapshot());p=[list(r) for r in native.scale_audit_per_rule_snapshot()];native.scale_audit_set_per_rule_enabled(False);return {"global":g,"per_rule":p}
 phases={}
 if arm=="full":
  begin();report=s._inner.run_rules_report(10000,False);phases["full"]={"report":report,"audit":end()}
 elif arm=="scoped_only":
  begin();report=s._inner.run_rules_scoped_delta_report(owner,10000,False);phases["scoped"]={"report":{k:report[k] for k in ("progress_steps","hit_progress_budget","deferred_effects_pending")},"audit":end()}
 else:
  begin();report=s._inner.run_rules_scoped_delta_report(owner,10000,False);phases["scoped"]={"report":{k:report[k] for k in ("progress_steps","hit_progress_budget","deferred_effects_pending")},"audit":end()}
  begin();fallback=s._inner.run_rules_report(10000,False);phases["fallback"]={"report":fallback,"audit":end()}
 graph=s.graph_to_dict();edges=graph["edges"];return {"arm":arm,"phases":phases,"graph":graph,"seen_edges":sum(e["type"].startswith("seen_") for e in edges),"grid_cells":sum(x["type"]=="WorldInstance" and "row" in x["attrs"] for x in graph["nodes"]),"writers":writers}
def worker(n,rep):
 path=f"/dev/shm/ocelot_queue_fallback_{os.getpid()}_{n}";name="/"+Path(path).name;write_frame(path)
 try:
  before=fingerprint();arms={a:capture(n,name,a) for a in ("full","scoped_only","scoped_fallback")};return {"n":n,"replicate":rep,"pid":os.getpid(),"before":before,"after":fingerprint(),"arms":arms}
 finally:Path(path).unlink(missing_ok=True)
def main():
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3])),sort_keys=True));return
 assert_measuring_engine()
 if sys.argv[1:]==["--lock"]:LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=locked:raise SystemExit("missing or stale source/native lock")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));started=datetime.now(timezone.utc).isoformat();runs=[]
 for n in (1,2,4,8):
  for rep in range(3):
   p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post=fingerprint();raw={"schema_version":1,"run_id":"substrate-remaining-deferred-queue-fallback-v1-20260926","started_utc":started,"locked_inputs":locked,"post_run_inputs":post,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 summary={"schema_version":1,"raw_workers_path":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"all_worker_inputs_stable":post==locked and all(r["before"]==locked==r["after"] for r in runs),"worker_count":len(runs)};OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n");print(json.dumps(summary,indent=2,sort_keys=True))
if __name__=="__main__":main()
