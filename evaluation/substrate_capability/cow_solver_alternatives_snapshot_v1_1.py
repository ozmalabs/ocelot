#!/usr/bin/env python3
"""Exercise reusable CoW snapshots as an actual native solver-alternative consumer."""
from __future__ import annotations
import hashlib, json, os, random, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as sr
from domains.engine_provenance import build_is_stale, rust_source_fingerprint
from substrate.seed_loader import engine_rules_only
from domains.can_native_orchestration import scoped_settle,native_audit_basin
SEED=ROOT/"seeds/can_native_reimplementation.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/COW_SOLVER_ALTERNATIVES_SNAPSHOT_V1_1_PREREG_20261001.md"
LOCK=ROOT/"evaluation/substrate_capability/cow_solver_alternatives_snapshot_v1_1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/cow_solver_alternatives_snapshot_v1_1_workers_20261001.json"
OUT=ROOT/"evaluation/reports/cow_solver_alternatives_snapshot_v1_1_20261001.json"
ANALYSIS=ROOT/"evaluation/reports/cow_solver_alternatives_snapshot_v1_1_analysis_20261001.json"
RUNNER=Path(__file__).resolve()
SOURCE_PATHS=("domains/can_native_orchestration.py","substrate/seed_loader.py","runners/dsl/src/rewrite.rs","runners/dsl/src/can_ops.rs","runners/dsl/src/graph.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
PERTURBATIONS=(-1.0,-0.25,0.5,1.25)
REPLICATES=5
SEED_BASE=20261001
MAX_STEPS=3000

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 files=(str(RUNNER.relative_to(ROOT)),"scripts/analyze_cow_solver_alternatives_snapshot_v1_1.py",str(PROTOCOL.relative_to(ROOT)),str(SEED.relative_to(ROOT)),*SOURCE_PATHS)
 return {"files":{x:sha(ROOT/x) for x in files},"native_path":str(Path(_native.__file__).resolve()),"native_sha256":sha(Path(_native.__file__).resolve()),"rust_source_fingerprint":rust_source_fingerprint(str(ROOT)),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def digest(sub):
 n=sub._inner
 return hashlib.sha256(json.dumps({"graph":n.graph_to_dict(),"rules":n.export_rules()},sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def fixture(rep):
 rng=random.Random(SEED_BASE+rep*65537)
 sub=sr.Substrate();native=sub._inner;seed_doc=json.loads(SEED.read_text());native.load_seed_manifest(engine_rules_only(seed_doc))
 mt=native.add_node("Microtheory",{"temperature":2.0,"discrete_mode":"3state","can_tick":0})
 concepts=[]
 for i in range(4):
  field=round(rng.uniform(-0.35,0.35),3)
  c=native.add_node("Concept",{"name":f"solver_alt_{i}","state":float((i%3)-1),"external_field":field,"identity_field":0.0})
  concepts.append(c);native.add_edge(mt,"has_concept",c,{})
 for a,b,w in ((0,1,.6),(1,0,.6),(0,2,-.8),(2,0,-.8),(0,3,.4),(3,0,.4)):
  native.add_edge(concepts[a],"causal_influence",concepts[b],{"weight":round(w+rng.uniform(-.1,.1),3)})
 return sub,mt,concepts

def run_arm(branch,mt,concepts,value):
 native=branch._inner
 before=float(native.node(concepts[0])["attrs"].get("external_field",0.0))
 native.set_attr(concepts[0],"external_field",float(value))
 t=time.perf_counter_ns();steps=scoped_settle(native,mt,MAX_STEPS);solve_ns=time.perf_counter_ns()-t
 basin=native_audit_basin(native,mt)
 states={str(int(c.value if hasattr(c,"value") else c)):float(native.node(c)["attrs"].get("state",0.0)) for c in concepts}
 fields={str(int(c.value if hasattr(c,"value") else c)):float(native.node(c)["attrs"].get("external_field",0.0)) for c in concepts}
 return {"pre_perturbation_field":before,"input_field":float(value),"steps":int(steps),"energy":float(basin["energy"]),"frustration":float(basin["frustration"]),"coverage":int(basin["coverage"]),"states":states,"fields":fields,"graph_digest":digest(branch),"solve_ns":solve_ns}

def worker(rep,perturbation):
 sub,mt,concepts=fixture(rep);primary_before=digest(sub);revision=list(sub.experiment_graph_rule_revision());base_states={str(int(c.value)):float(sub.node(c)["attrs"]["state"]) for c in concepts};base_fields={str(int(c.value)):float(sub.node(c)["attrs"]["external_field"]) for c in concepts}
 snapshot=sub._snapshot_with_backend("shared_graph_pages")
 if tuple(snapshot.source_revision)!=tuple(revision):raise RuntimeError("snapshot revision differs from primary")
 # Read-only fork confirms the captured immutable revision before any branch writes.
 probe=snapshot.fork();probe_digest=digest(probe)
 t=time.perf_counter_ns();cow=snapshot.fork();cow_fork_ns=time.perf_counter_ns()-t;cow_initial_digest=digest(cow);cow_result=run_arm(cow,mt,concepts,perturbation)
 t=time.perf_counter_ns();eager=sub.fork_full_copy_experiment();eager_fork_ns=time.perf_counter_ns()-t;eager_initial_digest=digest(eager);eager_result=run_arm(eager,mt,concepts,perturbation)
 sibling=snapshot.fork();sibling_digest=digest(sibling);sibling_fields={str(int(c.value)):float(sibling.node(c)["attrs"]["external_field"]) for c in concepts}
 return {"replicate":rep,"perturbation":float(perturbation),"pid":os.getpid(),"revision":revision,"snapshot":{"id":snapshot.id,"backend":snapshot._measurement_backend,"source_revision":list(snapshot.source_revision)},"primary_digest_before":primary_before,"primary_digest_after":digest(sub),"baseline_states":base_states,"baseline_fields":base_fields,"read_only_probe_digest":probe_digest,"cow_initial_digest":cow_initial_digest,"eager_initial_digest":eager_initial_digest,"cow":cow_result,"eager":eager_result,"cow_fork_ns":cow_fork_ns,"eager_fork_ns":eager_fork_ns,"sibling_digest_after":sibling_digest,"sibling_fields_after":sibling_fields}

def main():
 if sys.argv[1:]==["--lock"]:LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),float(sys.argv[3])),sort_keys=True));return
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale: "+"; ".join(stale))
 locked=fingerprint()
 if not LOCK.exists() or json.loads(LOCK.read_text())!=locked:raise SystemExit("source lock missing or stale")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")))
 started=time.time();runs=[]
 for rep in range(REPLICATES):
  for value in PERTURBATIONS:
   p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(rep),str(value)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
   runs.append(json.loads(p.stdout))
 post=fingerprint();raw={"protocol":"COW_SOLVER_ALTERNATIVES_SNAPSHOT_V1_1","locked_inputs":locked,"post_run_inputs":post,"started_epoch":started,"runs":runs};RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
 summary={"worker_count":len(runs),"all_worker_inputs_stable":locked==post and all(x["snapshot"]["backend"]=="shared_graph_pages" for x in runs),"raw_workers_path":str(RAW.relative_to(ROOT))};OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ROOT/"scripts/analyze_cow_solver_alternatives_snapshot_v1_1.py")],cwd=ROOT,env=env,check=True)
 print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
