#!/usr/bin/env python3
"""Audit matcher work at every clause prefix over independent graph motifs."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
import substrate_rs as sr
from substrate.seed_loader import engine_rules_only
BASE_PATH=ROOT/"evaluation/substrate_capability/can_productive_coactivation_closure_v1.py"
spec=importlib.util.spec_from_file_location("productive_base",BASE_PATH);BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
SEED=ROOT/"seeds/can_native_reimplementation.json";PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_MATCHER_PREFIX_WORK_V1_PREREG_20261001.md"
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/"scripts/analyze_substrate_matcher_prefix_work_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/substrate_matcher_prefix_work_v1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/substrate_matcher_prefix_work_v1_workers_20261001.json"
OUT=ROOT/"evaluation/reports/substrate_matcher_prefix_work_v1_analysis_20261001.json"
PATTERNS=("path4","star4","cycle4");TOPOLOGIES=("path","star","ring");SIZES=(16,32);ORDERS=("authored","reversed");REPS=3;MAX_STEPS=1000
SOURCES=("runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/scale_audit.rs","runners/dsl/src/py.rs","runners/dsl/src/graph.rs","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.build.json")
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 paths=(str(RUNNER.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(BASE_PATH.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(SEED.relative_to(ROOT)),*SOURCES)
 return {"files":{p:sha(ROOT/p) for p in paths},"native_path":str(Path(_native.__file__).resolve()),"native_sha256":sha(_native.__file__),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def pattern(name):
 if name=="path4":return [[f"x{i}","causal_influence",f"x{i+1}"] for i in range(4)]
 if name=="star4":return [["x0","causal_influence",f"x{i}"] for i in range(1,5)]
 if name=="cycle4":return [[f"x{i}","causal_influence",f"x{(i+1)%4}"] for i in range(4)]
 raise ValueError(name)
def graph_edges(n,topology):
 if topology=="path":return [(i,i+1) for i in range(n-1)]
 if topology=="star":return [(0,i) for i in range(1,n)]
 if topology=="ring":return [(i,(i+1)%n) for i in range(n)]
 raise ValueError(topology)
def run_worker(n,topology,pat,order,rep):
 start=fingerprint();seed=json.loads(SEED.read_text());vocab=copy.deepcopy(seed);vocab["rules"]=[];inner=sr.Substrate()._inner;inner.load_seed_manifest(engine_rules_only(vocab))
 concepts=[inner.add_node("Concept",{"name":f"c{i}"}) for i in range(n)]
 for a,b in graph_edges(n,topology):inner.add_edge(concepts[a],"causal_influence",concepts[b],{})
 base=copy.deepcopy(next(r for r in seed["rules"] if r.get("name")=="can_native_hebbian_mint"));edges=pattern(pat)
 if order=="reversed":edges=list(reversed(edges))
 base.update({"name":"matcher_prefix_work_probe","match":edges,"where":None,"effects":[],"match_type":"Concept"})
 inner.import_rules([base]);exported=inner.export_rules();exported=json.loads(exported) if isinstance(exported,str) else exported
 rule=next(r for r in exported if r["name"]=="matcher_prefix_work_probe");installed=[list(e) for e in rule["match"]];active=[r["name"] for r in exported if r.get("active")]
 before,_,_,_=BASE.graph_facts(inner);inner.scale_audit_set_enabled(False);inner.scale_audit_reset();inner.scale_audit_set_per_rule_enabled(True);inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True)
 t=time.perf_counter_ns();progress=int(inner.run_rules(MAX_STEPS));wall=time.perf_counter_ns()-t
 global_counts={str(k):int(v) for k,v in dict(inner.scale_audit_snapshot()).items()};per=[list(x) for x in inner.scale_audit_per_rule_snapshot()];clause=[list(x) for x in inner.scale_audit_match_clause_snapshot()];meta=[list(x) for x in inner.scale_audit_rule_metadata_snapshot()]
 inner.scale_audit_set_enabled(False);inner.scale_audit_set_per_rule_enabled(False);terminal=int(inner.run_rules(1));after,nodes,edges_count,_=BASE.graph_facts(inner);end=fingerprint()
 return {"n":n,"topology":topology,"pattern":pat,"order_input":order,"replicate":rep,"pid":os.getpid(),"start":start,"end":end,"installed_match":installed,"active_rules":active,"progress":progress,"wall_ns":wall,"terminal_progress":terminal,"before_digest":before,"after_digest":after,"nodes":nodes,"edges":edges_count,"graph_edge_count":len(graph_edges(n,topology)),"global":global_counts,"per_rule":per,"clause_candidates":clause,"rule_metadata":meta}
def main():
 if sys.argv[1:]==["--lock"]:LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+"\n");print(LOCK);return
 if len(sys.argv)>1 and sys.argv[1]=="--worker":print(json.dumps(run_worker(int(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5],int(sys.argv[6])),sort_keys=True));return
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale: "+"; ".join(stale))
 lock=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=lock:raise SystemExit("source lock missing or stale")
 env=dict(os.environ);env["PYTHONPATH"]=os.pathsep.join((str(ROOT),str(ROOT/"runners/dsl/python"),env.get("PYTHONPATH","")));runs=[]
 for pat in PATTERNS:
  for topology in TOPOLOGIES:
   for n in SIZES:
    for order in ORDERS:
     for rep in range(REPS):
      p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),topology,pat,order,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=600);r=json.loads(p.stdout);runs.append(r)
      pref="/".join(str(x) for x in [r["global"].get("cand_tested",0),*[v for _,_,v in r["clause_candidates"]]])
      print(f"pattern={pat} graph={topology} N={n} order={order} rep={rep} prefix={pref}",flush=True)
 post=fingerprint();RAW.write_text(json.dumps({"locked_inputs":lock,"post_run_inputs":post,"runs":runs},indent=2,sort_keys=True)+"\n")
 subprocess.run([sys.executable,str(ANALYZER)],cwd=ROOT,env=env,check=True);print(json.dumps({"workers":len(runs),"source_stable":lock==post,"raw":str(RAW.relative_to(ROOT))},indent=2))
if __name__=="__main__":main()
