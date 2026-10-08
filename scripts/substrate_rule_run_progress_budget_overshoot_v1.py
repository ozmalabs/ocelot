#!/usr/bin/env python3
"""Measure scheduler-pass overshoot of the rule progress budget."""
import argparse,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_RULE_RUN_PROGRESS_BUDGET_OVERSHOOT_V1_PREREG_20260928.md";ANALYZER=ROOT/"scripts/analyze_substrate_rule_run_progress_budget_overshoot_v1.py";LOCK=ROOT/"evaluation/substrate_capability/rule_run_progress_budget_overshoot_v1_lock_20260928.json";RAW=ROOT/"evaluation/reports/rule_run_progress_budget_overshoot_v1_20260928.json";SIZES=(1,2,4,8,16,32,64)
SOURCES=("runners/dsl/src/substrate.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/py.rs","runners/dsl/src/scale_audit.rs","runners/dsl/python/substrate_rs/__init__.py","scripts/substrate_rule_run_progress_budget_overshoot_v1.py","scripts/analyze_substrate_rule_run_progress_budget_overshoot_v1.py","docs/research/engine_substrate/SUBSTRATE_RULE_RUN_PROGRESS_BUDGET_OVERSHOOT_V1_PREREG_20260928.md")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 ext=Path(_native.__file__).resolve()
 return {"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"source_sha256":{x:sha(ROOT/x) for x in SOURCES},"native_extension_path":str(ext),"native_extension_sha256":sha(ext),"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json")}
def audit(fn):
 from substrate_rs import _native
 a=_native.Substrate;a.scale_audit_reset();a.scale_audit_set_enabled(True);t=time.perf_counter_ns();v=fn();dt=time.perf_counter_ns()-t;m=dict(a.scale_audit_snapshot());a.scale_audit_set_enabled(False);return dict(v),dt,{k:v for k,v in m.items() if v}
def cell(n):
 from substrate_rs import Substrate
 s=Substrate();g=s._inner;t=g.add_node("BudgetTarget",{});x=g.add_node("BudgetTrigger",{});g.add_edge_unchecked(x,"fires",t,{})
 for i in range(n):g.add_rule({"name":f"write_{i:03d}","match":[["x","fires","t"]],"where":None,"effects":[["set_attr_if_different","t",f"written_{i:03d}",i+1]]})
 first,ns1,m1=audit(lambda:g.run_rules_report(1,True));attrs=next(z["attrs"] for z in g.graph_to_dict()["nodes"] if int(z["id"])==t.value)
 second,ns2,m2=audit(lambda:g.run_rules_report(100000,True));attrs2=next(z["attrs"] for z in g.graph_to_dict()["nodes"] if int(z["id"])==t.value)
 return {"n":n,"first":{"report":dict(first),"elapsed_ns":ns1,"metrics":m1,"attribute_count":len(attrs),"attrs":attrs},"second":{"report":dict(second),"elapsed_ns":ns2,"metrics":m2,"attribute_count":len(attrs2),"attrs":attrs2}}
def worker(wid):
 locked=inputs()
 if json.loads(LOCK.read_text())["locked_inputs"]!=locked:raise RuntimeError("source/native lock mismatch")
 return {"worker_id":wid,"pid":os.getpid(),"platform":platform.platform(),"python":sys.version,"started_inputs":locked,"cells":[cell(n) for n in SIZES]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--worker",type=int);ap.add_argument("--write-lock",action="store_true");a=ap.parse_args()
 if a.write_lock:
  if LOCK.exists():raise SystemExit("refusing to overwrite lock")
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({"lock_id":"rule_run_progress_budget_overshoot_v1_20260928","locked_inputs":inputs(),"workers":3,"sizes":SIZES,"budget":1},indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 if a.worker is not None:print(json.dumps(worker(a.worker),sort_keys=True));return
 if RAW.exists():raise SystemExit("refusing to overwrite raw capture")
 lock=json.loads(LOCK.read_text())
 if inputs()!=lock["locked_inputs"]:raise SystemExit("source/native lock mismatch")
 runs=[]
 for wid in range(1,4):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(wid)],cwd=ROOT,text=True,capture_output=True)
  if cp.returncode:raise SystemExit(f"worker {wid} failed: {cp.stderr[-2000:]}")
  runs.append(json.loads(cp.stdout.strip().splitlines()[-1]))
 RAW.parent.mkdir(parents=True,exist_ok=True)
 with RAW.open("x") as f:f.write(json.dumps({"run_id":"rule_run_progress_budget_overshoot_v1_20260928","locked_inputs":lock["locked_inputs"],"protocol_sha256":sha(PROTOCOL),"analyzer_sha256":sha(ANALYZER),"lock_sha256":sha(LOCK),"runs":runs},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(runs),"cells_per_worker":len(runs[0]["cells"]),"raw":str(RAW.relative_to(ROOT))}))
if __name__=="__main__":main()
