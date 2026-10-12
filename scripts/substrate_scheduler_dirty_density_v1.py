#!/usr/bin/env python3
"""Locked positive-match scheduler sweep over dirty density and slot position."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
from substrate_rs import _native
from domains.engine_provenance import assert_measuring_engine
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SCHEDULER_DIRTY_DENSITY_V1_PREREG_20260926.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_SCHEDULER_DIRTY_DENSITY_V1_AMENDMENT_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/scheduler_dirty_density_v1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/substrate_scheduler_dirty_density_v1_20260926.json"
RAW=ROOT/"evaluation/reports/substrate_scheduler_dirty_density_v1_workers_raw_20260926.json"
RULE_COUNTS=(8,32,128);REPS=3
SOURCES=("runners/dsl/src/scale_audit.rs","runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/py.rs")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 paths=(*SOURCES,"scripts/substrate_scheduler_dirty_density_v1.py","scripts/analyze_substrate_scheduler_dirty_density_v1.py",str(PROTOCOL.relative_to(ROOT)),str(AMENDMENT.relative_to(ROOT)),"runners/dsl/python/substrate_rs/_native.build.json")
 return {"files":{p:sha(ROOT/p) for p in paths},"native_extension":sha(Path(_native.__file__).resolve()),"native_path":str(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def build(n,k,position):
 s=_native.Substrate();a=s.add_node("SchedulerNode",{});b=s.add_node("SchedulerNode",{})
 for i in range(n):s.add_rule({"name":f"positive_rule_{i}","match":[["x",f"trigger_{i}","y"]],"effects":[["add_edge","x",f"derived_{i}","y",{}]]})
 s.run_rules_report(1000,False)
 selected=list(range(k)) if position=="prefix" else list(range(n-k,n))
 for i in selected:s.add_edge_unchecked(a,f"trigger_{i}",b)
 return s,selected
def phase(n,k,position,audit):
 s,selected=build(n,k,position)
 _native.Substrate.scale_audit_set_enabled(False);_native.Substrate.scale_audit_reset()
 if audit:_native.Substrate.scale_audit_set_enabled(True)
 report=s.run_rules_report(1000,False)
 _native.Substrate.scale_audit_set_enabled(False)
 graph=s.graph_to_dict()
 return {"report":{key:report[key] for key in ("status","progress_steps","passes_completed","budget_overshoot")},"graph":graph,"derived_edge_count":sum(e["type"].startswith("derived_") for e in graph["edges"]),"trigger_edge_count":sum(e["type"].startswith("trigger_") for e in graph["edges"]),"counters":dict(_native.Substrate.scale_audit_snapshot()) if audit else {},"selected":selected}
def worker(n,k,position,rep):
 before=fingerprint();cells={"plain":phase(n,k,position,False),"audit":phase(n,k,position,True)}
 return {"rule_count":n,"dirty_count":k,"position":position,"replicate":rep,"pid":os.getpid(),"before":before,"after":fingerprint(),"cells":cells}
def main():
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4],int(sys.argv[5])),sort_keys=True));return
 assert_measuring_engine()
 if sys.argv[1:]==["--lock"]:LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=locked:raise SystemExit("missing or stale source/native lock")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")))
 started=datetime.now(timezone.utc).isoformat();runs=[]
 for n in RULE_COUNTS:
  for k in sorted({1,n//4,n}):
   for pos in ("prefix","suffix"):
    for rep in range(REPS):
     p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),str(k),pos,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
     runs.append(json.loads(p.stdout))
 post=fingerprint();raw={"schema_version":1,"run_id":"substrate-scheduler-dirty-density-v1-20260926","started_utc":started,"locked_inputs":locked,"post_run_inputs":post,"runs":runs}
 RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 result={"schema_version":1,"raw_workers_path":str(RAW.relative_to(ROOT)),"locked_inputs":locked,"post_run_inputs":post,"all_worker_inputs_stable":post==locked and all(r["before"]==locked==r["after"] for r in runs),"worker_count":len(runs)}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":main()
