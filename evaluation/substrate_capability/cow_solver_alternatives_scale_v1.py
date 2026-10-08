#!/usr/bin/env python3
"""Scale reusable CoW snapshots as a native CAN solver-alternative consumer."""
from __future__ import annotations
import hashlib,json,math,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as sr
from domains.engine_provenance import build_is_stale,rust_source_fingerprint
from substrate.seed_loader import engine_rules_only
from domains.can_native_orchestration import scoped_settle,native_audit_basin
SEED=ROOT/"seeds/can_native_reimplementation.json";PROTOCOL=ROOT/"docs/research/engine_substrate/COW_SOLVER_ALTERNATIVES_SCALE_V1_PREREG_20261001.md"
LOCK=ROOT/"evaluation/substrate_capability/cow_solver_alternatives_scale_v1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/cow_solver_alternatives_scale_v1_workers_20261001.json";OUT=ROOT/"evaluation/reports/cow_solver_alternatives_scale_v1_20261001.json"
ANALYZER=ROOT/"scripts/analyze_cow_solver_alternatives_scale_v1.py";RUNNER=Path(__file__).resolve()
SIZES=(32,128,256);TOPOLOGIES=("path","banded2");REPS=3;PERTURBATIONS=(-1.0,-0.25,0.5,1.25);MAX_STEPS=100000
SOURCES=("domains/can_native_orchestration.py","substrate/seed_loader.py","runners/dsl/src/rewrite.rs","runners/dsl/src/can_ops.rs","runners/dsl/src/graph.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 files=(str(RUNNER.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(SEED.relative_to(ROOT)),*SOURCES)
 return {"files":{x:sha(ROOT/x) for x in files},"native_path":str(Path(_native.__file__).resolve()),"native_sha256":sha(Path(_native.__file__).resolve()),"rust_source_fingerprint":rust_source_fingerprint(str(ROOT)),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def digest(sub):return hashlib.sha256(json.dumps({"graph":sub._inner.graph_to_dict(),"rules":sub._inner.export_rules()},sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def fixture(n,topology):
 sub=sr.Substrate();inner=sub._inner;inner.load_seed_manifest(engine_rules_only(json.loads(SEED.read_text())))
 mt=inner.add_node("Microtheory",{"temperature":2.0,"discrete_mode":"3state","can_tick":0});cs=[]
 for i in range(n):
  c=inner.add_node("Concept",{"name":f"c{i}","state":0.0,"external_field":round(0.55*math.sin(i*0.371),5),"identity_field":0.0});cs.append(c);inner.add_edge(mt,"has_concept",c,{})
 span=1 if topology=="path" else 2
 for i in range(n):
  for d in range(1,span+1):
   j=i+d
   if j>=n:continue
   w=0.5 if d==1 else (0.25 if i%2==0 else -0.25)
   inner.add_edge(cs[i],"causal_influence",cs[j],{"weight":w});inner.add_edge(cs[j],"causal_influence",cs[i],{"weight":w})
 return sub,mt,cs
def run(branch,mt,cs,value):
 native=branch._inner;native.set_attr(cs[0],"external_field",float(value));t=time.perf_counter_ns();steps=scoped_settle(native,mt,MAX_STEPS);settle_ns=time.perf_counter_ns()-t
 t=time.perf_counter_ns();terminal=scoped_settle(native,mt,1);fixed_probe_ns=time.perf_counter_ns()-t
 basin=native_audit_basin(native,mt);states=[float(native.node(c)["attrs"].get("state",0.0)) for c in cs]
 return {"input":float(value),"steps":int(steps),"terminal_progress":int(terminal),"energy":float(basin["energy"]),"frustration":float(basin["frustration"]),"coverage":int(basin["coverage"]),"states":states,"graph_digest":digest(branch),"settle_ns":settle_ns,"fixed_probe_ns":fixed_probe_ns}
def worker(n,topology,rep):
 sub,mt,cs=fixture(n,topology);base_digest=digest(sub);revision=list(sub.experiment_graph_rule_revision());base_states=[float(sub.node(c)["attrs"]["state"]) for c in cs]
 t=time.perf_counter_ns();snapshot=sub._snapshot_with_backend("shared_graph_pages");capture_ns=time.perf_counter_ns()-t
 alternatives=[]
 for value in PERTURBATIONS:
  t=time.perf_counter_ns();cow=snapshot.fork();cow_fork_ns=time.perf_counter_ns()-t
  t=time.perf_counter_ns();eager=sub.fork_full_copy_experiment();eager_fork_ns=time.perf_counter_ns()-t
  cow_result=run(cow,mt,cs,value);eager_result=run(eager,mt,cs,value)
  alternatives.append({"value":value,"cow_fork_ns":cow_fork_ns,"eager_fork_ns":eager_fork_ns,"cow":cow_result,"eager":eager_result})
 # A later fork checks the retained base and that no candidate contaminated a sibling.
 later=snapshot.fork();later_digest=digest(later);later_states=[float(later.node(c)["attrs"]["state"]) for c in cs]
 return {"n":n,"topology":topology,"replicate":rep,"pid":os.getpid(),"revision":revision,"snapshot":{"id":snapshot.id,"backend":snapshot._measurement_backend,"source_revision":list(snapshot.source_revision)},"capture_ns":capture_ns,"base_digest":base_digest,"primary_digest_after":digest(sub),"base_states":base_states,"later_fork_digest":later_digest,"later_fork_states":later_states,"alternatives":alternatives}
def main():
 if sys.argv[1:]==["--lock"]:LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],int(sys.argv[4])),sort_keys=True));return
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale: "+"; ".join(stale))
 locked=fingerprint()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=locked:raise SystemExit("source lock missing or stale")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));runs=[]
 for n in SIZES:
  for topology in TOPOLOGIES:
   for rep in range(REPS):
    proc=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),topology,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(proc.stdout))
 post=fingerprint();raw={"protocol":"COW_SOLVER_ALTERNATIVES_SCALE_V1","locked_inputs":locked,"post_run_inputs":post,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 summary={"worker_count":len(runs),"all_worker_inputs_stable":locked==post,"raw_workers_path":str(RAW.relative_to(ROOT))};OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True);print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
